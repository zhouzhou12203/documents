import numpy as np
from CoolProp.CoolProp import PropsSI

# 定义函数计算状态点的热物性
def calculate_thermodynamic_properties(p, T, fluid):
    """计算给定压力和温度的工质热物性，包括焓和熵"""
    h = PropsSI('H', 'P', p, 'T', T, fluid)  # 焓 J/kg
    s = PropsSI('S', 'P', p, 'T', T, fluid)  # 熵 J/kg/K
    return h, s

# 定义系统参数
# 超临界CO₂循环参数
P_in_CO2 = 7400000  # 主压缩机入口压力 (Pa)
T_in_CO2 = 550 + 273.15  # 主压缩机入口温度 (K)

# 氨水循环参数
P_in_ammonia = 200000  # 基氨水溶液入口压力 (Pa)
T_in_ammonia = 120 + 273.15  # 基氨水溶液入口温度 (K)
w_ammonia = 0.5  # 氨水质量分数

# R245fa循环参数
P_in_R245fa = 178000  # R245fa蒸发器入口压力 (Pa)
T_in_R245fa = 119.8 + 273.15  # R245fa入口温度 (K)

# 计算状态点的热物性
h_CO2, s_CO2 = calculate_thermodynamic_properties(P_in_CO2, T_in_CO2, 'CO2')
h_ammonia, s_ammonia = calculate_thermodynamic_properties(P_in_ammonia, T_in_ammonia, 'Ammonia')
h_R245fa, s_R245fa = calculate_thermodynamic_properties(P_in_R245fa, T_in_R245fa, 'R245fa')

# -------------------------
# 能量守恒计算示例
# -------------------------
def energy_balance(P_in, h_in, h_out, W_out):
    """
    能量守恒方程
    输入参数：
    P_in: 输入压力 (Pa)
    h_in: 输入焓 (J/kg)
    h_out: 输出焓 (J/kg)
    W_out: 功输出 (W)
    """
    Q_in = h_in  # 流入的热量，假设为焓值
    Q_out = h_out + W_out  # 输出的热量
    return Q_in, Q_out

# 计算能量守恒
W_output_CO2 = 10000  # CO2循环的功输出 (W)
Q_in_CO2, Q_out_CO2 = energy_balance(P_in_CO2, h_CO2, h_CO2 - 2000, W_output_CO2)  # 假设焓损失2000 J/kg
print(f"超临界CO₂循环能量守恒： Q_in = {Q_in_CO2} J/kg, Q_out = {Q_out_CO2} J/kg")

# -------------------------
# 㶲守恒计算示例
# -------------------------
def exergy_balance(h_in, s_in, h_out, s_out):
    """
    㶲守恒方程
    输入参数：
    h_in: 输入焓 (J/kg)
    s_in: 输入熵 (J/kg/K)
    h_out: 输出焓 (J/kg)
    s_out: 输出熵 (J/kg/K)
    """
    E_in = h_in - 0.1 * s_in  # 理论输入㶲
    E_out = h_out - 0.1 * s_out  # 理论输出㶲
    return E_in, E_out

# 计算㶲守恒
E_in_CO2, E_out_CO2 = exergy_balance(h_CO2, s_CO2, h_CO2 - 2000, s_CO2)
print(f"超临界CO₂循环㶲守恒： E_in = {E_in_CO2} kJ/kg, E_out = {E_out_CO2} kJ/kg")

# -------------------------
# 㶲经济守恒计算示例
# -------------------------
def exergoeconomic_balance(cost_in, cost_out, investment):
    """
    㶲经济守恒方程
    输入参数：
    cost_in: 输入㶲流成本
    cost_out: 输出㶲流成本
    investment: 建设投资
    """
    total_in = cost_in + investment
    total_out = cost_out
    return total_in, total_out

# 假设参数
cost_in_CO2 = 1000  # 输入㶲流成本 ($)
cost_out_CO2 = 1200  # 输出㶲流成本 ($)
investment_CO2 = 50000  # 建设投资 ($)

# 计算㶲经济守恒
total_in_CO2, total_out_CO2 = exergoeconomic_balance(cost_in_CO2, cost_out_CO2, investment_CO2)
print(f"超临界CO₂循环㶲经济守恒： Total In = {total_in_CO2} $, Total Out = {total_out_CO2} $")
