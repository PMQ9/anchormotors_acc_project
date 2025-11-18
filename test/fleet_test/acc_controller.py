"""
Adaptive Cruise Control (ACC) Controller - Python Implementation
Based on Anchormotors ACC controller v1.29

This module implements a state-based multimodal ACC controller
that mimics the MATLAB/Simulink implementation.
"""

import numpy as np
from enum import IntEnum
from dataclasses import dataclass
from typing import Tuple


class ACCState(IntEnum):
    """FSM States for ACC Controller"""
    NO_WAVE = 0      # Free driving without lead vehicle
    INTO_WAVE = 1    # Entering traffic
    IN_WAVE = 2      # Following lead vehicle
    OUT_OF_WAVE = 3  # Exiting traffic


@dataclass
class ACCParameters:
    """Tunable parameters for ACC controller"""

    # ROS-style tunable parameters
    no_wave_velo: float = 13.5  # m/s - velocity threshold for "no lead vehicle"
    wave_velo: float = 10.0     # m/s - velocity threshold for "in traffic"
    max_velo: float = 25.0      # m/s - maximum desired velocity

    # Control gains for each state
    # State 0: No Wave
    alpha_no_wave: float = 0.15
    tau_no_wave: float = 2.0
    beta_no_wave: float = 0.424

    # State 1: Into Wave
    alpha_into_wave: float = 0.7
    tau_into_wave: float = 2.4
    beta_into_wave: float = 0.23

    # State 2: In Wave
    alpha_in_wave: float = 0.2
    tau_in_wave: float = 2.5
    beta_in_wave: float = 0.35

    # State 3: Out of Wave
    alpha_out_wave: float = 1.1
    tau_out_wave: float = 2.4
    beta_out_wave: float = 0.24

    # Common parameters
    desired_distance: float = 10.0  # m - desired following distance
    max_accel: float = 1.5          # m/s² - maximum acceleration
    max_decel: float = -3.0         # m/s² - maximum deceleration
    speed_limit: float = 35.0       # m/s - absolute speed limit
    far_distance: float = 200.0     # m - "no lead vehicle" threshold
    close_distance: float = 75.0    # m - force following mode threshold

    # Filter parameters
    filter_coeff: float = 0.65      # Low-pass filter coefficient
    ma_window: int = 10             # Moving average window size
    sample_rate: float = 20.0       # For derivative calculation (assumes 50ms sample time)

    # State transition thresholds
    accel_threshold_neg_high: float = -0.5
    accel_threshold_neg_low: float = -0.25
    accel_threshold_pos_low: float = 0.25
    accel_threshold_pos_high: float = 0.5


class ACCController:
    """
    Adaptive Cruise Control Controller

    Implements a 5-state FSM-based ACC controller with:
    - Moving average filters for sensor smoothing
    - State-dependent control laws
    - Multi-layer safety features
    """

    def __init__(self, params: ACCParameters = None, dt: float = 0.05):
        """
        Initialize ACC controller

        Args:
            params: Controller parameters (uses defaults if None)
            dt: Control loop timestep in seconds (default 50ms = 20Hz)
        """
        self.params = params if params is not None else ACCParameters()
        self.dt = dt

        # State variables
        self.state = ACCState.NO_WAVE
        self.initialized = False

        # Filter buffers
        self.lead_vel_buffer = np.zeros(self.params.ma_window)
        self.lead_accel_buffer = np.zeros(self.params.ma_window)
        self.buffer_idx = 0
        self.buffer_sum_vel = 0.0
        self.buffer_sum_accel = 0.0

        # Delayed values
        self.prev_lead_vel_combined = 0.0
        self.prev_cmd_accel_filtered = 0.0

        # Smoothed values
        self.lead_vel_smooth = 0.0
        self.lead_accel_smooth = 0.0

    def reset(self):
        """Reset controller to initial state"""
        self.state = ACCState.NO_WAVE
        self.initialized = False
        self.lead_vel_buffer.fill(0.0)
        self.lead_accel_buffer.fill(0.0)
        self.buffer_idx = 0
        self.buffer_sum_vel = 0.0
        self.buffer_sum_accel = 0.0
        self.prev_lead_vel_combined = 0.0
        self.prev_cmd_accel_filtered = 0.0
        self.lead_vel_smooth = 0.0
        self.lead_accel_smooth = 0.0

    def _moving_average_update(self, new_val: float, buffer: np.ndarray,
                               buffer_sum: float) -> Tuple[float, float]:
        """
        Update moving average with new value

        Args:
            new_val: New value to add
            buffer: Circular buffer
            buffer_sum: Running sum

        Returns:
            (average, new_sum)
        """
        # Remove oldest value from sum
        old_val = buffer[self.buffer_idx]
        buffer_sum = buffer_sum - old_val + new_val

        # Update buffer
        buffer[self.buffer_idx] = new_val

        # Calculate average
        avg = buffer_sum / self.params.ma_window

        return avg, buffer_sum

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))

    def _update_filters(self, lead_dist: float, rel_vel: float, ego_vel: float):
        """
        Update moving average filters and calculate lead acceleration

        Args:
            lead_dist: Distance to lead vehicle (m)
            rel_vel: Relative velocity (lead - ego) (m/s)
            ego_vel: Ego vehicle velocity (m/s)
        """
        # Calculate lead velocity (combined signal)
        lead_vel_combined = ego_vel + rel_vel

        # Discrete derivative for lead acceleration
        lead_accel_raw = (lead_vel_combined - self.prev_lead_vel_combined) * self.params.sample_rate
        lead_accel_sat = self._clamp(lead_accel_raw, -3.5, 2.0)

        # Update moving averages
        self.lead_vel_smooth, self.buffer_sum_vel = self._moving_average_update(
            lead_vel_combined, self.lead_vel_buffer, self.buffer_sum_vel
        )

        self.lead_accel_smooth, self.buffer_sum_accel = self._moving_average_update(
            lead_accel_sat, self.lead_accel_buffer, self.buffer_sum_accel
        )

        # Update buffer index (circular)
        self.buffer_idx = (self.buffer_idx + 1) % self.params.ma_window

        # Store for next iteration
        self.prev_lead_vel_combined = lead_vel_combined

    def _update_state(self, lead_dist: float):
        """
        Update FSM state based on conditions

        Args:
            lead_dist: Distance to lead vehicle (m)
        """
        # Handle initial state (first call after reset)
        if not self.initialized:
            if self.lead_vel_smooth > self.params.no_wave_velo or lead_dist > 200.0:
                self.state = ACCState.NO_WAVE
            else:
                self.state = ACCState.IN_WAVE
            self.initialized = True
            return

        # State transitions based on current state
        if self.state == ACCState.NO_WAVE:
            # No Wave → Into Wave
            condition1 = (self.lead_accel_smooth < self.params.accel_threshold_neg_high and
                         self.lead_vel_smooth < self.params.no_wave_velo and
                         lead_dist < 200.0)
            condition2 = (self.lead_vel_smooth < self.params.no_wave_velo and
                         lead_dist < self.params.close_distance)

            if condition1 or condition2:
                self.state = ACCState.INTO_WAVE

        elif self.state == ACCState.INTO_WAVE:
            # Into Wave → In Wave
            if self.lead_vel_smooth <= self.params.wave_velo:
                self.state = ACCState.IN_WAVE
            # Into Wave → Out of Wave
            elif self.lead_accel_smooth >= self.params.accel_threshold_pos_low:
                self.state = ACCState.OUT_OF_WAVE
            # Into Wave → No Wave
            elif lead_dist > self.params.far_distance:
                self.state = ACCState.NO_WAVE

        elif self.state == ACCState.IN_WAVE:
            # In Wave → Out of Wave
            if (self.lead_accel_smooth > self.params.accel_threshold_pos_high and
                self.lead_vel_smooth > self.params.wave_velo):
                self.state = ACCState.OUT_OF_WAVE
            # In Wave → No Wave
            elif lead_dist > self.params.far_distance:
                self.state = ACCState.NO_WAVE

        elif self.state == ACCState.OUT_OF_WAVE:
            # Out of Wave → No Wave
            if (self.lead_vel_smooth > self.params.no_wave_velo or
                lead_dist > self.params.far_distance):
                self.state = ACCState.NO_WAVE
            # Out of Wave → Into Wave
            elif self.lead_accel_smooth <= self.params.accel_threshold_neg_low:
                self.state = ACCState.INTO_WAVE

    def _calculate_control(self, lead_dist: float, rel_vel: float, ego_vel: float) -> float:
        """
        Calculate commanded acceleration based on current state

        Args:
            lead_dist: Distance to lead vehicle (m)
            rel_vel: Relative velocity (lead - ego) (m/s)
            ego_vel: Ego vehicle velocity (m/s)

        Returns:
            Commanded acceleration (m/s²)
        """
        if self.state == ACCState.NO_WAVE:
            # Velocity approach controller
            desired_vel = min(self.params.max_velo, 35.0)
            vel_error = desired_vel - ego_vel
            vel_error_sat = self._clamp(vel_error, 0.0, 3.0)
            vel_approach = 0.333 * vel_error_sat
            vel_limiter = min(vel_approach, 1.0)

            # Distance-based acceleration
            distance_accel = (
                (lead_dist - self.params.desired_distance - self.params.tau_no_wave * rel_vel) *
                self.params.alpha_no_wave +
                self.params.beta_no_wave * ego_vel
            )
            distance_accel_sat = self._clamp(distance_accel, self.params.max_decel, self.params.max_accel)

            # Combined output
            cmd_accel = vel_limiter * distance_accel_sat

        elif self.state == ACCState.INTO_WAVE:
            cmd_accel = (
                (lead_dist - self.params.desired_distance - self.params.tau_into_wave * rel_vel) *
                self.params.alpha_into_wave +
                self.params.beta_into_wave * ego_vel
            )

        elif self.state == ACCState.IN_WAVE:
            cmd_accel = (
                (lead_dist - self.params.desired_distance - self.params.tau_in_wave * rel_vel) *
                self.params.alpha_in_wave +
                self.params.beta_in_wave * ego_vel
            )
            cmd_accel = self._clamp(cmd_accel, self.params.max_decel, self.params.max_accel)

        elif self.state == ACCState.OUT_OF_WAVE:
            cmd_accel = (
                (lead_dist - self.params.desired_distance - self.params.tau_out_wave * rel_vel) *
                self.params.alpha_out_wave +
                self.params.beta_out_wave * ego_vel
            )
        else:
            cmd_accel = 0.0

        return cmd_accel

    def _post_process(self, cmd_accel: float, ego_vel: float) -> float:
        """
        Apply post-processing: speed limiter, saturation, filtering

        Args:
            cmd_accel: Raw commanded acceleration (m/s²)
            ego_vel: Ego vehicle velocity (m/s)

        Returns:
            Filtered and saturated acceleration command (m/s²)
        """
        # Step 1: Speed limiter (no acceleration above speed limit)
        if ego_vel >= self.params.speed_limit:
            cmd_accel = min(cmd_accel, 0.0)

        # Step 2: Hard saturation
        cmd_accel = self._clamp(cmd_accel, self.params.max_decel, self.params.max_accel)

        # Step 3: Low-pass filter (anti-jerk)
        cmd_accel_filtered = (
            self.prev_cmd_accel_filtered +
            self.params.filter_coeff * (cmd_accel - self.prev_cmd_accel_filtered)
        )

        # Step 4: Final saturation
        cmd_accel_filtered = self._clamp(cmd_accel_filtered, self.params.max_decel, self.params.max_accel)

        # Store for next iteration
        self.prev_cmd_accel_filtered = cmd_accel_filtered

        return cmd_accel_filtered

    def step(self, lead_dist: float, rel_vel: float, ego_vel: float) -> Tuple[float, ACCState]:
        """
        Execute one control step

        Args:
            lead_dist: Distance to lead vehicle (m)
            rel_vel: Relative velocity (lead - ego) (m/s)
            ego_vel: Ego vehicle velocity (m/s)

        Returns:
            (cmd_accel, state): Commanded acceleration and current FSM state
        """
        # Update filters
        self._update_filters(lead_dist, rel_vel, ego_vel)

        # Update state machine
        self._update_state(lead_dist)

        # Calculate control based on state
        cmd_accel = self._calculate_control(lead_dist, rel_vel, ego_vel)

        # Post-processing
        cmd_accel_final = self._post_process(cmd_accel, ego_vel)

        return cmd_accel_final, self.state


if __name__ == "__main__":
    """Simple test of ACC controller"""
    import matplotlib.pyplot as plt

    # Create controller
    controller = ACCController()

    # Test scenario: approaching slower lead vehicle
    dt = 0.05  # 50ms timestep
    duration = 20.0  # 20 seconds
    steps = int(duration / dt)

    # Initial conditions
    ego_vel = 25.0  # m/s
    lead_vel = 15.0  # m/s
    lead_dist = 100.0  # m

    # Storage
    time = np.zeros(steps)
    ego_vels = np.zeros(steps)
    lead_vels = np.zeros(steps)
    distances = np.zeros(steps)
    accels = np.zeros(steps)
    states = np.zeros(steps)

    # Simulation loop
    for i in range(steps):
        time[i] = i * dt

        # Calculate relative velocity
        rel_vel = lead_vel - ego_vel

        # Get control command
        cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)

        # Store results
        ego_vels[i] = ego_vel
        lead_vels[i] = lead_vel
        distances[i] = lead_dist
        accels[i] = cmd_accel
        states[i] = state

        # Update ego vehicle (simple integration)
        ego_vel = max(0, ego_vel + cmd_accel * dt)

        # Update distance (relative motion)
        lead_dist = lead_dist + rel_vel * dt

    # Plot results
    fig, axes = plt.subplots(4, 1, figsize=(10, 10))

    axes[0].plot(time, distances)
    axes[0].set_ylabel('Distance (m)')
    axes[0].grid(True)
    axes[0].set_title('ACC Controller Test: Approaching Slower Lead Vehicle')

    axes[1].plot(time, ego_vels, label='Ego')
    axes[1].plot(time, lead_vels, label='Lead')
    axes[1].set_ylabel('Velocity (m/s)')
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(time, accels)
    axes[2].set_ylabel('Acceleration (m/s²)')
    axes[2].grid(True)

    axes[3].plot(time, states)
    axes[3].set_ylabel('State')
    axes[3].set_xlabel('Time (s)')
    axes[3].set_yticks([0, 1, 2, 3])
    axes[3].set_yticklabels(['No Wave', 'Into Wave', 'In Wave', 'Out of Wave'])
    axes[3].grid(True)

    plt.tight_layout()
    plt.savefig('test/fleet_test/acc_test.png', dpi=150)
    print("Test plot saved to test/fleet_test/acc_test.png")
    plt.show()
