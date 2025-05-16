# -*- coding:utf-8 -*-
import CoolProp.CoolProp as CP
import numpy as np

def check_state(p_Pa, T_K, fluid_name):
    """检查工质状态是否在有效范围内"""
    try:
        # 获取临界参数
        T_crit = CP.PropsSI('Tcrit', fluid_name)
        p_crit = CP.PropsSI('Pcrit', fluid_name)
        
        # 检查是否在临界点以上
        if T_K > T_crit and p_Pa > p_crit:
            return "超临界"
            
        # 获取饱和参数
        p_sat = CP.PropsSI('P', 'T', T_K, 'Q', 0, fluid_name)
        
        if abs(p_Pa - p_sat) < 1e3:  # 允许1kPa的误差
            return "饱和"
        elif p_Pa > p_sat:
            return "过冷"
        else:
            return "过热"
    except:
        return "未知"

def print_state(description, pressure_pa, temperature_c, fluid_name):
    """ 计算并打印工质在指定状态下的热物理性质 """
    T_K = temperature_c + 273.15
    p_Pa = pressure_pa
    
    try:
        # 检查状态
        state = check_state(p_Pa, T_K, fluid_name)
        
        # 计算基本物性
        h = CP.PropsSI('H', 'P', p_Pa, 'T', T_K, fluid_name) / 1000  # kJ/kg
        s = CP.PropsSI('S', 'P', p_Pa, 'T', T_K, fluid_name) / 1000  # kJ/kg·K
        rho = CP.PropsSI('D', 'P', p_Pa, 'T', T_K, fluid_name)  # kg/m³
        
        print(f"{description} ({fluid_name}):")
        print(f"  压力 = {pressure_pa/1e5:.3f} bar")
        print(f"  温度 = {temperature_c:.2f} °C")
        print(f"  状态 = {state}")
        print(f"  焓值 = {h:.2f} kJ/kg")
        print(f"  熵值 = {s:.4f} kJ/kg·K")
        print(f"  密度 = {rho:.2f} kg/m³")
        
        # 尝试计算其他物性
        try:
            cp = CP.PropsSI('C', 'P', p_Pa, 'T', T_K, fluid_name) / 1000  # kJ/kg·K
            print(f"  比热容 = {cp:.3f} kJ/kg·K")
        except:
            pass
            
        try:
            mu = CP.PropsSI('V', 'P', p_Pa, 'T', T_K, fluid_name) * 1e6  # μPa·s
            print(f"  动力粘度 = {mu:.2f} μPa·s")
        except:
            pass
            
        try:
            k = CP.PropsSI('L', 'P', p_Pa, 'T', T_K, fluid_name) * 1000  # mW/m·K
            print(f"  导热系数 = {k:.3f} mW/m·K")
        except:
            pass
            
        print()  # 空行
    except Exception as e:
        print(f"计算{fluid_name}物性时出错: {e}\n")

# 示例输入
if __name__ == "__main__":
    print("=== 超临界CO₂工质状态计算示例 ===")
    print_state("顶循环状态点，例如透平入口", 8e6, 550, 'CO2')
    print_state("底循环状态点，例如压缩机入口", 7.4e6, 32, 'CO2')

    print("=== R245fa有机朗肯循环工质状态计算示例 ===")
    # 调整到有效范围内的参数
    print_state("蒸发器入口状态", 2.5e5, 80, 'R245fa')  # 过冷状态
    print_state("蒸发器出口状态", 2.5e5, 120, 'R245fa')  # 过热状态


