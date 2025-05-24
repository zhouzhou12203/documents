import json
from state_point_calculator import StatePoint, to_kelvin, to_pascal
from cycle_components import (
    model_compressor_MC,
    model_turbine_T,
    model_pump_ORC,
    model_heat_exchanger_effectiveness,
    model_evaporator_GO,
    model_cooler_set_T_out,
    model_heater_set_T_out 
    # 确保所有在cycle_components.py中定义的模型函数都被导入
)

def load_cycle_parameters(filename="cycle_setup_parameters.json"):
    """从JSON文件加载循环设定参数"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            params = json.load(f)
        print(f"成功从 {filename} 加载循环参数。")
        return params
    except FileNotFoundError:
        print(f"错误: 参数文件 {filename} 未找到。请先运行 状态点计算.py 生成该文件。")
        return None
    except json.JSONDecodeError:
        print(f"错误: 参数文件 {filename} 格式不正确，无法解析。")
        return None
    except Exception as e:
        print(f"加载参数文件时发生未知错误: {e}")
        return None

def simulate_scbc_orc_cycle(params):
    """
    模拟SCBC/ORC联合循环。
    目前仅为框架，后续将填充详细的循环计算逻辑。
    """
    if params is None:
        print("由于参数加载失败，无法开始仿真。")
        return

    print("\n--- 开始SCBC/ORC联合循环仿真 ---")
    print("使用的设定参数:")
    # 为了简洁，可以只打印一部分关键参数或整个字典
    # print(json.dumps(params, indent=4, ensure_ascii=False)) 
    
    # 从参数中提取常用值
    scbc_params = params.get("scbc_parameters", {})
    orc_params = params.get("orc_parameters", {})
    ref_conditions = params.get("reference_conditions", {})
    # hx_common_params = params.get("heat_exchangers_common", {})

    print(f"\nSCBC主要参数:")
    print(f"  T5 (透平入口温度): {scbc_params.get('T5_turbine_inlet_C')} °C")
    print(f"  PR (主循环压比): {scbc_params.get('PR_main_cycle_pressure_ratio')}")
    print(f"  η_T (SCBC透平效率): {scbc_params.get('eta_T_turbine')}")
    print(f"  η_C (SCBC压缩机效率): {scbc_params.get('eta_C_compressor')}")

    # TODO: 
    # 1. 初始化循环的起始点（例如点1）的状态对象。
    #    P1 = to_pascal(scbc_params.get('p1_compressor_inlet_kPa'), 'kpa')
    #    T1 = to_kelvin(scbc_params.get('T1_compressor_inlet_C'))
    #    state1 = StatePoint(params["fluids"]["scbc"], "SCBC_P1")
    #    state1.props_from_PT(P1, T1)
    #    # 需要设定一个初始的总质量流量，或者基于phi_ER_MW反推
    
    # --- 初始化SCBC循环起点 (点1) ---
    scbc_fluid = params.get("fluids", {}).get("scbc", "CO2")
    
    p1_kpa = scbc_params.get('p1_compressor_inlet_kPa')
    t1_c = scbc_params.get('T1_compressor_inlet_C')
    # 根据表10 SCBC/ORC优化数据，点1的质量流量是1945.09 kg/s
    # 这个流量对应的是流经主压缩机MC和蒸发器GO热侧（8m->9）然后到主冷却器CS的流量。
    m_dot_mc_branch = 1945.09 # kg/s

    state1 = StatePoint(fluid_name=scbc_fluid, name="P1_MC_In")
    P1_Pa = to_pascal(p1_kpa, 'kpa')
    T1_K = to_kelvin(t1_c)
    state1.props_from_PT(P1_Pa, T1_K)
    state1.m_dot = m_dot_mc_branch

    if not state1.h:
        print("错误: 初始化SCBC点1失败。仿真终止。")
        return
    print("\n--- SCBC循环计算开始 ---")
    print("初始状态点1 (主压缩机进口):")
    print(state1)

    # --- 主压缩机 (MC) ---
    # 出口压力 P2 = P1 * PR_top
    # 效率 eta_C_scbc
    pr_top = scbc_params.get('PR_main_cycle_pressure_ratio')
    eta_mc = scbc_params.get('eta_C_compressor')
    P2_Pa = P1_Pa * pr_top

    state2, W_mc_J_kg = model_compressor_MC(state1, P2_Pa, eta_mc)
    if not state2:
        print("错误: 主压缩机MC计算失败。仿真终止。")
        return
    
    W_mc_total_MW = (W_mc_J_kg * state1.m_dot) / 1e6 if state1.m_dot else None

    print("\n计算得到状态点2 (主压缩机出口):")
    print(state2)
    if W_mc_total_MW is not None:
        print(f"主压缩机MC耗功: {W_mc_J_kg/1000:.2f} kJ/kg, 总功率: {W_mc_total_MW:.2f} MW")

    # 与论文表10点2对比 (P=24198 kPa, T=121.73 C, h=453.36 kJ/kg)
    print("对比论文表10 - 点2:")
    T2_paper_C = 121.73
    h2_paper_kJ = 453.36
    print(f"  计算 T2: {state2.T - 273.15:.2f}°C (论文: {T2_paper_C}°C)")
    print(f"  计算 h2: {state2.h / 1000:.2f} kJ/kg (论文: {h2_paper_kJ} kJ/kg)")
    
    # --- 低温回热器 (LTR) ---
    # 冷流进口: state2
    # 热流进口: state7 (来自HTR热出口) - 此处我们先用论文表10数据做假设进行初步计算
    # 效率: eta_L
    print("\n--- 低温回热器 (LTR) 计算 ---")
    eta_L = scbc_params.get('eta_L_LTR_effectiveness')
    
    # 假设点7状态 (LTR热进口) - 来自论文表10 SCBC/ORC优化数据
    # P=7400.00 kPa, T=306.16 C, m_dot=2641.42 kg/s (总流量)
    P7_assumed_kPa = 7400.00
    T7_assumed_C = 306.16
    # LTR热侧流量应为总流量，与点7一致
    # LTR冷侧流量是state2.m_dot (即m_dot_mc_branch = 1945.09 kg/s)
    m_dot_hot_ltr = scbc_params.get("m_dot_total_main_flow_kg_s", 2641.42) # 假设总流量，或从参数读取

    state7_assumed = StatePoint(scbc_fluid, "P7_LTR_HotIn_Assumed")
    state7_assumed.props_from_PT(to_pascal(P7_assumed_kPa, 'kpa'), to_kelvin(T7_assumed_C))
    state7_assumed.m_dot = m_dot_hot_ltr # SCBC主回路总流量

    if not (state7_assumed.h and state2.h):
        print("错误: LTR进口状态不完整 (state2或假设的state7)。仿真终止。")
        return

    print("LTR 热流进口 (点7 - 假设自论文表10):")
    print(state7_assumed)
    print("LTR 冷流进口 (点2 - 来自MC计算):")
    print(state2) # state2.m_dot 应该是 m_dot_mc_branch

    # 调用模型 (hot_fluid_is_C_min_side=True, 与我们之前测试LTR时吻合的设定一致)
    # LTR热出口是点8，冷出口是点3''(混合前)
    state8_calc_ltr, state_ltr_cold_out, Q_ltr_calc = model_heat_exchanger_effectiveness(
        state_hot_in=state7_assumed,
        state_cold_in=state2, # state2的m_dot是m_dot_mc_branch
        effectiveness=eta_L,
        hot_fluid_is_C_min_side=True,
        name_suffix="LTR"
    )

    if not (state8_calc_ltr and state_ltr_cold_out):
        print("错误: LTR计算失败。仿真终止。")
        return

    print("\n计算得到的LTR热流出口 (模拟点8):")
    print(state8_calc_ltr)
    print("计算得到的LTR冷流出口 (模拟点3'' - 混合前):")
    print(state_ltr_cold_out)
    if Q_ltr_calc is not None:
        print(f"LTR换热量 Q: {Q_ltr_calc / 1e6:.2f} MW")

    # 与论文表10点8对比 (LTR热出口)
    print("对比论文表10 - 点8 (LTR热出口):")
    T8_paper_C = 147.55
    h8_paper_kJ = 582.06
    # 注意：state8_calc_ltr.m_dot 将是热侧进口流量(m_dot_hot_ltr)。
    # 论文中点8的质量流量是分流后去RC或GO的一部分。我们主要对比P, T, h, s。
    print(f"  计算 T8: {state8_calc_ltr.T - 273.15:.2f}°C (论文: {T8_paper_C}°C)")
    print(f"  计算 h8: {state8_calc_ltr.h / 1000:.2f} kJ/kg (论文: {h8_paper_kJ} kJ/kg)")
    # 注意：state8_calc_ltr.m_dot 此时是 LTR 热侧的总流量 (m_dot_hot_ltr)
    # 实际点8分流后的流量需要单独处理

    # --- 再压缩机 (RC) ---
    # 进口状态与计算得到的 state8_calc_ltr 相同 (P,T,h,s)
    # 进口流量 m_dot_rc = m_dot_hot_ltr - m_dot_mc_branch (总流量 - 主压缩机流量)
    print("\n--- 再压缩机 (RC) 计算 ---")
    
    # 流量应为 m_dot_hot_ltr (2641.42) - m_dot_mc_branch (1945.09) = 696.33 kg/s
    # 这个流量值也对应论文中点3的总流量减去点2的流量 (如果点3是混合点的话)
    # m_dot_3_paper = 2641.42, m_dot_2_paper = 1945.09 => m_dot_rc_implied = 696.33
    m_dot_rc = m_dot_hot_ltr - state2.m_dot
    if abs(m_dot_rc - 696.33) > 0.01: # 校验一下流量计算
        print(f"警告: 计算得到的RC流量 {m_dot_rc:.2f} kg/s 与预期 696.33 kg/s 有差异。")
        m_dot_rc = 696.33 # 强制使用推断值以保证后续混合点流量正确

    state8r_rc_in = StatePoint(scbc_fluid, "P8r_RC_In")
    # 使用state8_calc_ltr的P,h来定义进口状态，以保持热力学一致性
    if state8_calc_ltr.P is None or state8_calc_ltr.h is None:
        print("错误: LTR热出口状态不完整，无法设定RC进口。仿真终止。")
        return
    state8r_rc_in.props_from_PH(state8_calc_ltr.P, state8_calc_ltr.h)
    state8r_rc_in.m_dot = m_dot_rc
    
    P_rc_out_Pa = state2.P # RC出口压力与MC出口压力相同
    eta_rc = scbc_params.get('eta_C_compressor')

    if not state8r_rc_in.h:
        print("错误: RC进口状态 (基于state8_calc_ltr) 不完整。仿真终止。")
        return

    print("RC 进口状态 (点8r - 基于计算的LTR热出口状态，流量调整):")
    print(state8r_rc_in)

    state_rc_out, W_rc_J_kg = model_compressor_MC(state8r_rc_in, P_rc_out_Pa, eta_rc)
    if not state_rc_out:
        print("错误: 再压缩机RC计算失败。仿真终止。")
        return

    W_rc_total_MW = (W_rc_J_kg * state_rc_out.m_dot) / 1e6 if state_rc_out.m_dot else None
    print("\n计算得到的再压缩机RC出口状态 (点3'_rc):")
    print(state_rc_out)
    if W_rc_total_MW is not None:
        print(f"再压缩机RC耗功: {W_rc_J_kg/1000:.2f} kJ/kg, 总功率: {W_rc_total_MW:.2f} MW")

    # --- 混合点3 (LTR冷出口 + RC出口) ---
    print("\n--- 混合点3 计算 ---")
    # 输入1: state_ltr_cold_out (来自LTR冷出口, 流量 state2.m_dot)
    # 输入2: state_rc_out (来自RC出口, 流量 m_dot_rc)
    
    m_dot_3_calc = state_ltr_cold_out.m_dot + state_rc_out.m_dot
    if abs(m_dot_3_calc) < 1e-6: # 避免除零
        print("错误: 混合点3总流量接近零。仿真终止。")
        return
        
    h3_mixed_J_kg = (state_ltr_cold_out.m_dot * state_ltr_cold_out.h +
                     state_rc_out.m_dot * state_rc_out.h) / m_dot_3_calc
    
    P3_mixed_Pa = state2.P # 假设混合后压力为高压侧压力 (MC/RC出口压力)

    state3_calc = StatePoint(scbc_fluid, "P3_Mixed_Calc")
    state3_calc.props_from_PH(P3_mixed_Pa, h3_mixed_J_kg)
    state3_calc.m_dot = m_dot_3_calc

    if not state3_calc.h:
        print("错误: 混合点3状态计算失败。仿真终止。")
        return

    print("\n计算得到的混合点3状态:")
    print(state3_calc)

    # 与论文表10点3对比
    print("对比论文表10 - 点3 (混合点):")
    T3_paper_C = 281.92
    h3_paper_kJ = 696.46
    m3_paper_kg_s = 2641.42 # 1945.09 (MC) + 696.33 (RC)
    print(f"  计算 T3: {state3_calc.T - 273.15:.2f}°C (论文: {T3_paper_C}°C)")
    print(f"  计算 h3: {state3_calc.h / 1000:.2f} kJ/kg (论文: {h3_paper_kJ} kJ/kg)")
    print(f"  计算 m_dot3: {state3_calc.m_dot:.2f} kg/s (论文: {m3_paper_kg_s} kg/s)")

    # --- 高温回热器 (HTR) ---
    # 冷流进口: state3_calc (流量 m_dot_3_calc)
    # 热流进口: state6 (来自透平T出口) - 此处先用论文表10数据做假设
    print("\n--- 高温回热器 (HTR) 计算 ---")
    eta_H = scbc_params.get('eta_H_HTR_effectiveness')
    
    # 假设点6状态 (HTR热进口) - 来自论文表10 SCBC/ORC优化数据
    P6_assumed_kPa = 7400.00
    T6_assumed_C = 455.03
    # HTR两侧流量应等于混合后的总流量 state3_calc.m_dot
    m_dot_htr_main = state3_calc.m_dot
    
    state6_assumed_htr_in = StatePoint(scbc_fluid, "P6_HTR_HotIn_Assumed")
    state6_assumed_htr_in.props_from_PT(to_pascal(P6_assumed_kPa, 'kpa'), to_kelvin(T6_assumed_C))
    state6_assumed_htr_in.m_dot = m_dot_htr_main

    if not (state6_assumed_htr_in.h and state3_calc.h):
        print("错误: HTR进口状态不完整。仿真终止。")
        return

    print("HTR 热流进口 (点6 - 假设自论文表10):")
    print(state6_assumed_htr_in)
    print("HTR 冷流进口 (点3 - 来自混合计算):")
    print(state3_calc)

    state7_htr_hot_out, state4_htr_cold_out, Q_htr_calc = model_heat_exchanger_effectiveness(
        state_hot_in=state6_assumed_htr_in,
        state_cold_in=state3_calc,
        effectiveness=eta_H,
        hot_fluid_is_C_min_side=True,
        name_suffix="HTR"
    )

    if not (state7_htr_hot_out and state4_htr_cold_out):
        print("错误: HTR计算失败。仿真终止。")
        return

    print("\n计算得到的HTR热流出口 (模拟点7):")
    print(state7_htr_hot_out)
    print("计算得到的HTR冷流出口 (模拟点4):")
    print(state4_htr_cold_out)
    if Q_htr_calc is not None: print(f"HTR换热量 Q: {Q_htr_calc / 1e6:.2f} MW")

    print("对比论文表10 - 点4 (HTR冷出口):")
    T4_paper_C = 417.94; h4_paper_kJ = 867.76
    print(f"  计算 T4: {state4_htr_cold_out.T - 273.15:.2f}°C (论文: {T4_paper_C}°C)")
    print(f"  计算 h4: {state4_htr_cold_out.h / 1000:.2f} kJ/kg (论文: {h4_paper_kJ} kJ/kg)")
    print("对比论文表10 - 点7 (HTR热出口):")
    T7_paper_C = 306.16; h7_paper_kJ = 761.08
    print(f"  计算 T7: {state7_htr_hot_out.T - 273.15:.2f}°C (论文: {T7_paper_C}°C)")
    print(f"  计算 h7: {state7_htr_hot_out.h / 1000:.2f} kJ/kg (论文: {h7_paper_kJ} kJ/kg)")

    # --- 吸热器 (ER) ---
    # 进口: state4_htr_cold_out
    # 出口目标温度: T5_turbine_inlet_C
    print("\n--- 吸热器 (ER) 计算 ---")
    T5_target_C = scbc_params.get('T5_turbine_inlet_C')
    
    state5_er_out, Q_er_calc = model_heater_set_T_out(
        state_in=state4_htr_cold_out,
        T_out_K=to_kelvin(T5_target_C),
        name_suffix="ER"
    )
    if not state5_er_out:
        print("错误: 吸热器ER计算失败。仿真终止。")
        return
        
    print("\n计算得到的吸热器ER出口状态 (点5 - SCBC透平进口):")
    print(state5_er_out)
    if Q_er_calc is not None: print(f"吸热器ER吸收热量 Q_ER: {Q_er_calc / 1e6:.2f} MW")

    print("对比论文表10 - 点5:")
    T5_paper_C = 599.85; h5_paper_kJ = 1094.91
    print(f"  计算 T5: {state5_er_out.T - 273.15:.2f}°C (论文: {T5_paper_C}°C)")
    print(f"  计算 h5: {state5_er_out.h / 1000:.2f} kJ/kg (论文: {h5_paper_kJ} kJ/kg)")

    # --- SCBC透平 (T) ---
    # 进口: state5_er_out
    # 出口压力: P1_Pa (循环低压, 即点6,7,8的压力)
    print("\n--- SCBC透平 (T) 计算 ---")
    eta_T = scbc_params.get('eta_T_turbine')
    P6_turbine_out_Pa = to_pascal(P7_assumed_kPa, 'kpa') # 与点7,点8同压, 即P_low_cycle

    state6_turbine_out, W_t_J_kg = model_turbine_T(state5_er_out, P6_turbine_out_Pa, eta_T)
    if not state6_turbine_out:
        print("错误: SCBC透平T计算失败。仿真终止。")
        return

    W_t_total_MW = (W_t_J_kg * state5_er_out.m_dot) / 1e6 if state5_er_out.m_dot else None
    print("\n计算得到的SCBC透平出口状态 (点6):")
    print(state6_turbine_out)
    if W_t_total_MW is not None: print(f"SCBC透平做功: {W_t_J_kg/1000:.2f} kJ/kg, 总功率: {W_t_total_MW:.2f} MW")

    print("对比论文表10 - 点6:")
    T6_paper_C = 455.03; h6_paper_kJ = 932.38
    print(f"  计算 T6: {state6_turbine_out.T - 273.15:.2f}°C (论文: {T6_paper_C}°C)")
    print(f"  计算 h6: {state6_turbine_out.h / 1000:.2f} kJ/kg (论文: {h6_paper_kJ} kJ/kg)")
    print(f"  迭代检查: 计算得到的T6 ({state6_turbine_out.T-273.15:.2f}°C) vs 假设的T6_HTR进口 ({T6_assumed_C}°C)")
    print(f"  迭代检查: 计算得到的h6 ({state6_turbine_out.h/1000:.2f}kJ/kg) vs 假设的h6_HTR进口 ({state6_assumed_htr_in.h/1000:.2f}kJ/kg)")
    
    # 此时，计算得到的 state6_turbine_out 是HTR热进口的更新值。
    # 计算得到的 state7_htr_hot_out 是LTR热进口的更新值。
    # 这些将用于下一轮迭代。

    print("\nSCBC主回路高温高压侧及透平初步计算完成。")
    print("后续需要加入迭代逻辑使state6和state7收敛，并完成ORC侧及SCBC低温侧计算。")
    print("\n后续仿真逻辑待实现...")


if __name__ == '__main__':
    cycle_params = load_cycle_parameters()
    if cycle_params:
        simulate_scbc_orc_cycle(cycle_params)