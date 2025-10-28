% choose your file!
[fileName, pathName] = uigetfile('*.bag');
bag = rosbag([pathName, fileName]);

% Extract timeseries
vel_x       = timeseries(select(bag,'Topic','/egocar/car/state/vel_x'));
cmd_accel   = timeseries(select(bag,'Topic','/egocar/cmd_accel'));
rel_vel     = timeseries(select(bag,'Topic','/egocar/rel_vel'));
lead_dist   = timeseries(select(bag,'Topic','/egocar/lead_dist'));
lead_vel_x  = timeseries(select(bag,'Topic','/leadcar/car/state/vel_x'));
ego_mode    = timeseries(select(bag,'Topic','/egocar/acc_mode')); % used for coloring

% List of topics
topics = {vel_x, cmd_accel, rel_vel, lead_dist, lead_vel_x, ego_mode};
titles = { ...
    'Ego Velocity X (m/s)', ...
    'Commanded Acceleration (m/s^2)', ...
    'Relative Velocity (m/s)', ...
    'Relative Lead Distance (m)', ...
    'Lead Car Velocity (m/s)', ...
    'Ego ACC Mode' ...
};

numPlots = numel(topics);

% Match mode timestamps to each topic by interpolation
modeTime = ego_mode.Time;
modeData = ego_mode.Data;
uniqueModes = unique(modeData);
numModes = length(uniqueModes);
colors = lines(numModes); % distinct colors for each mode

figure;

for i = 1:numPlots
    subplot(numPlots,1,i);
    hold on;
    
    % Interpolate mode values for current topic timestamps
    topicTime = topics{i}.Time;
    topicData = topics{i}.Data;
    modeInterp = interp1(modeTime, modeData, topicTime, 'nearest', 'extrap');

    % Plot each segment in its mode color
    for m = 1:numModes
        idx = modeInterp == uniqueModes(m);
        scatter(topicTime(idx), topicData(idx), 12, colors(m,:), 'filled');
    end

    title(titles{i});
    ylabel('Value');
    grid on;
    if i == numPlots
        xlabel('Time (s)');
    else
        set(gca, 'XTickLabel', []);
    end
    hold off;
end

legendStrings = "Mode " + string(uniqueModes);
legend(legendStrings, 'Location', 'bestoutside');
sgtitle('ROS Bag Timeseries by Topic - Colored by ACC Mode');
fontsize(gcf,"scale",1.4)
