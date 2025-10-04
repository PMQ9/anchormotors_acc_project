% run_all_models_skip_subsystem_name.m
% -------------------------------------------------------------------------
% Runs every Simulink model in a folder (and its subfolders)
% Skips any model with 'subsystem' in its filename
% -------------------------------------------------------------------------

% === USER CONFIGURATION ===
modelsFolder = fullfile(pwd, 'test', 'multi_veh_test/');
searchSubfolders = false;                  % set false for top-level only
closeAfterSim = true;                     % close models after running

% -------------------------------------------------------------------------
% Find model files
if searchSubfolders
    modelFiles = [ ...
        dir(fullfile(modelsFolder, '**', '*.slx')); ...
        dir(fullfile(modelsFolder, '**', '*.mdl')) ...
    ];
else
    modelFiles = [ ...
        dir(fullfile(modelsFolder, '*.slx')); ...
        dir(fullfile(modelsFolder, '*.mdl')) ...
    ];
end

if isempty(modelFiles)
    fprintf('No Simulink models found in "%s".\n', modelsFolder);
    return;
end

% -------------------------------------------------------------------------
fprintf('Found %d models.\n\n', numel(modelFiles));

% -------------------------------------------------------------------------
for k = 1:numel(modelFiles)
    modelPath = fullfile(modelFiles(k).folder, modelFiles(k).name);
    [~, modelName, ext] = fileparts(modelPath);

    % Skip any model with 'subsystem' in its name
    if contains(lower(modelName), 'subsystem')
        fprintf('Skipping model (name contains "subsystem"): %s%s\n', modelName, ext);
        continue;
    end

    fprintf('\n=============================================================\n');
    fprintf('Simulating model (%d of %d): %s\n', k, numel(modelFiles), modelName);
    fprintf('-------------------------------------------------------------\n');

    try
        % Load the model without opening GUI
        load_system(modelPath);

        % Run simulation (normal mode so disp() messages appear)
        simOut = sim(modelName, 'SimulationMode', 'normal', 'StopTime', '20');
        fprintf('Simulation completed successfully: %s%s\n', modelName, ext);
    catch ME
        fprintf(2, 'Error running model "%s": %s\n', modelName, ME.message);
    end

    fprintf('=============================================================\n\n');

    % Close model (optional)
    if closeAfterSim
        bdclose(modelName);
    end
end

fprintf('All simulations complete.\n');
