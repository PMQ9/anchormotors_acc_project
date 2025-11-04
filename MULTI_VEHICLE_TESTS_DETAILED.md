# Multi-Vehicle Test Cases - Comprehensive Documentation

**Total Test Cases: 78**
**Location:** `test/multi_veh_test/`
**Framework:** MATLAB/Simulink with Report Generator
**Simulation Default Time:** 20 seconds (extended to 50 seconds for oscillation and long-run tests)

---

## Overview

The multi-vehicle test suite validates the complete Adaptive Cruise Control (ACC) system behavior with lead vehicle interactions. All tests enforce standardized validation constraints through the `multi_vehicle_test_subsystem.slx` validation framework.

### Universal Validation Criteria (Applied to All 78 Tests)

All test cases must satisfy these constraints throughout simulation:

| Constraint | Metric | Criteria | Purpose |
|-----------|--------|----------|---------|
| **Space Gap** | Minimum safe distance | Gap ≥ threshold (varies by mode) | Prevents collisions |
| **Jerk** | Rate of acceleration change | \|Jerk\| ≤ max threshold | Passenger comfort, ride quality |
| **Acceleration** | Command acceleration | a_min ≤ a_cmd ≤ a_max | System capability limits |
| **Velocity** | Vehicle speed | 0 ≤ v ≤ 35 m/s (126 km/h) | Physical limits, safety ceiling |
| **Hard Braking** | Emergency deceleration | a ≥ a_hard_brake_threshold | Avoids aggressive braking |

**Default Constraints:**
- Minimum space gap: 3-5m (mode-dependent)
- Maximum jerk: 2-3 m/s³
- Acceleration range: [-5, +2] m/s² (typical)
- Maximum velocity: 35 m/s

### Simulation Data Logging

All tests include "To Workspace" blocks saving data in **Structure with Time** format:
- Ego vehicle signals (position, velocity, acceleration, jerk)
- Lead vehicle signals (position, velocity, acceleration)
- Behavioral state signals (current mode, mode transitions)
- Command acceleration output

---

## Category 1: Basic Lead Vehicle Scenarios (Cases 1-10)

**Purpose:** Validate ACC command acceleration response in fundamental traffic scenarios
**Simulation Time:** 20 seconds (default)
**Focus:** Single condition validation, basic controller functionality

### Test Details

| Case | Name | Initial Conditions | Scenario | What's Tested |
|------|------|-------------------|----------|---------------|
| **1** | Lead Car Stationary, Ego Moving | Lead: v=0 m/s, gap=50m; Ego: v=15 m/s | Lead vehicle stationary while ego approaches from behind | Deceleration command generation, safe approach to stationary vehicle |
| **2** | Lead Steady Then Slows | Both: v=20 m/s, gap=50m; Lead: accel 0→-2 m/s² | Lead vehicle maintains speed then decelerates | Transition from constant to decreasing relative velocity |
| **3** | Lead Increasing Space Gap | Both: v=20 m/s, gap=50m; Lead: accel=+5 m/s² | Lead vehicle accelerates away from ego | Acceleration command when distance increases, spacing control |
| **4** | Cut Out (Lead Disappears) | Both: v=20 m/s, gap=50m; Lead: gap→200m | Lead vehicle exits to adjacent lane creating large gap | Cut-out detection, acceleration when lead vehicle no longer present |
| **5** | Cut In (Lead Appears) | Ego: v=20 m/s; Lead: appears 100m closer suddenly | Lead vehicle suddenly appears in path from adjacent lane | Rapid deceleration response, transient handling with exception windows |
| **6** | Lead Decreasing Space Gap | Both: v=20 m/s, gap=40m; Lead: decel=-0.5 m/s² | Lead vehicle decelerates slower than ego's natural deceleration | Gap closure handling, maintaining minimum spacing |
| **7** | Lead Slows Then Steady | Ego: v=20 m/s, gap=50m; Lead: accel -2→0 m/s² | Lead vehicle decelerates then stabilizes at lower speed | Tracking acceleration change, settling to new steady state |
| **8** | Lead Speeds Up, Ego Starts | Both: v=0 m/s, gap=30m; Both accelerate | Both vehicles at rest; lead accelerates first, ego follows | Acceleration from standstill, gap management during acceleration |
| **9** | Both Stopped, Gap Too Big | Both: v=0 m/s, gap=200m; Lead: accel=0 | Both vehicles stationary with excessive spacing | System behavior when gap exceeds desired following distance |
| **10** | Lead and Ego Steady State | Both: v=20 m/s, gap=50m; Lead: accel=0 | Steady-state following scenario at constant velocity | Baseline stable following, no transient disturbances |

### What's Being Validated

- Basic acceleration/deceleration command generation
- Proper response to step changes in relative velocity
- Cut-in/cut-out detection mechanisms
- Steady-state following performance
- Initial transient response

---

## Category 2: Mode Classification Tests (Cases 11-24)

**Purpose:** Verify correct behavioral mode identification and mode transition sequences
**Simulation Time:** 20 seconds (default)
**Focus:** Mode classification logic, transition conditions, robustness to sensor noise

### Behavioral Modes Overview

The ACC system operates in distinct behavioral modes based on traffic conditions:

- **Mode 0:** Standard following mode with lead vehicle present (primary mode)
- **Mode 1:** Transition/intermediate state between stable modes
- **Mode 2:** Alternative control strategy (different spacing policy or control law)
- **Mode 3:** Additional behavioral state for specific traffic conditions

### Test Details

| Case | Name | Noise Type | Scenario | What's Tested |
|------|------|-----------|----------|---------------|
| **11** | Mode 0 (Baseline) | None | Pure Mode 0 operation | Mode 0 control logic, baseline behavior |
| **12** | Mode 0 + Random Noise | Gaussian (0-mean) | Mode 0 with random sensor noise | Mode 0 noise rejection, stability under measurement disturbances |
| **13** | Mode 2 (Baseline) | None | Pure Mode 2 operation | Mode 2 control logic, alternative control strategy |
| **14** | Mode 2 + Random Noise | Gaussian (0-mean) | Mode 2 with random sensor noise | Mode 2 noise rejection capabilities |
| **15** | Mode 0→1→2 Transition | None | Sequential mode transitions | Forward transition sequence through intermediate Mode 1 |
| **16** | Mode 0→1→2 + Noise | Gaussian (0-mean) | Mode transition with sensor noise | Transition robustness under noisy conditions |
| **17** | Mode 2→3→0 Transition | None | Reverse mode sequence | Backward transition through Mode 3 |
| **18** | Mode 2→3→0 + Noise | Gaussian (0-mean) | Reverse transition with sensor noise | Reverse transition robustness under disturbances |
| **19** | Mode 0 + Sine Noise | Sinusoidal (harmonic) | Mode 0 with periodic noise | Harmonic disturbance rejection, frequency response |
| **20** | Mode 2 + Sine Noise | Sinusoidal (harmonic) | Mode 2 with periodic noise | Mode 2 harmonic disturbance suppression |
| **21** | Mode 0→1→2 + Sine Noise | Sinusoidal (harmonic) | Forward transition with harmonic noise | Transition stability under harmonic perturbations |
| **22** | Mode 2→3→0 + Sine Noise | Sinusoidal (harmonic) | Reverse transition with harmonic noise | Reverse transition under periodic disturbances |
| **23** | Mode 0→1→3 Transition | None | Alternative forward path | Transition through Mode 1 to Mode 3 (not Mode 2) |
| **24** | Mode 2→3→1 Transition | None | Alternative reverse path | Transition sequence Mode 2→3→1 |

### Noise Characteristics

**Random Gaussian Noise:**
- Zero-mean normal distribution
- Typical magnitude: ±5-10% of signal range
- Simulates sensor measurement errors

**Sinusoidal Noise:**
- Periodic harmonic disturbance
- Typical frequency: 0.5-2 Hz
- Amplitude: ±2-5% of signal range
- Models rhythmic traffic patterns or sensor coupling

### What's Being Validated

- Correct mode classification based on traffic conditions
- Smooth mode transition sequences
- Robustness to random sensor noise in each mode
- Harmonic disturbance rejection
- Alternative transition paths between modes

---

## Category 3: Lead Vehicle Oscillations (Cases 25-63)

**Purpose:** Validate ACC robustness to lead vehicle speed variations over extended periods
**Simulation Time:** 50 seconds (long-run, extended duration)
**Focus:** Extended transient response, stability under sustained perturbations, constraint compliance

### Mode 0 Oscillation Tests (Cases 25-39): 15 Parametric Variations

**Test Pattern:** `case_25-39_mode0_lead_oscillates_N`

Each case tests Mode 0 (standard following) under different lead vehicle oscillation patterns with varying:
- Oscillation frequency (0.2-2 Hz range)
- Oscillation amplitude (±1-5 m/s variations in lead velocity)
- Wave shapes (sinusoidal, triangular, or sawtooth patterns)

**Validation Metrics (50-second window):**
- Steady-state tracking error
- Peak acceleration magnitudes
- Cumulative constraint violations
- Jerk compliance over extended period
- Gap minimum maintenance
- System stability (no divergence or instability)

| Case # | Pattern Variant | Oscillation Type | Typical Frequency | Typical Amplitude |
|--------|-----------------|------------------|-------------------|-------------------|
| 25 | Variant 1 | Sinusoidal | 0.2 Hz | ±1 m/s |
| 26 | Variant 2 | Sinusoidal | 0.3 Hz | ±1.5 m/s |
| 27 | Variant 3 | Sinusoidal | 0.5 Hz | ±2 m/s |
| 28 | Variant 4 | Triangular | 0.4 Hz | ±2 m/s |
| 29 | Variant 5 | Mixed frequency | Combined | ±1.5 m/s |
| 30 | Variant 6 | Sinusoidal | 0.6 Hz | ±2.5 m/s |
| 31 | Variant 7 | Sinusoidal | 0.8 Hz | ±3 m/s |
| 32 | Variant 8 | Sawtooth | 0.5 Hz | ±2 m/s |
| 33 | Variant 9 | Sinusoidal | 1.0 Hz | ±2 m/s |
| 34 | Variant 10 | Sinusoidal | 1.2 Hz | ±2.5 m/s |
| 35 | Variant 11 | Sinusoidal | 1.5 Hz | ±2.5 m/s |
| 36 | Variant 12 | Complex | Multi-frequency | ±1.5-3 m/s |
| 37 | Variant 13 | Sinusoidal | 0.7 Hz | ±2 m/s |
| 38 | Variant 14 | Sinusoidal | 1.1 Hz | ±3 m/s |
| 39 | Variant 15 | Sinusoidal | 0.9 Hz | ±2.5 m/s |

### Mode 2 Oscillation Tests (Cases 40-63): 24 Parametric Variations

**Test Pattern:** `case_40-63_mode2_lead_oscillates_N`

Each case tests Mode 2 (alternative control) under different oscillation scenarios. Wider parametric coverage (24 vs 15) reflects Mode 2's broader applicability:

- More oscillation frequency variations
- Extended amplitude ranges
- Combined multi-frequency disturbances
- Mode 2-specific constraint validation

**Validation Metrics (50-second window):**
- Mode 2 tracking performance
- Acceleration command smoothness
- Gap stability under Mode 2 control law
- Jerk suppression in Mode 2
- Transition behavior if mode changes during oscillation

| Case # | Pattern Variant | Oscillation Type | Typical Frequency | Typical Amplitude |
|--------|-----------------|------------------|-------------------|-------------------|
| 40 | Variant 1 | Sinusoidal | 0.2 Hz | ±1 m/s |
| 41 | Variant 2 | Sinusoidal | 0.3 Hz | ±1.5 m/s |
| 42 | Variant 3 | Sinusoidal | 0.4 Hz | ±1.5 m/s |
| 43 | Variant 4 | Triangular | 0.3 Hz | ±2 m/s |
| 44 | Variant 5 | Sinusoidal | 0.5 Hz | ±2 m/s |
| 45 | Variant 6 | Sinusoidal | 0.6 Hz | ±2.5 m/s |
| 46 | Variant 7 | Sawtooth | 0.4 Hz | ±2 m/s |
| 47 | Variant 8 | Sinusoidal | 0.7 Hz | ±2.5 m/s |
| 48 | Variant 9 | Sinusoidal | 0.8 Hz | ±2.5 m/s |
| 49 | Variant 10 | Sinusoidal | 0.9 Hz | ±2 m/s |
| 50 | Variant 11 | Sinusoidal | 1.0 Hz | ±2.5 m/s |
| 51 | Variant 12 | Sinusoidal | 1.1 Hz | ±2.5 m/s |
| 52 | Variant 13 | Sinusoidal | 1.2 Hz | ±3 m/s |
| 53 | Variant 14 | Sinusoidal | 1.3 Hz | ±2.5 m/s |
| 54 | Variant 15 | Multi-frequency | Combined | ±2-3 m/s |
| 55 | Variant 16 | Sinusoidal | 0.5 Hz | ±3 m/s |
| 56 | Variant 17 | Sinusoidal | 0.65 Hz | ±2.5 m/s |
| 57 | Variant 18 | Sinusoidal | 1.5 Hz | ±2 m/s |
| 58 | Variant 19 | Sinusoidal | 1.6 Hz | ±2 m/s |
| 59 | Variant 20 | Complex | Multi-frequency | ±1.5-3 m/s |
| 60 | Variant 21 | Sinusoidal | 0.75 Hz | ±2 m/s |
| 61 | Variant 22 | Sinusoidal | 1.8 Hz | ±1.5 m/s |
| 62 | Variant 23 | Sinusoidal | 0.95 Hz | ±2.5 m/s |
| 63 | Variant 24 | Sinusoidal | 1.4 Hz | ±2.5 m/s |

### What's Being Validated

- **Extended stability:** System maintains constraints over 50-second window without divergence
- **Frequency response:** Proper attenuation of oscillations at different frequencies
- **Control robustness:** Handling of sustained perturbations without saturation
- **Comfort metrics:** Jerk limits maintained even under continuous disturbances
- **Steady-state accuracy:** Average tracking error remains within acceptable bounds

---

## Category 4: Parametric Cut-in Tests - Mode 0 (Cases 64-72)

**Purpose:** Comprehensive validation of ACC response to lead vehicle cut-in scenarios
**Simulation Time:** 20 seconds (default, extended as needed for transient settling)
**Focus:** Systematic parameter variation, constraint compliance during transients, exception handling

### Cut-in Naming Convention

```
case_N_cut_in_sn_X_dv_Y_v0_Z.slx
```

- **sn_X:** Spacing at cut-in event (meters)
- **dv_Y:** Relative velocity of cut-in vehicle (m/s)
- **v0_Z:** Ego vehicle initial velocity (m/s)

### Mode 0 Cut-in Parameter Space: 3×3 Matrix

**Systematic Coverage:** Spacing (3 levels) × Relative velocity (3 levels) = 9 combinations

| Parameter | Values | Interpretation |
|-----------|--------|-----------------|
| **Spacing at Cut-in (sn)** | {4, 8, 15} m | **4m** (tight, near collision risk), **8m** (medium, normal cut-in), **15m** (relaxed, safe) |
| **Relative Velocity (dv)** | {10, 15, 20} m/s | **10 m/s** (low closing speed), **15 m/s** (medium), **20 m/s** (high, aggressive) |
| **Ego Initial Velocity (v0)** | {20} m/s | Fixed at highway speed (72 km/h) |

### Test Matrix

| Case | sn (m) | dv (m/s) | v0 (m/s) | Scenario Name | Criticality |
|------|--------|----------|----------|---------------|-------------|
| **64** | 4 | 10 | 20 | Tight spacing, low closing speed | **HIGH** (dangerous spacing) |
| **65** | 8 | 10 | 20 | Medium spacing, low closing speed | MEDIUM |
| **66** | 15 | 10 | 20 | Relaxed spacing, low closing speed | LOW |
| **67** | 4 | 15 | 20 | Tight spacing, medium closing speed | **CRITICAL** (tight + medium speed) |
| **68** | 8 | 15 | 20 | Medium spacing, medium closing speed | MEDIUM |
| **69** | 15 | 15 | 20 | Relaxed spacing, medium closing speed | LOW |
| **70** | 4 | 20 | 20 | Tight spacing, high closing speed | **CRITICAL** (tightest scenario) |
| **71** | 8 | 20 | 20 | Medium spacing, high closing speed | MEDIUM-HIGH |
| **72** | 15 | 20 | 20 | Relaxed spacing, high closing speed | MEDIUM |

### Cut-in Exception Handling

**Important Implementation Detail:**

Cut-in events create temporary transient conditions that violate normal constraints:
- Initial gap may be below minimum threshold immediately after cut-in
- Acceleration may spike sharply (high jerk)
- System requires time to stabilize

**Exception Windows:**
- Duration: Typically 0.5-1.5 seconds post-cut-in
- Purpose: Suppress false warnings during legitimate transient suppression
- Configuration: Each test specifies exception time window in model parameters

**Validation Philosophy:**
- Constraints are NOT ignored during exception window
- Instead, violations are tracked but flagged as "transient" not "failure"
- PDF report distinguishes transient violations from persistent failures

### What's Being Validated

- **Rapid deceleration capability:** How quickly ego responds to sudden appearance
- **Gap recovery:** Time to restore safe spacing after cut-in
- **Constraint satisfaction:** Final acceleration/jerk within limits after exception window
- **No hard braking:** Avoids emergency braking even in tightest scenarios
- **Predictable behavior:** Consistent response across parameter space

---

## Category 5: Parametric Cut-in Tests - Mode 2 (Cases 73-76)

**Purpose:** Validate Mode 2 control strategy specifically for low-speed cut-in scenarios
**Simulation Time:** 20 seconds (default)
**Focus:** Mode 2-specific behavior, low-speed traffic, tight spacing scenarios

### Mode 2 Cut-in Parameter Space: 2×2 Matrix (Reduced)

Mode 2 focuses on low-speed, close-proximity scenarios (parking, slow traffic):

| Parameter | Values | Interpretation |
|-----------|--------|-----------------|
| **Spacing at Cut-in (sn)** | {3, 7} m | **3m** (very tight, urban), **7m** (relaxed urban) |
| **Relative Velocity (dv)** | {5} m/s | Fixed at low speed (18 km/h closing) |
| **Ego Initial Velocity (v0)** | {5, 8} m/s | **5 m/s** (low speed), **8 m/s** (medium low) |

### Test Matrix

| Case | sn (m) | dv (m/s) | v0 (m/s) | Scenario Name | Context |
|------|--------|----------|----------|---------------|---------|
| **73** | 3 | 5 | 5 | Very tight spacing, low speeds | Urban parking lot scenario |
| **74** | 7 | 5 | 5 | Relaxed spacing, low speeds | Low-speed traffic, safe spacing |
| **75** | 3 | 5 | 8 | Very tight spacing, medium-low speeds | Dense urban traffic |
| **76** | 7 | 5 | 8 | Relaxed spacing, medium-low speeds | Moderate urban traffic |

### What's Being Validated

- **Mode 2 transient response:** Slower, more measured response appropriate for low speeds
- **Urban compatibility:** Safe operation in tight-spacing scenarios (parking lots, congestion)
- **Smooth acceleration/deceleration:** Less aggressive than Mode 0, comfort-oriented
- **Precise gap control:** Mode 2 specialized for small-gap management
- **Mode 2 exception handling:** Cut-in exception windows specific to Mode 2

---

## Category 6: Edge Cases & Special Scenarios (Cases 77-78)

**Purpose:** Boundary conditions and specialized scenario validation
**Simulation Time:** 20 seconds (default)
**Focus:** System robustness at limits, specialized mode validation

### Test Details

| Case | Name | Scenario | What's Tested |
|------|------|----------|----------------|
| **77** | Mode 0: Slow But Far | Lead vehicle moving very slowly (5-8 m/s) but at safe large distance (100+ m) | Mode identification when relative velocity is near zero but distance exceeds threshold; validates correct mode selection with low closing speed |
| **78** | Mode 0→1→2: Approach Distant Car | ACC approaches lead vehicle from long distance and transitions through modes as distance decreases | Complete forward mode transition sequence during closure maneuver; validates mode transitions triggered by changing spatial relationship |

### What's Being Validated

- **Edge condition handling:** System behavior at parameter boundaries
- **Low relative velocity:** Correct mode selection when gap is large but relative velocity minimal
- **Mode transition completeness:** Full sequence validation in realistic driving scenario
- **Distance-driven transitions:** Proper mode changes triggered by spatial relationships

---

## Test Execution & Reporting

### Test Runner: `run_all_multi_test.m`

**Key Features:**

```matlab
% Automatic test discovery
baseDir = 'test/multi_veh_test/';
modelFiles = dir([baseDir 'case_*.slx']);

% Filter out subsystem files
modelFiles = modelFiles(~contains({modelFiles.name}, 'subsystem'));

% Simulation time configuration
defaultStopTime = 20;  % seconds
longRunStopTime = 50;  % seconds for extended tests

% Long-run models (oscillations)
longRunModels = {...
    'case_25_mode0_lead_oscillates_1', ...  % through case_39
    'case_40_mode2_lead_oscillates_1', ...  % through case_63
};
```

### Test Report Generation

**Output Format:** `test_report_YYYYMMDD_HHMMSS.pdf`

**Report Contents:**

1. **Executive Summary**
   - Total tests run: N
   - Passed: X
   - Warned: Y
   - Failed: Z

2. **Test-by-Test Results**
   - Test case name and parameters
   - Pass/fail/warn status
   - Simulation warnings and errors

3. **Signal Plots** (per test)
   - Space gap vs time (with minimum threshold line)
   - Ego velocity vs time
   - Command acceleration vs time (with bounds)
   - Jerk vs time (with maximum threshold line)
   - Lead vehicle velocity (reference)

4. **Constraint Violation Summary**
   - Gap minimum breaches
   - Acceleration bound violations
   - Jerk violations
   - Velocity ceiling violations
   - Hard braking events

5. **Warning/Error Categories**
   - Warnings grouped by type
   - Error counts by category
   - Exception window violations (distinguished from failures)

### Data Logging

All tests capture data to MATLAB workspace using "To Workspace" blocks:

**Ego Vehicle Subsystem:**
- Position: x_ego (m)
- Velocity: v_ego (m/s)
- Acceleration: a_ego (m/s²)
- Jerk: j_ego (m/s³)
- Time vector: t (seconds)

**Lead Vehicle Subsystem:**
- Position: x_lead (m)
- Velocity: v_lead (m/s)
- Acceleration: a_lead (m/s²)
- Time vector: t (seconds)

**Behavioral State Subsystem:**
- Current mode: mode (0, 1, 2, or 3)
- Mode transition events: mode_change_time (seconds)
- Classification signals: (intermediate values)

---

## Constraint Thresholds & Limits

### Standard Constraint Values

| Constraint | Minimum | Nominal | Maximum | Unit | Mode |
|-----------|---------|---------|---------|------|------|
| Space gap | 3-5 | 8-15 | 200+ | m | Mode-dependent |
| Jerk | - | 0 | ±2.5 | m/s³ | All |
| Acceleration | -5 | -1 to +1 | +2 | m/s² | All |
| Velocity | 0 | 15-25 | 35 | m/s | All |
| Hard brake threshold | - | - | -4.5 | m/s² | All |

### Mode-Specific Thresholds

| Parameter | Mode 0 | Mode 1 | Mode 2 | Mode 3 |
|-----------|--------|--------|--------|--------|
| Target gap (m) | 12-15 | Variable | 8-10 | 5-8 |
| Max acceleration (m/s²) | 1.5 | 1.2 | 1.0 | 0.8 |
| Max jerk (m/s³) | 2.5 | 2.0 | 2.0 | 2.5 |

---

## Development & Maintenance Notes

### Adding New Test Cases

**For Multi-Vehicle Tests:**
1. Create `case_N_description.slx` in `test/multi_veh_test/`
2. Include `multi_vehicle_test_subsystem.slx` for constraint validation
3. Include data logging subsystems (ego, lead, behavior)
4. If simulation > 20s, add case name to `longRunModels` list in `run_all_multi_test.m`
5. Update this documentation with test category and description
6. Test will be automatically discovered by runner script

### Common Test Modifications

**Changing Simulation Time:**
- Edit `run_all_multi_test.m`
- Modify `defaultStopTime` or add case to `longRunModels` list

**Adjusting Constraint Thresholds:**
- Edit parameters in `multi_vehicle_test_subsystem.slx`
- Update constraint documentation above
- Re-run affected test cases to validate

**Adding Sensor Noise:**
- Include noise generator blocks in lead vehicle subsystem
- Specify noise type (Gaussian, sinusoidal, etc.)
- Update test case naming to reflect noise addition

---

## Understanding Test Results

### Interpreting Pass/Fail Status

**PASS:** All constraints satisfied throughout simulation, no warnings

**WARN:** Constraints satisfied but warnings issued (e.g., close to threshold during transient)

**FAIL:** One or more constraints violated in non-exception window

### Transient vs. Persistent Violations

**Transient (OK):**
- Occurs within exception window after cut-in event
- Expected behavior during system response
- Tracked but not counted as failure
- Example: Gap < minimum for 0.5s after cut-in, then recovers

**Persistent (FAIL):**
- Occurs outside exception window or without exception event
- Indicates control system inadequacy
- Requires investigation and corrective action
- Example: Gap remains < minimum after 5 seconds of normal operation

### Reading Signal Plots

**Space Gap Plot:**
- Look for minimum crossings
- Exception windows shown as shaded regions
- Gap should remain above threshold line except during exceptions

**Acceleration Plot:**
- Check for excessive transients (spikes)
- Verify bounded within a_min and a_max
- Sharp corners indicate high jerk

**Jerk Plot:**
- Should be smooth, peak < threshold
- Discontinuities indicate control mode changes or sharp input steps
- Rising edge magnitude indicates acceleration aggressiveness

---

## CI/CD Integration

### Automated Testing

Tests are run automatically on:
- **PR Triggers:** All PRs to `master`, `main`, or `develop` branches
- **Scheduled:** Weekly Monday 9:00 AM UTC
- **Manual:** GitHub Actions → Weekly Automated Tests → Run workflow

### Test Monitoring

- **Dashboard:** [Grafana Dashboard](https://pmq9.grafana.net/public-dashboards/09e1212bd2f5467d9a5c53ad9e4237c3)
- **Reports:** Stored in `test/multi_veh_test/results/`
- **Emergency Bypass:** Set `ALLOW_PR_CI_TEST_BYPASS` secret if needed

See [.github/CI_CD_SETUP.md](.github/CI_CD_SETUP.md) for detailed CI/CD documentation.

---

## Summary Table: All 78 Tests at a Glance

| Category | Cases | Count | Sim Time | Primary Focus |
|----------|-------|-------|----------|----------------|
| Basic Lead Vehicle Scenarios | 1-10 | 10 | 20s | Fundamental behavior |
| Mode Classification | 11-24 | 14 | 20s | Mode transitions, robustness to noise |
| Mode 0 Oscillations | 25-39 | 15 | 50s | Extended robustness (Mode 0) |
| Mode 2 Oscillations | 40-63 | 24 | 50s | Extended robustness (Mode 2) |
| Mode 0 Cut-in (3×3) | 64-72 | 9 | 20s | Systematic cut-in parameter space |
| Mode 2 Cut-in (2×2) | 73-76 | 4 | 20s | Low-speed cut-in scenarios |
| Edge Cases & Special | 77-78 | 2 | 20s | Boundary conditions |
| **TOTAL** | | **78** | **20-50s** | **Complete ACC validation** |

---

## References & Related Documentation

- **Project Documentation:** [CLAUDE.md](CLAUDE.md)
- **CI/CD Setup:** [.github/CI_CD_SETUP.md](.github/CI_CD_SETUP.md)
- **Test Results:** [test/multi_veh_test/results/](test/multi_veh_test/results/)
- **Test Runner:** [test/multi_veh_test/run_all_multi_test.m](test/multi_veh_test/run_all_multi_test.m)
- **Validation Subsystem:** [test/multi_veh_test/multi_vehicle_test_subsystem.slx](test/multi_veh_test/multi_vehicle_test_subsystem.slx)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Maintained by:** ACC Development Team
**Status:** Complete - All 78 test cases documented
