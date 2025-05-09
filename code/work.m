% ȷ�� Matlab �� Python ��������ȷ����

% ���ٽ�CO?�������Բ�ѯ
p_CO2 = 8e6; % ���ٽ�CO?ѹ����Pa��
T_CO2 = 550 + 273.15; % ���ٽ�CO?�¶ȣ�K��

h_CO2 = py.CoolProp.CoolProp.PropsSI('H', 'P', p_CO2, 'T', T_CO2, 'CO2'); % ��
s_CO2 = py.CoolProp.CoolProp.PropsSI('S', 'P', p_CO2, 'T', T_CO2, 'CO2'); % ��

fprintf('���ٽ�CO?: �� = %.2f J/kg, �� = %.2f J/kg/K\n', double(h_CO2), double(s_CO2));

% R245fa�������Բ�ѯ
p_R245fa = 1e6; % R245faѹ����Pa��
T_R245fa = 90 + 273.15; % R245fa�¶ȣ�K��

h_R245fa = py.CoolProp.CoolProp.PropsSI('H', 'P', p_R245fa, 'T', T_R245fa, 'R245fa'); % ��
s_R245fa = py.CoolProp.CoolProp.PropsSI('S', 'P', p_R245fa, 'T', T_R245fa, 'R245fa'); % ��

fprintf('R245fa: �� = %.2f J/kg, �� = %.2f J/kg/K\n', double(h_R245fa), double(s_R245fa));

% ��ˮ��Һ�������Բ�ѯ���Խ���ʽ��
w_ammonia = 0.45; % ��ˮ����������45%��
T_ammonia = 120; % �¶ȣ���C��
p_ammonia = 1e5; % ��ˮѹ����Pa��

% ��ˮ��Һ���ʺ��أ�ʾ����ʽ�����������ʵ�������޸ģ�
h_ammonia = w_ammonia * (2000 + 4 * T_ammonia) + (1 - w_ammonia) * (1000 + 2 * T_ammonia);
s_ammonia = w_ammonia * (6 + 0.1 * T_ammonia) + (1 - w_ammonia) * (2 + 0.05 * T_ammonia);

fprintf('��ˮ��Һ: �� = %.2f J/kg, �� = %.2f J/kg/K\n', h_ammonia, s_ammonia);
