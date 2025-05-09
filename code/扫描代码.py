import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

# 计算系统性能的示例函数
def calculate_system_performance(P_CO2, T_CO2, T_ammonia, P_R245fa):
    # 计算超临界CO₂焓
    h_CO2 = PropsSI('H', 'P', P_CO2, 'T', T_CO2, 'CO2')
    # 计算氨的焓（需确保温度在可行范围内）
    h_ammonia = PropsSI('H', 'P', P_R245fa, 'T', T_ammonia, 'Ammonia')
    return h_CO2 + h_ammonia / 10000  # 示例性能

# 设置参数范围，确保氨的温度范围不低于其最低饱和温度（195.495 K）
P_in_CO2_range = np.linspace(5000000, 8000000, 5)  # 压力范围 (Pa)
T_in_CO2_range = np.linspace(500, 600, 5)  # 温度范围 (K)
T_in_ammonia_range = np.linspace(200, 250, 5)  # 修改后的温度范围，> 195.495 K
P_in_R245fa_range = np.linspace(150000, 250000, 5)  # 压力范围 (Pa)

# 初始化结果存储
results = []

# 运行参数扫描
for P_CO2 in P_in_CO2_range:
    for T_CO2 in T_in_CO2_range:
        for T_ammonia in T_in_ammonia_range:
            for P_R245fa in P_in_R245fa_range:
                try:
                    # 进行热性能计算
                    performance = calculate_system_performance(P_CO2, T_CO2, T_ammonia, P_R245fa)
                    results.append((P_CO2, T_CO2, T_ammonia, P_R245fa, performance))
                except Exception as e:
                    print(f"计算出错：{e}")

# 提取结果数据
P_CO2_results = [r[0] for r in results]
performance_results = [r[4] for r in results]

# 画图分析
plt.figure(figsize=(10, 6))
plt.plot(P_CO2_results, performance_results, marker='o', linestyle='-')
plt.title('Effect of CO₂ Inlet Pressure on System Performance', fontsize=14)
plt.xlabel('CO₂ Inlet Pressure (Pa)', fontsize=12)
plt.ylabel('System Performance (Example Indicator)', fontsize=12)
plt.grid()
plt.show()
