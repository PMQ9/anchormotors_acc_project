"""
Fleet Test for ACC Controller

Tests different penetration rates of ACC-equipped vehicles in a platoon.
Compares ACC behavior against human driver model.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from acc_controller import ACCController, ACCParameters, ACCState
from typing import List, Tuple
import os
from typing import List, Tuple, Dict, Callable
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime


class HumanDriver:
    """
    Simple human driver model using Intelligent Driver Model (IDM)

    This provides a baseline comparison for ACC performance.
    """

    def __init__(self, desired_velocity: float = 25.0,
                 time_headway: float = 1.5,
                 min_spacing: float = 5.0,
                 max_accel: float = 1.0,
                 comfortable_decel: float = 2.0,
                 accel_exponent: float = 4.0):
        """
        Initialize human driver model

        Args:
            desired_velocity: Desired free-flow velocity (m/s)
            time_headway: Desired time headway (s)
            min_spacing: Minimum spacing (m)
            max_accel: Maximum acceleration (m/s²)
            comfortable_decel: Comfortable deceleration (m/s²)
            accel_exponent: Acceleration exponent (typically 4)
        """
        self.v0 = desired_velocity
        self.T = time_headway
        self.s0 = min_spacing
        self.a = max_accel
        self.b = comfortable_decel
        self.delta = accel_exponent

        # Add some reaction delay
        self.reaction_time = 0.2  # 200ms delay
        self.delay_buffer = []

    def step(self, lead_dist: float, rel_vel: float, ego_vel: float, dt: float) -> float:
        """
        Calculate acceleration using IDM

        Args:
            lead_dist: Distance to lead vehicle (m)
            rel_vel: Relative velocity (lead - ego) (m/s)
            ego_vel: Current velocity (m/s)
            dt: Timestep (s)

        Returns:
            Commanded acceleration (m/s²)
        """
        # IDM equation
        # a = a_max * [1 - (v/v0)^delta - (s*/s)^2]
        # where s* = s0 + v*T + v*Δv / (2*sqrt(a*b))

        # Free-flow acceleration
        if ego_vel < 0.01:
            ego_vel = 0.01  # Avoid division by zero

        free_accel = 1.0 - (ego_vel / self.v0) ** self.delta

        # Interaction term
        approach_rate = -rel_vel  # Negative rel_vel means approaching
        s_star = self.s0 + ego_vel * self.T + (ego_vel * approach_rate) / (2 * np.sqrt(self.a * self.b))

        if lead_dist < 1.0:
            lead_dist = 1.0  # Avoid division by zero

        interaction_term = (s_star / lead_dist) ** 2

        # Combined acceleration
        accel = self.a * (free_accel - interaction_term)

        # Clamp to reasonable limits
        accel = max(-3.0, min(1.5, accel))

        # Add reaction delay
        self.delay_buffer.append(accel)
        delay_steps = int(self.reaction_time / dt)
        if len(self.delay_buffer) > delay_steps:
            accel = self.delay_buffer.pop(0)
        else:
            accel = 0.0

        return accel


class Vehicle:
    """Represents a single vehicle in the fleet"""

    def __init__(self, vehicle_id: int, is_acc: bool, initial_position: float,
                 initial_velocity: float, dt: float = 0.05,
                 acc_params: ACCParameters = None):
        """
        Initialize vehicle

        Args:
            vehicle_id: Unique vehicle identifier
            is_acc: True if ACC-equipped, False for human driver
            initial_position: Initial position (m)
            initial_velocity: Initial velocity (m/s)
            dt: Simulation timestep (s)
            acc_params: ACC parameters (if ACC-equipped)
        """
        self.id = vehicle_id
        self.is_acc = is_acc
        self.position = initial_position
        self.velocity = initial_velocity
        self.acceleration = 0.0
        self.dt = dt

        # Initialize controller or driver model
        if is_acc:
            self.controller = ACCController(params=acc_params, dt=dt)
            self.state = ACCState.NO_WAVE
        else:
            self.driver = HumanDriver()
            self.state = -1  # Human drivers don't have ACC states

    def update(self, lead_vehicle=None):
        """
        Update vehicle state for one timestep

        Args:
            lead_vehicle: Lead vehicle object (None if no lead vehicle)
        """
        if lead_vehicle is None:
            # No lead vehicle - cruise at desired speed
            desired_speed = 25.0
            self.acceleration = 0.5 * (desired_speed - self.velocity)
            self.acceleration = max(-3.0, min(1.5, self.acceleration))
        else:
            # Calculate spacing and relative velocity
            lead_dist = lead_vehicle.position - self.position
            rel_vel = lead_vehicle.velocity - self.velocity

            # Get acceleration command
            if self.is_acc:
                self.acceleration, self.state = self.controller.step(lead_dist, rel_vel, self.velocity)
            else:
                self.acceleration = self.driver.step(lead_dist, rel_vel, self.velocity, self.dt)

        # Update velocity and position
        self.velocity = max(0.0, self.velocity + self.acceleration * self.dt)
        self.position = self.position + self.velocity * self.dt


class FleetSimulation:
    """Simulates a fleet of vehicles with mixed ACC penetration"""

    def __init__(self, n_vehicles: int, penetration_rate: float,
                 dt: float = 0.05, duration: float = 100.0,
                 acc_params: ACCParameters = None):
        """
        Initialize fleet simulation

        Args:
            n_vehicles: Number of vehicles in fleet
            penetration_rate: Fraction of ACC-equipped vehicles (0.0 to 1.0)
            dt: Simulation timestep (s)
            duration: Simulation duration (s)
            acc_params: ACC parameters for ACC-equipped vehicles
        """
        self.n_vehicles = n_vehicles
        self.penetration_rate = penetration_rate
        self.dt = dt
        self.duration = duration
        self.steps = int(duration / dt)
        self.acc_params = acc_params if acc_params is not None else ACCParameters()

        # Initialize vehicles
        self.vehicles = []
        self._initialize_vehicles()

        # Data storage
        self.time = np.zeros(self.steps)
        self.positions = np.zeros((self.steps, n_vehicles))
        self.velocities = np.zeros((self.steps, n_vehicles))
        self.accelerations = np.zeros((self.steps, n_vehicles))
        self.space_gaps = np.zeros((self.steps, n_vehicles))
        self.states = np.zeros((self.steps, n_vehicles))

    def _initialize_vehicles(self):
        """Initialize vehicle fleet with random ACC distribution"""
        # Determine which vehicles have ACC
        n_acc_vehicles = int(self.n_vehicles * self.penetration_rate)
        acc_indices = np.random.choice(self.n_vehicles, size=n_acc_vehicles, replace=False)

        # Create vehicles with equilibrium spacing
        # Equilibrium gap = desired_distance + time_headway * velocity
        # Using tau=2.5s (In Wave), v=20m/s: gap = 10 + 2.5*20 = 60m
        initial_velocity = 20.0
        initial_spacing = 10.0 + 2.5 * initial_velocity  # ~60m equilibrium spacing

        for i in range(self.n_vehicles):
            is_acc = i in acc_indices
            position = i * initial_spacing
            vehicle = Vehicle(
                vehicle_id=i,
                is_acc=is_acc,
                initial_position=position,
                initial_velocity=initial_velocity,
                dt=self.dt,
                acc_params=self.acc_params
            )
            self.vehicles.append(vehicle)

    def run(self, lead_vehicle_profile=None):
        """
        Run simulation

        Args:
            lead_vehicle_profile: Function that returns lead vehicle velocity at time t
                                  If None, lead vehicle maintains constant speed
        """
        # Lead vehicle starts one spacing interval ahead of the last vehicle
        initial_velocity = 20.0
        initial_spacing = 10.0 + 2.5 * initial_velocity  # Match initialization spacing
        lead_position = self.n_vehicles * initial_spacing
        lead_velocity = 20.0

        for step in range(self.steps):
            t = step * self.dt
            self.time[step] = t

            # Update lead vehicle
            if lead_vehicle_profile is not None:
                lead_velocity = lead_vehicle_profile(t)

            lead_position += lead_velocity * self.dt

            # Update all vehicles (from front to back)
            for i in range(self.n_vehicles - 1, -1, -1):
                # Get lead vehicle for this vehicle
                if i == self.n_vehicles - 1:
                    # Last vehicle follows the lead vehicle
                    lead_veh = type('obj', (object,), {
                        'position': lead_position,
                        'velocity': lead_velocity
                    })()
                else:
                    # Follow vehicle ahead in platoon
                    lead_veh = self.vehicles[i + 1]

                # Update vehicle
                self.vehicles[i].update(lead_veh)

                # Store data
                self.positions[step, i] = self.vehicles[i].position
                self.velocities[step, i] = self.vehicles[i].velocity
                self.accelerations[step, i] = self.vehicles[i].acceleration
                self.states[step, i] = self.vehicles[i].state

                # Calculate space gap
                if i == self.n_vehicles - 1:
                    self.space_gaps[step, i] = lead_position - self.vehicles[i].position
                else:
                    self.space_gaps[step, i] = self.vehicles[i + 1].position - self.vehicles[i].position

    def plot_results(self, filename: str = None):
        """
        Create comprehensive visualization of fleet behavior

        Args:
            filename: Filename to save plot (if None, just display)
        """
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(5, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Color scheme: ACC vehicles in blue, human in red
        colors = ['blue' if v.is_acc else 'red' for v in self.vehicles]
        labels = [f'V{i} (ACC)' if v.is_acc else f'V{i} (Human)'
                  for i, v in enumerate(self.vehicles)]

        # 1. Position vs Time
        ax1 = fig.add_subplot(gs[0, :])
        for i in range(self.n_vehicles):
            ax1.plot(self.time, self.positions[:, i], color=colors[i], alpha=0.7, linewidth=1.5)
        ax1.set_ylabel('Position (m)', fontsize=12)
        ax1.set_title(f'Fleet Simulation - {self.penetration_rate*100:.0f}% ACC Penetration Rate ({self.n_vehicles} vehicles)',
                     fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        # Only show legend if <= 10 vehicles, otherwise just show color code
        if self.n_vehicles <= 10:
            ax1.legend(labels, ncol=min(self.n_vehicles, 6), fontsize=8)
        else:
            # Create simple legend for color coding only
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor='blue', label='ACC vehicles'),
                             Patch(facecolor='red', label='Human drivers')]
            ax1.legend(handles=legend_elements, fontsize=10)

        # 2. Space Gap vs Time
        ax2 = fig.add_subplot(gs[1, :])
        for i in range(self.n_vehicles):
            ax2.plot(self.time, self.space_gaps[:, i], color=colors[i], alpha=0.7, linewidth=1.5)
        ax2.axhline(y=10.0, color='green', linestyle='--', label='Desired gap (10m)', linewidth=2)
        ax2.axhline(y=5.0, color='orange', linestyle='--', label='Min safe gap (5m)', linewidth=2)
        ax2.set_ylabel('Space Gap (m)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=8)

        # 3. Velocity vs Time
        ax3 = fig.add_subplot(gs[2, :])
        for i in range(self.n_vehicles):
            ax3.plot(self.time, self.velocities[:, i], color=colors[i], alpha=0.7, linewidth=1.5)
        ax3.set_ylabel('Velocity (m/s)', fontsize=12)
        ax3.grid(True, alpha=0.3)

        # 4. Acceleration vs Time
        ax4 = fig.add_subplot(gs[3, :])
        for i in range(self.n_vehicles):
            ax4.plot(self.time, self.accelerations[:, i], color=colors[i], alpha=0.7, linewidth=1.5)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.axhline(y=1.5, color='red', linestyle='--', label='Max accel', linewidth=1)
        ax4.axhline(y=-3.0, color='red', linestyle='--', label='Max decel', linewidth=1)
        ax4.set_ylabel('Acceleration (m/s²)', fontsize=12)
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=8)

        # 5. ACC States (only for ACC vehicles)
        ax5 = fig.add_subplot(gs[4, 0])
        acc_indices = [i for i, v in enumerate(self.vehicles) if v.is_acc]
        if acc_indices:
            for i in acc_indices:
                ax5.plot(self.time, self.states[:, i], label=f'V{i}', linewidth=1.5, alpha=0.7)
            ax5.set_ylabel('ACC State', fontsize=12)
            ax5.set_xlabel('Time (s)', fontsize=12)
            ax5.set_yticks([0, 1, 2, 3])
            ax5.set_yticklabels(['No Wave', 'Into Wave', 'In Wave', 'Out Wave'], fontsize=9)
            ax5.grid(True, alpha=0.3)
            # Only show legend if <= 8 ACC vehicles
            if len(acc_indices) <= 8:
                ax5.legend(fontsize=8, ncol=2)
            ax5.set_title(f'ACC Vehicle States ({len(acc_indices)} vehicles)', fontsize=12)
        else:
            ax5.text(0.5, 0.5, 'No ACC vehicles', ha='center', va='center', fontsize=14)
            ax5.set_xlabel('Time (s)', fontsize=12)

        # 6. Statistics Summary
        ax6 = fig.add_subplot(gs[4, 1])
        ax6.axis('off')

        # Calculate statistics
        min_gaps = np.min(self.space_gaps, axis=0)
        mean_gaps = np.mean(self.space_gaps, axis=0)
        max_accels = np.max(np.abs(self.accelerations), axis=0)
        mean_vels = np.mean(self.velocities, axis=0)

        stats_text = f"Fleet Statistics:\n"
        stats_text += f"{'='*40}\n"
        stats_text += f"Penetration Rate: {self.penetration_rate*100:.1f}%\n"
        stats_text += f"Number of Vehicles: {self.n_vehicles}\n"
        stats_text += f"ACC Vehicles: {sum(1 for v in self.vehicles if v.is_acc)}\n"
        stats_text += f"Human Vehicles: {sum(1 for v in self.vehicles if not v.is_acc)}\n\n"

        stats_text += f"Space Gaps:\n"
        stats_text += f"  Min: {np.min(min_gaps):.2f} m\n"
        stats_text += f"  Mean: {np.mean(mean_gaps):.2f} m\n"
        stats_text += f"  Max: {np.max(mean_gaps):.2f} m\n\n"

        stats_text += f"Velocities:\n"
        stats_text += f"  Min: {np.min(self.velocities):.2f} m/s\n"
        stats_text += f"  Mean: {np.mean(mean_vels):.2f} m/s\n"
        stats_text += f"  Max: {np.max(self.velocities):.2f} m/s\n\n"

        stats_text += f"Accelerations:\n"
        stats_text += f"  Max Accel: {np.max(self.accelerations):.2f} m/s²\n"
        stats_text += f"  Max Decel: {np.min(self.accelerations):.2f} m/s²\n"

        ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"  -> Plot saved to {filename}")
        else:
            print("  WARNING: No filename provided, plot not saved")

        plt.close(fig)  # Close figure to free memory

    def calculate_metrics(self) -> dict:
        """
        Calculate performance metrics for the fleet

        Returns:
            Dictionary of metrics
        """
        metrics = {
            'min_space_gap': np.min(self.space_gaps),
            'mean_space_gap': np.mean(self.space_gaps),
            'std_space_gap': np.std(self.space_gaps),
            'max_decel': np.min(self.accelerations),
            'max_accel': np.max(self.accelerations),
            'mean_velocity': np.mean(self.velocities),
            'velocity_std': np.std(self.velocities),
            'num_close_calls': np.sum(self.space_gaps < 5.0),  # Gaps below 5m
            'string_stability': self._calculate_string_stability()
        }
        return metrics

    def _calculate_string_stability(self) -> float:
        """
        Calculate string stability metric

        String stability: ratio of velocity variance at end vs beginning
        < 1.0 means stable (disturbances attenuate)
        > 1.0 means unstable (disturbances amplify)
        """
        # Use last 20% vs first 20% of simulation
        n_start = int(0.2 * self.steps)
        n_end = int(0.2 * self.steps)

        var_start = np.var(self.velocities[:n_start, :])
        var_end = np.var(self.velocities[-n_end:, :])

        if var_start < 1e-6:
            return 1.0
        return var_end / var_start


# ============================================================================
# Lead Vehicle Profile Functions for Different Test Scenarios
# ============================================================================

def constant_speed_profile(speed: float):
    """Create a constant speed profile"""
    return lambda t: speed

def oscillating_profile(base_speed: float, amplitude: float, period: float):
    """Create an oscillating speed profile"""
    return lambda t: base_speed + amplitude * np.sin(2 * np.pi * t / period)

def sudden_acceleration_profile(initial_speed: float, final_speed: float, accel_time: float):
    """Create a profile with sudden acceleration at t=20s"""
    def profile(t):
        if t < 20.0:
            return initial_speed
        elif t < 20.0 + accel_time:
            # Linear acceleration
            progress = (t - 20.0) / accel_time
            return initial_speed + (final_speed - initial_speed) * progress
        else:
            return final_speed
    return profile

def sudden_deceleration_profile(initial_speed: float, final_speed: float, decel_time: float):
    """Create a profile with sudden deceleration at t=20s"""
    def profile(t):
        if t < 20.0:
            return initial_speed
        elif t < 20.0 + decel_time:
            # Linear deceleration
            progress = (t - 20.0) / decel_time
            return initial_speed + (final_speed - initial_speed) * progress
        else:
            return final_speed
    return profile

def step_change_profile(speeds: List[float], step_duration: float):
    """Create a profile with step changes in velocity"""
    def profile(t):
        step_index = int(t / step_duration) % len(speeds)
        return speeds[step_index]
    return profile

def multi_oscillation_profile(base_speed: float):
    """Create a complex profile with multiple oscillation frequencies"""
    def profile(t):
        # Combine multiple frequencies for complex behavior
        slow_osc = 3.0 * np.sin(2 * np.pi * t / 40.0)  # 40s period
        fast_osc = 2.0 * np.sin(2 * np.pi * t / 10.0)  # 10s period
        return base_speed + slow_osc + fast_osc
    return profile


def compare_penetration_rates(n_vehicles: int = 8,
                              penetration_rates: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0],
                              duration: float = 100.0,
                              lead_vehicle_profile=None,
                              scenario_name: str = "scenario"):
    """
    Compare fleet behavior at different ACC penetration rates

    Args:
        n_vehicles: Number of vehicles in fleet
        penetration_rates: List of penetration rates to test
        duration: Simulation duration (s)
        lead_vehicle_profile: Lead vehicle velocity profile function
    """
    results = {}

    # Create output directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)

    # Run simulations for each penetration rate
    for rate in penetration_rates:
        print(f"\n{'='*60}")
        print(f"Running simulation with {rate*100:.0f}% ACC penetration...")
        print(f"{'='*60}")

        sim = FleetSimulation(
            n_vehicles=n_vehicles,
            penetration_rate=rate,
            duration=duration
        )

        sim.run(lead_vehicle_profile=lead_vehicle_profile)

        # Plot results
        filename = f"{output_dir}/{scenario_name}_penetration_{int(rate*100):03d}.png"
        sim.plot_results(filename=filename)

        # Calculate metrics
        metrics = sim.calculate_metrics()
        results[rate] = metrics

        print(f"\nMetrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")

    # Create comparison plot
    _plot_comparison(results, output_dir, scenario_name)

    return results


def _plot_comparison(results: dict, output_dir: str, scenario_name: str = "scenario"):
    """Create comparison plots across penetration rates"""

    rates = sorted(results.keys())
    metrics_to_plot = ['min_space_gap', 'mean_space_gap', 'max_decel',
                      'velocity_std', 'string_stability']

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for idx, metric in enumerate(metrics_to_plot):
        values = [results[r][metric] for r in rates]
        axes[idx].plot([r*100 for r in rates], values, 'o-', linewidth=2, markersize=8)
        axes[idx].set_xlabel('ACC Penetration Rate (%)', fontsize=11)
        axes[idx].set_ylabel(metric.replace('_', ' ').title(), fontsize=11)
        axes[idx].grid(True, alpha=0.3)
        axes[idx].set_xticks([r*100 for r in rates])

    # Summary text
    axes[5].axis('off')
    summary = "Penetration Rate Comparison\n" + "="*40 + "\n\n"
    summary += "Key Observations:\n\n"

    # Get min and max penetration rates
    min_rate = min(rates)
    max_rate = max(rates)

    # String stability comparison
    stability_min = results[min_rate]['string_stability']
    stability_max = results[max_rate]['string_stability']
    summary += f"String Stability:\n"
    summary += f"  {min_rate*100:.0f}% ACC: {stability_min:.3f}\n"
    summary += f"  {max_rate*100:.0f}% ACC: {stability_max:.3f}\n"
    if stability_max < stability_min:
        summary += f"  -> {((stability_min-stability_max)/stability_min*100):.1f}% improvement\n\n"
    else:
        summary += f"  -> {((stability_max-stability_min)/stability_min*100):.1f}% degradation\n\n"

    # Safety comparison
    gap_min = results[min_rate]['min_space_gap']
    gap_max = results[max_rate]['min_space_gap']
    summary += f"Minimum Space Gap:\n"
    summary += f"  {min_rate*100:.0f}% ACC: {gap_min:.2f} m\n"
    summary += f"  {max_rate*100:.0f}% ACC: {gap_max:.2f} m\n\n"

    axes[5].text(0.1, 0.9, summary, transform=axes[5].transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.suptitle('ACC Penetration Rate Impact on Fleet Performance', fontsize=14, fontweight='bold')
    plt.tight_layout()

    filename = f"{output_dir}/{scenario_name}_comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"  -> Comparison plot saved to {filename}")
    plt.close()  # Close figure to free memory


def generate_pdf_report(output_dir: str, scenarios: Dict[str, dict]):
    """
    Generate a comprehensive PDF report with all test results

    Args:
        output_dir: Directory containing the result plots
        scenarios: Dictionary mapping scenario names to their descriptions
    """
    pdf_filename = f"{output_dir}/fleet_test_comprehensive_report.pdf"

    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=1  # Center
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Title page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("Fleet Test Comprehensive Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_text = """
    This report presents comprehensive fleet test results for the Anchormotors ACC (Adaptive Cruise Control) system.
    The tests evaluate fleet behavior under various scenarios including different lead vehicle speeds,
    oscillations, sudden accelerations/decelerations, and state changes. Each scenario is tested across
    multiple ACC penetration rates to understand the impact of ACC-equipped vehicles on overall fleet performance.
    """
    story.append(Paragraph(summary_text, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))

    # Test Configuration
    story.append(Paragraph("Test Configuration", heading_style))
    config_data = [
        ['Parameter', 'Value'],
        ['Number of Vehicles', '25'],
        ['Simulation Duration', '100 seconds'],
        ['Time Step', '0.05 seconds'],
        ['Penetration Rates Tested', '5%, 10%, 20%, 50%, 75%, 100%'],
        ['Initial Velocity', '20 m/s'],
        ['Initial Spacing', '~60 m (equilibrium)']
    ]
    config_table = Table(config_data, colWidths=[3*inch, 3*inch])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(config_table)
    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("Test Scenarios", heading_style))
    story.append(Spacer(1, 0.2*inch))

    toc_data = [['#', 'Scenario Name', 'Description']]
    for idx, (scenario_name, scenario_info) in enumerate(scenarios.items(), 1):
        toc_data.append([str(idx), scenario_name, scenario_info['description']])

    toc_table = Table(toc_data, colWidths=[0.5*inch, 2*inch, 4*inch])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # Add each scenario's results
    for idx, (scenario_name, scenario_info) in enumerate(scenarios.items(), 1):
        # Scenario header
        story.append(Paragraph(f"Scenario {idx}: {scenario_name}", heading_style))
        story.append(Paragraph(f"<i>{scenario_info['description']}</i>", styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))

        # Add comparison plot first (summary)
        comparison_file = f"{output_dir}/{scenario_name}_comparison.png"
        if os.path.exists(comparison_file):
            img = Image(comparison_file, width=7*inch, height=4.67*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))

        # Add detailed plots for each penetration rate
        story.append(Paragraph(f"Detailed Results by Penetration Rate",
                              ParagraphStyle('SubHeading', parent=styles['Heading3'],
                                           fontSize=13, spaceAfter=10)))

        penetration_rates = [5, 10, 20, 50, 75, 100]
        for rate in penetration_rates:
            detail_file = f"{output_dir}/{scenario_name}_penetration_{rate:03d}.png"
            if os.path.exists(detail_file):
                story.append(PageBreak())
                story.append(Paragraph(f"{rate}% ACC Penetration",
                                      ParagraphStyle('RateHeading', parent=styles['Heading4'],
                                                   fontSize=12, spaceAfter=8)))
                img = Image(detail_file, width=7*inch, height=5.25*inch)
                story.append(img)

        story.append(PageBreak())

    # Build PDF
    doc.build(story)
    print(f"\n{'='*70}")
    print(f"PDF Report Generated: {pdf_filename}")
    print(f"{'='*70}\n")

    return pdf_filename


if __name__ == "__main__":
    """Run fleet test with various scenarios"""

    # Configuration
    N_VEHICLES = 25
    PENETRATION_RATES = [0.05, 0.10, 0.20, 0.50, 0.75, 1.0]
    DURATION = 100.0

    print("\n" + "="*70)
    print("FLEET TEST CONFIGURATION")
    print("="*70)
    print(f"Vehicles: {N_VEHICLES}")
    print(f"Penetration rates: {[f'{r*100:.0f}%' for r in PENETRATION_RATES]}")
    print(f"Initial velocity: 20 m/s")
    print(f"Initial spacing: ~60 m (equilibrium for In Wave state)")
    print("="*70)

    # Scenario 1: Lead vehicle maintains constant speed
    print("\n" + "="*70)
    print(f"SCENARIO 1: Constant Lead Vehicle Speed ({N_VEHICLES} vehicles)")
    print("="*70)
    print(f"Testing penetration rates: {[f'{r*100:.0f}%' for r in PENETRATION_RATES]}")

    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=lambda t: 20.0  # Constant 20 m/s
    )

    # Scenario 2: Lead vehicle with speed oscillations
    print("\n" + "="*70)
    print(f"SCENARIO 2: Oscillating Lead Vehicle Speed ({N_VEHICLES} vehicles)")
    print("="*70)
    print(f"Testing penetration rates: {[f'{r*100:.0f}%' for r in PENETRATION_RATES]}")

    def oscillating_profile(t):
        """Lead vehicle oscillates between 15-25 m/s"""
        return 20.0 + 5.0 * np.sin(2 * np.pi * t / 20.0)

    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=oscillating_profile
    )

    print("\n" + "="*70)
    print("Fleet test completed! Check test/fleet_test/results/ for output plots.")
    print("="*70)
