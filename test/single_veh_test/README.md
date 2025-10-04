# Single Vehicle Tests

## How to Run Tests

Running the MATLAB script ```run_all_single_test.m``` will iterate through all the models that define the single vehicle tests. Each test has a function defined that will print any errors in execution to the console. In most of the single vehicle tests, only the command acceleration is tested. We wamt to make sure that the ACC output acceleration is reasonable in the given situation.

## Test Cases

### 1. Lead Vehicle Suddenly Stops

### 2. Ego Vehicle Stopped, Space Gap Too Small

### 3. Lead Vehicle Accelerating
This simulation is defined in ```lead_rapid_increase_space.slx```.

The test defines a scenario where the space gap is rapidly increasing. The ego velocity is 10 m/s. The relative velocity is undefined.

The expected behavior is that the command acceleration should be positive.

### 4. Lead Car Disappears

### 5. Lead Car Appears

### 6. Relative Velocity 0, High Space Gap
This simulation is defined in ```zero_relative_v_high_gap.slx```.

The test defines a scenario where the relative velocity is 0 m/s. The space gap is a constant 100 m. The ego velocity is a constant 10 m/s.

The expected behavior is that the command acceleration should be positive.

### 7. Relative Velocity 0, Low Space Gap

### 8. Negative Relative Velocity, High Space Gap

### 9. Ego Vehicle Stopped, Lead Car Accelerating
This simulation is defined in ```ego_stopped_lead_accelerating.slx```.

The test defines a scenario where the space gap and and relative velocity are increasing. The ego velocity is 0 m/s.

Th expected behavior is that the command acceleration should be positive.

### 10. Lead Vehicle Gradually Slows to a Stop