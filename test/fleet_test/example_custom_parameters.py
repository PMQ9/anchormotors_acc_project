"""
Example: Customizing ACC Parameters

This script demonstrates how to tune ACC parameters for different behaviors.
"""

import numpy as np
import matplotlib.pyplot as plt
from acc_controller import ACCController, ACCParameters
from fleet_test import FleetSimulation
import os


def compare_parameter_sets():
    """Compare different parameter configurations"""

    # Define three parameter sets
    configs = {
        'Default': ACCParameters(),

        'Conservative': ACCParameters(
            # Lower speed limits
            max_velo=20.0,
            # Gentler acceleration limits
            max_accel=1.0,
            max_decel=-2.0,
            # Longer time headways
            tau_no_wave=2.5,
            tau_into_wave=3.0,
            tau_in_wave=3.0,
            tau_out_wave=3.0,
            # Lower gains for smoother control
            alpha_in_wave=0.15,
            alpha_into_wave=0.5,
            # More filtering
            filter_coeff=0.4
        ),

        'Aggressive': ACCParameters(
            # Higher speed limits
            max_velo=30.0,
            # Shorter time headways
            tau_no_wave=1.5,
            tau_into_wave=1.8,
            tau_in_wave=2.0,
            tau_out_wave=1.8,
            # Higher gains for faster response
            alpha_in_wave=0.3,
            alpha_into_wave=0.9,
            alpha_out_wave=1.3,
            # Less filtering
            filter_coeff=0.8
        )
    }

    # Test scenario: approaching slower traffic
    dt = 0.05
    duration = 40.0
    steps = int(duration / dt)

    results = {}

    for name, params in configs.items():
        print(f"\nTesting {name} configuration...")

        controller = ACCController(params=params, dt=dt)

        # Initial conditions
        ego_vel = 25.0
        lead_vel = 15.0
        lead_dist = 100.0

        # Storage
        time = np.arange(steps) * dt
        ego_vels = np.zeros(steps)
        distances = np.zeros(steps)
        accels = np.zeros(steps)
        jerks = np.zeros(steps - 1)

        for i in range(steps):
            rel_vel = lead_vel - ego_vel
            cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)

            ego_vels[i] = ego_vel
            distances[i] = lead_dist
            accels[i] = cmd_accel

            # Calculate jerk
            if i > 0:
                jerks[i-1] = (cmd_accel - accels[i-1]) / dt

            # Update
            ego_vel = max(0, ego_vel + cmd_accel * dt)
            lead_dist = lead_dist + rel_vel * dt

        results[name] = {
            'time': time,
            'ego_vels': ego_vels,
            'distances': distances,
            'accels': accels,
            'jerks': jerks,
            'max_jerk': np.max(np.abs(jerks)),
            'max_decel': np.min(accels),
            'settling_time': _calculate_settling_time(ego_vels, lead_vel)
        }

        print(f"  Max jerk: {results[name]['max_jerk']:.2f} m/s³")
        print(f"  Max decel: {results[name]['max_decel']:.2f} m/s²")
        print(f"  Settling time: {results[name]['settling_time']:.1f} s")

    # Plot comparison
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))

    colors = {'Default': 'blue', 'Conservative': 'green', 'Aggressive': 'red'}

    for name, data in results.items():
        axes[0].plot(data['time'], data['distances'], label=name,
                    color=colors[name], linewidth=2)
        axes[1].plot(data['time'], data['ego_vels'], label=name,
                    color=colors[name], linewidth=2)
        axes[2].plot(data['time'], data['accels'], label=name,
                    color=colors[name], linewidth=2)
        axes[3].plot(data['time'][:-1], data['jerks'], label=name,
                    color=colors[name], linewidth=2)

    axes[0].axhline(y=10, color='gray', linestyle='--', label='Desired gap')
    axes[0].set_ylabel('Distance (m)', fontsize=11)
    axes[0].set_title('ACC Parameter Comparison: Approaching Slower Traffic', fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].axhline(y=15, color='gray', linestyle='--', label='Lead velocity')
    axes[1].set_ylabel('Velocity (m/s)', fontsize=11)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    axes[2].axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    axes[2].set_ylabel('Acceleration (m/s²)', fontsize=11)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    axes[3].axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    axes[3].set_ylabel('Jerk (m/s³)', fontsize=11)
    axes[3].set_xlabel('Time (s)', fontsize=11)
    axes[3].grid(True, alpha=0.3)
    axes[3].legend()

    plt.tight_layout()

    os.makedirs('test/fleet_test/results', exist_ok=True)
    filename = 'test/fleet_test/results/parameter_comparison.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to {filename}")

    plt.show()


def _calculate_settling_time(velocities, target_velocity, threshold=0.5):
    """Calculate time to settle within threshold of target"""
    for i, v in enumerate(velocities):
        if abs(v - target_velocity) <= threshold:
            # Check if it stays settled
            if all(abs(velocities[i:i+20]) - target_velocity < threshold):
                return i * 0.05  # Convert to seconds
    return len(velocities) * 0.05


def fleet_comparison_conservative_vs_aggressive():
    """Compare conservative vs aggressive parameters in fleet simulation"""

    print("\n" + "="*70)
    print("Fleet Test: Conservative vs Aggressive Parameters")
    print("="*70)

    # Lead vehicle with oscillations
    def oscillating_lead(t):
        return 20.0 + 3.0 * np.sin(2 * np.pi * t / 15.0)

    # Conservative fleet
    print("\nRunning conservative fleet...")
    conservative_params = ACCParameters(
        max_velo=20.0,
        tau_in_wave=3.0,
        alpha_in_wave=0.15,
        filter_coeff=0.4
    )

    sim_conservative = FleetSimulation(
        n_vehicles=6,
        penetration_rate=1.0,  # All ACC
        duration=80.0,
        acc_params=conservative_params
    )
    sim_conservative.run(lead_vehicle_profile=oscillating_lead)

    # Aggressive fleet
    print("Running aggressive fleet...")
    aggressive_params = ACCParameters(
        max_velo=30.0,
        tau_in_wave=2.0,
        alpha_in_wave=0.3,
        filter_coeff=0.8
    )

    sim_aggressive = FleetSimulation(
        n_vehicles=6,
        penetration_rate=1.0,  # All ACC
        duration=80.0,
        acc_params=aggressive_params
    )
    sim_aggressive.run(lead_vehicle_profile=oscillating_lead)

    # Compare metrics
    metrics_conservative = sim_conservative.calculate_metrics()
    metrics_aggressive = sim_aggressive.calculate_metrics()

    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    print(f"{'Metric':<25} {'Conservative':>15} {'Aggressive':>15} {'Difference':>15}")
    print("-"*70)

    for key in metrics_conservative.keys():
        cons_val = metrics_conservative[key]
        agg_val = metrics_aggressive[key]
        diff = agg_val - cons_val
        diff_pct = (diff / cons_val * 100) if abs(cons_val) > 1e-6 else 0

        print(f"{key:<25} {cons_val:>15.3f} {agg_val:>15.3f} {diff_pct:>14.1f}%")

    # Plot both
    sim_conservative.plot_results('test/fleet_test/results/fleet_conservative.png')
    sim_aggressive.plot_results('test/fleet_test/results/fleet_aggressive.png')

    print("\n✓ Fleet comparison complete!")


def demonstrate_tuning_effects():
    """Show the effect of individual parameter changes"""

    print("\n" + "="*70)
    print("Demonstrating Individual Parameter Effects")
    print("="*70)

    # Base parameters
    base_params = ACCParameters()

    # Test different time headways
    print("\n1. Effect of Time Headway (tau_in_wave)")
    print("-" * 50)

    dt = 0.05
    duration = 30.0
    steps = int(duration / dt)
    time = np.arange(steps) * dt

    tau_values = [1.5, 2.0, 2.5, 3.0]
    results = {}

    for tau in tau_values:
        params = ACCParameters()
        params.tau_in_wave = tau
        controller = ACCController(params=params, dt=dt)

        ego_vel = 20.0
        lead_vel = 15.0
        lead_dist = 80.0

        distances = np.zeros(steps)

        for i in range(steps):
            rel_vel = lead_vel - ego_vel
            cmd_accel, _ = controller.step(lead_dist, rel_vel, ego_vel)

            distances[i] = lead_dist
            ego_vel = max(0, ego_vel + cmd_accel * dt)
            lead_dist = lead_dist + rel_vel * dt

        final_gap = distances[-1]
        results[tau] = distances

        print(f"  tau = {tau:.1f}s → Final gap = {final_gap:.1f} m")

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    for tau, distances in results.items():
        ax.plot(time, distances, label=f'τ = {tau:.1f}s', linewidth=2)

    ax.axhline(y=10, color='gray', linestyle='--', label='Desired (10m)')
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_ylabel('Distance to Lead (m)', fontsize=11)
    ax.set_title('Effect of Time Headway Parameter', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()

    filename = 'test/fleet_test/results/tau_effect.png'
    plt.savefig(filename, dpi=150)
    print(f"Plot saved to {filename}\n")
    plt.show()


if __name__ == "__main__":
    # Example 1: Compare parameter sets
    print("="*70)
    print("EXAMPLE 1: Parameter Set Comparison")
    print("="*70)
    compare_parameter_sets()

    # Example 2: Fleet-level comparison
    print("\n" + "="*70)
    print("EXAMPLE 2: Fleet-Level Comparison")
    print("="*70)
    fleet_comparison_conservative_vs_aggressive()

    # Example 3: Individual parameter effects
    print("\n" + "="*70)
    print("EXAMPLE 3: Individual Parameter Effects")
    print("="*70)
    demonstrate_tuning_effects()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("Check test/fleet_test/results/ for output plots")
    print("="*70 + "\n")
