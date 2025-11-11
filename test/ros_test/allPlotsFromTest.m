% Choose your ROS bag file
[fileName, pathName] = uigetfile('*.bag');
bag = rosbag([pathName, fileName]);

% Extract time series from correct topic names in the bag
vel_x         = timeseries(select(bag,'Topic','/car/state/vel_x'));
cmd_accel_pre = timeseries(select(bag,'Topic','/cmd_accel_pre'));
cmd_accel     = timeseries(select(bag,'Topic','/cmd_accel'));
rel_vel_rev   = timeseries(select(bag,'Topic','/rel_vel_reversed'));
lead_dist     = timeseries(select(bag,'Topic','/lead_dist_extra'));
ego_mode      = timeseries(select(bag,'Topic','/acc_mode')); % Used for coloring

% --- Compute lead vehicle velocity ---
% Interpolate rel_vel_reversed to match vel_x timestamps
rel_interp = interp1(rel_vel_rev.Time, rel_vel_rev.Data, vel_x.Time, 'linear', 'extrap');
lead_vel_data = vel_x.Data + rel_interp;
lead_vel = timeseries(lead_vel_data, vel_x.Time);

% List of topics (now includes lead velocity)
topics = {vel_x, lead_vel, cmd_accel_pre, cmd_accel, rel_vel_rev, lead_dist, ego_mode};
titles = { ...
    'Ego Velocity X (m/s)', ...
    'Lead Velocity (m/s)', ...
    'Commanded Acceleration (Pre) (m/s^2)', ...
    'Commanded Acceleration (Final) (m/s^2)', ...
    'Relative Velocity (Reversed) (m/s)', ...
    'Lead Distance (m)', ...
    'Ego ACC Mode' ...
};

numPlots = numel(topics);

% --- Mode coloring setup ---
modeTime = ego_mode.Time;
modeData = ego_mode.Data;
uniqueModes = unique(modeData);
numModes = length(uniqueModes);
colors = lines(numModes);

figure;

for i = 1:numPlots
    subplot(numPlots,1,i);
    hold on;
    
    % Interpolate mode for each topic
    topicTime = topics{i}.Time;
    topicData = topics{i}.Data;
    modeInterp = interp1(modeTime, modeData, topicTime, 'nearest', 'extrap');

    % Plot by mode color
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
fontsize(gcf,"scale",1.4);
