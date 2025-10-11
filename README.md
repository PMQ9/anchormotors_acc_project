# anchormotors project

# User Manual

## Requirements
- MATLAB 2025a
- MATLAB Report Generator toolbox

## Automated Testing

Run all test cases automatically with timestamped PDF reports and plots.

**Single Vehicle Tests:**
- **Headless (Windows)**: Double-click `test/single_veh_test/run_tests.bat`
- **MATLAB Console**: Run `test/single_veh_test/run_all_single_test.m`
- **Results**: `test/single_veh_test/results/test_report_YYYYMMDD_HHMMSS.pdf`

**Multi Vehicle Tests:**
- **Headless (Windows)**: Double-click `test/multi_veh_test/run_tests.bat`
- **MATLAB Console**: Run `test/multi_veh_test/run_all_multi_test.m`
- **Results**: `test/multi_veh_test/results/test_report_YYYYMMDD_HHMMSS.pdf`

**Setup Requirements:**
- Add **To Workspace** blocks to Simulink models (Format: `Structure with Time`)
- MATLAB Report Generator toolbox must be installed

**Report Contents:**
- Pass/fail summary for all test cases
- Individual test results with plots
- Captured warnings and errors from simulation