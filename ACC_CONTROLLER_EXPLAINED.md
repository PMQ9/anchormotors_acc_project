# Adaptive Cruise Control (ACC) Controller - Technical Documentation

## Overview

The Anchormotors ACC controller is a **state-based multimodal controller** for autonomous vehicle longitudinal control. It implements adaptive cruise control with lead vehicle following capabilities using a 5-state finite state machine.

**Version**: 1.29 (Simulink Coder R2025b)
**Control Rate**: Typically 100 Hz
**Generated Code**: Auto-generated from MATLAB/Simulink (DO NOT manually edit)

---

## System Architecture

### Inputs
| Topic | Description | Units | Source |
|-------|-------------|-------|--------|
| `lead_dist` | Distance to lead vehicle | meters | Radar/LIDAR + safety buffer |
| `rel_vel` | Relative velocity (lead - ego) | m/s | Differential velocity |
| `ego_vel` | Ego vehicle velocity | m/s | Vehicle state |

### Outputs
| Topic | Description | Units | Range |
|-------|-------------|-------|-------|
| `cmd_accel` | Command acceleration | m/s² | [-3.0, 1.5] |
| `state_logic` | Current FSM state | enum | {0,1,2,3} |

### State Encoding
- **0** = No Wave (free driving)
- **1** = Into Wave (entering traffic)
- **2** = In Wave (following lead vehicle)
- **3** = Out of Wave (exiting traffic)

---

## Control Algorithm

### 1. Signal Processing

#### Moving Average Filter (10-sample window)
Two moving average filters smooth sensor data:
- **Lead Velocity Smoothing**: Filters combined velocity signal
- **Lead Acceleration Smoothing**: Filters differentiated acceleration

**Implementation**: Circular buffer with running sum, 10-sample window

#### Discrete Derivative (Lead Acceleration)
Calculates lead vehicle acceleration from velocity:
```
lead_accel = (lead_velocity[k] - lead_velocity[k-1]) * 20.0
```
- Sample rate factor: 20.0 (implies 50ms sample time)
- Saturation: [-3.5, 2.0] m/s²

---

### 2. State Machine Logic

The controller uses a **5-state finite state machine** to handle different traffic scenarios:

```
    ┌─────────┐
    │ Initial │
    └────┬────┘
         │
    ┌────┴─────────┬──────────────┐
    │              │              │
    v              v              v
┌─────────┐   ┌──────────┐   ┌─────────┐
│ No Wave │◄─►│Into Wave │◄─►│ In Wave │
└─────────┘   └──────────┘   └────┬────┘
     ▲             ▲               │
     │             │               │
     │        ┌────┴───────┐       │
     └────────┤ Out of Wave│◄──────┘
              └────────────┘
```

#### State Transition Conditions

**Initial State**
- **→ No Wave**: `lead_velocity > no_wave_velo` OR `lead_dist > 200m`
- **→ In Wave**: `lead_velocity ≤ no_wave_velo` AND `lead_dist ≤ 200m`

**No Wave (Free Driving)**
- **→ Into Wave**:
  - (`accel_smooth < -0.5` AND `lead_velocity < no_wave_velo` AND `lead_dist < 200m`) OR
  - (`lead_velocity < no_wave_velo` AND `lead_dist < 75m`)

**Into Wave (Entering Traffic)**
- **→ In Wave**: `lead_velocity_smooth ≤ wave_velo`
- **→ Out of Wave**: `accel_smooth ≥ 0.25`
- **→ No Wave**: `lead_dist > 200m`

**In Wave (Following)**
- **→ Out of Wave**: `accel_smooth > 0.5` AND `lead_velocity > wave_velo`
- **→ No Wave**: `lead_dist > 200m`

**Out of Wave (Exiting Traffic)**
- **→ No Wave**: `lead_velocity_smooth > no_wave_velo` OR `lead_dist > 200m`
- **→ Into Wave**: `accel_smooth ≤ -0.25`

---

### 3. Control Laws by State

All control laws follow the general form of **Intelligent Driver Model (IDM)**-style control:

```
cmd_accel = α * (d_actual - d_desired - τ * v_ego) + β * v_rel
```

Where:
- **α** = Distance error gain
- **τ** = Time headway (desired time gap)
- **β** = Velocity damping gain
- **d_desired** = Desired following distance

#### State 0: No Wave (Free Driving)
Dual-objective controller: reach desired velocity while maintaining safe distance.

```c++
// Velocity approach controller
desired_vel = min(max_velo, 35.0)  // Use ROS param or hard limit
vel_error = desired_vel - ego_vel
vel_error_sat = clamp(vel_error, 0, 3.0)
vel_approach = 0.333 * vel_error_sat
vel_limiter = min(vel_approach, 1.0)

// Distance-based acceleration
distance_accel = ((lead_dist - 10.0) - 2.0 * rel_vel) * 0.15 + 0.424 * ego_vel
distance_accel_sat = clamp(distance_accel, -3.0, 1.5)

// Combined output (velocity limiter acts as soft constraint)
cmd_accel = vel_limiter * distance_accel_sat
```

**Parameters:**
- α = 0.15 (distance gain)
- τ = 2.0 s (time headway)
- β = 0.424 (velocity gain)
- d_desired = 10 m
- max_velocity = 35 m/s (or ROS parameter `max_velo`)

**Characteristics:**
- Gentle distance control (low α)
- Strong velocity damping (high β)
- Soft velocity limiting approach

#### State 1: Into Wave (Entering Traffic)
Aggressive controller for catching up to slower traffic.

```c++
cmd_accel = ((lead_dist - 10.0) - 2.4 * ego_vel) * 0.7 + 0.23 * rel_vel
```

**Parameters:**
- α = 0.7 (high distance gain)
- τ = 2.4 s (time headway)
- β = 0.23 (velocity gain)
- d_desired = 10 m

**Characteristics:**
- High distance gain → faster convergence
- Moderate time headway
- Low velocity damping → allows speed adjustment

#### State 2: In Wave (Following)
Conservative controller for stable car-following.

```c++
cmd_accel = ((lead_dist - 10.0) - 2.5 * rel_ego) * 0.2 + 0.35 * rel_vel
cmd_accel = clamp(cmd_accel, -3.0, 1.5)
```

**Parameters:**
- α = 0.2 (low distance gain)
- τ = 2.5 s (longer time headway)
- β = 0.35 (velocity gain)
- d_desired = 10 m

**Characteristics:**
- Low distance gain → smoother control
- Longest time headway → more conservative
- Moderate velocity damping
- Output saturation: [-3.0, 1.5] m/s²

#### State 3: Out of Wave (Exiting Traffic)
Very aggressive controller for accelerating away from traffic.

```c++
cmd_accel = ((lead_dist - 10.0) - 2.4 * ego_vel) * 1.1 + 0.24 * rel_vel
```

**Parameters:**
- α = 1.1 (very high distance gain)
- τ = 2.4 s (time headway)
- β = 0.24 (velocity gain)
- d_desired = 10 m

**Characteristics:**
- Highest distance gain → most aggressive
- Low velocity damping → rapid acceleration
- No explicit saturation (relies on post-processing)

---

### 4. Post-Processing and Output Filtering

After state-based control calculation, several safety layers are applied:

#### Step 1: Speed Limiter
```c++
if (ego_vel >= 35.0) {
    cmd_accel = min(cmd_accel, 0.0)  // Only allow deceleration
}
```

#### Step 2: Hard Saturation
```c++
cmd_accel = clamp(cmd_accel, -3.0, 1.5)
```

#### Step 3: Low-Pass Filter (Anti-jerk)
```c++
// First-order exponential filter
cmd_accel_filtered = cmd_accel_filtered + 0.65 * (cmd_accel - cmd_accel_filtered)
```
- **Filter coefficient**: 0.65
- **Time constant**: ≈ 1.54 samples (at 100 Hz: ~15 ms)
- **Purpose**: Smooth rapid changes, reduce mechanical stress

#### Step 4: Final Output Saturation
```c++
cmd_accel_output = clamp(cmd_accel_filtered, -3.0, 1.5)
```

---

## Tunable Parameters

### ROS Parameters (Dynamic Configuration)

These parameters can be set via ROS parameter server **before** launching the node:

| Parameter | Default | Units | Description | Usage |
|-----------|---------|-------|-------------|-------|
| `no_wave_velo` | 13.5 | m/s | Velocity threshold for "no lead vehicle" detection | State transitions |
| `wave_velo` | 10.0 | m/s | Velocity threshold for "in traffic" detection | State transitions |
| `max_velo` | 25.0 | m/s | Maximum desired velocity in No Wave mode | Speed limiting |
| `tau`* | 2.0 | s | Time headway (unused in current version) | N/A |
| `alpha`* | 1.1 | - | Distance gain (unused in current version) | N/A |

**Note**: Parameters marked with * are read but not currently used by the control logic.

**Setting Parameters:**
```bash
rosparam set /no_wave_velo 15.0
rosparam set /wave_velo 12.0
rosparam set /max_velo 30.0
roslaunch anchormotors anchormotors.launch
```

### Hard-Coded Control Gains

These are **compiled into the code** and require regeneration from Simulink to modify:

#### Distance Control Gains (α)
| State | Gain | Aggressiveness | Purpose |
|-------|------|----------------|---------|
| No Wave | 0.15 | Very Low | Gentle cruising |
| Into Wave | 0.7 | High | Quick convergence |
| In Wave | 0.2 | Low | Stable following |
| Out of Wave | 1.1 | Very High | Rapid separation |

#### Time Headway (τ)
| State | Value (s) | Gap at 30 m/s |
|-------|-----------|---------------|
| No Wave | 2.0 | 60 m |
| Into Wave | 2.4 | 72 m |
| In Wave | 2.5 | 75 m |
| Out of Wave | 2.4 | 72 m |

#### Velocity Damping Gains (β)
| State | Gain | Characteristic |
|-------|------|----------------|
| No Wave | 0.424 | Strong damping |
| Into Wave | 0.23 | Weak damping |
| In Wave | 0.35 | Moderate damping |
| Out of Wave | 0.24 | Weak damping |

#### Other Constants
- **Desired following distance**: 10 m (all states)
- **Maximum acceleration**: 1.5 m/s²
- **Maximum deceleration**: -3.0 m/s²
- **Speed limit**: 35 m/s (126 km/h)
- **Far distance threshold**: 200 m (no lead vehicle)
- **Close distance threshold**: 75 m (force following mode)
- **Filter coefficient**: 0.65 (low-pass filter)

---

## Safety Features

### Multi-Layer Safety Architecture

1. **State Machine Logic**
   - Automatic transition to safe states based on distance
   - Emergency transitions at 75m and 200m thresholds

2. **Acceleration Limiting**
   - Hard limits: [-3.0, 1.5] m/s²
   - Speed-dependent limiting: zero accel above 35 m/s

3. **External Safety Integration** (see [anchormotors.launch](launch/anchormotors.launch))
   - **Control Barrier Function (CBF)**: Verifies safety before command execution
   - **Topic remapping**: `cmd_accel` → `cmd_accel_pre` (pre-safety layer)
   - **Distance buffer**: Lead distance reduced by 10m for conservative control

4. **Signal Filtering**
   - Moving average filters reduce sensor noise
   - Acceleration saturation prevents unrealistic dynamics
   - Low-pass filter reduces control jerk

---

## Tuning Guidelines

### For More Conservative Behavior
- ↓ Decrease `no_wave_velo` (detects traffic earlier)
- ↓ Decrease `max_velo` (lower cruise speed)
- ↓ Decrease distance gains (α) - **requires Simulink regeneration**
- ↑ Increase time headway (τ) - **requires Simulink regeneration**

### For More Aggressive Behavior
- ↑ Increase `no_wave_velo` (stays in free driving longer)
- ↑ Increase `max_velo` (higher cruise speed)
- ↑ Increase distance gains (α) - **requires Simulink regeneration**
- ↓ Decrease time headway (τ) - **requires Simulink regeneration**

### For Smoother Ride
- ↓ Decrease filter coefficient (current: 0.65) - **requires Simulink regeneration**
- ↓ Decrease acceleration limits - **requires Simulink regeneration**
- ↑ Increase moving average window size - **requires Simulink regeneration**

### Warning
Most tuning requires modifying the **source MATLAB/Simulink model** and regenerating C++ code. Only ROS parameters (`no_wave_velo`, `wave_velo`, `max_velo`) can be adjusted without recompilation.

---

## Algorithm Summary

The controller implements a **gain-scheduled car-following algorithm** based on traffic conditions:

1. **No Wave**: Cruise to desired speed with gentle distance control
2. **Into Wave**: Aggressively reduce speed to match traffic
3. **In Wave**: Maintain stable following with conservative gains
4. **Out of Wave**: Rapidly accelerate away from slow traffic

The control law resembles the **Intelligent Driver Model (IDM)** with velocity-dependent damping:

```
a = α(Δd - τΔv) + βv_ego
```

Key differences from standard IDM:
- State-dependent gain scheduling
- Explicit velocity damping term
- Soft velocity limiting in No Wave mode
- Multi-stage saturation and filtering

---

## Implementation Details

### Execution Model
- **Rate-based execution**: Fixed-rate control loop (typically 100 Hz)
- **Real-time synchronization**: Semaphore-based thread coordination
- **Message passing**: Latest message paradigm (no queuing)

### Numeric Safety
- **NaN/Inf handling**: Special floating-point utilities prevent undefined behavior
- **Saturation before arithmetic**: Prevents overflow in calculations
- **Type safety**: Explicit conversions between ROS messages and internal types

### Memory Management
- **Stateful computation**: Uses delays, moving averages, and state memory
- **Circular buffers**: Efficient moving average implementation
- **Pre-allocated storage**: No dynamic memory allocation during runtime

---

## References

### Source Files
- **Main Controller**: [src/anchormotors.cpp](src/anchormotors.cpp) (835 lines)
- **ROS Interface**: [src/rosnodeinterface.cpp](src/rosnodeinterface.cpp) (181 lines)
- **Parameter Handling**: [include/anchormotors/slros_generic_param.h](include/anchormotors/slros_generic_param.h)
- **Hardware Launch**: [launch/anchormotors.launch](launch/anchormotors.launch)
- **Simulation Launch**: [launch/anchormotorsDocker.launch](launch/anchormotorsDocker.launch)

### Testing
See [launch/README.md](launch/README.md) for 10 comprehensive test scenarios covering:
- Various lead vehicle distances (20m - 100m)
- Different ego velocities (1-20 m/s)
- State transition validation
- Safety margin verification

---

## Modification Procedure

### To Change Control Parameters:
1. Open source MATLAB/Simulink model (v1.29)
2. Modify desired gain blocks or constants
3. Regenerate C++ code using Simulink Coder (ert.tlc target)
4. Commit updated files: `anchormotors.cpp`, `anchormotors.h`, `anchormotors_data.cpp`
5. Rebuild and test

### Files That Should NOT Be Manually Edited:
- `src/anchormotors.cpp`
- `src/anchormotors_data.cpp`
- `include/anchormotors/anchormotors.h`
- `include/anchormotors/anchormotors_types.h`
- `include/anchormotors/rt_*.h/cpp`
- `include/anchormotors/slros_*.h/cpp`

### Files Safe to Edit:
- `src/rosnodeinterface.cpp` (ROS integration layer)
- `launch/*.launch` (configuration files)
- `CMakeLists.txt` (build system)
- Installation scripts in `anchormotors/` directory

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Simulink Model Version**: 1.29
**Coder Version**: R2025b
