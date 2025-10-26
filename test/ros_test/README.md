# Utilities for testing and visualizing bag files created from ROS

In this test folder, we have utilities for running ROS tests and analyzing the results from bag files.

## run_ros_test.py

Fully automated ROS testing workflow for the anchormotors package from the [cs3892-2025F repository](https://github.com/PMQ9/anchormotors_acc_project).

This script handles the complete testing workflow:
1. Start Docker container
2. Build project
3. Start roscore in background
4. Run test
5. Copy bag file to local machine

### Usage

```bash
python run_ros_test.py --test TEST_NUMBER --workspace-root PATH_TO_ROSSIM [OPTIONS]
```

### Required Arguments

- `--workspace-root PATH`: Path to the rossim workspace root directory (e.g., `/path/to/cs3892-2025F/src/rossim`)

### Optional Arguments

- `--test NUMBER`: Test number to run (e.g., 01, 02, 03, etc.)
- `--launch-dir PATH`: Path to launch files directory (auto-detected from workspace-root if not specified)
- `--bagfile-dir PATH`: Directory to save bag files (default: `./bagfiles` relative to script)
- `--no-build`: Skip the build step
- `--list`: List all available tests

### Examples

```bash
# List available tests
python run_ros_test.py --list --workspace-root "/path/to/rossim"

# Run test 01 with full build
python run_ros_test.py --test 01 --workspace-root "/path/to/rossim"

# Run test 08 without rebuilding
python run_ros_test.py --test 08 --no-build --workspace-root "/path/to/rossim"

# Run test 10 with custom bag file output directory
python run_ros_test.py --test 10 --workspace-root "/path/to/rossim" --bagfile-dir "./my_bagfiles"
```

## MATLAB Analysis Scripts

### allPlots.m
In this script, user can choose one bag file which user wants to test when running this file. Then it creates one big plot which depicts 6 different fields: Ego Velocity, Command Acceleration, Relative Velocity, Relative Lead Distance, Lead Car Velocity, Ego ACC mode.

### replay_two_cars.m, testResult.m
In these scripts, these are scripts replaying two cars in animation and running it, which are copied and pasted from the professors' codes. 