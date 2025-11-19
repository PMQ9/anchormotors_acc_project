from __future__ import annotations
from controller import Controller

class Car:
    def __init__(self, controller, v0, x0, lead_car, max_velocity):
        # --- State variables (single values) ---
        self.position = x0
        self.velocity = v0
        self.lead_car = lead_car
        self.max_velocity = max_velocity
        self.controller = controller

        # --- History arrays ---
        self.positions = [x0]
        self.velocities = [v0]
        self.cmd_accels = []
        self.space_gaps = []
        self.relative_velocities = []

        # Initialize gap + rel_vel
        if lead_car is not None:
            gap = lead_car.position - x0
            rel_vel = lead_car.velocity - v0
        else:
            gap = float('inf')
            rel_vel = 0.0

        self.current_gap = gap
        self.current_rel_vel = rel_vel

        self.space_gaps.append(gap)
        self.relative_velocities.append(rel_vel)

    # ------------------------------------------------------------
    # 1. Compute acceleration (using PREVIOUS timestep values)
    # ------------------------------------------------------------
    def compute_acceleration(self):
        """Compute commanded acceleration based on current state."""

        if self.lead_car is None:
            gap = float('inf')
            rel_vel = 0.0
        else:
            gap = self.lead_car.position - self.position
            rel_vel = self.lead_car.velocity - self.velocity

        self.current_gap = gap
        self.current_rel_vel = rel_vel

        accel = self.controller.command_acceleration(
            self.velocity,
            space_gap=gap,
            relative_velocity=rel_vel,
            max_velocity=self.max_velocity
        )

        return accel

    # ------------------------------------------------------------
    # 2. Apply simultaneous update (Euler integration)
    # ------------------------------------------------------------
    def apply_update(self, accel, dt):
        """Update velocity and position from the supplied acceleration."""

        # v(t+dt)
        self.velocity += accel * dt
        self.velocity = max(self.velocity, 0)

        # x(t+dt)
        self.position += self.velocity * dt

    # ------------------------------------------------------------
    # 3. Record history after all updates are complete
    # ------------------------------------------------------------
    def record_history(self, accel):
        self.positions.append(self.position)
        self.velocities.append(self.velocity)
        self.cmd_accels.append(accel)
        self.space_gaps.append(self.current_gap)
        self.relative_velocities.append(self.current_rel_vel)
