from enum import Enum
from scipy.interpolate import CubicSpline
import numpy as np
from scipy.interpolate import interp1d
import math

class Mode(Enum):
    INITIAL = -1
    NO_WAVE = 0
    INTO_WAVE = 1
    IN_WAVE = 2
    OUT_OF_WAVE = 3

class Controller:
    def command_acceleration(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        raise NotImplementedError("Subclass must implement abstract method")

class IntelligentDriverModel(Controller):
    def command_acceleration(self, ego_velocity, space_gap, relative_velocity,
                             max_velocity=35.0, no_wave_velocity=13.5,
                             wave_velocity=10.0, time_step=0.1):
        # IDM parameters
        v0 = max_velocity

        T = 1.5

        s0 = 5.0

        a = 1.0

        b = 2.0

        delta = 4.0

        # Prevent invalid or dangerous inputs
        ego_velocity = max(0.0, ego_velocity)                 # no backward speed
        space_gap = max(0.1, space_gap)                      # prevent division by zero
        rel = -relative_velocity

        # Safe sqrt
        ab = max(1e-6, a * b)

        # Desired dynamic gap
        s_star = s0 + max(0.0, ego_velocity * T + (ego_velocity * rel) / (2 * math.sqrt(ab)))

        # IDM acceleration
        try:
            dv_dt = a * (1 - (ego_velocity / v0)**delta - (s_star / space_gap)**2)
        except OverflowError:
            dv_dt = -5.0   # strong brake fallback

        # Clamp acceleration to vehicle capability
        return max(-3.0, min(1.5, dv_dt))

class OurController(Controller):
    def __init__(self):
        self.cmd_accel_history = [0]
        self.lead_velocity_history = []
        self.lead_velocity_derivative_history = []
        self.modes_history = []
        self.mode = Mode.INITIAL

    def classification(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        lead_velocity = ego_velocity + relative_velocity
        self.lead_velocity_history.append(lead_velocity)

        lead_velocity_derivative = 0
        if len(self.lead_velocity_history) > 1:
            lead_velocity_derivative = (
                self.lead_velocity_history[-1] - self.lead_velocity_history[-2]
            ) / time_step
        else:
            lead_velocity_derivative = 0


        lead_velocity_derivative = max(min(2.0, lead_velocity_derivative), -3.5)
        self.lead_velocity_derivative_history.append(lead_velocity_derivative)
        
        lead_velocity_moving_average = sum(self.lead_velocity_history[-10:]) / len(self.lead_velocity_history[-10:])

        lead_acceleration_moving_average = sum(self.lead_velocity_derivative_history[-10:]) / len(self.lead_velocity_derivative_history[-10:])

        new_mode = self.mode

        if self.mode == Mode.INITIAL:
            if lead_velocity > no_wave_velocity or space_gap > 200:
                new_mode = Mode.NO_WAVE
            elif lead_velocity <= no_wave_velocity and space_gap <= 200:
                new_mode = Mode.IN_WAVE
        elif self.mode == Mode.NO_WAVE:
            if (lead_acceleration_moving_average < -0.5 and lead_velocity < no_wave_velocity and space_gap < 200) or (lead_velocity < no_wave_velocity and space_gap < 75):
                new_mode = Mode.INTO_WAVE
        elif self.mode == Mode.INTO_WAVE:
            if lead_velocity_moving_average <= wave_velocity:
                new_mode = Mode.IN_WAVE
            elif lead_acceleration_moving_average >= 0.25:
                new_mode = Mode.OUT_OF_WAVE
            elif space_gap > 200:
                new_mode = Mode.NO_WAVE
        elif self.mode == Mode.IN_WAVE:
            if lead_acceleration_moving_average > 0.5 and lead_velocity > wave_velocity:
                new_mode = Mode.OUT_OF_WAVE
            elif space_gap > 200:
                new_mode = Mode.NO_WAVE
        elif self.mode == Mode.OUT_OF_WAVE:
            if lead_velocity_moving_average > no_wave_velocity:
                new_mode = Mode.NO_WAVE
            elif lead_acceleration_moving_average <= -0.25:
                new_mode = Mode.INTO_WAVE
            elif space_gap > 200:
                new_mode = Mode.NO_WAVE

        self.mode = new_mode
        return new_mode

    def no_wave(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        cmd_accel = 0

        max_velo = min(35, max_velocity)

        soft_velocity_a = min(1, (1/3) * min(3, max(0, max_velo - ego_velocity)))

        alpha = 0.15

        s_min = 10
        
        tau = 2.0

        beta = 0.424

        soft_velocity_b = min(1.5, max(-3, alpha * (space_gap - s_min - (ego_velocity * tau)) + (beta * relative_velocity)))

        cmd_accel = min(1.5, max(-3, soft_velocity_a * soft_velocity_b))

        return cmd_accel

    def into_wave(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        cmd_accel = 0

        alpha = 0.7
        tau = 2.4

        s_min = 10
        k = 0.23

        cmd_accel = alpha * (space_gap - s_min - tau * ego_velocity) + k * relative_velocity

        return cmd_accel

    def in_wave(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        cmd_accel = 0

        alpha = 0.2

        tau = 2.5

        s_min = 10.0

        beta = 0.35

        cmd_accel = alpha * (space_gap - s_min - (ego_velocity * tau)) + (relative_velocity * beta)

        cmd_accel = min(1.5, max(-3.0, cmd_accel))

        return cmd_accel

    def out_of_wave(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        cmd_accel = 0

        alpha = 1.1

        tau = 2.4

        s_min = 10.0

        k = 0.24

        cmd_accel = alpha * (space_gap - s_min - (tau * ego_velocity)) + (k * relative_velocity)

        return cmd_accel

    def command_acceleration(self, ego_velocity, space_gap, relative_velocity, max_velocity = 35.0, no_wave_velocity = 13.5, wave_velocity = 10.0, time_step = 0.1):
        mode = self.classification(ego_velocity, space_gap, relative_velocity, max_velocity, no_wave_velocity, wave_velocity, time_step)

        self.modes_history.append(mode)

        cmd_accel = 0
        cmd_accel_target = 0

        if mode == Mode.NO_WAVE:
            cmd_accel_target = self.no_wave(ego_velocity, space_gap, relative_velocity, max_velocity, no_wave_velocity, wave_velocity, time_step)
        elif mode == Mode.INTO_WAVE:
            cmd_accel_target = self.into_wave(ego_velocity, space_gap, relative_velocity, max_velocity, no_wave_velocity, wave_velocity, time_step)
        elif mode == Mode.IN_WAVE:
            cmd_accel_target = self.in_wave(ego_velocity, space_gap, relative_velocity, max_velocity, no_wave_velocity, wave_velocity, time_step)
        elif mode == Mode.OUT_OF_WAVE:
            cmd_accel_target = self.out_of_wave(ego_velocity, space_gap, relative_velocity, max_velocity, no_wave_velocity, wave_velocity, time_step)

        cmd_accel_target = max(-3.0, min(1.5, cmd_accel_target))

        if ego_velocity >= 35:
            cmd_accel_target = min(cmd_accel_target, 0.0)

        accel_t_minus_one = self.cmd_accel_history[-1]

        beta = 0.65

        cmd_accel = beta * (cmd_accel_target - accel_t_minus_one) + accel_t_minus_one

        self.cmd_accel_history.append(cmd_accel)

        cmd_accel = max(-3.0, min(1.5, cmd_accel))

        return cmd_accel

class TrajectoryFollower(Controller):
    """Follow a NGSIM trajectory using cubic splines with internal position tracking."""

    def __init__(self, time_vector, position_vector):  
        """  
        Args:  
            time_vector: array of time stamps in seconds  
            position_vector: array of positions in meters  
        """  
        self.time_vector = np.array(time_vector)  
        self.position_vector = np.array(position_vector)  

        # cubic spline for position  
        self.pos_spline = CubicSpline(self.time_vector, self.position_vector, extrapolate=True)  

        # derivatives for velocity and acceleration  
        self.vel_spline = self.pos_spline.derivative()  
        self.acc_spline = self.vel_spline.derivative()  

        # track internal ego position  
        self.ego_position = self.pos_spline(self.time_vector[0])  
        self.last_time = self.time_vector[0]  

    def command_acceleration(self, ego_velocity, space_gap, relative_velocity,  
                            max_velocity=35.0, no_wave_velocity=13.5,  
                            wave_velocity=10.0, time_step=0.1):  
        """  
        PD + feedforward controller to track trajectory.  
        """  
        t = self.last_time  
        self.last_time += time_step  

        # reference values from spline  
        x_ref = float(self.pos_spline(t))  
        v_ref = float(self.vel_spline(t))  
        a_ref = float(self.acc_spline(t))  

        # PD control on position and velocity errors  
        k_p = 0.8  # increase gain for more aggressive tracking  
        k_d = 0.5  

        pos_error = x_ref - self.ego_position  
        vel_error = v_ref - ego_velocity  

        # total acceleration command: feedforward + PD  
        accel = a_ref + k_p * pos_error + k_d * vel_error  

        # update internal position estimate  
        self.ego_position += ego_velocity * time_step  

        # clip to realistic vehicle limits  
        accel = np.clip(accel, -3.0, 1.5)  

        return accel  