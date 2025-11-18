"""
Full Fleet Test Suite for ACC Controller

Comprehensive test suite that runs multiple scenarios:
1. Different constant speeds
2. Different oscillation patterns
3. Sudden acceleration
4. Sudden deceleration
5. Step changes in velocity (state oscillations)
6. Complex multi-frequency oscillations

Generates a comprehensive PDF report with all results.
"""

import os
import sys
from fleet_test import (
    compare_penetration_rates,
    generate_pdf_report,
    constant_speed_profile,
    oscillating_profile,
    sudden_acceleration_profile,
    sudden_deceleration_profile,
    step_change_profile,
    multi_oscillation_profile
)


def run_all_scenarios():
    """Run all fleet test scenarios and generate comprehensive report"""

    # Configuration
    N_VEHICLES = 25
    PENETRATION_RATES = [0.05, 0.10, 0.20, 0.50, 0.75, 1.0]
    DURATION = 100.0

    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)

    # Dictionary to store scenario information for PDF report
    scenarios = {}

    print("\n" + "="*80)
    print(" "*20 + "COMPREHENSIVE FLEET TEST SUITE")
    print("="*80)
    print(f"Configuration:")
    print(f"  - Number of Vehicles: {N_VEHICLES}")
    print(f"  - Penetration Rates: {[f'{r*100:.0f}%' for r in PENETRATION_RATES]}")
    print(f"  - Simulation Duration: {DURATION}s")
    print(f"  - Output Directory: {output_dir}")
    print("="*80 + "\n")

    # ========================================================================
    # SCENARIO 1: Different Constant Speeds
    # ========================================================================
    print("\n" + "="*80)
    print("SCENARIO 1: Lead Vehicle at Different Constant Speeds")
    print("="*80)
    print("Testing how the fleet responds to different lead vehicle speeds")
    print("-"*80)

    # 1a. Slow constant speed (15 m/s)
    scenario_name = "01a_constant_slow"
    scenarios[scenario_name] = {
        'description': 'Lead vehicle maintains constant slow speed (15 m/s)'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=constant_speed_profile(15.0),
        scenario_name=scenario_name
    )

    # 1b. Medium constant speed (20 m/s) - baseline
    scenario_name = "01b_constant_medium"
    scenarios[scenario_name] = {
        'description': 'Lead vehicle maintains constant medium speed (20 m/s) - baseline'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=constant_speed_profile(20.0),
        scenario_name=scenario_name
    )

    # 1c. Fast constant speed (25 m/s)
    scenario_name = "01c_constant_fast"
    scenarios[scenario_name] = {
        'description': 'Lead vehicle maintains constant fast speed (25 m/s)'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=constant_speed_profile(25.0),
        scenario_name=scenario_name
    )

    # ========================================================================
    # SCENARIO 2: Different Oscillation Patterns
    # ========================================================================
    print("\n" + "="*80)
    print("SCENARIO 2: Lead Vehicle Oscillations (Different Patterns)")
    print("="*80)
    print("Testing fleet response to various oscillation frequencies and amplitudes")
    print("-"*80)

    # 2a. Small amplitude, slow oscillation
    scenario_name = "02a_oscillation_small_slow"
    scenarios[scenario_name] = {
        'description': 'Small amplitude (±2 m/s), slow period (30s) oscillation around 20 m/s'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=oscillating_profile(base_speed=20.0, amplitude=2.0, period=30.0),
        scenario_name=scenario_name
    )

    # 2b. Medium amplitude, medium oscillation
    scenario_name = "02b_oscillation_medium"
    scenarios[scenario_name] = {
        'description': 'Medium amplitude (±5 m/s), medium period (20s) oscillation around 20 m/s'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=oscillating_profile(base_speed=20.0, amplitude=5.0, period=20.0),
        scenario_name=scenario_name
    )

    # 2c. Large amplitude, fast oscillation
    scenario_name = "02c_oscillation_large_fast"
    scenarios[scenario_name] = {
        'description': 'Large amplitude (±7 m/s), fast period (10s) oscillation around 20 m/s'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=oscillating_profile(base_speed=20.0, amplitude=7.0, period=10.0),
        scenario_name=scenario_name
    )

    # 2d. Multi-frequency oscillation (complex pattern)
    scenario_name = "02d_oscillation_multi_frequency"
    scenarios[scenario_name] = {
        'description': 'Complex multi-frequency oscillation combining slow (40s) and fast (10s) periods'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=multi_oscillation_profile(base_speed=20.0),
        scenario_name=scenario_name
    )

    # ========================================================================
    # SCENARIO 3: Sudden Acceleration
    # ========================================================================
    print("\n" + "="*80)
    print("SCENARIO 3: Sudden Acceleration")
    print("="*80)
    print("Testing fleet response to sudden speed increases")
    print("-"*80)

    # 3a. Gradual acceleration
    scenario_name = "03a_sudden_accel_gradual"
    scenarios[scenario_name] = {
        'description': 'Gradual acceleration from 15 m/s to 25 m/s over 5 seconds (at t=20s)'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=sudden_acceleration_profile(initial_speed=15.0, final_speed=25.0, accel_time=5.0),
        scenario_name=scenario_name
    )

    # 3b. Rapid acceleration
    scenario_name = "03b_sudden_accel_rapid"
    scenarios[scenario_name] = {
        'description': 'Rapid acceleration from 15 m/s to 25 m/s over 2 seconds (at t=20s)'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=sudden_acceleration_profile(initial_speed=15.0, final_speed=25.0, accel_time=2.0),
        scenario_name=scenario_name
    )

    # ========================================================================
    # SCENARIO 4: Sudden Deceleration
    # ========================================================================
    print("\n" + "="*80)
    print("SCENARIO 4: Sudden Deceleration")
    print("="*80)
    print("Testing fleet response to sudden speed decreases (critical safety scenario)")
    print("-"*80)

    # 4a. Gradual deceleration
    scenario_name = "04a_sudden_decel_gradual"
    scenarios[scenario_name] = {
        'description': 'Gradual deceleration from 25 m/s to 15 m/s over 5 seconds (at t=20s)'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=sudden_deceleration_profile(initial_speed=25.0, final_speed=15.0, decel_time=5.0),
        scenario_name=scenario_name
    )

    # 4b. Rapid deceleration (emergency braking scenario)
    scenario_name = "04b_sudden_decel_rapid"
    scenarios[scenario_name] = {
        'description': 'Rapid deceleration from 25 m/s to 15 m/s over 2 seconds (at t=20s) - emergency braking'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=sudden_deceleration_profile(initial_speed=25.0, final_speed=15.0, decel_time=2.0),
        scenario_name=scenario_name
    )

    # 4c. Severe emergency braking
    scenario_name = "04c_sudden_decel_severe"
    scenarios[scenario_name] = {
        'description': 'Severe deceleration from 25 m/s to 10 m/s over 3 seconds (at t=20s) - severe emergency'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=sudden_deceleration_profile(initial_speed=25.0, final_speed=10.0, decel_time=3.0),
        scenario_name=scenario_name
    )

    # ========================================================================
    # SCENARIO 5: Step Changes (State Oscillations)
    # ========================================================================
    print("\n" + "="*80)
    print("SCENARIO 5: Step Changes in Velocity (State Oscillations)")
    print("="*80)
    print("Testing fleet response when lead vehicle oscillates between different speed states")
    print("-"*80)

    # 5a. Two-state oscillation
    scenario_name = "05a_step_changes_two_state"
    scenarios[scenario_name] = {
        'description': 'Step changes between 15 m/s and 25 m/s every 15 seconds'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=step_change_profile(speeds=[15.0, 25.0], step_duration=15.0),
        scenario_name=scenario_name
    )

    # 5b. Three-state oscillation
    scenario_name = "05b_step_changes_three_state"
    scenarios[scenario_name] = {
        'description': 'Step changes cycling through 15 m/s, 20 m/s, 25 m/s every 10 seconds'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=step_change_profile(speeds=[15.0, 20.0, 25.0], step_duration=10.0),
        scenario_name=scenario_name
    )

    # 5c. Frequent state changes
    scenario_name = "05c_step_changes_frequent"
    scenarios[scenario_name] = {
        'description': 'Frequent step changes between 18 m/s and 22 m/s every 8 seconds'
    }
    print(f"\n  Running: {scenario_name}")
    compare_penetration_rates(
        n_vehicles=N_VEHICLES,
        penetration_rates=PENETRATION_RATES,
        duration=DURATION,
        lead_vehicle_profile=step_change_profile(speeds=[18.0, 22.0], step_duration=8.0),
        scenario_name=scenario_name
    )

    # ========================================================================
    # Generate Comprehensive PDF Report
    # ========================================================================
    print("\n" + "="*80)
    print("GENERATING COMPREHENSIVE PDF REPORT")
    print("="*80)

    pdf_file = generate_pdf_report(output_dir, scenarios)

    # ========================================================================
    # Test Complete
    # ========================================================================
    print("\n" + "="*80)
    print(" "*25 + "TEST SUITE COMPLETE!")
    print("="*80)
    print(f"\nResults Summary:")
    print(f"  - Total Scenarios Run: {len(scenarios)}")
    print(f"  - Output Directory: {output_dir}")
    print(f"  - PDF Report: {pdf_file}")
    print(f"\nScenarios Tested:")
    for idx, (name, info) in enumerate(scenarios.items(), 1):
        print(f"  {idx:2d}. {name}: {info['description']}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    run_all_scenarios()
