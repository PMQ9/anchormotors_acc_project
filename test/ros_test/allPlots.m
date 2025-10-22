% choose your file!
[fileName, pathName] = uigetfile('*.bag');
bag = rosbag([pathName, fileName]);

% Extract timeseries
vel_x       = timeseries(select(bag,'Topic','/egocar/car/state/vel_x'));
cmd_accel   = timeseries(select(bag,'Topic','/egocar/cmd_accel'));
rel_vel     = timeseries(select(bag,'Topic','/egocar/rel_vel'));
lead_dist   = timeseries(select(bag,'Topic','/egocar/lead_dist'));
lead_vel_x  = timeseries(select(bag,'Topic','/leadcar/car/state/vel_x'));
ego_mode    = timeseries(select(bag,'Topic','/egocar/acc_mode'));

% Time t0
t0 = vel_x.Time(1);

% Create figure with subplots
figure;
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

for i = 1:numPlots
    subplot(numPlots,1,i);
    plot(topics{i}.Time - t0, topics{i}.Data, '.');
    title(titles{i});
    ylabel('Value');
    if i == numPlots
        xlabel('Time (s)');
    else
        set(gca, 'XTickLabel', []); % Hide x labels except last
    end
    grid on;
end

sgtitle('ROS Bag Timeseries by Topic');
fontsize(gcf,"scale",1.4)
