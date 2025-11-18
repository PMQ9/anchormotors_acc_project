"""
Quick runner for 25-vehicle fleet test at specific penetration rates

Tests: 5%, 10%, 20%, 50%, 75%, 100% ACC penetration
"""

import numpy as np
from fleet_test import compare_penetration_rates


def main():
    """Run 25-vehicle fleet test with specified penetration rates"""

    # Configuration
    N_VEHICLES = 25
    PENETRATION_RATES = [0.05, 0.10, 0.20, 0.50, 0.75, 1.0]
    DURATION = 100.0  # seconds

    print("\n" + "="*80)
    print("25-VEHICLE FLEET TEST")
    print("="*80)
    print(f"Number of vehicles: {N_VEHICLES}")
    print(f"Penetration rates: {[f'{r*100:.0f}%' for r in PENETRATION_RATES]}")
    print(f"Simulation duration: {DURATION} seconds")
    print("="*80 + "\n")

    # Scenario 1: Constant speed lead vehicle
    print("\n" + "="*80)
    print("SCENARIO 1: Constant Lead Vehicle Speed (20 m/s)")
    print("="*80)

    results_constant = compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=lambda t: 20.0
    )

    # Scenario 2: Oscillating lead vehicle
    print("\n" + "="*80)
    print("SCENARIO 2: Oscillating Lead Vehicle Speed (15-25 m/s)")
    print("="*80)

    def oscillating_profile(t):
        """Lead vehicle oscillates between 15-25 m/s with 20s period"""
        return 20.0 + 5.0 * np.sin(2 * np.pi * t / 20.0)

    results_oscillating = compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=oscillating_profile
    )

    # Print summary comparison
    print("\n" + "="*80)
    print("SUMMARY: String Stability Comparison")
    print("="*80)
    print(f"{'Penetration':<15} {'Constant Lead':<20} {'Oscillating Lead':<20}")
    print("-"*80)

    for rate in PENETRATION_RATES:
        const_stability = results_constant[rate]['string_stability']
        osc_stability = results_oscillating[rate]['string_stability']
        print(f"{rate*100:>5.0f}%          {const_stability:>15.4f}     {osc_stability:>19.4f}")

    print("\n" + "="*80)
    print("SUMMARY: Minimum Space Gap Comparison (Safety)")
    print("="*80)
    print(f"{'Penetration':<15} {'Constant Lead':<20} {'Oscillating Lead':<20}")
    print("-"*80)

    for rate in PENETRATION_RATES:
        const_gap = results_constant[rate]['min_space_gap']
        osc_gap = results_oscillating[rate]['min_space_gap']
        print(f"{rate*100:>5.0f}%          {const_gap:>12.2f} m     {osc_gap:>16.2f} m")

    print("\n" + "="*80)
    print("Test completed successfully!")
    print("Check test/fleet_test/results/ for detailed plots")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
