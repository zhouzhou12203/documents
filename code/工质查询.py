# -*- coding:utf-8 -*-
import CoolProp.CoolProp as CP
import numpy as np

def print_state(description, pressure_pa, temperature_c, fluid_name):
    """ 计算并打印工质在指定状态下的热物理性质 """
    T_K = temperature_c + 273.15
    p_Pa = pressure_pa
    try:
        h = CP.PropsSI('H', 'P', p_Pa, 'T', T_K, fluid_name) / 1000  # kJ/kg
        s = CP.PropsSI('S', 'P', p_Pa, 'T', T_K, fluid_name) / 1000  # kJ/kg·K
        print(f"{description} ({fluid_name}):")
        print(f"  压力 = {pressure_pa/1e5:.3f} bar")
        print(f"  温度 = {temperature_c:.2f} °C")
        print(f"  焓值 = {h:.2f} kJ/kg")
        print(f"  熵值 = {s:.4f} kJ/kg·K\n")
    except Exception as e:
        print(f"计算{fluid_name}物性时出错: {e}\n")

def nh3_water_properties(temperature_c, pressure_pa, ammonia_mass_fraction):
    """
    模拟计算氨水溶液焓和熵
    这里只做示范，实际氨水复杂，需要详细模型或数据库。
    采用简单线性经验近似作为示例：

    h = h_water + w*(h_ammonia - h_water)
    s = s_water + w*(s_ammonia - s_water)
    """
    T = temperature_c + 273.15  # K
    p = pressure_pa

    # 水对应状态（饱和水近似）
    h_water = 4180 * temperature_c * 1e-3  # kJ/kg，粗略估计
    s_water = 4.18 * np.log(T/273.15) * 1e-3  # kJ/kg*K，粗略估计

    # 氨气对应状态（用理想气近似）
    # 下面数值仅举例，不代表真实物性
    h_ammonia = 1500 + 2 * temperature_c  # kJ/kg
    s_ammonia = 5.0 + 0.01 * temperature_c  # kJ/kg*K

    w = ammonia_mass_fraction
    h_mix = h_water * (1-w) + h_ammonia * w
    s_mix = s_water * (1-w) + s_ammonia * w

    return h_mix, s_mix

def print_nh3water_state(description, temperature_c, pressure_pa, ammonia_mass_fraction):
    h, s = nh3_water_properties(temperature_c, pressure_pa, ammonia_mass_fraction)
    print(f"{description} (氨水溶液):")
    print(f"  压力 = {pressure_pa/1e5:.3f} bar")
    print(f"  温度 = {temperature_c:.2f} °C")
    print(f"  氨质量分数 = {ammonia_mass_fraction:.2f}")
    print(f"  焓值（估算）= {h:.2f} kJ/kg")
    print(f"  熵值（估算）= {s:.4f} kJ/kg·K\n")

# 示例输入
if __name__ == "__main__":
    print("=== 超临界CO₂工质状态计算示例 ===")
    print_state("顶循环状态点，例如透平入口", 8e6, 550, 'CO2')

    print("=== R245fa有机朗肯循环工质状态计算示例 ===")
    print_state("蒸发器入口状态", 1.7e5, 120, 'R245fa')

    print("=== 氨水溶液热物性估算示例 ===")
    print_nh3water_state("基氨水溶液状态点", 120, 1.5e5, 0.45)

    print("=== 其他可计算状态点，请根据实际需要自行调用以上函数 ===")
