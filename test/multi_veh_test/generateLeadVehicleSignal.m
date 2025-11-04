function lead_cmd_accel = generateLeadVehicleSignal(t, ~, ~, lead_velo)
    % GENERATELEADVEHICLESIGNAL
    % MATLAB Function for Simulink MATLAB Function block
    % Generates lead vehicle acceleration commands for case_79_long_full_test
    %
    % Inputs:
    %   t          : Current simulation time (seconds)
    %   v_0        : Not used (placeholder for compatibility)
    %   x_0        : Not used (placeholder for compatibility)
    %   lead_velo  : Current lead vehicle velocity (m/s)
    %
    % Output:
    %   lead_cmd_accel : Lead vehicle acceleration command (m/s²)
    %
    % Usage: Place in MATLAB Function block with signature:
    %   lead_cmd_accel = generateLeadVehicleSignal(t, v_0, x_0, lead_velo)
    %
    % Test Timeline (850 seconds):
    %   0-100s    : Mode 0 stable with sinusoidal oscillation (v > 13.5 m/s)
    %   100-200s  : Mode 2 stable with sinusoidal oscillation (v <= 13.5 m/s)
    %   200-400s  : Into wave scenarios (5 x 40s) - decelerate then follow
    %   400-600s  : Out of wave scenarios (5 x 40s) - follow then accelerate
    %   600-750s  : Mode 0 cut-in scenarios (5 x 30s, high-speed)
    %   750-850s  : Mode 2 cut-in scenarios (5 x 20s, low-speed: v <= 13.5 m/s)
    %
    % Mode Classification:
    %   Mode 0: lead_velo > 13.5 m/s (normal highway following)
    %   Mode 2: lead_velo <= 13.5 m/s (urban/low-speed following)

    % =====================================================================
    % SCENARIO 1: Mode 0 Stable Operation (0-100s)
    % Maintain ~25 m/s with sinusoidal oscillation
    % =====================================================================
    if (t > 0) && (t <= 100)
        target_v = 25;

        % Add sinusoidal variation (0.5 Hz, ±3 m/s)
        v_variation = 3 * sin(2*pi*0.5*t);
        desired_v = target_v + v_variation;

        % Simple P-controller: accel = gain * (desired - actual)
        lead_cmd_accel = 0.1 * (desired_v - lead_velo);

        % Limit acceleration
        lead_cmd_accel = max(lead_cmd_accel, -2);
        lead_cmd_accel = min(lead_cmd_accel, 1.5);
        return;
    end

    % =====================================================================
    % SCENARIO 2: Mode 2 Stable Operation (100-200s)
    % Maintain ~10 m/s with sinusoidal oscillation (Mode 2: v <= 13.5 m/s)
    % =====================================================================
    if (t > 100) && (t <= 200)
        target_v = 10;

        % Add sinusoidal variation (0.3 Hz, ±2 m/s)
        t_local = t - 100;
        v_variation = 2 * sin(2*pi*0.3*t_local);
        desired_v = target_v + v_variation;

        lead_cmd_accel = 0.12 * (desired_v - lead_velo);

        % Limit acceleration (Mode 2 is smoother)
        lead_cmd_accel = max(lead_cmd_accel, -1.5);
        lead_cmd_accel = min(lead_cmd_accel, 1.0);
        return;
    end

    % =====================================================================
    % SCENARIOS 3-7: Into Wave (200-400s)
    % Decelerate from Mode 0 (high speed) to Mode 2 (low speed)
    % Crosses Mode threshold at 13.5 m/s
    % 5 scenarios x 40 seconds
    % =====================================================================
    if (t > 200) && (t <= 400)
        t_scenario = t - 200;
        scenario_num = floor(t_scenario / 40) + 1;
        t_local = mod(t_scenario, 40);

        % Each scenario has different initial and target velocities
        initial_vels = [28, 30, 32, 34, 36];  % Mode 0 (>13.5 m/s)
        target_vels = [9, 10, 11, 12, 13];     % Mode 2 (<=13.5 m/s)

        v_initial = initial_vels(scenario_num);
        v_target = target_vels(scenario_num);

        % Smooth deceleration: ramp down over 25 seconds, then oscillate
        if t_local < 25
            % Deceleration phase: linear ramp
            desired_v = v_initial - (v_initial - v_target) * (t_local / 25);
        else
            % Oscillation phase: maintain target with small oscillation
            v_osc = 0.5 * sin(2*pi*0.2*(t_local - 25));
            desired_v = v_target + v_osc;
        end

        lead_cmd_accel = 0.15 * (desired_v - lead_velo);
        lead_cmd_accel = max(lead_cmd_accel, -2.0);
        lead_cmd_accel = min(lead_cmd_accel, 1.0);
        return;
    end

    % =====================================================================
    % SCENARIOS 8-12: Out of Wave (400-600s)
    % Accelerate from Mode 2 (low speed) to Mode 0 (high speed)
    % Crosses Mode threshold at 13.5 m/s
    % 5 scenarios x 40 seconds
    % =====================================================================
    if (t > 400) && (t <= 600)
        t_scenario = t - 400;
        scenario_num = floor(t_scenario / 40) + 1;
        t_local = mod(t_scenario, 40);

        target_vels = [9, 10, 11, 12, 13];     % Mode 2 (<=13.5 m/s)
        final_vels = [28, 30, 32, 34, 36];     % Mode 0 (>13.5 m/s)

        v_target = target_vels(scenario_num);
        v_final = final_vels(scenario_num);

        % Smooth acceleration: oscillate for 15s, then ramp up
        if t_local < 15
            % Initial oscillation phase
            v_osc = 0.3 * sin(2*pi*0.2*t_local);
            desired_v = v_target + v_osc;
        else
            % Acceleration phase: linear ramp
            time_accel = t_local - 15;
            desired_v = v_target + (v_final - v_target) * (time_accel / 25);
        end

        lead_cmd_accel = 0.12 * (desired_v - lead_velo);
        lead_cmd_accel = max(lead_cmd_accel, -1.0);
        lead_cmd_accel = min(lead_cmd_accel, 2.0);
        return;
    end

    % =====================================================================
    % SCENARIOS 13-17: Mode 0 Cut-in Tests (600-750s)
    % Lead vehicle cut-in: sudden appearance, then decelerate to follow
    % 5 scenarios x 30 seconds
    % =====================================================================
    if (t > 600) && (t <= 750)
        t_scenario = t - 600;
        scenario_num = floor(t_scenario / 30) + 1;
        t_local = mod(t_scenario, 30);

        % Parametric cut-in definitions
        ego_vels = [20, 18, 25, 22, 20];
        rel_vels = [10, 15, 20, 15, 10];

        v0 = ego_vels(scenario_num);
        dv = rel_vels(scenario_num);

        cut_in_time = 2;  % Cut-in event at t=2s

        if t_local < cut_in_time
            % Before cut-in: lead is moving faster
            desired_v = v0 + dv;
        else
            % After cut-in: decelerate to ego velocity
            time_since_cut = t_local - cut_in_time;

            if time_since_cut < 8
                % Deceleration phase: ramp down over 8 seconds
                desired_v = (v0 + dv) - dv * (time_since_cut / 8);
            else
                % Settling phase: maintain with slight oscillation
                v_osc = 0.5 * sin(2*pi*0.3*(time_since_cut - 8));
                desired_v = v0 + v_osc;
            end
        end

        % P-controller with physical velocity limit
        lead_cmd_accel = 0.2 * (desired_v - lead_velo);
        lead_cmd_accel = max(lead_cmd_accel, -3.0);
        lead_cmd_accel = min(lead_cmd_accel, 1.5);
        return;
    end

    % =====================================================================
    % SCENARIOS 18-22: Mode 2 Cut-in Tests (750-850s)
    % Low-speed cut-in scenarios
    % 5 scenarios x 20 seconds
    % =====================================================================
    if (t > 750) && (t <= 850)
        t_scenario = t - 750;
        scenario_num = floor(t_scenario / 20) + 1;
        t_local = mod(t_scenario, 20);

        % Mode 2 low-speed cut-in parameters
        ego_vels = [8, 5, 8, 5, 6];
        rel_vels = [5, 5, 5, 5, 4];

        v0 = ego_vels(scenario_num);
        dv = rel_vels(scenario_num);

        cut_in_time = 1;  % Faster cut-in for low speed

        if t_local < cut_in_time
            desired_v = v0 + dv;
        else
            time_since_cut = t_local - cut_in_time;

            if time_since_cut < 5
                % Deceleration phase: ramp down over 5 seconds
                desired_v = (v0 + dv) - dv * (time_since_cut / 5);
            else
                % Settling phase
                v_osc = 0.2 * sin(2*pi*0.2*(time_since_cut - 5));
                desired_v = v0 + v_osc;
            end
        end

        % Mode 2 is smoother with lower acceleration limits
        lead_cmd_accel = 0.15 * (desired_v - lead_velo);
        lead_cmd_accel = max(lead_cmd_accel, -1.5);
        lead_cmd_accel = min(lead_cmd_accel, 1.0);
        return;
    end

    % =====================================================================
    % DEFAULT: Maintain current velocity
    % =====================================================================
    lead_cmd_accel = 0;

end
