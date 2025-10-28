% choose your file
[fileName, pathName] = uigetfile('*.bag');
bag = rosbag([pathName, fileName]);

% Extract timeseries
vel_x     = timeseries(select(bag,'Topic','/egocar/car/state/vel_x'));   % Ego velocity
lead_dist = timeseries(select(bag,'Topic','/egocar/lead_dist'));         % Space gap
ego_mode  = timeseries(select(bag,'Topic','/egocar/acc_mode'));          % Mode

% Interpolate signals to align with ego velocity timestamps
commonTime = vel_x.Time;
leadDistInterp = interp1(lead_dist.Time, lead_dist.Data, commonTime, 'linear', 'extrap');
modeInterp     = interp1(ego_mode.Time, ego_mode.Data, commonTime, 'nearest', 'extrap');

% Unique modes and colors
uniqueModes = unique(modeInterp);
numModes = numel(uniqueModes);
colors = lines(numModes);  % MATLAB default distinct colors

% Scatter plot
figure; hold on;
for m = 1:numModes
    idx = modeInterp == uniqueModes(m);
    scatter(vel_x.Data(idx), leadDistInterp(idx), 15, colors(m,:), 'filled');
end

xlabel('Ego Velocity (m/s)');
ylabel('Space Gap (m)');
title('Space Gap vs Ego Velocity (Colored by ACC Mode)');
legend("Mode " + string(uniqueModes), 'Location', 'best');
grid on;
fontsize(gcf,"scale",1.4);
