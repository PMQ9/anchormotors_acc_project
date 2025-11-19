import numpy as np
import random
import matplotlib.pyplot as plt
from controller import OurController, IntelligentDriverModel, Controller
from car import Car

class Simulation:
    def __init__(self,
                 lead_car: Controller,
                 n_cars: int,
                 percentage: float,
                 dt: float,
                 total_time: float,
                 initial_spacing: float,
                 initial_speed: float,
                 max_velocity: float = 35.0,
                 random_seed: int = 42):

        self.n_cars = n_cars
        self.dt = dt
        self.percentage = percentage

        # Leader uses the provided controller
        self.lead_car = Car(
            controller=lead_car,
            v0=initial_speed,
            x0=0.0,
            lead_car=None,
            max_velocity=max_velocity,
        )
        self.cars = [self.lead_car]

        # Create controllers for followers
        self.controllers = []
        random.seed(random_seed)

        n_followers = n_cars - 1
        n_our = int(percentage * n_followers)

        choices = [True] * n_our + [False] * (n_followers - n_our)
        random.shuffle(choices)

        for use_our in choices:
            if use_our:
                self.controllers.append(OurController())
            else:
                self.controllers.append(IntelligentDriverModel())

        # Create follower cars
        for i in range(n_followers):
            x0 = -(i+1) * initial_spacing
            car = Car(
                controller=self.controllers[i],
                v0=initial_speed,
                x0=x0,
                lead_car=self.cars[i],
                max_velocity=max_velocity,
            )
            self.cars.append(car)



        n_steps = int(total_time / dt)

        for step in range(n_steps):

            # --- 1. Compute accelerations for all cars (using old states) ---
            accels = []
            for i in range(n_cars):
                accels.append(self.cars[i].compute_acceleration())

            # --- 2. Apply updates simultaneously ---
            for i in range(n_cars):
                self.cars[i].apply_update(accels[i], dt)

            # --- 3. Record histories ---
            for i in range(n_cars):
                self.cars[i].record_history(accels[i])


        self.positions = [car.positions for car in self.cars]
        self.velocities = [car.velocities for car in self.cars]
        self.accelerations = [car.cmd_accels for car in self.cars]
        self.gaps = [car.space_gaps for car in self.cars]
        self.cmd_accels = [car.cmd_accels for car in self.cars]

    def plot_space_gaps(self):
        gaps = np.array(self.gaps)
        t = np.arange(gaps.shape[1]) * self.dt

        plt.figure(figsize=(12,6))

        # Track which categories we've already added for legend
        legend_added = {"Leader": False, "OurController": False, "IDM": False}

        for i in range(self.n_cars):
            car = self.cars[i]

            if i == 0:
                color = "black"
                label = "Leader" if not legend_added["Leader"] else None
                legend_added["Leader"] = True
            elif isinstance(car.controller, OurController):
                color = "red"
                label = "OurController" if not legend_added["OurController"] else None
                legend_added["OurController"] = True
            else:
                color = "blue"
                label = "IDM" if not legend_added["IDM"] else None
                legend_added["IDM"] = True

            plt.plot(t, gaps[i], color=color, label=label)

        plt.xlabel("Time (s)")
        plt.ylabel("Space Gap (m)")
        plt.title(f"Space Gaps for All Cars, {self.percentage}%")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_positions(self):
        positions = np.array(self.positions)
        t = np.arange(positions.shape[1]) * self.dt

        plt.figure(figsize=(12,6))

        # Track which categories we've already added for legend
        legend_added = {"Leader": False, "OurController": False, "IDM": False}

        for i in range(self.n_cars):
            car = self.cars[i]

            if i == 0:
                color = "black"
                label = "Leader" if not legend_added["Leader"] else None
                legend_added["Leader"] = True
            elif isinstance(car.controller, OurController):
                color = "red"
                label = "OurController" if not legend_added["OurController"] else None
                legend_added["OurController"] = True
            else:
                color = "blue"
                label = "IDM" if not legend_added["IDM"] else None
                legend_added["IDM"] = True

            plt.plot(t, positions[i], color=color, label=label)

        plt.xlabel("Time (s)")
        plt.ylabel("Position (m)")
        plt.title(f"Position for All Cars, {self.percentage}%")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_velocities(self):
        velocities = np.array(self.velocities)
        t = np.arange(velocities.shape[1]) * self.dt

        plt.figure(figsize=(12,6))
        legend_added = {"Leader": False, "OurController": False, "IDM": False}

        for i in range(self.n_cars):
            car = self.cars[i]

            if i == 0:
                color = "black"
                label = "Leader" if not legend_added["Leader"] else None
                legend_added["Leader"] = True
            elif isinstance(car.controller, OurController):
                color = "red"
                label = "OurController" if not legend_added["OurController"] else None
                legend_added["OurController"] = True
            else:
                color = "blue"
                label = "IDM" if not legend_added["IDM"] else None
                legend_added["IDM"] = True

            plt.plot(t, velocities[i], color=color, label=label)

        plt.xlabel("Time (s)")
        plt.ylabel("Velocity (m/s)")
        plt.title(f"Velocities for All Cars, {self.percentage}%")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_accelerations(self):
        accelerations = np.array(self.accelerations)
        t = np.arange(accelerations.shape[1]) * self.dt

        plt.figure(figsize=(12,6))
        legend_added = {"Leader": False, "OurController": False, "IDM": False}

        for i in range(self.n_cars):
            car = self.cars[i]

            if i == 0:
                color = "black"
                label = "Leader" if not legend_added["Leader"] else None
                legend_added["Leader"] = True
            elif isinstance(car.controller, OurController):
                color = "red"
                label = "OurController" if not legend_added["OurController"] else None
                legend_added["OurController"] = True
            else:
                color = "blue"
                label = "IDM" if not legend_added["IDM"] else None
                legend_added["IDM"] = True

            plt.plot(t, accelerations[i], color=color, label=label)

        plt.xlabel("Time (s)")
        plt.ylabel("Velocity (m/s^2)")
        plt.title(f"Accelerations for All Cars, {self.percentage}%")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_relative_velocities(self):
        velocities = np.array(self.velocities)
        t = np.arange(velocities.shape[1]) * self.dt

        plt.figure(figsize=(12,6))
        legend_added = {"OurController": False, "IDM": False}

        for i in range(1, self.n_cars):
            follower = self.cars[i]

            if isinstance(follower.controller, OurController):
                color = "red"
                label = "OurController" if not legend_added["OurController"] else None
                legend_added["OurController"] = True
            else:
                color = "blue"
                label = "IDM" if not legend_added["IDM"] else None
                legend_added["IDM"] = True

            rel_vel = velocities[i-1] - velocities[i]
            plt.plot(t, rel_vel, color=color, label=label)

        plt.xlabel("Time (s)")
        plt.ylabel("Relative Velocity (m/s)")
        plt.title(f"Relative Velocities for All Car Pairs, {self.percentage}%")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()



    def plot_modes(self):
        DT = self.dt
        t = np.arange(len(self.cars[0].positions)) * DT  # time vector

        plt.figure(figsize=(12, 5))

        for i, car in enumerate(self.cars):
            if isinstance(car.controller, OurController):
                modes = [mode.value for mode in car.controller.modes_history]

                # Plot on same axes
                plt.step(t[:len(modes)], modes, where='post', label=f'Car {i}')

        plt.ylim(-1.5, 3.5)
        plt.yticks(
            [-1, 0, 1, 2, 3],
            ['INITIAL', 'NO_WAVE', 'INTO_WAVE', 'IN_WAVE', 'OUT_OF_WAVE']
        )
        plt.xlabel('Time (s)')
        plt.ylabel('Mode')
        plt.title(f'Controller Mode over Time — All Cars Using OurController, {self.percentage}%')
        plt.grid(True)
        plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.0))  # keeps plot clean
        plt.tight_layout()
        plt.show()

    def plot_speed_boxplot(self):
        """
        Plot a boxplot of each car's speed on one plot, color-coded by controller type.
        """
        speeds_all = [np.array(car.velocities) for car in self.cars]
        colors = []

        for i, car in enumerate(self.cars):
            if i == 0:
                colors.append("black")           # leader
            elif isinstance(car.controller, OurController):
                colors.append("red")             # our controller
            else:
                colors.append("blue")            # IDM

        plt.figure(figsize=(14,6))
        box = plt.boxplot(speeds_all, patch_artist=True, positions=range(self.n_cars))

        # Color each box
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        # Color medians
        for median, color in zip(box['medians'], colors):
            median.set_color("black")

        plt.xlabel("Car Index")
        plt.ylabel("Speed (m/s)")
        plt.title(f"Speed Distribution per Car, {self.percentage}%")
        plt.grid(True, axis='y')
        plt.xticks(range(self.n_cars), [str(i) for i in range(self.n_cars)])
        plt.tight_layout()
        plt.show()

    def compute_metrics(self, hard_brake_threshold=-3.0):
        """
        Compute key metrics for the simulation.

        Returns:
            dict containing:
                - max_jerk_per_car: list of max jerks
                - string_stability: max deviation of space gaps from desired spacing
                - num_crashes: total number of cars that crash (space_gap <= 0)
                - first_crash_index: index of the first car that crashes
                - hard_brake_times: list of total time each car spent braking hard
        """
        max_jerk_per_car = []
        hard_brake_times = []
        num_crashes = 0
        first_crash_index = None

        string_stability = 0  # could define as max deviation of spacing from initial spacing

        for i, car in enumerate(self.cars):
            # Convert to numpy arrays for convenience
            accels = np.array(car.cmd_accels)
            positions = np.array(car.positions)
            gaps = np.array(car.space_gaps)

            # --- Max jerk ---
            jerk = np.diff(accels) / self.dt
            max_jerk = np.max(np.abs(jerk))
            max_jerk_per_car.append(max_jerk)

            # --- Hard brake time ---
            hard_brake_time = np.sum(accels <= hard_brake_threshold) * self.dt
            hard_brake_times.append(hard_brake_time)

            # --- Crashes ---
            if np.any(gaps <= 0):
                num_crashes += 1
                if first_crash_index is None:
                    first_crash_index = i

            # --- String stability ---
            if i > 0:  # only followers
                desired_gap = positions[0] - positions[i]  # or initial spacing
                max_deviation = np.max(np.abs(gaps - desired_gap))
                string_stability = max(string_stability, max_deviation)

        metrics = {
            "max_jerk_per_car": max_jerk_per_car,
            "string_stability": string_stability,
            "num_crashes": num_crashes,
            "first_crash_index": first_crash_index,
            "hard_brake_times": hard_brake_times
        }

        return metrics
