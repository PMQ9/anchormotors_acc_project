"""
Basic test script for ACC controller

Quick validation that the controller is working correctly.
"""

import numpy as np
import matplotlib.pyplot as plt
from acc_controller import ACCController, ACCParameters, ACCState


def test_scenario_1_approaching_slower_vehicle():
    """Test: Approaching slower lead vehicle from behind"""
    print("\n" + "="*60)
    print("Test 1: Approaching Slower Lead Vehicle")
    print("="*60)

    controller = ACCController()

    dt = 0.05
    duration = 30.0
    steps = int(duration / dt)

    # Initial conditions
    ego_vel = 25.0  # m/s (90 km/h)
    lead_vel = 15.0  # m/s (54 km/h)
    lead_dist = 100.0  # m

    # Storage
    time = np.arange(steps) * dt
    ego_vels = np.zeros(steps)
    distances = np.zeros(steps)
    accels = np.zeros(steps)
    states = np.zeros(steps)

    for i in range(steps):
        rel_vel = lead_vel - ego_vel
        cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)

        ego_vels[i] = ego_vel
        distances[i] = lead_dist
        accels[i] = cmd_accel
        states[i] = state

        # Update (simple integration)
        ego_vel = max(0, ego_vel + cmd_accel * dt)
        lead_dist = lead_dist + rel_vel * dt

    # Verify results
    final_gap = distances[-1]
    final_vel = ego_vels[-1]

    print(f"Initial gap: {distances[0]:.1f} m")
    print(f"Final gap: {final_gap:.1f} m")
    print(f"Initial ego velocity: {ego_vels[0]:.1f} m/s")
    print(f"Final ego velocity: {final_vel:.1f} m/s")
    print(f"Lead velocity: {lead_vel:.1f} m/s")
    print(f"Min gap: {np.min(distances):.1f} m")
    print(f"Max decel: {np.min(accels):.2f} m/s²")

    # Assertions
    assert final_gap >= 5.0, "Gap too small!"
    assert abs(final_vel - lead_vel) < 1.0, "Did not match lead velocity!"
    assert np.min(distances) >= 5.0, "Minimum gap violated!"

    print("✓ Test PASSED")

    return time, ego_vels, distances, accels, states


def test_scenario_2_lead_vehicle_sudden_stop():
    """Test: Lead vehicle suddenly decelerates"""
    print("\n" + "="*60)
    print("Test 2: Lead Vehicle Sudden Stop")
    print("="*60)

    controller = ACCController()

    dt = 0.05
    duration = 20.0
    steps = int(duration / dt)

    # Initial conditions
    ego_vel = 20.0  # m/s
    lead_vel = 20.0  # m/s
    lead_dist = 50.0  # m

    # Storage
    time = np.arange(steps) * dt
    ego_vels = np.zeros(steps)
    lead_vels = np.zeros(steps)
    distances = np.zeros(steps)
    accels = np.zeros(steps)
    states = np.zeros(steps)

    for i in range(steps):
        # Lead vehicle suddenly brakes at t=5s
        if time[i] >= 5.0 and time[i] < 10.0:
            lead_accel = -2.0
        else:
            lead_accel = 0.0

        rel_vel = lead_vel - ego_vel
        cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)

        ego_vels[i] = ego_vel
        lead_vels[i] = lead_vel
        distances[i] = lead_dist
        accels[i] = cmd_accel
        states[i] = state

        # Update
        ego_vel = max(0, ego_vel + cmd_accel * dt)
        lead_vel = max(0, lead_vel + lead_accel * dt)
        lead_dist = lead_dist + rel_vel * dt

    min_gap = np.min(distances)
    print(f"Min gap during braking: {min_gap:.1f} m")
    print(f"Max ego deceleration: {np.min(accels):.2f} m/s²")

    assert min_gap >= 5.0, "Collision risk! Gap too small"
    assert np.min(accels) >= -3.0, "Deceleration limit violated"

    print("✓ Test PASSED")

    return time, ego_vels, lead_vels, distances, accels, states


def test_scenario_3_state_transitions():
    """Test: Verify state transitions work correctly"""
    print("\n" + "="*60)
    print("Test 3: State Transitions")
    print("="*60)

    controller = ACCController()

    dt = 0.05
    duration = 50.0
    steps = int(duration / dt)

    # Initial conditions
    ego_vel = 25.0  # m/s
    lead_vel = 25.0  # m/s
    lead_dist = 150.0  # m

    # Storage
    time = np.arange(steps) * dt
    states = np.zeros(steps)

    for i in range(steps):
        # Lead vehicle varies speed
        if time[i] < 10:
            lead_vel = 25.0  # Same speed
        elif time[i] < 20:
            lead_vel = 12.0  # Slow down (should trigger Into Wave)
        elif time[i] < 30:
            lead_vel = 8.0   # Very slow (should trigger In Wave)
        elif time[i] < 40:
            lead_vel = 20.0  # Speed up (should trigger Out of Wave)
        else:
            lead_vel = 25.0  # Back to cruise (should trigger No Wave)

        rel_vel = lead_vel - ego_vel
        cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)

        states[i] = state

        # Update
        ego_vel = max(0, ego_vel + cmd_accel * dt)
        lead_dist = max(10, lead_dist + rel_vel * dt)

    # Check that we visited different states
    unique_states = set(states)
    print(f"States visited: {unique_states}")

    assert len(unique_states) >= 3, "Controller did not transition between states!"
    print("✓ Test PASSED")

    return time, states


def plot_all_tests():
    """Run all tests and create comprehensive plot"""
    print("\n" + "="*70)
    print("Running ACC Controller Validation Tests")
    print("="*70)

    # Run tests
    t1, v1, d1, a1, s1 = test_scenario_1_approaching_slower_vehicle()
    t2, v2, lv2, d2, a2, s2 = test_scenario_2_lead_vehicle_sudden_stop()
    t3, st3 = test_scenario_3_state_transitions()

    # Create plots
    fig = plt.figure(figsize=(16, 10))

    # Test 1
    ax1 = plt.subplot(3, 3, 1)
    ax1.plot(t1, d1, 'b-', linewidth=2)
    ax1.axhline(y=10, color='g', linestyle='--', label='Desired gap')
    ax1.set_ylabel('Distance (m)')
    ax1.set_title('Test 1: Approaching Slower Vehicle')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2 = plt.subplot(3, 3, 2)
    ax2.plot(t1, v1, 'b-', linewidth=2, label='Ego')
    ax2.axhline(y=15, color='r', linestyle='--', label='Lead')
    ax2.set_ylabel('Velocity (m/s)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    ax3 = plt.subplot(3, 3, 3)
    ax3.plot(t1, a1, 'b-', linewidth=2)
    ax3.set_ylabel('Acceleration (m/s²)')
    ax3.grid(True, alpha=0.3)

    # Test 2
    ax4 = plt.subplot(3, 3, 4)
    ax4.plot(t2, d2, 'b-', linewidth=2)
    ax4.axhline(y=5, color='r', linestyle='--', label='Min safe gap')
    ax4.set_ylabel('Distance (m)')
    ax4.set_title('Test 2: Lead Vehicle Sudden Stop')
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    ax5 = plt.subplot(3, 3, 5)
    ax5.plot(t2, v2, 'b-', linewidth=2, label='Ego')
    ax5.plot(t2, lv2, 'r-', linewidth=2, label='Lead')
    ax5.set_ylabel('Velocity (m/s)')
    ax5.grid(True, alpha=0.3)
    ax5.legend()

    ax6 = plt.subplot(3, 3, 6)
    ax6.plot(t2, a2, 'b-', linewidth=2)
    ax6.axhline(y=-3.0, color='r', linestyle='--', label='Max decel')
    ax6.set_ylabel('Acceleration (m/s²)')
    ax6.grid(True, alpha=0.3)
    ax6.legend()

    # Test 3
    ax7 = plt.subplot(3, 3, 7)
    ax7.plot(t3, st3, 'b-', linewidth=2)
    ax7.set_ylabel('State')
    ax7.set_xlabel('Time (s)')
    ax7.set_title('Test 3: State Transitions')
    ax7.set_yticks([0, 1, 2, 3])
    ax7.set_yticklabels(['No Wave', 'Into', 'In Wave', 'Out'])
    ax7.grid(True, alpha=0.3)

    # State distribution for Test 1
    ax8 = plt.subplot(3, 3, 8)
    ax8.plot(t1, s1, 'b-', linewidth=2)
    ax8.set_ylabel('State')
    ax8.set_xlabel('Time (s)')
    ax8.set_yticks([0, 1, 2, 3])
    ax8.set_yticklabels(['No Wave', 'Into', 'In Wave', 'Out'])
    ax8.grid(True, alpha=0.3)

    # State distribution for Test 2
    ax9 = plt.subplot(3, 3, 9)
    ax9.plot(t2, s2, 'b-', linewidth=2)
    ax9.set_ylabel('State')
    ax9.set_xlabel('Time (s)')
    ax9.set_yticks([0, 1, 2, 3])
    ax9.set_yticklabels(['No Wave', 'Into', 'In Wave', 'Out'])
    ax9.grid(True, alpha=0.3)

    plt.suptitle('ACC Controller Validation Tests', fontsize=14, fontweight='bold')
    plt.tight_layout()

    # Save
    import os
    os.makedirs('test/fleet_test/results', exist_ok=True)
    filename = 'test/fleet_test/results/acc_validation_tests.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n✓ All tests PASSED!")
    print(f"Plot saved to {filename}")

    plt.show()


if __name__ == "__main__":
    plot_all_tests()

    print("\n" + "="*70)
    print("ACC Controller is working correctly!")
    print("You can now run the full fleet test with: python fleet_test.py")
    print("="*70 + "\n")
