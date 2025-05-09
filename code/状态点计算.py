import numpy as np
from CoolProp.CoolProp import PropsSI

# 定义状态点计算函数
def calculate_state_CO2(p, T):
    """计算CO₂的热物性"""
    h = PropsSI('H', 'P', p, 'T', T, 'CO2')  # 焓 J/kg
    s = PropsSI('S', 'P', p, 'T', T, 'CO2')  # 熵 J/kg/K
    return h, s

def calculate_state_R245fa(p, T):
    """计算R245fa的热物性"""
    h = PropsSI('H', 'P', p, 'T', T, 'R245fa')  # 焓 J/kg
    s = PropsSI('S', 'P', p, 'T', T, 'R245fa')  # 熵 J/kg/K
    return h, s

def calculate_state_ammonia(w, T):
    """假设基氨水溶液的焓和熵（简化模型）"""
    h = w * (2000 + 4 * T) + (1 - w) * (1000 + 2 * T)  # 焓（简化估算公式）
    s = w * (6 + 0.1 * T) + (1 - w) * (2 + 0.05 * T)  # 熵（简化估算公式）
    return h, s

# 系统参数
P_CO2 = 7400e3  # 超临界CO₂主压缩机入口压强 (Pa)
T_CO2_in = 550 + 273.15  # 稳态超临界CO2入口温度 (K)

# 计算CO₂状态
h_CO2, s_CO2 = calculate_state_CO2(P_CO2, T_CO2_in)
print(f'超临界CO₂: 焓 = {h_CO2:.2f} J/kg, 熵 = {s_CO2:.2f} J/kg/K')

P_R245fa = 178e3  # R245fa蒸发器入口压力 (Pa)
T_R245fa_in = 120 + 273.15  # R245fa入口温度 (K)

# 计算R245fa状态
h_R245fa, s_R245fa = calculate_state_R245fa(P_R245fa, T_R245fa_in)
print(f'R245fa: 焓 = {h_R245fa:.2f} J/kg, 熵 = {s_R245fa:.2f} J/kg/K')

# 计算氨水
w_ammonia = 0.45  # 氨水质量分数
T_ammonia_in = 120  # 氨水入口温度 (°C)
h_ammonia, s_ammonia = calculate_state_ammonia(w_ammonia, T_ammonia_in)
print(f'氨水溶液: 焓 = {h_ammonia:.2f} J/kg, 熵 = {s_ammonia:.2f} J/kg/K')
