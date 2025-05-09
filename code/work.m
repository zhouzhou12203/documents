% 确认 Matlab 和 Python 环境已正确连接

% 超临界CO?的热物性查询
p_CO2 = 8e6; % 超临界CO?压力（Pa）
T_CO2 = 550 + 273.15; % 超临界CO?温度（K）

h_CO2 = py.CoolProp.CoolProp.PropsSI('H', 'P', p_CO2, 'T', T_CO2, 'CO2'); % 焓
s_CO2 = py.CoolProp.CoolProp.PropsSI('S', 'P', p_CO2, 'T', T_CO2, 'CO2'); % 熵

fprintf('超临界CO?: 焓 = %.2f J/kg, 熵 = %.2f J/kg/K\n', double(h_CO2), double(s_CO2));

% R245fa的热物性查询
p_R245fa = 1e6; % R245fa压力（Pa）
T_R245fa = 90 + 273.15; % R245fa温度（K）

h_R245fa = py.CoolProp.CoolProp.PropsSI('H', 'P', p_R245fa, 'T', T_R245fa, 'R245fa'); % 焓
s_R245fa = py.CoolProp.CoolProp.PropsSI('S', 'P', p_R245fa, 'T', T_R245fa, 'R245fa'); % 熵

fprintf('R245fa: 焓 = %.2f J/kg, 熵 = %.2f J/kg/K\n', double(h_R245fa), double(s_R245fa));

% 氨水溶液的热物性查询（自建公式）
w_ammonia = 0.45; % 氨水质量分数（45%）
T_ammonia = 120; % 温度（°C）
p_ammonia = 1e5; % 氨水压力（Pa）

% 氨水溶液的焓和熵（示例公式，这里需根据实际文献修改）
h_ammonia = w_ammonia * (2000 + 4 * T_ammonia) + (1 - w_ammonia) * (1000 + 2 * T_ammonia);
s_ammonia = w_ammonia * (6 + 0.1 * T_ammonia) + (1 - w_ammonia) * (2 + 0.05 * T_ammonia);

fprintf('氨水溶液: 焓 = %.2f J/kg, 熵 = %.2f J/kg/K\n', h_ammonia, s_ammonia);
