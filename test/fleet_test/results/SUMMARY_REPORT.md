# Synthetic Fleet Simulation — Summary Report

**Date**: 2026-02-23
**Controller**: 4-State FSM-Based ACC (acc_controller.py)
**Fleet**: 25 vehicles, IDM human drivers (1.5s headway, 200ms reaction delay)
**Penetration rates tested**: 5%, 10%, 20%, 50%, 75%, 100% ACC
**Simulation**: 100s duration, 20 Hz control rate, initial velocity 20 m/s

---

## 1. Test Matrix

| # | Scenario | Lead Vehicle Behavior |
|---|----------|-----------------------|
| 01a | Constant slow | Steady 15 m/s |
| 01b | Constant medium | Steady 20 m/s (baseline) |
| 01c | Constant fast | Steady 25 m/s |
| 02a | Small slow oscillation | ±2 m/s, 30s period |
| 02b | Medium oscillation | ±5 m/s, 20s period |
| 02c | Large fast oscillation | ±7 m/s, 10s period |
| 02d | Multi-frequency oscillation | Combined 40s + 10s periods |
| 03a | Gradual acceleration | 15→25 m/s over 5s |
| 03b | Rapid acceleration | 15→25 m/s over 2s |
| 04a | Gradual deceleration | 25→15 m/s over 5s |
| 04b | Rapid deceleration | 25→15 m/s over 2s (emergency) |
| 04c | Severe deceleration | 25→10 m/s over 3s |
| 05a | Two-state step changes | 15↔25 m/s every 15s |
| 05b | Three-state step changes | 15→20→25 m/s every 10s |
| 05c | Frequent step changes | 18↔22 m/s every 8s |

---

## 2. Metrics

- **Min Space Gap (m)**: Smallest inter-vehicle gap — safety indicator
- **Mean Space Gap (m)**: Average following distance
- **Max Decel (m/s²)**: Hardest braking event — comfort/safety
- **Velocity Std (m/s)**: Fleet speed variance — throughput efficiency
- **String Stability**: Ratio of velocity variance (tail vs head); <1.0 = stable, >1.0 = amplifying

---

## 3. Results Summary by Scenario

### 3.1 Constant Speed (01a–01c)

| Scenario | String Stability (5%→100%) | Improvement | Min Gap (5%→100%) |
|----------|---------------------------|-------------|-------------------|
| 01a Slow (15 m/s) | 2.70 → 0.00 | ~100% | 28.6 m → 43.2 m |
| 01b Medium (20 m/s) | 2.46 → 0.00 | ~100% | 44.6 m → 54.3 m |
| 01c Fast (25 m/s) | 1.01 → 0.00 | ~100% | 56.5 m → 68.0 m |

**Observations**: Excellent performance in steady-state conditions. At 100% ACC, string stability drops to near zero (perfect attenuation). Min space gap increases substantially (~50% larger at 100% vs 5%). Very low deceleration demands (< 0.4 m/s²). The initial transient from fleet settling is the only source of disturbance.

### 3.2 Oscillation Patterns (02a–02d)

| Scenario | String Stability (5%→100%) | Improvement | Min Gap (5%→100%) |
|----------|---------------------------|-------------|-------------------|
| 02a Small slow | 3.57 → 2.09 | 41.2% | 39.5 m → 50.2 m |
| 02b Medium | 2.12 → 1.08 | 50.4% | 40.9 m → 44.7 m |
| 02c Large fast | 2.15 → 0.40 | 82.1% | 43.5 m → 45.5 m |
| 02d Multi-frequency | 1.86 → **10.8** | **-185%** (degraded) | 37.5 m → 45.7 m |

**Observations**: Performance scales well for single-frequency oscillations. Larger/faster oscillations actually see better improvement than small/slow ones. However, **02d (multi-frequency) is a notable failure case** — string stability degrades dramatically at 100% ACC (10.8 vs 1.86), with velocity std rising from 0.9 to 1.6. The controller struggles with superimposed frequency content. Min gap still improves, so safety is not compromised — the issue is amplification of velocity oscillations through the fleet.

### 3.3 Sudden Acceleration (03a–03b)

| Scenario | String Stability (5%→100%) | Improvement | Min Gap (5%→100%) |
|----------|---------------------------|-------------|-------------------|
| 03a Gradual (5s) | 0.54 → 0.10 | 86.2% | 29.4 m → 43.2 m |
| 03b Rapid (2s) | 0.59 → 0.08 | 88.4% | 29.5 m → 43.2 m |

**Observations**: Strong performance. String stability already <1.0 even at 5% (acceleration is inherently easier than braking). At 100% ACC, disturbance attenuation is excellent. Min gap increases by ~47%. Max decel remains mild (~1.4 m/s²).

### 3.4 Sudden Deceleration (04a–04c) — Safety-Critical

| Scenario | String Stability (5%→100%) | Improvement | Min Gap (5%→100%) |
|----------|---------------------------|-------------|-------------------|
| 04a Gradual (5s) | 20.5 → 2.60 | 98.0% | 26.6 m → 43.2 m |
| 04b Rapid (2s) | 29.6 → 2.31 | 98.7% | 28.6 m → 43.2 m |
| 04c Severe (25→10) | 47.7 → 0.37 | 99.2% | 18.1 m → 32.8 m |

**Observations**: This is where the controller's impact is most dramatic. At 5% ACC, sudden deceleration causes severe string instability (ratios of 20–48×), meaning velocity disturbances amplify massively through the fleet. At 100% ACC, these ratios collapse to 0.4–2.6. Min gap improves significantly (18→33 m in the severe case). Max deceleration reaches -2.96 m/s² at 100% ACC (within the -3.0 limit) for rapid braking — the controller uses nearly the full braking authority. Jerk peaks at ~6.8 m/s³ at 100% ACC (above the 2.5 comfort threshold, but this is an emergency scenario). At 5% ACC with mostly human drivers, max jerk reaches 11.8 m/s³ — the ACC still dramatically improves comfort.

### 3.5 Step Changes (05a–05c)

| Scenario | String Stability (5%→100%) | Improvement | Min Gap (5%→100%) |
|----------|---------------------------|-------------|-------------------|
| 05a Two-state | 0.33 → 0.83 | **-55.7%** (degraded) | 30.7 m → 43.2 m |
| 05b Three-state | 0.88 → 0.76 | 13.2% | 34.2 m → 43.3 m |
| 05c Frequent | 2.10 → 0.20 | 90.2% | 41.5 m → 50.0 m |

**Observations**: Mixed results. 05c (frequent small steps, ±2 m/s) shows excellent improvement (90%). However, **05a (large two-state steps) degrades** from 0.33 to 0.83 at 100% — though both values are still <1.0, meaning the fleet remains string-stable, the ACC fleet attenuates disturbances less effectively than the human fleet for this pattern. 05b shows marginal improvement. Notably, min gap always improves substantially, so safety is never compromised.

---

## 4. Cross-Scenario Trends

### 4.1 String Stability
- **Best scenarios**: Constant speed (100% improvement), severe deceleration (99%), frequent steps (90%)
- **Worst scenarios**: Multi-frequency oscillation (-185% degradation), two-state steps (-56%)
- **Pattern**: The controller excels at damping single disturbances and high-frequency patterns but can amplify multi-frequency or large-amplitude periodic inputs

### 4.2 Minimum Space Gap
- **Always improves** with higher ACC penetration across all 15 scenarios — no exceptions
- Typical improvement: 30–50% increase from 5% to 100% penetration
- No collisions or near-misses (gap never approaches 5 m safe minimum) in any scenario

### 4.3 Braking Severity (Max Decel)
- Steady-state: < 0.5 m/s² (negligible)
- Oscillations: 1.0–3.0 m/s² depending on amplitude
- Emergency braking: Up to -2.96 m/s² (within -3.0 limit)
- Higher ACC penetration generally requires harder braking in deceleration scenarios (the controller commits to faster braking to maintain gaps), but this stays within limits

### 4.4 Velocity Standard Deviation
- **Increases** with ACC penetration in most oscillation and step-change scenarios
- This is counterintuitive but reflects the ACC's larger time headway (tau ~2.3s vs IDM's 1.5s) — ACC vehicles are more responsive to lead speed changes, tracking them rather than damping them
- Despite higher velocity variance, the fleet remains safer (larger gaps) and more string-stable in most cases

---

## 5. Key Strengths

1. **Safety**: Min space gap improves in every scenario at every penetration rate. Zero collisions across all 90 simulation runs.
2. **Emergency response**: Dramatic reduction in string instability for sudden braking events (up to 99% improvement). This is the most safety-critical scenario category, and the controller handles it well.
3. **Steady-state tracking**: Near-perfect string stability (ratio → 0) for constant-speed following.
4. **Graceful penetration scaling**: Even 10–20% ACC penetration provides measurable benefits in most scenarios.

## 6. Key Weaknesses

1. **Multi-frequency oscillations** (02d): String stability degrades by 185% at 100% ACC. The controller amplifies combined frequency content. This likely stems from the state machine's transition logic interacting poorly with complex wave patterns.
2. **Large-amplitude step changes** (05a): Mild degradation in string stability (though still <1.0). The controller's large tau (2.3s) makes it overshoot during abrupt transitions.
3. **Jerk in transients**: Max jerk reaches 6.8 m/s³ during emergency braking (above 2.5 comfort threshold). The low-pass filter (coeff=0.65) helps but cannot fully smooth step responses.
4. **Velocity variance increase**: In oscillatory scenarios, higher ACC penetration can increase fleet velocity variance even while improving stability ratios. This reflects the tracking-vs-damping tradeoff of the controller gains.

## 7. Recommendations

1. **Multi-frequency robustness**: Investigate adding frequency-dependent gain scheduling or a more sophisticated filter to prevent amplification of combined wave patterns.
2. **State transition smoothing**: The FSM transitions (especially IN_WAVE ↔ OUT_OF_WAVE) during large step changes may benefit from hysteresis or ramp blending to avoid gain discontinuities.
3. **Jerk limiting**: Consider a dedicated jerk limiter (clamp rate of acceleration change) rather than relying solely on the low-pass filter, particularly for emergency scenarios.
4. **Tau tuning**: The time headway (~2.3s) provides excellent safety margins but contributes to velocity variance. A lower tau in steady-state with dynamic increase during disturbances could improve both metrics.

---

## 8. File Inventory

| File Type | Count | Description |
|-----------|-------|-------------|
| Comparison plots (*_comparison.png) | 15 | Metrics vs penetration rate per scenario |
| Detailed plots (*_penetration_*.png) | 90+ | Full fleet dynamics per scenario/rate |
| PDF report | 1 | 107-page comprehensive report |
| **Total simulation runs** | **90** | 15 scenarios × 6 penetration rates |
