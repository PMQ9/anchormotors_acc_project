function replay_two_cars_ts(car1, car2, varargin)
% replay_two_cars_ts  Animate two cars from their own time series.
%   Each car input can be:
%     - timeseries:  Time & Data (x [m])
%     - timetable:   RowTimes & 1 variable (x [m])
%     - numeric Nx2: [t, x]
%     - struct:      .t, .x
%
% Name-Value options:
%   'L'           : car length [m], default 4.0
%   'W'           : car width  [m], default 1.8
%   'y1'          : lateral pos car 1 [m], default +1.0
%   'y2'          : lateral pos car 2 [m], default -1.0
%   'Speed'       : playback speed multiplier, default 1
%   'Trail'       : true/false, draw trails, default true
%   'Label1'      : label for car 1, default 'Car 1'
%   'Label2'      : label for car 2, default 'Car 2'
%   'Ego'         : 1 or 2 (which car to center on), default 1
%   'Window'      : MIN x-span (m), default 80
%   'WindowMax'   : MAX x-span (m); [] = no hard max (default [])
%   'Signals'     : cell array of extra time series to plot at bottom
%                   (each: timeseries/timetable/Nx2/struct(.t,.x))
%   'SignalNames' : cellstr of labels for Signals (optional)
%   'SignalHeight': height fraction for signal axes (0.15–0.45), default 0.25

% ---------- Parse inputs ----------
p = inputParser;
p.addParameter('L', 4.0, @(v)isnumeric(v)&&isscalar(v)&&v>0);
p.addParameter('W', 1.8, @(v)isnumeric(v)&&isscalar(v)&&v>0);
p.addParameter('y1', 1.0, @(v)isnumeric(v)&&isscalar(v));
p.addParameter('y2', -1.0, @(v)isnumeric(v)&&isscalar(v));
p.addParameter('Speed', 1, @(v)isnumeric(v)&&isscalar(v)&&v>0);
p.addParameter('Trail', true, @(v)islogical(v)&&isscalar(v));
p.addParameter('Label1', 'Car 1', @(v)isstring(v)||ischar(v));
p.addParameter('Label2', 'Car 2', @(v)isstring(v)||ischar(v));
p.addParameter('Ego', 1, @(v)isnumeric(v)&&isscalar(v)&&ismember(v,[1 2]));
p.addParameter('Window', 80, @(v)isnumeric(v)&&isscalar(v)&&v>0);
p.addParameter('WindowMax', [], @(v)isempty(v)||(isnumeric(v)&&isscalar(v)&&v>0));
p.addParameter('Signals', {}, @(v)iscell(v));
p.addParameter('SignalNames', {}, @(v)iscellstr(v)||isstring(v));
p.addParameter('SignalHeight', 0.25, @(v)isnumeric(v)&&isscalar(v)&&v>=0.15&&v<=0.45);
p.parse(varargin{:});
L = p.Results.L; W = p.Results.W;
y1 = p.Results.y1; y2 = p.Results.y2;
spd = p.Results.Speed;
drawTrail = p.Results.Trail;
lab1 = string(p.Results.Label1); lab2 = string(p.Results.Label2);
ego  = p.Results.Ego;
winMin  = p.Results.Window;
winMax  = p.Results.WindowMax;
signals = p.Results.Signals;
sigNames = cellstr(string(p.Results.SignalNames));
sigH    = p.Results.SignalHeight;

% ---------- Cars: extract & prep ----------
[t1, x1] = get_tx(car1);  [t1, x1] = sort_tx(t1, x1);
[t2, x2] = get_tx(car2);  [t2, x2] = sort_tx(t2, x2);
t0  = min([t1(1), t2(1)]);
t1s = to_seconds(t1, t0);
t2s = to_seconds(t2, t0);
tu  = unique([t1s; t2s]);                 % unified playback timeline

% Interpolate & clamp
x1u = interp1(t1s, x1, tu, 'linear', 'extrap'); x1u(tu<t1s(1))=x1(1); x1u(tu>t1s(end))=x1(end);
x2u = interp1(t2s, x2, tu, 'linear', 'extrap'); x2u(tu<t2s(1))=x2(1); x2u(tu>t2s(end))=x2(end);

% ---------- Extra signals (resampled to tu) ----------
numSig = numel(signals);
sigY = [];
if numSig > 0
    sigY = zeros(numSig, numel(tu));
    for i = 1:numSig
        [ts_i, ys_i] = get_tx(signals{i});
        [ts_i, ys_i] = sort_tx(ts_i, ys_i);
        tsi = to_seconds(ts_i, t0);
        yi  = interp1(tsi, ys_i, tu, 'linear', 'extrap');
        yi(tu < tsi(1)) = ys_i(1);
        yi(tu > tsi(end)) = ys_i(end);
        sigY(i,:) = yi(:).';
    end
    if isempty(sigNames) || numel(sigNames) ~= numSig
        sigNames = arrayfun(@(k)sprintf('Signal %d',k), 1:numSig, 'uni', 0);
    end
end

% ---------- Figure & manual layout (no RowHeight) ----------
clf; figure(gcf); set(gcf,'Color','w','Name','Two-Car Replay');

% Manual normalized layout: top playback axis and bottom signal axis
left = 0.08; right = 0.06; top = 0.06; bottom = 0.10; midGap = 0.06;
playH = 1 - top - bottom - (numSig>0)*sigH - (numSig>0)*midGap;
if playH <= 0.2, playH = 0.2; end

axPlay = axes('Position',[left, bottom + (numSig>0)*(sigH+midGap), 1-left-right, playH]);
hold(axPlay,'on'); axis(axPlay,'equal'); grid(axPlay,'on');
xlabel(axPlay,'Longitudinal position x [m]');
ylabel(axPlay,'Lateral position y [m]');
title(axPlay,'Replay of Two Cars (Top-Down)');

% y-limits fixed; x-limits updated per frame
yPad = 3*W;
ylim(axPlay, [min([y1,y2])-yPad, max([y1,y2])+yPad]);

% Car geometry & graphics
carXY = [ -L/2  -W/2;  L/2  -W/2;  L/2   W/2; -L/2   W/2 ];
T1 = hgtransform('Parent', axPlay);
T2 = hgtransform('Parent', axPlay);
patch('XData',carXY(:,1),'YData',carXY(:,2),'Parent',T1, ...
      'FaceColor',[0.2 0.6 1.0],'EdgeColor','k','LineWidth',1.0);
plot(T1, [L/2 L/2], [-W/4 W/4], 'k-', 'LineWidth',2);
patch('XData',carXY(:,1),'YData',carXY(:,2),'Parent',T2, ...
      'FaceColor',[1.0 0.5 0.2],'EdgeColor','k','LineWidth',1.0);
plot(T2, [L/2 L/2], [-W/4 W/4], 'k-', 'LineWidth',2);

% Labels
labelOffset = W * 0.8;
label1 = text(axPlay, x1u(1), y1 + labelOffset, lab1, ...
    'HorizontalAlignment','center','VerticalAlignment','bottom', ...
    'FontWeight','bold','Color',[0.1 0.3 0.7],'FontSize',10);
label2 = text(axPlay, x2u(1), y2 + labelOffset, lab2, ...
    'HorizontalAlignment','center','VerticalAlignment','bottom', ...
    'FontWeight','bold','Color',[0.8 0.3 0.1],'FontSize',10);

% Trails
if drawTrail
    trail1 = plot(axPlay, x1u(1), y1, '-', 'LineWidth', 1.0);
    trail2 = plot(axPlay, x2u(1), y2, '-', 'LineWidth', 1.0);
else
    trail1 = []; trail2 = [];
end

% Bottom signals axis (optional)
if numSig > 0
    axSig = axes('Position',[left, bottom, 1-left-right, sigH]);
    hold(axSig,'on'); grid(axSig,'on');
    tt = tu;  % seconds since t0
    for i = 1:numSig
        plot(axSig, tt, sigY(i,:), 'LineWidth', 1.0);
    end
    legend(axSig, sigNames, 'Location','eastoutside');
    xlabel(axSig, 'Time [s]'); ylabel(axSig, 'Value');

    % time cursor (xline newer; fallback to a manual line if unavailable)
    try
        tc = xline(axSig, tt(1), '--', 'Cursor', 'LabelOrientation','horizontal');
    catch
        tc = line(axSig, [tt(1) tt(1)], ylim(axSig), 'LineStyle','--', 'Color',[0 0 0]);
    end
else
    axSig = []; tc = [];
end

% Initial placement
set(T1, 'Matrix', makehgtform('translate',[x1u(1) + L/2, y1, 0]));  % lead car: odom = rear axle
set(T2, 'Matrix', makehgtform('translate',[x2u(1) - L/2, y2, 0]));  % ego car: odom = front axle
update_labels(1);

% ---- Axis padding & min/max span rules ----
xMargin  = 1.5*L;
baseMin  = max(winMin, 4*L);     % sensible minimum

% Initial ego-centered view
egoX0 = (ego==1) * x1u(1) + (ego==2) * x2u(1);
dist0 = abs(x1u(1) - x2u(1));
need0 = dist0 + 2*xMargin;
span0 = max(baseMin, need0);
if ~isempty(winMax), span0 = min(span0, winMax); end
xlim(axPlay, [egoX0 - span0/2, egoX0 + span0/2]);

% ---------- Animation ----------
N = numel(tu);
for k = 1:N
    % Update car poses & labels
    set(T1, 'Matrix', makehgtform('translate',[x1u(k) + L/2, y1, 0]));
    set(T2, 'Matrix', makehgtform('translate',[x2u(k) - L/2, y2, 0]));
    update_labels(k);

    % Trails
    if drawTrail
        set(trail1, 'XData', x1u(1:k), 'YData', y1*ones(1,k));
        set(trail2, 'XData', x2u(1:k), 'YData', y2*ones(1,k));
    end

    % Dynamic x-limits: center on ego, clamp between min and max
    egoX = (ego==1) * x1u(k) + (ego==2) * x2u(k);
    dist = abs(x1u(k) - x2u(k));
    need = dist + 2*xMargin;
    span = max(baseMin, need);
    if ~isempty(winMax), span = min(span, winMax); end
    xlim(axPlay, [egoX - span/2, egoX + span/2]);

    % Update time cursor
    if ~isempty(axSig)
        try
            tc.Value = tu(k);  % xline path
        catch
            set(tc, 'XData', [tu(k) tu(k)], 'YData', ylim(axSig)); % manual line path
        end
    end

    drawnow limitrate nocallbacks;
    if k < N
        dt = (tu(k+1) - tu(k)) / spd;
        if dt > 0, pause(min(dt, 0.05)); end
    end
end

% ===== nested helper =====
    function update_labels(idx)
        set(label1, 'Position', [x1u(idx), y1 + labelOffset, 0]);
        set(label2, 'Position', [x2u(idx), y2 + labelOffset, 0]);
    end
end

% ===== Helpers =====
function [t, x] = get_tx(s)
    if isa(s, 'timeseries')
        t = s.Time;  x = s.Data;
    elseif istimetable(s)
        if width(s) ~= 1, error('Timetable must have exactly one variable (position x).'); end
        t = s.Properties.RowTimes; x = s{:,1};
    elseif isnumeric(s)
        if size(s,2) < 2, error('Numeric input must be Nx2 [t, x].'); end
        t = s(:,1); x = s(:,2);
    elseif isstruct(s) && isfield(s,'t') && isfield(s,'x')
        t = s.t; x = s.x;
    else
        error('Unsupported input type.');
    end
    t = t(:); x = x(:);
end

function [t, x] = sort_tx(t, x)
    if isnumeric(t) && any(t > 7e5) && any(t < 1e6)
        try t = datetime(t, 'ConvertFrom','datenum'); end %#ok<TRYNC>
    end
    if isdatetime(t) || isduration(t)
        [t, idx] = sort(t);
    else
        [t, idx] = sort(t(:));
    end
    x = x(idx);
end

function ts = to_seconds(t, t0)
    if isdatetime(t) || isduration(t)
        ts = seconds(t - t0);
    else
        ts = t - t0;
    end
    ts = ts(:);
end