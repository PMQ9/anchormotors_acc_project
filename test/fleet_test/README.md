## Fleet Test for ACC Controller

This directory contains a Python implementation of the Anchormotors ACC controller and fleet simulation tools to test different penetration rates of ACC-equipped vehicles.

### Files

- **[acc_controller.py](acc_controller.py)** - Python implementation of the ACC controller
  - Mimics the MATLAB/Simulink controller behavior
  - Fully tunable parameters
  - 5-state FSM (No Wave, Into Wave, In Wave, Out of Wave)
  - Moving average filters, low-pass filtering, and saturation

- **[fleet_test.py](fleet_test.py)** - Fleet simulation and penetration rate testing
  - Simulates platoons of 25 vehicles with mixed ACC/human drivers
  - Tests penetration rates: 5%, 10%, 20%, 50%, 75%, 100%
  - Human driver model based on Intelligent Driver Model (IDM)
  - Comprehensive visualization and metrics
  - Compares different penetration rates

- **[run_25_vehicle_test.py](run_25_vehicle_test.py)** - Quick runner for 25-vehicle fleet test
  - Runs both constant and oscillating lead vehicle scenarios
  - Prints summary comparison tables
  - Focused on string stability and safety metrics

### Requirements

```bash
pip install numpy matplotlib
```

### Quick Start

#### Test ACC Controller Alone

```bash
cd test/fleet_test
python acc_controller.py
```

This runs a simple test scenario and generates a plot showing the controller behavior.

#### Run Fleet Test (25 Vehicles)

```bash
cd test/fleet_test
python fleet_test.py
```

This runs comprehensive fleet simulations with **25 vehicles** comparing different ACC penetration rates:
- **Penetration rates tested**: 5%, 10%, 20%, 50%, 75%, 100%
- **Scenario 1**: Constant lead vehicle speed (20 m/s)
- **Scenario 2**: Oscillating lead vehicle speed (15-25 m/s)

**Quick runner**:
```bash
python run_25_vehicle_test.py
```

Results are saved to `test/fleet_test/results/`

### ACC Controller Usage

```python
from acc_controller import ACCController, ACCParameters

# Create controller with default parameters
controller = ACCController()

# Or customize parameters
params = ACCParameters()
params.max_velo = 30.0  # m/s
params.alpha_in_wave = 0.3  # Increase following gain
controller = ACCController(params=params, dt=0.05)

# Control loop
for _ in range(steps):
    cmd_accel, state = controller.step(lead_dist, rel_vel, ego_vel)
    # Apply cmd_accel to vehicle
```

### Fleet Test Usage

```python
from fleet_test import FleetSimulation

# Create fleet with 50% ACC penetration
sim = FleetSimulation(
    n_vehicles=8,
    penetration_rate=0.5,  # 50% ACC
    dt=0.05,
    duration=100.0
)

# Run simulation with constant lead vehicle
sim.run(lead_vehicle_profile=lambda t: 20.0)

# Plot results
sim.plot_results(filename='my_fleet_test.png')

# Get metrics
metrics = sim.calculate_metrics()
print(metrics)
```

### Tunable Parameters

All ACC controller parameters can be tuned via `ACCParameters`:

#### ROS-Style Parameters (Runtime Tunable)
- `no_wave_velo` (default: 13.5 m/s) - Threshold for "no lead vehicle"
- `wave_velo` (default: 10.0 m/s) - Threshold for "in traffic"
- `max_velo` (default: 25.0 m/s) - Maximum desired velocity

#### State-Dependent Control Gains

**No Wave (Free Driving)**
- `alpha_no_wave` (default: 0.15) - Distance gain
- `tau_no_wave` (default: 2.0 s) - Time headway
- `beta_no_wave` (default: 0.424) - Velocity damping

**Into Wave (Entering Traffic)**
- `alpha_into_wave` (default: 0.7) - Distance gain
- `tau_into_wave` (default: 2.4 s) - Time headway
- `beta_into_wave` (default: 0.23) - Velocity damping

**In Wave (Following)**
- `alpha_in_wave` (default: 0.2) - Distance gain
- `tau_in_wave` (default: 2.5 s) - Time headway
- `beta_in_wave` (default: 0.35) - Velocity damping

**Out of Wave (Exiting Traffic)**
- `alpha_out_wave` (default: 1.1) - Distance gain
- `tau_out_wave` (default: 2.4 s) - Time headway
- `beta_out_wave` (default: 0.24) - Velocity damping

#### Other Parameters
- `desired_distance` (default: 10.0 m) - Desired following distance
- `max_accel` (default: 1.5 m/s²) - Maximum acceleration
- `max_decel` (default: -3.0 m/s²) - Maximum deceleration
- `speed_limit` (default: 35.0 m/s) - Absolute speed limit
- `filter_coeff` (default: 0.65) - Low-pass filter coefficient
- `ma_window` (default: 10) - Moving average window size

### Fleet Test Metrics

The fleet simulation calculates the following metrics:

- **min_space_gap** - Minimum gap observed (safety metric)
- **mean_space_gap** - Average gap maintained
- **std_space_gap** - Gap variance (comfort metric)
- **max_decel** - Maximum deceleration (comfort/safety)
- **max_accel** - Maximum acceleration
- **mean_velocity** - Average fleet velocity (throughput)
- **velocity_std** - Velocity variance across fleet
- **num_close_calls** - Number of times gap < 5m
- **string_stability** - Variance amplification ratio (< 1.0 = stable)

### Visualization Outputs

The fleet test generates comprehensive plots showing:

1. **Position vs Time** - Trajectory of each vehicle (color-coded: blue=ACC, red=human)
2. **Space Gap vs Time** - Following distance for each vehicle
3. **Velocity vs Time** - Speed profile of each vehicle
4. **Acceleration vs Time** - Commanded acceleration for each vehicle
5. **ACC States vs Time** - FSM state for ACC-equipped vehicles
6. **Statistics Summary** - Key metrics and performance indicators

### Example: Comparing Penetration Rates

```python
from fleet_test import compare_penetration_rates

# Test different penetration rates
results = compare_penetration_rates(
    n_vehicles=8,
    penetration_rates=[0.0, 0.25, 0.5, 0.75, 1.0],
    duration=100.0,
    lead_vehicle_profile=lambda t: 20.0  # Constant speed
)

# Results contains metrics for each penetration rate
for rate, metrics in results.items():
    print(f"{rate*100}% ACC: String Stability = {metrics['string_stability']:.3f}")
```

### Custom Lead Vehicle Profiles

You can define custom lead vehicle behavior:

```python
# Constant speed
lead_profile = lambda t: 20.0

# Sinusoidal oscillation
lead_profile = lambda t: 20.0 + 5.0 * np.sin(2 * np.pi * t / 20.0)

# Acceleration/deceleration
def lead_profile(t):
    if t < 20:
        return 20.0
    elif t < 40:
        return 20.0 - 0.5 * (t - 20)  # Decelerate
    else:
        return 10.0  # Constant slower speed

sim.run(lead_vehicle_profile=lead_profile)
```

### Tuning for Different Behaviors

**More Conservative ACC**:
```python
params = ACCParameters()
params.alpha_in_wave = 0.15  # Reduce distance gain (smoother)
params.tau_in_wave = 3.0     # Increase time headway (larger gaps)
params.max_velo = 20.0       # Lower cruise speed
```

**More Aggressive ACC**:
```python
params = ACCParameters()
params.alpha_in_wave = 0.3   # Increase distance gain (faster response)
params.tau_in_wave = 2.0     # Decrease time headway (tighter gaps)
params.max_velo = 30.0       # Higher cruise speed
```

**Smoother Ride**:
```python
params = ACCParameters()
params.filter_coeff = 0.4    # Slower filter (less jerk)
params.max_accel = 1.0       # Lower acceleration limit
params.max_decel = -2.0      # Gentler braking
```

### Integration with MATLAB Tests

This Python implementation is designed to match the behavior of the MATLAB/Simulink controller. You can:

1. Compare Python results with MATLAB test cases
2. Rapidly prototype parameter changes before updating Simulink
3. Perform large-scale Monte Carlo simulations
4. Test scenarios difficult to implement in Simulink

### Notes

- **Sample Time**: Default is 50ms (20Hz), matching typical ACC control rates
- **Human Driver Model**: Uses IDM with 200ms reaction delay
- **Initial Conditions**: All vehicles start at 20 m/s, spaced 50m apart
- **Random Distribution**: ACC vehicles are randomly distributed in the fleet
- **String Stability**: Key metric for platoon behavior - values < 1.0 indicate stable propagation of disturbances

### References

- Main controller documentation: [ACC_CONTROLLER_EXPLAINED.md](../../ACC_CONTROLLER_EXPLAINED.md)
- MATLAB/Simulink implementation: [acc_subsystem.slx](../../acc_subsystem.slx)
- Test framework: [test/multi_veh_test/](../multi_veh_test/)

---

**Created**: 2025-11-18
**Python Version**: 3.7+
**Dependencies**: numpy, matplotlib
