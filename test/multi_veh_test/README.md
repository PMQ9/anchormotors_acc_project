# Multi Vehicle Tests

## How to Run Tests

Running the MATLAB script ```run_all_multi_test.m``` will iterate through all the models that define the multiple vehicle tests. ChatGPT wrote this script. Each test includes the ```multi_vehicle_test_subsystem.slx```. This subsystem checks the following:

- The space gap must be above a minimum value.
- The magnitude of the jerk must be below a certain value.
- The acceleration needs to be between a minimum and maximum value.
- The velocity needs to be zero or positive, bounded by an upper bound.
- The acceleration should not be in the hard braking range.

Any failed tests and the time of failure are printed to the console.

## Test Cases

### 1. Lead Vehicle Stationary, Ego Vehicle Nonzero Velocity
This simulation is defined in ```case_1_leadcar_stationary_egocar_move25a.slx```.

The initial space gap is 50 m. The lead car has a velocity of 0 m/s and an acceleration of 0 m/s2. The ego car has an initial velocity of 15 m/s.

### 2. Lead Vehicle Steady Then Slows
This simulation is defined in ```case_2_lead_steady_then_slow.slx```.

The initial space gap is 50 m. Both vehicles start with a velocity of 20 m/s. The lead vehicle begins with zero acceleration and starts to decelerate after a few seconds.

### 3. Lead Vehicle Increasing Space Gap
This simulation is defined in ```case_3_lead_increasing_space_gap.slx```.

The initial space gap is 50 m. Both vehicles start with a velocity of 20 m/s. The lead vehicle has a constant acceleration of 5 m/s2.

### 4. Lead Vehicle Cut Out
This simulation is defined in ```case_4_cut_out.slx```.

Both cars have an initial velocity of 20 m/s. The space gap jumps from 50 m to 200 m.

### 5. Lead Vehicle Cut In
This simulation is defined in ```case_5_cut_in_25a.slx```.

The initial velocity of the ego car is 20 m/s. The initial ego position is 20 m. The lead car starts 500 m away and then drops 100 m closer.

### 6. Lead Vehicle Decreasing Space Gap
This simulation is defined in ```case_6_lead_decreasing_space_gap.slx```.

The initial space gap is 40 m. Both vehicles start with a velocity of 20 m/s. The lead vehicle has a constant deceleration of -0.5 m/s2.

### 7. Lead Vehicle Slows Then Steady
This simulation is defined in ```case_7_lead_slow_down_then_steady.slx```.

The initial space gap is 50 m. The initial ego velocity is 20 m/s. The lead vehicle has an initial acceleration of -2 m/s2 then 0 m/s2. The lead vehicle initial velocity is 20 m/s.

### 8. Lead Vehicle Steady Then Speeds Up
This simulation is defined in ``````.

### 9. Lead Vehicle and Ego Vehicle Stopped, Space Gap Too Big
This simulation is defined in ```case_9_both_stopped_gap_too_big.slx```.

The initial space gap is 20 m. Both vehicles start with a velocity of 0 m/s. The lead vehicle has a constant acceleration of 0 m/s2.

### 10. Lead Vehicle and Ego Vehicle Steady State
This simulation is defined in ```case_10_lead_gradually_slows_down.slx```.

The initial space gap is 50 m. Both cars have an initial velocity of 20 m/s. The lead vehicle has a command acceleration of 0 m/s2.