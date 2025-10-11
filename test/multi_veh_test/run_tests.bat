@echo off
REM =========================================================================
REM Headless Test Runner for Multi Vehicle Test Cases
REM =========================================================================
REM Description:
REM   Runs all Simulink test cases in headless mode (no GUI) and generates
REM   a comprehensive PDF report with plots and warnings.
REM
REM Usage:
REM   Double-click this file or run from command line: run_tests.bat
REM
REM Output:
REM   - Results saved to: test\multi_veh_test\results\
REM   - PDF report: test_report_YYYYMMDD_HHMMSS.pdf
REM
REM Requirements:
REM   - MATLAB installed and available in PATH
REM   - MATLAB Report Generator toolbox
REM =========================================================================

echo =========================================================================
echo Starting Automated Test Suite...
echo =========================================================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Remove trailing backslash
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Calculate the project root directory (two levels up from script directory)
set PROJECT_DIR=%SCRIPT_DIR%\..\..

REM Convert to forward slashes for MATLAB compatibility
set MATLAB_SCRIPT_DIR=%SCRIPT_DIR:\=/%
set MATLAB_PROJECT_DIR=%PROJECT_DIR:\=/%

echo Test directory: %SCRIPT_DIR%
echo MATLAB script directory: %MATLAB_SCRIPT_DIR%
echo MATLAB project directory: %MATLAB_PROJECT_DIR%
echo.

REM Run MATLAB in batch mode (no GUI), setting the working directory to the project root
matlab -batch "try, cd('%MATLAB_PROJECT_DIR%'); disp(['Current directory set to: ', pwd]); addpath('%MATLAB_SCRIPT_DIR%'); run_all_multi_test; catch e, disp(['Error: ', e.message]); exit(1); end; exit;"

echo.
echo =========================================================================
echo Test execution complete!
=========================================================================
echo.
echo Results are available in: %SCRIPT_DIR%\results\
echo.

pause