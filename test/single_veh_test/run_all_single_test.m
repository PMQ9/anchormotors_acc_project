% -------------------------------------------------------------------------
% Runs every Simulink model in a folder (and its subfolders)
% Skips any model with 'subsystem' in its filename
% Generates a comprehensive PDF report with plots and warnings
% -------------------------------------------------------------------------

% === USER CONFIGURATION ===
modelsFolder = fullfile(pwd, 'test', 'single_veh_test/');
searchSubfolders = false;                  % set false for top-level only
closeAfterSim = false;                     % close models after running
generatePDFReport = true;                 % generate PDF report
outputFolder = fullfile(modelsFolder, 'results');  % folder for outputs

% Create output folder if it doesn't exist
if ~exist(outputFolder, 'dir')
    mkdir(outputFolder);
end

% Initialize report data structure
reportData = struct();
reportData.testCases = {};
reportData.timestamp = datestr(now, 'yyyy-mm-dd HH:MM:SS');

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

    % Initialize test case data
    testCase = struct();
    testCase.name = modelName;
    testCase.status = 'Failed';
    testCase.warnings = {};
    testCase.errors = {};
    testCase.plotFiles = {};

    % Setup warning capture - use diary to capture all warnings
    warningFile = fullfile(outputFolder, sprintf('%s_warnings.txt', modelName));
    lastwarn(''); % Clear last warning
    warnState = warning('query', 'all');
    warning('on', 'all');

    % Start diary to capture all output including warnings
    diary(warningFile);
    diaryWasOn = strcmp(get(0,'Diary'),'on');

    try
        % Load the model without opening GUI
        load_system(modelPath);

        % Run simulation (normal mode so disp() messages appear)
        simOut = sim(modelName, 'SimulationMode', 'normal', 'StopTime', '20');
        fprintf('Simulation completed successfully: %s%s\n', modelName, ext);
        testCase.status = 'Passed';

        % Export plots if scope data or logged signals are available
        try
            % Try to generate plots from simulation output
            plotFile = generatePlotsFromSimulation(simOut, modelName, outputFolder);
            if ~isempty(plotFile)
                testCase.plotFiles = [testCase.plotFiles, {plotFile}];
            end
        catch plotErr
            fprintf('Warning: Could not generate plots for %s: %s\n', modelName, plotErr.message);
        end

    catch ME
        fprintf(2, 'Error running model "%s": %s\n', modelName, ME.message);
        testCase.errors = {ME.message};
        testCase.status = 'Failed';
    end

    % Stop diary
    diary off;

    % Read captured warnings and errors from file
    if exist(warningFile, 'file')
        fid = fopen(warningFile, 'r');
        if fid ~= -1
            fileContent = fread(fid, '*char')';
            fclose(fid);

            % Split into lines
            lines = strsplit(fileContent, '\n');

            % Parse different types of messages
            for lineIdx = 1:length(lines)
                line = strtrim(lines{lineIdx});

                % Skip empty lines and known non-warning lines
                if isempty(line) || ...
                   contains(line, '=============================================================') || ...
                   contains(line, 'Simulating model') || ...
                   contains(line, 'Simulation completed successfully') || ...
                   contains(line, 'Generated plot')
                    continue;
                end

                % Capture lines starting with "Warning:" (MATLAB warnings)
                if startsWith(line, 'Warning:')
                    warningMsg = strtrim(line);
                    % Clean up MATLAB hyperlinks
                    warningMsg = regexprep(warningMsg, '<a[^>]*>', '');
                    warningMsg = regexprep(warningMsg, '</a>', '');
                    warningMsg = regexprep(warningMsg, 'href="[^"]*"', '');
                    testCase.warnings{end+1} = warningMsg;
                % Capture lines starting with "Error:" (disp output from blocks)
                elseif startsWith(line, 'Error:')
                    testCase.warnings{end+1} = line;
                % Capture any line with "href" (Stateflow warnings with links)
                elseif contains(line, 'href') && ~isempty(regexp(line, '[a-zA-Z]', 'once'))
                    warningMsg = strtrim(line);
                    % Clean up MATLAB hyperlinks
                    warningMsg = regexprep(warningMsg, '<a[^>]*>', '');
                    warningMsg = regexprep(warningMsg, '</a>', '');
                    warningMsg = regexprep(warningMsg, 'href="[^"]*"', '');
                    if ~isempty(warningMsg) && ~any(strcmp(testCase.warnings, warningMsg))
                        testCase.warnings{end+1} = warningMsg;
                    end
                end
            end

            % Also check for lastwarn in case some warnings weren't captured
            [lastWarnMsg, lastWarnId] = lastwarn;
            if ~isempty(lastWarnMsg)
                fullMsg = sprintf('[%s] %s', lastWarnId, lastWarnMsg);
                % Add only if not already captured
                if ~any(contains(testCase.warnings, lastWarnMsg))
                    testCase.warnings{end+1} = fullMsg;
                end
            end
        end
    end

    warning(warnState); % Restore warning state

    % Print warning summary
    if ~isempty(testCase.warnings)
        fprintf('  Captured %d warning(s) for %s\n', length(testCase.warnings), modelName);
    end

    % Add test case to report data
    reportData.testCases{end+1} = testCase;

    fprintf('=============================================================\n\n');

    % Close model (optional)
    if closeAfterSim
        bdclose(modelName);
    end
end

fprintf('All simulations complete.\n');

% -------------------------------------------------------------------------
% Generate PDF Report
if generatePDFReport
    fprintf('\n=============================================================\n');
    fprintf('Generating PDF Report...\n');
    fprintf('-------------------------------------------------------------\n');

    try
        pdfFilename = fullfile(outputFolder, sprintf('test_report_%s.pdf', datestr(now, 'yyyymmdd_HHMMSS')));
        generatePDFReport_func(reportData, pdfFilename);
        fprintf('PDF Report generated successfully: %s\n', pdfFilename);
    catch ME
        fprintf(2, 'Error generating PDF report: %s\n', ME.message);
    end

    fprintf('=============================================================\n');
end

% -------------------------------------------------------------------------
% Helper function to generate plots from simulation output
function plotFile = generatePlotsFromSimulation(simOut, modelName, outputFolder)
    plotFile = '';

    % Collect all available data to plot
    dataToPlot = {};
    dataNames = {};

    % Method 1: Check for logsout (Signal Logging)
    if ~isempty(simOut)
        try
            if isprop(simOut, 'logsout') && ~isempty(simOut.logsout)
                logsout = simOut.logsout;
                for i = 1:logsout.numElements
                    signal = logsout.getElement(i);
                    dataToPlot{end+1} = struct('time', signal.Values.Time, 'data', signal.Values.Data);
                    dataNames{end+1} = signal.Name;
                end
            end
        catch ME
            fprintf('Could not extract logsout: %s\n', ME.message);
        end
    end

    % Method 2: Check for To Workspace blocks (variables in simOut)
    if ~isempty(simOut)
        try
            % Get all property names from simOut
            if isobject(simOut)
                props = properties(simOut);
                for i = 1:length(props)
                    propName = props{i};
                    % Skip known non-data properties
                    if strcmp(propName, 'logsout') || strcmp(propName, 'ErrorMessage')
                        continue;
                    end

                    try
                        propData = simOut.(propName);
                        % Check if it's a timeseries or structure with time
                        if isa(propData, 'timeseries')
                            dataToPlot{end+1} = struct('time', propData.Time, 'data', propData.Data);
                            dataNames{end+1} = propName;
                        elseif isstruct(propData) && isfield(propData, 'time') && isfield(propData, 'signals')
                            % Structure with Time format from To Workspace
                            dataToPlot{end+1} = struct('time', propData.time, 'data', propData.signals.values);
                            dataNames{end+1} = propName;
                        end
                    catch
                        % Skip if we can't process this property
                        continue;
                    end
                end
            end
        catch ME
            fprintf('Could not extract To Workspace data: %s\n', ME.message);
        end
    end

    % Method 3: Check base workspace for To Workspace variables
    % Get all variables from base workspace that might be from this simulation
    try
        wsVars = evalin('base', 'who');
        for i = 1:length(wsVars)
            varName = wsVars{i};
            try
                varData = evalin('base', varName);

                % Check if it's a timeseries
                if isa(varData, 'timeseries')
                    % Check if not already added
                    if ~any(strcmp(dataNames, varName))
                        dataToPlot{end+1} = struct('time', varData.Time, 'data', varData.Data);
                        dataNames{end+1} = varName;
                    end
                % Check if it's a structure with time (To Workspace format)
                elseif isstruct(varData) && isfield(varData, 'time') && isfield(varData, 'signals')
                    if ~any(strcmp(dataNames, varName))
                        dataToPlot{end+1} = struct('time', varData.time, 'data', varData.signals.values);
                        dataNames{end+1} = varName;
                    end
                end
            catch
                % Skip if we can't access this variable
                continue;
            end
        end
    catch ME
        fprintf('Could not access base workspace: %s\n', ME.message);
    end

    % Create plot if we have any data
    numSignals = length(dataToPlot);
    if numSignals > 0
        try
            fig = figure('Visible', 'off', 'Position', [100, 100, 1200, 800]);

            % Set white background for figure and paper
            set(fig, 'Color', 'white');
            set(fig, 'InvertHardcopy', 'off');  % Preserve colors when saving

            % Determine subplot layout
            nRows = ceil(sqrt(numSignals));
            nCols = ceil(numSignals / nRows);

            for i = 1:numSignals
                subplot(nRows, nCols, i);
                data = dataToPlot{i};

                % Handle different data dimensions
                if size(data.data, 2) == 1
                    % Single column data
                    plot(data.time, data.data, 'LineWidth', 1.5);
                else
                    % Multi-column data (plot all columns)
                    plot(data.time, data.data, 'LineWidth', 1.5);
                    legend(arrayfun(@(x) sprintf('Col %d', x), 1:size(data.data, 2), 'UniformOutput', false), ...
                           'TextColor', 'black', 'EdgeColor', 'black');
                end

                title(strrep(dataNames{i}, '_', '\_'), 'FontSize', 10, 'FontWeight', 'bold', 'Color', 'black');
                xlabel('Time (s)', 'Color', 'black');
                ylabel('Value', 'Color', 'black');
                grid on;

                % Set white background and dark axes for subplot
                set(gca, 'Color', 'white', ...
                         'XColor', 'black', ...
                         'YColor', 'black', ...
                         'GridColor', [0.5, 0.5, 0.5], ...
                         'GridAlpha', 0.15, ...
                         'MinorGridColor', [0.6, 0.6, 0.6], ...
                         'MinorGridAlpha', 0.08, ...
                         'LineWidth', 1);
            end

            sgtitle(strrep(modelName, '_', '\_'), 'FontSize', 14, 'FontWeight', 'bold');

            % Save figure with white background
            plotFile = fullfile(outputFolder, sprintf('%s_plots.png', modelName));
            saveas(fig, plotFile);
            close(fig);

            fprintf('Generated plot with %d signals for %s\n', numSignals, modelName);
        catch ME
            fprintf('Error creating plots: %s\n', ME.message);
        end
    else
        fprintf('No data found to plot for %s\n', modelName);
    end
end

% -------------------------------------------------------------------------
% Helper function to generate PDF report
function generatePDFReport_func(reportData, pdfFilename)
    import mlreportgen.report.*
    import mlreportgen.dom.*

    % Create report
    rpt = Report(pdfFilename, 'pdf');
    rpt.Layout.Landscape = false;

    % Title Page
    tp = TitlePage();
    tp.Title = 'Single Vehicle Test Results';
    tp.Subtitle = sprintf('Generated: %s', reportData.timestamp);
    tp.Author = 'Anchor Motors ACC System';
    add(rpt, tp);

    % Table of Contents
    add(rpt, TableOfContents);

    % Summary Chapter
    ch = Chapter('Summary');

    totalTests = length(reportData.testCases);
    passedTests = sum(cellfun(@(x) strcmp(x.status, 'Passed'), reportData.testCases));
    failedTests = totalTests - passedTests;

    p = Paragraph(sprintf('Total Tests: %d', totalTests));
    p.Style = {FontSize('14pt'), Bold()};
    add(ch, p);

    p = Paragraph(sprintf('Passed: %d', passedTests));
    p.Style = {FontSize('14pt'), Color('green'), Bold()};
    add(ch, p);

    p = Paragraph(sprintf('Failed: %d', failedTests));
    p.Style = {FontSize('14pt'), Color('red'), Bold()};
    add(ch, p);

    add(rpt, ch);

    % Individual Test Cases
    for i = 1:length(reportData.testCases)
        testCase = reportData.testCases{i};

        % Create chapter for each test case
        ch = Chapter(strrep(testCase.name, '_', ' '));

        % Status
        p = Paragraph(sprintf('Status: %s', testCase.status));
        if strcmp(testCase.status, 'Passed')
            p.Style = {FontSize('12pt'), Color('green'), Bold()};
        else
            p.Style = {FontSize('12pt'), Color('red'), Bold()};
        end
        add(ch, p);

        % Add plots if available
        if ~isempty(testCase.plotFiles)
            add(ch, Paragraph('Test Results:'));
            add(ch, Paragraph(' ')); % Spacer

            for j = 1:length(testCase.plotFiles)
                if exist(testCase.plotFiles{j}, 'file')
                    img = Image(testCase.plotFiles{j});
                    % Make images larger - set explicit width to 90% of page width
                    img.Style = {ScaleToFit(false), Width('6.5in'), Height('4.5in')};
                    add(ch, img);
                    add(ch, Paragraph(' ')); % Add spacing after image
                end
            end
        end

        % Add warnings if any
        if ~isempty(testCase.warnings)
            add(ch, Heading2('Warnings'));
            for j = 1:length(testCase.warnings)
                p = Paragraph(testCase.warnings{j});
                p.Style = {FontFamily('Courier'), FontSize('10pt'), Color('orange')};
                add(ch, p);
            end
        end

        % Add errors if any
        if ~isempty(testCase.errors)
            add(ch, Heading2('Errors'));
            for j = 1:length(testCase.errors)
                p = Paragraph(testCase.errors{j});
                p.Style = {FontFamily('Courier'), FontSize('10pt'), Color('red')};
                add(ch, p);
            end
        end

        add(rpt, ch);
    end

    % Close and generate report
    close(rpt);
end
