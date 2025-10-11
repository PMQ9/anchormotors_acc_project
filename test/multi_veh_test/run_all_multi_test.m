% -------------------------------------------------------------------------
% Runs every Simulink model in a folder (and its subfolders)
% Skips any model with 'subsystem' in its filename
% Generates a comprehensive PDF report with plots and warnings
% -------------------------------------------------------------------------

% === USER CONFIGURATION ===
modelsFolder = fullfile(pwd, 'test', 'multi_veh_test/');

% Add project root and all subdirectories to path
addpath(genpath(pwd));
fprintf('Added project paths from: %s\n', pwd);

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
    testCase.status = 'Passed';  % Default to passed, will be updated based on warnings/errors
    testCase.warnings = {};
    testCase.errors = {};
    testCase.warningTypes = containers.Map('KeyType', 'char', 'ValueType', 'any');  % Map for unique warning types
    testCase.errorTypes = containers.Map('KeyType', 'char', 'ValueType', 'any');    % Map for unique error types
    testCase.unclassifiedTypes = containers.Map('KeyType', 'char', 'ValueType', 'any');  % Map for unclassified messages
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
        % Status will be determined after parsing warnings/errors

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
        % Store critical simulation error
        errorType = sprintf('Simulation Error: %s', ME.message);
        testCase.errorTypes(errorType) = struct('count', 1, 'firstOccurrence', errorType);
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

                % Capture lines starting with "Error:" (disp output from blocks)
                if startsWith(line, 'Error:')
                    % Extract error type by removing timestamps and specific numeric values
                    errorType = extractMessageType(line);

                    % Update error type count
                    if testCase.errorTypes.isKey(errorType)
                        data = testCase.errorTypes(errorType);
                        data.count = data.count + 1;
                        testCase.errorTypes(errorType) = data;
                    else
                        testCase.errorTypes(errorType) = struct('count', 1, 'firstOccurrence', line);
                    end

                % Capture lines starting with "Warning:" (MATLAB warnings)
                elseif startsWith(line, 'Warning:')
                    warningMsg = strtrim(line);
                    % Clean up MATLAB hyperlinks
                    warningMsg = regexprep(warningMsg, '<a[^>]*>', '');
                    warningMsg = regexprep(warningMsg, '</a>', '');
                    warningMsg = regexprep(warningMsg, 'href="[^"]*"', '');

                    % Extract warning type
                    warningType = extractMessageType(warningMsg);

                    % Update warning type count
                    if testCase.warningTypes.isKey(warningType)
                        data = testCase.warningTypes(warningType);
                        data.count = data.count + 1;
                        testCase.warningTypes(warningType) = data;
                    else
                        testCase.warningTypes(warningType) = struct('count', 1, 'firstOccurrence', warningMsg);
                    end

                % Capture any line with "href" or other messages (unclassified warnings)
                elseif ~isempty(line) && ~isempty(regexp(line, '[a-zA-Z]', 'once'))
                    unclassifiedMsg = strtrim(line);
                    % Clean up MATLAB hyperlinks
                    unclassifiedMsg = regexprep(unclassifiedMsg, '<a[^>]*>', '');
                    unclassifiedMsg = regexprep(unclassifiedMsg, '</a>', '');
                    unclassifiedMsg = regexprep(unclassifiedMsg, 'href="[^"]*"', '');

                    if ~isempty(unclassifiedMsg)
                        % Extract message type
                        msgType = extractMessageType(unclassifiedMsg);

                        % Update unclassified type count
                        if testCase.unclassifiedTypes.isKey(msgType)
                            data = testCase.unclassifiedTypes(msgType);
                            data.count = data.count + 1;
                            testCase.unclassifiedTypes(msgType) = data;
                        else
                            testCase.unclassifiedTypes(msgType) = struct('count', 1, 'firstOccurrence', unclassifiedMsg);
                        end
                    end
                end
            end

            % Also check for lastwarn in case some warnings weren't captured
            [lastWarnMsg, lastWarnId] = lastwarn;
            if ~isempty(lastWarnMsg)
                warningType = extractMessageType(lastWarnMsg);
                if testCase.warningTypes.isKey(warningType)
                    data = testCase.warningTypes(warningType);
                    data.count = data.count + 1;
                    testCase.warningTypes(warningType) = data;
                else
                    fullMsg = sprintf('[%s] %s', lastWarnId, lastWarnMsg);
                    testCase.warningTypes(warningType) = struct('count', 1, 'firstOccurrence', fullMsg);
                end
            end
        end
    end

    warning(warnState); % Restore warning state

    % Determine final test status based on errors and warnings (not unclassified)
    numErrors = testCase.errorTypes.Count;
    numWarnings = testCase.warningTypes.Count;
    numUnclassified = testCase.unclassifiedTypes.Count;

    if numErrors > 0
        testCase.status = 'Failed';
    elseif numWarnings > 0
        testCase.status = 'Passed with warnings';
    else
        testCase.status = 'Passed';
    end

    % Print warning/error summary
    if numErrors > 0
        fprintf('  Captured %d unique error type(s) for %s\n', numErrors, modelName);
    end
    if numWarnings > 0
        fprintf('  Captured %d unique warning type(s) for %s\n', numWarnings, modelName);
    end
    if numUnclassified > 0
        fprintf('  Captured %d unclassified message type(s) for %s\n', numUnclassified, modelName);
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
% Helper function to extract message type (remove timestamps and specific values)
function msgType = extractMessageType(msg)
    % Remove timestamps in various formats
    % Pattern: at t=X.XXX or at t = X.XXX
    msgType = regexprep(msg, 'at t\s*=\s*[\d\.]+', 'at t=<TIME>');

    % Replace specific numeric values with placeholders
    % Pattern: standalone numbers (positive or negative, with decimals)
    msgType = regexprep(msgType, ':\s*-?[\d\.]+\s+at', ': <VALUE> at');
    msgType = regexprep(msgType, ':\s*-?[\d\.]+\s*$', ': <VALUE>');

    % Pattern: numbers followed by > or < (like "> 0.500")
    msgType = regexprep(msgType, '-?[\d\.]+\s*>', '<VALUE> >');
    msgType = regexprep(msgType, '-?[\d\.]+\s*<', '<VALUE> <');

    % Pattern: violation values (like "violation: X.XXX")
    msgType = regexprep(msgType, 'violation:\s*-?[\d\.]+', 'violation: <VALUE>');
    msgType = regexprep(msgType, 'detected:\s*-?[\d\.]+', 'detected: <VALUE>');
    msgType = regexprep(msgType, 'limit:\s*-?[\d\.]+', 'limit: <VALUE>');
    msgType = regexprep(msgType, 'exceeded\s+limit:\s*-?[\d\.]+', 'exceeded limit: <VALUE>');

    % Pattern: gap values
    msgType = regexprep(msgType, 'gap\s+violation:\s*-?[\d\.]+', 'gap violation: <VALUE>');

    % Clean up any remaining standalone decimal numbers in the middle of text
    msgType = regexprep(msgType, '\s-?[\d\.]+\s', ' <VALUE> ');
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
                fprintf('DEBUG: Found %d properties in simOut\n', length(props));
                for i = 1:length(props)
                    propName = props{i};
                    % Skip known non-data properties
                    if strcmp(propName, 'logsout') || strcmp(propName, 'ErrorMessage') || strcmp(propName, 'SimulationMetadata') || strcmp(propName, 'tout')
                        continue;
                    end

                    try
                        propData = simOut.(propName);
                        % Check if it's a timeseries or structure with time
                        if isa(propData, 'timeseries')
                            dataToPlot{end+1} = struct('time', propData.Time, 'data', propData.Data);
                            dataNames{end+1} = propName;
                            fprintf('DEBUG: Added timeseries %s\n', propName);
                        elseif isstruct(propData) && isfield(propData, 'time') && isfield(propData, 'signals')
                            % Structure with Time format from To Workspace
                            % Squeeze to remove singleton dimensions (handles 3D data like [1 1 56])
                            dataToPlot{end+1} = struct('time', squeeze(propData.time), 'data', squeeze(propData.signals.values));
                            dataNames{end+1} = propName;
                            fprintf('DEBUG: Added struct %s\n', propName);
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
                        % Squeeze to remove singleton dimensions
                        dataToPlot{end+1} = struct('time', squeeze(varData.time), 'data', squeeze(varData.signals.values));
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
    tp.Title = 'Multi Vehicle Test Results';
    tp.Subtitle = sprintf('Generated: %s', reportData.timestamp);
    tp.Author = 'Anchor Motors ACC System';
    add(rpt, tp);

    % Table of Contents
    add(rpt, TableOfContents);

    % Summary Chapter
    ch = Chapter('Summary');

    totalTests = length(reportData.testCases);
    passedTests = sum(cellfun(@(x) strcmp(x.status, 'Passed'), reportData.testCases));
    passedWithWarningsTests = sum(cellfun(@(x) strcmp(x.status, 'Passed with warnings'), reportData.testCases));
    failedTests = sum(cellfun(@(x) strcmp(x.status, 'Failed'), reportData.testCases));

    p = Paragraph(sprintf('Total Tests: %d', totalTests));
    p.Style = {FontSize('14pt'), Bold()};
    add(ch, p);

    p = Paragraph(sprintf('Passed: %d', passedTests));
    p.Style = {FontSize('14pt'), Color('green'), Bold()};
    add(ch, p);

    p = Paragraph(sprintf('Passed with warnings: %d', passedWithWarningsTests));
    p.Style = {FontSize('14pt'), Color('orange'), Bold()};
    add(ch, p);

    p = Paragraph(sprintf('Failed: %d', failedTests));
    p.Style = {FontSize('14pt'), Color('red'), Bold()};
    add(ch, p);

    % Add detailed list of test results by category
    if passedTests > 0
        add(ch, Paragraph(' '));
        p = Paragraph('Passed Tests:');
        p.Style = {FontSize('12pt'), Color('green'), Bold()};
        add(ch, p);
        for i = 1:length(reportData.testCases)
            if strcmp(reportData.testCases{i}.status, 'Passed')
                p = Paragraph(sprintf('  - %s', strrep(reportData.testCases{i}.name, '_', ' ')));
                add(ch, p);
            end
        end
    end

    if passedWithWarningsTests > 0
        add(ch, Paragraph(' '));
        p = Paragraph('Passed with Warnings Tests:');
        p.Style = {FontSize('12pt'), Color('orange'), Bold()};
        add(ch, p);
        for i = 1:length(reportData.testCases)
            if strcmp(reportData.testCases{i}.status, 'Passed with warnings')
                p = Paragraph(sprintf('  - %s', strrep(reportData.testCases{i}.name, '_', ' ')));
                add(ch, p);
            end
        end
    end

    if failedTests > 0
        add(ch, Paragraph(' '));
        p = Paragraph('Failed Tests:');
        p.Style = {FontSize('12pt'), Color('red'), Bold()};
        add(ch, p);
        for i = 1:length(reportData.testCases)
            if strcmp(reportData.testCases{i}.status, 'Failed')
                p = Paragraph(sprintf('  - %s', strrep(reportData.testCases{i}.name, '_', ' ')));
                add(ch, p);
            end
        end
    end

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
        elseif strcmp(testCase.status, 'Passed with warnings')
            p.Style = {FontSize('12pt'), Color('orange'), Bold()};
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

        % Add errors if any
        if testCase.errorTypes.Count > 0
            add(ch, Heading2('Errors Summary'));
            errorKeys = keys(testCase.errorTypes);
            for j = 1:length(errorKeys)
                errorKey = errorKeys{j};
                errorData = testCase.errorTypes(errorKey);

                % Format: "Error type (count: X)"
                p = Paragraph(sprintf('%s (Count: %d)', errorKey, errorData.count));
                p.Style = {FontFamily('Courier'), FontSize('10pt'), Color('red'), Bold()};
                add(ch, p);

                % Add first occurrence as example
                if errorData.count > 1
                    p = Paragraph(sprintf('  Example: %s', errorData.firstOccurrence));
                    p.Style = {FontFamily('Courier'), FontSize('9pt'), Color('gray')};
                    add(ch, p);
                end
                add(ch, Paragraph(' ')); % Spacer
            end
        end

        % Add warnings if any
        if testCase.warningTypes.Count > 0
            add(ch, Heading2('Warnings Summary'));
            warningKeys = keys(testCase.warningTypes);
            for j = 1:length(warningKeys)
                warningKey = warningKeys{j};
                warningData = testCase.warningTypes(warningKey);

                % Format: "Warning type (count: X)"
                p = Paragraph(sprintf('%s (Count: %d)', warningKey, warningData.count));
                p.Style = {FontFamily('Courier'), FontSize('10pt'), Color('orange'), Bold()};
                add(ch, p);

                % Add first occurrence as example
                if warningData.count > 1
                    p = Paragraph(sprintf('  Example: %s', warningData.firstOccurrence));
                    p.Style = {FontFamily('Courier'), FontSize('9pt'), Color('gray')};
                    add(ch, p);
                end
                add(ch, Paragraph(' ')); % Spacer
            end
        end

        % Add unclassified warnings if any
        if testCase.unclassifiedTypes.Count > 0
            add(ch, Heading2('Unclassified Warnings'));
            unclassifiedKeys = keys(testCase.unclassifiedTypes);
            for j = 1:length(unclassifiedKeys)
                unclassifiedKey = unclassifiedKeys{j};
                unclassifiedData = testCase.unclassifiedTypes(unclassifiedKey);

                % Format: "Message type (count: X)"
                p = Paragraph(sprintf('%s (Count: %d)', unclassifiedKey, unclassifiedData.count));
                p.Style = {FontFamily('Courier'), FontSize('10pt'), Color('gray'), Bold()};
                add(ch, p);

                % Add first occurrence as example
                if unclassifiedData.count > 1
                    p = Paragraph(sprintf('  Example: %s', unclassifiedData.firstOccurrence));
                    p.Style = {FontFamily('Courier'), FontSize('9pt'), Color('gray')};
                    add(ch, p);
                end
                add(ch, Paragraph(' ')); % Spacer
            end
        end

        add(rpt, ch);
    end

    % Close and generate report
    close(rpt);
end
