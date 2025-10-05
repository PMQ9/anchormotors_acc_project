# Single Vehicle Tests

## How to Run Tests

Running the MATLAB script ```run_all_single_test.m``` will iterate through all the models that define the single vehicle tests. Each test has a function defined that will print any errors in execution to the console. In most of the single vehicle tests, only the command acceleration is tested. We wamt to make sure that the ACC output acceleration is reasonable in the given situation.

## Test Cases

### 1. Lead Vehicle Suddenly Stops
This simulation is defined in ```case_1_lead_veh_sudden_stop_25a.slx```.

The test defines a case where the lead vehicle suddenly stops. The ego velocity is 10 m/s. The relative velocity is 10 m/s. The space gap rapidly decreases.

The expected behavior is that the command acceleration should be negative.

### 2. Ego Vehicle Stopped, Space Gap Too Small
This simulation is defined in ```case_2_ego0_gap_not_desired.slx```.

The test defines a cases where the space gap is too small and the ego vehicle is stopped. The ego velocity is 0 m/s. The space gap is 0.9 m. The relative velocity is less than 5 m.

The expected behavior is that the command acceleration should be 0.

### 3. Lead Vehicle Accelerating
This simulation is defined in ```case_3_lead_rapid_increase_space.slx```.

The test defines a scenario where the space gap is rapidly increasing. The ego velocity is 10 m/s. The relative velocity is undefined.

The expected behavior is that the command acceleration should be positive.

### 4. Lead Car Disappears
This simulation is defined in ```case_4_lead_disappears.slx```.

The test defines a scenario where the lead disappears. The ego velocity is 10 m/s. The space gap rapidly jumps from 20 m to 280 m. The relative velocity is undefined.

The expected behavior is that the acceleration should be positive.

### 5. Lead Car Appears
This simulation is defined in ```case_5_lead_car_appears25a.slx```.

The test defines a scenario where the lead suddenly appears. The ego velocity is 10 m/s. The space gap is undefined until 3 s then takes a value of 15 m. The relative velocity increases.

The expected behavior is that the command acceleration should be negative.

### 6. Relative Velocity 0, High Space Gap
This simulation is defined in ```zero_relative_v_high_gap.slx```.

The test defines a scenario where the relative velocity is 0 m/s. The space gap is a constant 100 m. The ego velocity is a constant 10 m/s.

The expected behavior is that the command acceleration should be positive.

### 7. Relative Velocity 0, Low Space Gap
This simulation is defined in ```case_7_zero_relative_v_low_gap.slx```.

This test defines a scenario where the cars are going the same speed but the space gap is small. Relative velocity is 0 m/s. The space gap is 1 m. The ego velocity is 10 m/s.

The expected behavior is that the acceleration is negative.

### 8. Negative Relative Velocity, High Space Gap
This simulation is defined in ```case_8_sn_high_neg_delta_v25a.slx```.

This test defines a scenario where ego car is faster and the space gap is high. Ego velocity is 15 m/s. Space gap is 50 m. Relative velocity -5 m/s.

The expected behavior is that the acceleration is positive.

### 9. Ego Vehicle Stopped, Lead Car Accelerating
This simulation is defined in ```case_9_ego_stopped_lead_accelerating.slx```.

The test defines a scenario where the space gap and and relative velocity are increasing. The ego velocity is 0 m/s.

Th expected behavior is that the command acceleration should be positive.

### 10. Lead Vehicle Gradually Slows to a Stop
This simulation is defined in ```case_10_lead_gradually_slows_down.slx```.

The test defines a scenario where the lead vehicle gradually stops. The ego velocity is 10 m/s. The relative velocity decreases. The space gap is 19.9 m.

The expected behavior is that the command acceleration should be negative.