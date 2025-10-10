# anchormotors project

# User Manual

## Requirements
- MATLAB 2025a
- MATLAB Report Generator toolbox

## Automated Testing

### Single Vehicle Test Suite

Automatically run all single vehicle test cases with automated reporting:

**Quick Start:**
1. Add **To Workspace** blocks to your Simulink models
   - Format: `Structure with Time`
   - Variable name: e.g., `ego_velocity`, `lead_position`

2. Run tests:
   - **Headless (Windows)**: Double-click `test/single_veh_test/run_tests.bat`
   - **MATLAB Console**: Run `test/single_veh_test/run_all_single_test.m`

3. View results in: `test/single_veh_test/results/`
   - `test_report_YYYYMMDD_HHMMSS.pdf` - Comprehensive PDF report
   - `*_plots.png` - Plot images for each test case
   - `*_warnings.txt` - Warning logs

**Report Contents:**
- Test summary (passed/failed counts)
- Individual test case results with plots
- Captured warnings and errors from Simulink blocks
- Test execution timestamp

### Single Vehicle Test Suite

WIP