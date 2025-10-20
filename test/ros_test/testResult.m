% choose your file!
[fileName, pathName] = uigetfile('*.bag');

bag = rosbag([pathName, fileName]);


%% extract the x velocity information
vel_x_bag = select(bag,'Topic','/egocar/car/state/vel_x');
vel_x = timeseries(vel_x_bag);

%% extract the cmd_accel information
cmd_accel_bag = select(bag,'Topic','/egocar/cmd_accel');
cmd_accel = timeseries(cmd_accel_bag);

%% extract relative velocity of lead car
rel_vel_bag = select(bag,'Topic','/egocar/rel_vel');
rel_vel = timeseries(rel_vel_bag);

%% extract relative distance of lead car
lead_dist_bag = select(bag,'Topic','/egocar/lead_dist');
lead_dist = timeseries(lead_dist_bag);

%% extract distance traveled of lead car
lead_odom_bag = select(bag,'Topic','/leadcar/odom_x');
lead_odom = timeseries(lead_odom_bag);

%% extract distance traveled of lead car
lead_vel_x_bag = select(bag,'Topic','/leadcar/car/state/vel_x');
lead_vel_x = timeseries(lead_vel_x_bag);


%% extract distance traveled of ego car
ego_odom_bag = select(bag,'Topic','/egocar/odom_x');
ego_odom = timeseries(ego_odom_bag);


% time t0
t0 = vel_x.Time(1);

%% plot the results
figure
hold on
scatter(vel_x.Time(:)-t0, vel_x.Data(:),marker='.')
% plot(rel_vel)
scatter(rel_vel.Time(:)-t0,rel_vel.Data(:),marker='.');
% plot(lead_dist);
scatter(lead_dist.Time(:)-t0,lead_dist.Data(:),marker='.')
legend({'vel x (m/s)','rel vel (m/s)','lead dist (m)'})
ylabel('meters or meters/second')
xlabel('Unix time in GMT')
title('Speed, Relative Velocity, and Relative Distance')
axis equal
fontsize(gcf,"scale",2.5)

%% plot the odometry
figure
hold on
scatter(lead_odom.Time(:)-t0,lead_odom.Data(:),marker='.');
scatter(ego_odom.Time(:)-t0,ego_odom.Data(:),marker='.')
legend({'lead odom (m)','ego odom (m)'})
ylabel('meters')
xlabel('Unix time in GMT')
title('Speed, Relative Velocity, and Relative Distance')
axis equal
fontsize(gcf,"scale",2.5)

% pause

%% now, replay!
figure
replay_two_cars_ts(lead_odom, ego_odom, 'Label1', 'Lead Car', ...
    'Label2', 'Ego Car', 'Ego', 2, ...
    'Window', 80, ...
    'WindowMax', 120, ...
    'Signals', {lead_vel_x, vel_x, rel_vel, lead_dist, cmd_accel}, ...
    'SignalNames', {'lead\_vel\_x', 'vel\_x', 'rel\_vel', 'lead\_dist', 'cmd\_accel'})