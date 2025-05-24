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
    
    # --- SCBC高温侧迭代计算 (HTR, ER, Turbine T, LTR) ---
    print("\n--- 开始SCBC高温侧迭代计算 ---")
    max_iter_scbc = scbc_params.get("max_iter_scbc_main_loop", 20)
    tol_scbc_h_kJ_kg = scbc_params.get("tol_scbc_h_kJ_kg", 0.1) # 焓值收敛容差 0.1 kJ/kg

    # 初始化迭代起点 (state6: HTR热进口, state7: LTR热进口)
    # 使用论文数据或参数文件中的初始估计值
    P_low_cycle_Pa = to_pascal(scbc_params.get('P_low_cycle_kPa_guess', 7400.00), 'kpa') # 低压侧压力，用于透平出口和回热器热侧
    
    # state6_iter (HTR热进口, 即透平出口)
    T6_iter_C_guess = scbc_params.get('T6_HTR_hot_in_C_guess', 455.03) # 来自论文表10
    state6_iter = StatePoint(scbc_fluid, "P6_Iter_HTR_HotIn")
    state6_iter.props_from_PT(P_low_cycle_Pa, to_kelvin(T6_iter_C_guess))
    # 总流量 m_dot_total_main_flow_kg_s 在HTR, ER, Turbine中流动
    m_dot_total_main_flow_kg_s = scbc_params.get("m_dot_total_main_flow_kg_s", 2641.42)
    state6_iter.m_dot = m_dot_total_main_flow_kg_s
    if not state6_iter.h:
        print(f"错误: 初始化SCBC迭代点 state6_iter 失败 (T={T6_iter_C_guess}°C, P={P_low_cycle_Pa/1000}kPa)。仿真终止。")
        return

    # state7_iter (LTR热进口, 即HTR热出口)
    T7_iter_C_guess = scbc_params.get('T7_LTR_hot_in_C_guess', 306.16) # 来自论文表10
    state7_iter = StatePoint(scbc_fluid, "P7_Iter_LTR_HotIn")
    state7_iter.props_from_PT(P_low_cycle_Pa, to_kelvin(T7_iter_C_guess))
    state7_iter.m_dot = m_dot_total_main_flow_kg_s # LTR热侧也是总流量
    if not state7_iter.h:
        print(f"错误: 初始化SCBC迭代点 state7_iter 失败 (T={T7_iter_C_guess}°C, P={P_low_cycle_Pa/1000}kPa)。仿真终止。")
        return
        
    # 声明变量以便在循环外访问最终值
    state3_calc = None; state4_htr_cold_out = None; state5_er_out = None
    state6_turbine_out = None; state7_htr_hot_out = None
    state8_calc_ltr = None; state_ltr_cold_out = None
    W_t_J_kg = None; W_rc_J_kg = None; Q_er_calc = None; Q_ltr_calc = None; Q_htr_calc = None
    W_t_total_MW = None; W_rc_total_MW = None

    converged_scbc = False
    for i_scbc in range(max_iter_scbc):
        print(f"\nSCBC主回路迭代 {i_scbc + 1}/{max_iter_scbc}:")
        h6_old_J_kg = state6_iter.h
        h7_old_J_kg = state7_iter.h

        # --- 再计算混合点3 (依赖 state_ltr_cold_out, 而 state_ltr_cold_out 依赖 state7_iter) ---
        # 为了迭代的稳定性，第一次迭代时，RC和混合点3的计算需要基于初始的state7_iter来计算LTR
        # 后续迭代中，RC和混合点3的计算应该在LTR计算之后，使用更新的state_ltr_cold_out

        # --- 低温回热器 (LTR) ---
        # 冷流进口: state2 (固定)
        # 热流进口: state7_iter (上一轮HTR热出口)
        print(f"  LTR 热流进口 (state7_iter): T={(state7_iter.T - 273.15):.2f}°C, h={(state7_iter.h / 1000):.2f}kJ/kg")
        eta_L = scbc_params.get('eta_L_LTR_effectiveness')
        if not (state7_iter.h and state2.h):
            print("错误: LTR进口状态不完整 (state2或state7_iter)。迭代终止。")
            return
        
        _state8_calc_ltr, _state_ltr_cold_out, _Q_ltr_calc = model_heat_exchanger_effectiveness(
            state_hot_in=state7_iter,
            state_cold_in=state2,
            effectiveness=eta_L,
            hot_fluid_is_C_min_side=True, # 假设CO2在高温高压下比热容通常更大
            name_suffix=f"LTR_Iter{i_scbc+1}"
        )
        if not (_state8_calc_ltr and _state_ltr_cold_out):
            print("错误: LTR计算在迭代中失败。迭代终止。")
            return
        state8_calc_ltr, state_ltr_cold_out, Q_ltr_calc = _state8_calc_ltr, _state_ltr_cold_out, _Q_ltr_calc
        print(f"  LTR 热出口 (state8_calc_ltr): T={(state8_calc_ltr.T - 273.15):.2f}°C, h={(state8_calc_ltr.h / 1000):.2f}kJ/kg")
        print(f"  LTR 冷出口 (state_ltr_cold_out): T={(state_ltr_cold_out.T - 273.15):.2f}°C, h={(state_ltr_cold_out.h / 1000):.2f}kJ/kg")

        # --- 再压缩机 (RC) ---
        # 进口状态与计算得到的 state8_calc_ltr 相同 (P,T,h,s)
        # 进口流量 m_dot_rc = m_dot_total_main_flow_kg_s - m_dot_mc_branch
        m_dot_rc = m_dot_total_main_flow_kg_s - state2.m_dot # state2.m_dot is m_dot_mc_branch
        if abs(m_dot_rc - 696.33) > 0.01: # 论文推断值
             print(f"警告 (Iter {i_scbc+1}): 计算得到的RC流量 {m_dot_rc:.2f} kg/s 与预期 696.33 kg/s 有差异。")
             # m_dot_rc = 696.33 # 可选：强制

        state8r_rc_in = StatePoint(scbc_fluid, f"P8r_RC_In_Iter{i_scbc+1}")
        if state8_calc_ltr.P is None or state8_calc_ltr.h is None:
            print("错误: LTR热出口状态不完整，无法设定RC进口。迭代终止。")
            return
        state8r_rc_in.props_from_PH(state8_calc_ltr.P, state8_calc_ltr.h)
        state8r_rc_in.m_dot = m_dot_rc
        
        P_rc_out_Pa = state2.P # RC出口压力与MC出口压力相同
        eta_rc = scbc_params.get('eta_C_compressor')
        if not state8r_rc_in.h:
            print("错误: RC进口状态不完整。迭代终止。")
            return
        
        _state_rc_out, _W_rc_J_kg = model_compressor_MC(state8r_rc_in, P_rc_out_Pa, eta_rc)
        if not _state_rc_out:
            print("错误: 再压缩机RC计算失败。迭代终止。")
            return
        state_rc_out, W_rc_J_kg = _state_rc_out, _W_rc_J_kg
        W_rc_total_MW = (W_rc_J_kg * state_rc_out.m_dot) / 1e6 if state_rc_out.m_dot else None
        print(f"  RC 出口 (state_rc_out): T={(state_rc_out.T - 273.15):.2f}°C, h={(state_rc_out.h / 1000):.2f}kJ/kg")


        # --- 混合点3 (LTR冷出口 + RC出口) ---
        m_dot_3_calc = state_ltr_cold_out.m_dot + state_rc_out.m_dot
        if abs(m_dot_3_calc) < 1e-6:
            print("错误: 混合点3总流量接近零。迭代终止。")
            return
        h3_mixed_J_kg = (state_ltr_cold_out.m_dot * state_ltr_cold_out.h + \
                         state_rc_out.m_dot * state_rc_out.h) / m_dot_3_calc
        P3_mixed_Pa = state2.P

        _state3_calc = StatePoint(scbc_fluid, f"P3_Mixed_Iter{i_scbc+1}")
        _state3_calc.props_from_PH(P3_mixed_Pa, h3_mixed_J_kg)
        _state3_calc.m_dot = m_dot_3_calc
        if not _state3_calc.h:
            print("错误: 混合点3状态计算失败。迭代终止。")
            return
        state3_calc = _state3_calc
        print(f"  混合点3 (state3_calc): T={(state3_calc.T - 273.15):.2f}°C, h={(state3_calc.h / 1000):.2f}kJ/kg, m={state3_calc.m_dot:.2f}kg/s")
        # 校验总流量是否与 m_dot_total_main_flow_kg_s 一致
        if abs(state3_calc.m_dot - m_dot_total_main_flow_kg_s) > 0.01:
            print(f"警告 (Iter {i_scbc+1}): 混合点3流量 {state3_calc.m_dot:.2f} kg/s 与预设总流量 {m_dot_total_main_flow_kg_s:.2f} kg/s 不符。")
            state3_calc.m_dot = m_dot_total_main_flow_kg_s # 强制总流量


        # --- 高温回热器 (HTR) ---
        # 冷流进口: state3_calc (上一计算结果)
        # 热流进口: state6_iter (上一轮透平出口)
        print(f"  HTR 热流进口 (state6_iter): T={(state6_iter.T - 273.15):.2f}°C, h={(state6_iter.h / 1000):.2f}kJ/kg")
        eta_H = scbc_params.get('eta_H_HTR_effectiveness')
        if not (state6_iter.h and state3_calc.h):
            print("错误: HTR进口状态不完整。迭代终止。")
            return
        
        _state7_htr_hot_out, _state4_htr_cold_out, _Q_htr_calc = model_heat_exchanger_effectiveness(
            state_hot_in=state6_iter,
            state_cold_in=state3_calc,
            effectiveness=eta_H,
            hot_fluid_is_C_min_side=True,
            name_suffix=f"HTR_Iter{i_scbc+1}"
        )
        if not (_state7_htr_hot_out and _state4_htr_cold_out):
            print("错误: HTR计算失败。迭代终止。")
            return
        state7_htr_hot_out, state4_htr_cold_out, Q_htr_calc = _state7_htr_hot_out, _state4_htr_cold_out, _Q_htr_calc
        print(f"  HTR 热出口 (state7_new): T={(state7_htr_hot_out.T - 273.15):.2f}°C, h={(state7_htr_hot_out.h / 1000):.2f}kJ/kg")
        print(f"  HTR 冷出口 (state4_htr_cold_out): T={(state4_htr_cold_out.T - 273.15):.2f}°C, h={(state4_htr_cold_out.h / 1000):.2f}kJ/kg")

        # --- 吸热器 (ER) ---
        T5_target_C = scbc_params.get('T5_turbine_inlet_C')
        _state5_er_out, _Q_er_calc = model_heater_set_T_out(
            state_in=state4_htr_cold_out,
            T_out_K=to_kelvin(T5_target_C),
            name_suffix=f"ER_Iter{i_scbc+1}"
        )
        if not _state5_er_out:
            print("错误: 吸热器ER计算失败。迭代终止。")
            return
        state5_er_out, Q_er_calc = _state5_er_out, _Q_er_calc
        print(f"  ER 出口 (state5_er_out): T={(state5_er_out.T - 273.15):.2f}°C, h={(state5_er_out.h / 1000):.2f}kJ/kg")

        # --- SCBC透平 (T) ---
        eta_T = scbc_params.get('eta_T_turbine')
        # 透平出口压力 P6_turbine_out_Pa 应等于循环低压 P_low_cycle_Pa
        _state6_turbine_out, _W_t_J_kg = model_turbine_T(state5_er_out, P_low_cycle_Pa, eta_T)
        if not _state6_turbine_out:
            print("错误: SCBC透平T计算失败。迭代终止。")
            return
        state6_turbine_out, W_t_J_kg = _state6_turbine_out, _W_t_J_kg
        W_t_total_MW = (W_t_J_kg * state5_er_out.m_dot) / 1e6 if state5_er_out.m_dot else None
        print(f"  透平出口 (state6_new): T={(state6_turbine_out.T - 273.15):.2f}°C, h={(state6_turbine_out.h / 1000):.2f}kJ/kg")

        # 更新迭代变量
        state6_iter = state6_turbine_out
        state7_iter = state7_htr_hot_out
        
        # 检查收敛
        delta_h6_kJ_kg = abs(state6_iter.h - h6_old_J_kg) / 1000
        delta_h7_kJ_kg = abs(state7_iter.h - h7_old_J_kg) / 1000
        print(f"  收敛检查: Δh6={delta_h6_kJ_kg:.4f} kJ/kg, Δh7={delta_h7_kJ_kg:.4f} kJ/kg (目标 < {tol_scbc_h_kJ_kg} kJ/kg)")

        if delta_h6_kJ_kg < tol_scbc_h_kJ_kg and delta_h7_kJ_kg < tol_scbc_h_kJ_kg:
            converged_scbc = True
            print(f"SCBC主回路在迭代 {i_scbc + 1} 次后收敛。")
            break
    
    if not converged_scbc:
        print(f"警告: SCBC主回路在 {max_iter_scbc} 次迭代后未收敛。使用最后计算值。")

    print("\n--- SCBC高温侧迭代计算结束 ---")
    print("最终计算得到的SCBC状态点（迭代后）:")
    print("点6 (HTR热进口/透平出口):")
    print(state6_iter) # state6_iter 现在是收敛的 state6_turbine_out
    print("点7 (LTR热进口/HTR热出口):")
    print(state7_iter) # state7_iter 现在是收敛的 state7_htr_hot_out
    print("点3 (HTR冷进口/混合点):")
    print(state3_calc)
    print("点4 (ER进口/HTR冷出口):")
    print(state4_htr_cold_out)
    print("点5 (透平进口/ER出口):")
    print(state5_er_out)
    print("点8 (LTR热出口):") # state8_calc_ltr 是在最后一次成功迭代中计算的
    print(state8_calc_ltr)
    print("LTR冷出口 (去混合点):")
    print(state_ltr_cold_out)
    print("RC出口 (去混合点):") # state_rc_out 是在最后一次成功迭代中计算的
    print(state_rc_out)

    if W_t_total_MW is not None:
        print(f"SCBC透平做功 (迭代后): {W_t_J_kg/1000:.2f} kJ/kg, 总功率: {W_t_total_MW:.2f} MW")
    if W_rc_total_MW is not None:
        print(f"再压缩机RC耗功 (迭代后): {W_rc_J_kg/1000:.2f} kJ/kg, 总功率: {W_rc_total_MW:.2f} MW")
    if Q_er_calc is not None: print(f"吸热器ER吸收热量 Q_ER (迭代后): {Q_er_calc / 1e6:.2f} MW")


    # --- SCBC低温侧计算 ---
    # 点8分流后的主流 (去GO)
    # state8_calc_ltr 是LTR热出口，流量是 m_dot_total_main_flow_kg_s
    # 去RC的流量是 m_dot_rc
    # 去GO的流量是 m_dot_mc_branch = state2.m_dot
    # 点8分流后的主流 (去GO)
    # state8_calc_ltr 是LTR热出口，流量是 m_dot_hot_ltr (总流量)
    # 去RC的流量是 m_dot_rc
    # 去GO的流量是 m_dot_mc_branch = state2.m_dot
    
    print("\n--- SCBC低温侧计算 ---")
    
    state8_go_in = StatePoint(scbc_fluid, "P8_GO_HotIn")
    if state8_calc_ltr.P is None or state8_calc_ltr.h is None:
        print("错误: LTR热出口状态 (state8_calc_ltr) 不完整，无法设定GO进口。仿真终止。")
        return
    state8_go_in.props_from_PH(state8_calc_ltr.P, state8_calc_ltr.h)
    state8_go_in.m_dot = state2.m_dot # 流量是主压缩机分支的流量

    if not state8_go_in.h:
        print("错误: GO热侧进口状态 (state8_go_in) 初始化失败。仿真终止。")
        return

    print("\n蒸发器GO SCBC热侧进口状态 (点8_go_in - 基于计算的LTR热出口状态，流量调整):")
    print(state8_go_in)

    # --- 蒸发器GO (SCBC热侧) ---
    # 设定GO的SCBC侧出口温度 T9
    # 从论文表10，点9: T=125.25 C, P=7400 kPa (与点8同压)
    T9_target_C = scbc_params.get('T9_go_hot_out_C', 125.25)
    
    state9_go_hot_out, Q_go_scbc_side_J_s = model_cooler_set_T_out(
        state_in=state8_go_in,
        T_out_K=to_kelvin(T9_target_C),
        name_suffix="GO_SCBC_HotSide"
    )

    if not state9_go_hot_out:
        print("错误: 蒸发器GO SCBC热侧计算失败。仿真终止。")
        return
        
    print("\n计算得到的蒸发器GO SCBC热侧出口状态 (点9):")
    print(state9_go_hot_out)
    if Q_go_scbc_side_J_s is not None:
        print(f"蒸发器GO SCBC热侧放出热量 Q_GO_SCBC: {abs(Q_go_scbc_side_J_s) / 1e6:.2f} MW (此热量被ORC吸收)")

    print("对比论文表10 - 点9 (GO SCBC热出口):")
    T9_paper_C = 125.25; h9_paper_kJ = 460.95
    m9_paper_kg_s = 1945.09 # 等于主压缩机流量
    print(f"  计算 T9: {(state9_go_hot_out.T - 273.15):.2f}°C (论文: {T9_paper_C}°C)")
    print(f"  计算 h9: {(state9_go_hot_out.h / 1000):.2f} kJ/kg (论文: {h9_paper_kJ} kJ/kg)")
    print(f"  计算 m_dot9: {state9_go_hot_out.m_dot:.2f} kg/s (论文: {m9_paper_kg_s} kg/s, MC流量: {state2.m_dot:.2f} kg/s)")


    # --- 主冷却器 (CS) ---
    print("\n--- 主冷却器 (CS) 计算 ---")
    T1_target_K_cs_out = T1_K # 已在脚本开头定义 (state1 的温度)
    
    state1_cs_out_calc, Q_cs_J_s = model_cooler_set_T_out(
        state_in=state9_go_hot_out,
        T_out_K=T1_target_K_cs_out,
        name_suffix="CS"
    )

    if not state1_cs_out_calc:
        print("错误: 主冷却器CS计算失败。仿真终止。")
        return
        
    print("\n计算得到的主冷却器CS出口状态 (应接近初始点1):")
    print(state1_cs_out_calc) # Assumes StatePoint.__str__ handles units correctly
    if Q_cs_J_s is not None:
        print(f"主冷却器CS放出热量 Q_CS: {abs(Q_cs_J_s) / 1e6:.2f} MW")

    # 检查SCBC循环在点1的闭合性
    print("\nSCBC循环闭合检查 (点1 - 主压缩机进口):")
    # Assuming state1 and state1_cs_out_calc.P are in Pa, state1.h in J/kg
    print(f"  初始定义的 state1: T={(state1.T - 273.15):.2f}°C, P={(state1.P / 1000):.2f} kPa, h={(state1.h / 1000):.2f} kJ/kg")
    print(f"  CS计算出口 state1_cs_out_calc: T={(state1_cs_out_calc.T - 273.15):.2f}°C, P={(state1_cs_out_calc.P / 1000):.2f} kPa, h={(state1_cs_out_calc.h / 1000):.2f} kJ/kg")
    
    delta_T1 = abs(state1.T - state1_cs_out_calc.T)
    delta_P1 = abs(state1.P - state1_cs_out_calc.P)
    delta_h1 = abs(state1.h - state1_cs_out_calc.h)
    print(f"  差异: ΔT={delta_T1:.3f} K, ΔP={delta_P1/1000:.3f} kPa (预期接近0, 因P_low_cycle ≈ P1_param), Δh={delta_h1/1000:.3f} kJ/kg")

    # 更新SCBC状态点字典
    scbc_states = {
        "P1_MC_In_Initial": state1,
        "P2_MC_Out": state2,
        "P3''_LTR_ColdOut": state_ltr_cold_out,
        "P8r_RC_In": state8r_rc_in,
        "P3'_RC_Out": state_rc_out,
        "P3_Mixed_HTR_ColdIn": state3_calc,
        "P4_HTR_ColdOut_ER_In": state4_htr_cold_out,
        "P5_ER_Out_Turbine_In": state5_er_out,
        "P6_Turbine_Out": state6_turbine_out,
        "P7_HTR_HotOut": state7_htr_hot_out,
        "P8_LTR_HotOut_Total": state8_calc_ltr,
        "P8_GO_HotIn": state8_go_in,
        "P9_GO_HotOut_CS_In": state9_go_hot_out,
        "P1_CS_Out_Calculated": state1_cs_out_calc,
    }
    
    # SCBC 净功和效率 (初步，基于单次计算，未迭代)
    if W_t_total_MW is not None and W_mc_total_MW is not None and W_rc_total_MW is not None:
        W_net_scbc_MW = W_t_total_MW - W_mc_total_MW - W_rc_total_MW
        print(f"\nSCBC净输出功 (初步): {W_net_scbc_MW:.2f} MW")
        if Q_er_calc is not None and Q_er_calc > 0: # Q_er_calc is from ER model
            Q_in_scbc_MW = Q_er_calc / 1e6
            eta_scbc_thermal = W_net_scbc_MW / Q_in_scbc_MW
            print(f"SCBC吸热器吸热量 Q_ER: {Q_in_scbc_MW:.2f} MW")
            print(f"SCBC热效率 (初步, W_net/Q_ER): {eta_scbc_thermal*100:.2f}%")
        else:
            print("SCBC吸热器吸热量为零或未计算，无法计算热效率。")
    else:
        print("\n部分功率未计算，无法得到SCBC净功和效率。")

    print("\n--- SCBC循环单次计算完成 (未进行迭代收敛) ---")
    
    # 存储 Q_go_scbc_side_J_s (SCBC侧在GO中放出的热量) 以供ORC侧使用
    # Q_go_scbc_side_J_s 是负值，表示放出。ORC吸收的热量是其绝对值。
    if Q_go_scbc_side_J_s is not None:
        params["intermediate_results"] = params.get("intermediate_results", {})
        params["intermediate_results"]["Q_GO_to_ORC_J_s"] = abs(Q_go_scbc_side_J_s)
        params["intermediate_results"]["T9_GO_HotOut_K"] = state9_go_hot_out.T
        params["intermediate_results"]["P8_GO_HotIn_Pa"] = state8_go_in.P
        params["intermediate_results"]["m_dot_GO_HotSide_kg_s"] = state8_go_in.m_dot
        # 也传递一下SCBC侧GO进口温度，作为ORC侧蒸发温度的上限参考
        params["intermediate_results"]["T8_GO_HotIn_K"] = state8_go_in.T


    print("后续需要加入迭代逻辑使state6和state7收敛，并完成ORC侧计算。")
    
    # --- SCBC 最终性能计算 (基于迭代收敛后的值) ---
    W_net_scbc_MW_final = None
    eta_scbc_thermal_final = None
    Q_in_scbc_MW_final = None

    if W_t_total_MW is not None and W_mc_total_MW is not None and W_rc_total_MW is not None:
        W_net_scbc_MW_final = W_t_total_MW - W_mc_total_MW - W_rc_total_MW
        print(f"\nSCBC净输出功 (迭代后): {W_net_scbc_MW_final:.2f} MW")
        if Q_er_calc is not None and Q_er_calc > 0:
            Q_in_scbc_MW_final = Q_er_calc / 1e6
            eta_scbc_thermal_final = W_net_scbc_MW_final / Q_in_scbc_MW_final
            print(f"SCBC吸热器吸热量 Q_ER (迭代后): {Q_in_scbc_MW_final:.2f} MW")
            print(f"SCBC热效率 (迭代后, W_net/Q_ER): {eta_scbc_thermal_final*100:.2f}%")
        else:
            print("SCBC吸热器吸热量为零或未计算 (迭代后)，无法计算SCBC热效率。")
    else:
        print("\n部分SCBC功率未计算 (迭代后)，无法得到SCBC净功和效率。")


    # --- 调用ORC仿真 ---
    W_net_orc_MW = 0  # 初始化ORC净功为0，以防ORC仿真失败或跳过
    if "intermediate_results" in params and params["intermediate_results"].get("Q_GO_to_ORC_J_s"):
        print("\n\n--- 开始ORC独立循环仿真 ---")
        orc_results = simulate_orc_standalone(
            orc_params=params.get("orc_parameters", {}),
            common_params=params,
            intermediate_scbc_data=params["intermediate_results"]
        )
        if orc_results and orc_results.get("W_net_orc_MW") is not None:
            print("\n--- ORC独立循环仿真完成 ---")
            W_net_orc_MW = orc_results.get("W_net_orc_MW", 0)
            print(f"ORC净输出功: {W_net_orc_MW:.2f} MW")
            if orc_results.get("eta_orc_thermal") is not None:
                 print(f"ORC热效率: {orc_results.get('eta_orc_thermal')*100:.2f}%")
        else:
            print("ORC独立循环仿真失败或未返回有效结果。")
    else:
        print("\n由于SCBC到ORC的换热数据不完整，跳过ORC仿真。")

    # --- 联合循环性能计算 ---
    print("\n\n--- 联合循环总性能 ---")
    if W_net_scbc_MW_final is not None:
        W_net_combined_MW = W_net_scbc_MW_final + W_net_orc_MW
        print(f"SCBC净输出功: {W_net_scbc_MW_final:.2f} MW")
        print(f"ORC净输出功: {W_net_orc_MW:.2f} MW")
        print(f"联合循环总净输出功: {W_net_combined_MW:.2f} MW")

        if Q_in_scbc_MW_final is not None and Q_in_scbc_MW_final > 1e-6:
            eta_combined_thermal = W_net_combined_MW / Q_in_scbc_MW_final
            print(f"总输入热量 (SCBC ER): {Q_in_scbc_MW_final:.2f} MW")
            print(f"联合循环总热效率: {eta_combined_thermal*100:.2f}%")
        else:
            print("无法计算联合循环总热效率，因SCBC总输入热量未知或为零。")
    else:
        print("无法计算联合循环总性能，因SCBC净功未知。")
        
    print("\n--- SCBC/ORC联合循环仿真结束 ---")


def simulate_orc_standalone(orc_params, common_params, intermediate_scbc_data):
    """
    模拟独立的ORC循环。
    接收来自SCBC的热量进行蒸发。
    """
    orc_fluid = common_params.get("fluids", {}).get("orc", "Isopentane")
    print(f"ORC工质: {orc_fluid}")

    Q_from_scbc_J_s = intermediate_scbc_data.get("Q_GO_to_ORC_J_s")
    T_scbc_go_hot_in_K = intermediate_scbc_data.get("T8_GO_HotIn_K") # SCBC侧GO进口温度
    T_scbc_go_hot_out_K = intermediate_scbc_data.get("T9_GO_HotOut_K") # SCBC侧GO出口温度
    # P_scbc_go_hot_in_Pa = intermediate_scbc_data.get("P8_GO_HotIn_Pa")
    # m_dot_scbc_go_hot_kg_s = intermediate_scbc_data.get("m_dot_GO_HotSide_kg_s")

    if not Q_from_scbc_J_s or not T_scbc_go_hot_in_K or not T_scbc_go_hot_out_K:
        print("错误: ORC仿真缺少来自SCBC的关键换热数据 (热量或温度)。")
        return None

    print(f"接收来自SCBC的热量 Q_eva_orc: {Q_from_scbc_J_s / 1e6:.2f} MW")
    print(f"SCBC侧GO热源温度范围: {T_scbc_go_hot_in_K - 273.15:.2f}°C (进口) to {T_scbc_go_hot_out_K - 273.15:.2f}°C (出口)")

    # ORC参数提取
    P_cond_kPa_orc = orc_params.get('P_cond_kPa_orc', 100) # 假设值，应从参数文件读取
    # 假设泵进口为冷凝压力下的饱和液体
    # Corrected line 540 from previous diff might be here or slightly offset.
    # The original error was: T_pump_in_C_orc_default = StatePoint(orc_fluid, "_temp").props_from_PQ(to_pascal(P_cond_kPa_orc, 'kpa'), 0).T_C
    # It should have been corrected to something like:
    _temp_sat_liq_for_default = StatePoint(orc_fluid, "_temp_sat_liq_orc_pump_in_default")
    _temp_sat_liq_for_default.props_from_PQ(to_pascal(P_cond_kPa_orc, 'kpa'), 0)
    T_pump_in_C_orc_default_calc = (_temp_sat_liq_for_default.T - 273.15) if _temp_sat_liq_for_default.T is not None else 25.0
    T_pump_in_C_orc = orc_params.get('T_pump_in_C_orc', T_pump_in_C_orc_default_calc)
    
    eta_P_orc = orc_params.get('eta_P_orc', 0.80)
    eta_T_orc = orc_params.get('eta_T_orc', 0.85)
    # 蒸发器出口目标：例如，相对于SCBC热源出口温度的最小接近温差
    approach_temp_eva_K_orc = orc_params.get('approach_temp_eva_K_orc', 5.0) # 5K温差 (热源与ORC工质之间的最小允许温差)
    delta_T_superheat_orc_K = orc_params.get('delta_T_superheat_orc_K', 5.0) # ORC透平进口目标过热度, 5K

    # ORC质量流量的估算/迭代起点 - 这是一个关键参数，可能需要迭代或基于能量平衡反算
    # 简单估算：m_dot_orc * (h_eva_out - h_eva_in) = Q_from_scbc_J_s
    # 假设一个初始值，后续可能需要调整
    m_dot_orc_kg_s_initial_guess = orc_params.get('m_dot_orc_kg_s', 100.0) # kg/s - 需要更合理的初值或迭代方法
    if m_dot_orc_kg_s_initial_guess is None: m_dot_orc_kg_s_initial_guess = 100.0


    print(f"\nORC主要参数:")
    print(f"  冷凝压力 P_cond: {P_cond_kPa_orc} kPa")
    print(f"  泵进口温度 T_pump_in: {T_pump_in_C_orc:.2f} °C")
    print(f"  泵效率 η_P_orc: {eta_P_orc}")
    print(f"  透平效率 η_T_orc: {eta_T_orc}")
    print(f"  蒸发器出口目标过热度: {delta_T_superheat_orc_K} K")
    print(f"  蒸发器与热源最小接近温差: {approach_temp_eva_K_orc} K")
    print(f"  ORC初始估算流量: {m_dot_orc_kg_s_initial_guess} kg/s (待优化)")

    # --- ORC循环状态点计算 ---
    orc_states = {}

    # 点o1: 泵进口 (冷凝器出口)
    state_o1_pump_in = StatePoint(orc_fluid, "P_o1_PumpIn")
    P_o1_Pa = to_pascal(P_cond_kPa_orc, 'kpa')
    T_o1_K_param = to_kelvin(T_pump_in_C_orc) # 参数文件中设定的温度，作为参考

    # 直接将泵进口设置为在冷凝压力下的饱和液体状态
    print(f"信息: 将ORC泵进口 (点o1) 设置为在压力 {P_cond_kPa_orc} kPa 下的饱和液体状态 (Q=0)。")
    state_o1_pump_in.props_from_PQ(P_o1_Pa, 0) # 使用P和Q=0定义饱和液体
    
    # 获取并打印计算得到的饱和温度，与参数文件中的设定值对比
    if state_o1_pump_in.T is not None:
        T_o1_K_saturated = state_o1_pump_in.T
        print(f"  计算得到的该压力下饱和温度为: {T_o1_K_saturated - 273.15:.2f} °C (参数中T_pump_in_C_orc参考值: {T_pump_in_C_orc:.2f} °C)")
        if abs(T_o1_K_saturated - T_o1_K_param) > 0.1: # 如果差异大于0.1K
             print(f"  注意: 参数文件中的泵进口温度 {T_pump_in_C_orc:.2f}°C 与计算得到的饱和温度 {T_o1_K_saturated - 273.15:.2f}°C 不完全一致。脚本将使用饱和液体状态。")
    
    state_o1_pump_in.m_dot = m_dot_orc_kg_s_initial_guess # 假设的ORC流量

    if not state_o1_pump_in.h:
        print("错误: 初始化ORC点o1 (泵进口) 失败。ORC仿真终止。")
        return None
    orc_states["P_o1_PumpIn"] = state_o1_pump_in
    print("\nORC状态点o1 (泵进口):")
    print(state_o1_pump_in)

    # --- ORC泵 (P_ORC) ---
    # 泵出口压力 P_o2 = 蒸发压力。这个压力是未知的，取决于蒸发过程。
    # 这是一个难点：蒸发压力和ORC流量需要同时确定，以满足蒸发器能量平衡和温差约束。
    # 简化：假设一个蒸发压力，或者基于SCBC侧压力和温差进行估算。
    # 论文中ORC蒸发压力约为 2000-3000 kPa (R245fa)
    # 假设蒸发压力 P_eva_orc_kPa，这个值也应该来自参数或优化
    P_eva_orc_kPa_assumed = orc_params.get('P_eva_kPa_orc', 2500) # 假设值
    P_o2_pump_out_Pa = to_pascal(P_eva_orc_kPa_assumed, 'kpa')
    
    state_o2_pump_out, W_p_orc_J_kg = model_pump_ORC(state_o1_pump_in, P_o2_pump_out_Pa, eta_P_orc)
    if not state_o2_pump_out:
        print("错误: ORC泵计算失败。ORC仿真终止。")
        return None
    orc_states["P_o2_PumpOut_EvaIn"] = state_o2_pump_out
    
    W_p_orc_total_MW = (W_p_orc_J_kg * state_o1_pump_in.m_dot) / 1e6 if state_o1_pump_in.m_dot else None
    print("\n计算得到ORC泵出口状态 (点o2 - 蒸发器进口):")
    print(state_o2_pump_out)
    if W_p_orc_total_MW is not None:
        print(f"ORC泵耗功: {W_p_orc_J_kg/1000:.2f} kJ/kg, 总功率: {W_p_orc_total_MW:.3f} MW")

    # --- ORC蒸发器 (GO - ORC侧) ---
    # 热源: SCBC (T_scbc_go_hot_in_K, T_scbc_go_hot_out_K)
    # 冷流: ORC (state_o2_pump_out -> state_o3_eva_out)
    # 目标: ORC工质在出口达到 T_o3_target_K
    # T_o3_target_K 可以是 T_scbc_go_hot_out_K - approach_temp_eva_K_orc (如果SCBC出口温度是最低点)
    # 或者 T_scbc_go_hot_in_K - approach_temp_eva_K_orc (如果SCBC进口温度是ORC能达到的最高点附近)
    
    # 计算当前蒸发压力下的饱和温度
    _temp_sat_eva = StatePoint(orc_fluid, "_temp_sat_eva_orc")
    _temp_sat_eva.props_from_PQ(P_o2_pump_out_Pa, 1.0) # Q=1 for saturated vapor temp
    T_sat_orc_eva_K = _temp_sat_eva.T

    if T_sat_orc_eva_K is None:
        print(f"错误: 无法获取ORC在蒸发压力 {P_eva_orc_kPa_assumed} kPa下的饱和温度。ORC仿真终止。")
        return None

    # 目标1: 基于过热度的目标出口温度
    T_o3_target_superheated_K = T_sat_orc_eva_K + delta_T_superheat_orc_K
    
    # 目标2: 基于热源温度和最小接近温差的上限温度
    T_o3_limit_from_source_K = T_scbc_go_hot_in_K - approach_temp_eva_K_orc
    
    # 最终目标出口温度是两者中较小的一个，但必须确保至少是过热的
    T_o3_final_target_K = min(T_o3_target_superheated_K, T_o3_limit_from_source_K)

    if T_o3_final_target_K <= T_sat_orc_eva_K:
        print(f"警告: 计算得到的ORC蒸发器最终目标出口温度 {T_o3_final_target_K-273.15:.2f}°C 不高于或仅等于饱和温度 {T_sat_orc_eva_K-273.15:.2f}°C。")
        print(f"  这可能意味着蒸发压力过高，或热源温度不足，或接近温差/过热度设定不合理。")
        print(f"  将尝试以目标过热温度 {T_o3_target_superheated_K-273.15:.2f}°C 进行，但这可能不满足热源温差约束。")
        # 如果严格要求，这里可以调整 T_o3_final_target_K，或者报错。
        # 为简单起见，如果目标过热温度本身就超过了热源限制，那么之前的min已经处理了。
        # 如果是 T_o3_target_superheated_K <= T_sat_orc_eva_K (例如delta_T_superheat_orc_K <=0)，则需要修正。
        if T_o3_target_superheated_K <= T_sat_orc_eva_K : # 确保目标至少是饱和温度以上一点点
            T_o3_final_target_K = T_sat_orc_eva_K + 0.1 # 略高于饱和，避免数值问题
            print(f"  修正ORC蒸发器出口目标温度为微过热: {T_o3_final_target_K-273.15:.2f}°C")


    print(f"\n--- ORC蒸发器 (GO) 计算 ---")
    print(f"  ORC蒸发压力 (假设): {P_eva_orc_kPa_assumed} kPa (饱和温度: {T_sat_orc_eva_K-273.15:.2f}°C)")
    print(f"  ORC侧进口: 点o2 (来自泵出口)")
    print(f"  SCBC热源进口温度 (参考): {T_scbc_go_hot_in_K-273.15:.2f}°C")
    print(f"  SCBC热源出口温度 (参考): {T_scbc_go_hot_out_K-273.15:.2f}°C")
    print(f"  ORC侧最终目标出口温度 (考虑过热和热源限制): {T_o3_final_target_K-273.15:.2f}°C")
    
    # 使用 model_heater_set_T_out 模拟蒸发器，热量来自外部 Q_from_scbc_J_s
    # 但 model_heater_set_T_out 是设定出口温度，然后计算需要多少热量。
    # 我们是已知热量，需要计算出口温度和是否能达到。
    # 或者，使用 model_evaporator_GO，它需要知道热源的流量和进出口状态。
    # 这里需要一个迭代过程来匹配ORC流量和出口状态，使得吸收的热量等于Q_from_scbc_J_s
    # 并且满足温差约束 (目标是过热蒸汽)。

    # 重新计算 T_o3_final_target_K 以确保它是过热的
    if T_sat_orc_eva_K is not None:
        T_target_superheated_K = T_sat_orc_eva_K + delta_T_superheat_orc_K
        T_limit_from_source_K = T_scbc_go_hot_in_K - approach_temp_eva_K_orc
        
        T_o3_final_target_K = min(T_target_superheated_K, T_limit_from_source_K)
        
        # 确保最终目标至少比饱和温度高一点点，以实现过热
        if T_o3_final_target_K < T_sat_orc_eva_K + 0.1: # 如果目标不是明显的过热
            T_o3_final_target_K = T_sat_orc_eva_K + delta_T_superheat_orc_K # 优先保证过热度
            if T_o3_final_target_K >= T_scbc_go_hot_in_K - approach_temp_eva_K_orc: # 如果过热目标违反了热源温差
                 # 这种情况比较棘手，意味着在当前蒸发压力下，可能无法同时满足过热度和与热源的最小温差
                 # 可以选择牺牲部分过热度，或者提示参数不合理
                 T_o3_final_target_K = T_scbc_go_hot_in_K - approach_temp_eva_K_orc # 优先满足热源温差
                 print(f"警告: ORC目标过热度可能无法在满足热源最小温差 {approach_temp_eva_K_orc}K 的情况下完全实现。")
                 print(f"  蒸发压力: {P_eva_orc_kPa_assumed} kPa (Tsat={T_sat_orc_eva_K-273.15:.2f}°C)")
                 print(f"  SCBC热源进口T: {T_scbc_go_hot_in_K-273.15:.2f}°C. ORC出口目标T被限制为: {T_o3_final_target_K-273.15:.2f}°C")
                 if T_o3_final_target_K <= T_sat_orc_eva_K: # 如果限制后的温度还是不够高
                     print(f"错误: ORC出口目标温度 {T_o3_final_target_K-273.15:.2f}°C 不高于饱和温度 {T_sat_orc_eva_K-273.15:.2f}°C。请检查参数。")
                     # return None # 或者设置一个略高于饱和的温度继续尝试
                     T_o3_final_target_K = T_sat_orc_eva_K + 0.1 # 强制微小过热
    else: # T_sat_orc_eva_K is None, should not happen if P_eva is valid
        print("错误: 无法确定ORC蒸发饱和温度，无法设定准确的过热目标。")
        return None

    print(f"  修正后的ORC蒸发器最终目标出口温度: {T_o3_final_target_K-273.15:.2f}°C")

    # 迭代调整ORC质量流量 m_dot_orc，以满足蒸发器出口温度约束
    m_dot_orc_current_kg_s = m_dot_orc_kg_s_initial_guess
    max_iter_orc_mdot = orc_params.get("max_iter_orc_mdot", 20)
    tol_orc_T_approach = orc_params.get("tol_orc_T_approach_K", 0.5) # 0.5 K 容差
    m_dot_adj_factor_high = 1.05 # 流量调整因子（当温度过高时增加流量）
    m_dot_adj_factor_low = 0.95  # 流量调整因子（当温度过低时减少流量）
    m_dot_min_kg_s = orc_params.get("m_dot_orc_min_kg_s", 1.0)
    m_dot_max_kg_s = orc_params.get("m_dot_orc_max_kg_s", 1000.0)

    state_o3_eva_out = None
    converged_orc_mdot = False

    print(f"  开始迭代调整ORC流量以匹配蒸发器出口温度目标 {T_o3_final_target_K-273.15:.2f}°C...")

    for i_mdot_orc in range(max_iter_orc_mdot):
        if state_o2_pump_out.h is None:
            print("错误: ORC泵出口焓值未知，无法进行蒸发器迭代。")
            return None
        
        h_o3_calc_J_kg = state_o2_pump_out.h + Q_from_scbc_J_s / m_dot_orc_current_kg_s
        
        _temp_state_o3 = StatePoint(orc_fluid, f"P_o3_Iter{i_mdot_orc+1}")
        _temp_state_o3.props_from_PH(state_o2_pump_out.P, h_o3_calc_J_kg) # 假设蒸发器等压
        _temp_state_o3.m_dot = m_dot_orc_current_kg_s

        if not _temp_state_o3.h or not _temp_state_o3.T:
            print(f"警告: ORC蒸发器出口状态在迭代 {i_mdot_orc+1} (m_dot={m_dot_orc_current_kg_s:.2f} kg/s) 时计算失败。尝试调整流量。")
            m_dot_orc_current_kg_s *= (m_dot_adj_factor_high if m_dot_orc_current_kg_s < (m_dot_min_kg_s + m_dot_max_kg_s)/2 else m_dot_adj_factor_low)
            m_dot_orc_current_kg_s = max(m_dot_min_kg_s, min(m_dot_max_kg_s, m_dot_orc_current_kg_s))
            continue

        T_o3_current_K = _temp_state_o3.T
        error_T_K = T_o3_current_K - T_o3_final_target_K # 使用新的最终目标温度
        
        # 检查是否过热或超临界
        # 对于R245fa在2.5MPa，临界温度约154°C。目标温度13x°C，应为亚临界。
        # 所以主要判断是否过热 (q is None or q >= 1.0 and T > T_sat)
        is_proper_outlet_state = False
        if _temp_state_o3.q is None or _temp_state_o3.q < 0: # CoolProp对单相区（过热/超临界/过冷）返回 < 0 的干度值 (通常是-1)
            # 进一步确认是否真的是过热 (温度高于饱和温度)
            if T_sat_orc_eva_K is not None and T_o3_current_K > T_sat_orc_eva_K + 1e-2: # 确保是过热，而不是恰好在饱和点或过冷
                 is_proper_outlet_state = True
            elif T_sat_orc_eva_K is None and _temp_state_o3.q is None: # 超临界流体，没有饱和温度
                 is_proper_outlet_state = True
        elif _temp_state_o3.q >= 1.0: # 饱和干蒸汽 (Q=1)
             if T_sat_orc_eva_K is not None and abs(T_o3_current_K - T_sat_orc_eva_K) < 0.1: # 温度应接近饱和温度
                # 如果目标是饱和干蒸汽，这也是可接受的
                # 但我们的目标通常是过热，所以这个分支可能较少触发为True
                # 如果delta_T_superheat_orc_K为0，则此分支可能为True
                if delta_T_superheat_orc_K < 0.1: # 如果目标就是饱和干蒸汽
                    is_proper_outlet_state = True
        
        q_display_orc = f"{_temp_state_o3.q:.4f}" if _temp_state_o3.q is not None else 'N/A'
        print(f"  Iter {i_mdot_orc+1}/{max_iter_orc_mdot}: m_dot={m_dot_orc_current_kg_s:.2f} kg/s, T_o3={T_o3_current_K-273.15:.2f}°C, Target T_o3={T_o3_final_target_K-273.15:.2f}°C, Err={error_T_K:.2f}K, Q={q_display_orc}, ProperState={is_proper_outlet_state}")

        if abs(error_T_K) < tol_orc_T_approach and is_proper_outlet_state:
            state_o3_eva_out = _temp_state_o3
            converged_orc_mdot = True
            print(f"  ORC流量迭代收敛于 m_dot={m_dot_orc_current_kg_s:.2f} kg/s, T_o3={(state_o3_eva_out.T - 273.15):.2f}°C.")
            break
        
        if error_T_K > 0:
            m_dot_orc_current_kg_s *= m_dot_adj_factor_high
        else:
            m_dot_orc_current_kg_s *= m_dot_adj_factor_low
        
        m_dot_orc_current_kg_s = max(m_dot_min_kg_s, min(m_dot_max_kg_s, m_dot_orc_current_kg_s))
        state_o3_eva_out = _temp_state_o3

    if not converged_orc_mdot:
        print(f"警告: ORC流量迭代在 {max_iter_orc_mdot} 次后未收敛。使用最后计算的状态。")
        if state_o3_eva_out is None or not state_o3_eva_out.h :
             print(f"错误: ORC蒸发器出口在多次迭代后仍无法计算。仿真终止。")
             return None
        q_display_final = state_o3_eva_out.q if hasattr(state_o3_eva_out, 'q') and state_o3_eva_out.q is not None else 'N/A'
        print(f"  最终使用: m_dot={state_o3_eva_out.m_dot:.2f} kg/s, T_o3={(state_o3_eva_out.T - 273.15):.2f}°C, Q={q_display_final}")

    if not state_o3_eva_out.h:
        print("错误: ORC蒸发器出口状态在迭代后无效。ORC仿真终止。")
        return None

    # 更新泵进口、泵出口和蒸发器进口的流量为迭代后的值
    state_o1_pump_in.m_dot = state_o3_eva_out.m_dot
    # 重新计算泵出口状态和功，因为流量和可能的进口状态（如果迭代中调整了o1）已改变
    # 假设state_o1_pump_in的热力学状态不变，仅流量改变
    _temp_pump_in_for_recalc = StatePoint(orc_fluid, "_temp_pump_in_recalc")
    _temp_pump_in_for_recalc.props_from_PH(state_o1_pump_in.P, state_o1_pump_in.h) # 使用原P,h
    _temp_pump_in_for_recalc.m_dot = state_o3_eva_out.m_dot # 新流量

    state_o2_pump_out, W_p_orc_J_kg = model_pump_ORC(_temp_pump_in_for_recalc, P_o2_pump_out_Pa, eta_P_orc)
    if not state_o2_pump_out:
        print("错误: ORC泵在流量更新后重新计算失败。ORC仿真终止。")
        return None
    # state_o2_pump_out 的流量已经是正确的了，因为它从 _temp_pump_in_for_recalc 继承

    W_p_orc_total_MW = (W_p_orc_J_kg * state_o2_pump_out.m_dot) / 1e6 if state_o2_pump_out.m_dot else None
    print("\nORC泵出口状态 (点o2 - 流量更新后):")
    print(state_o2_pump_out)
    if W_p_orc_total_MW is not None:
        print(f"ORC泵耗功 (流量更新后): {W_p_orc_J_kg/1000:.2f} kJ/kg, 总功率: {W_p_orc_total_MW:.3f} MW")
    orc_states["P_o1_PumpIn"] = _temp_pump_in_for_recalc # 更新字典中的泵进口状态（主要是流量）
    orc_states["P_o2_PumpOut_EvaIn"] = state_o2_pump_out # 更新字典中的泵出口状态

    if state_o3_eva_out.T > (T_scbc_go_hot_in_K - approach_temp_eva_K_orc + tol_orc_T_approach):
        print(f"最终警告: ORC蒸发器出口温度 {(state_o3_eva_out.T - 273.15):.2f}°C 仍然过高。")
        print(f"  目标上限: {(T_scbc_go_hot_in_K - approach_temp_eva_K_orc)-273.15:.2f}°C。")

    if hasattr(state_o3_eva_out, 'q') and state_o3_eva_out.q is not None and state_o3_eva_out.q < 1.0: # Check attribute exists
         print(f"最终警告: ORC蒸发器出口为两相流 (Q={state_o3_eva_out.q:.3f})，T={(state_o3_eva_out.T - 273.15):.2f}°C。透平进口通常需要过热蒸汽。")
    
    orc_states["P_o3_EvaOut_TurbineIn"] = state_o3_eva_out
    print("\n计算得到的ORC蒸发器出口状态 (点o3 - 透平进口, 流量迭代后):")
    print(state_o3_eva_out)
    
    # 确保 state_o2_pump_out.h 是有效的，然后再计算 Q_eva_orc_calc_MW
    if state_o2_pump_out.h and state_o3_eva_out.h and state_o3_eva_out.m_dot:
        Q_eva_orc_calc_MW = (state_o3_eva_out.h - state_o2_pump_out.h) * state_o3_eva_out.m_dot / 1e6
        print(f"ORC蒸发器实际吸热量 (流量迭代后): {Q_eva_orc_calc_MW:.2f} MW (应等于来自SCBC的 {Q_from_scbc_J_s/1e6:.2f} MW)")
        if abs(Q_eva_orc_calc_MW - Q_from_scbc_J_s/1e6) > 0.01 * (Q_from_scbc_J_s/1e6): # 1% 差异
            print(f"警告: ORC蒸发器吸收热量与SCBC提供热量差异较大。这可能由于流量迭代未完全精确或焓差计算问题。")
    else:
        print("错误: 无法计算ORC蒸发器吸热量，因泵出口或蒸发器出口焓值无效。")
        Q_eva_orc_calc_MW = 0


    # --- ORC透平 (T_ORC) ---
    # 进口: state_o3_eva_out
    # 出口压力: P_cond_kPa_orc (P_o1_Pa)
    state_o4_turbine_out, W_t_orc_J_kg = model_turbine_T(state_o3_eva_out, P_o1_Pa, eta_T_orc)
    if not state_o4_turbine_out:
        print("错误: ORC透平计算失败。ORC仿真终止。")
        return None
    orc_states["P_o4_TurbineOut_CondIn"] = state_o4_turbine_out

    W_t_orc_total_MW = (W_t_orc_J_kg * state_o3_eva_out.m_dot) / 1e6 if state_o3_eva_out.m_dot else None
    print("\n计算得到的ORC透平出口状态 (点o4 - 冷凝器进口):")
    print(state_o4_turbine_out)
    if W_t_orc_total_MW is not None:
        print(f"ORC透平做功: {W_t_orc_J_kg/1000:.2f} kJ/kg, 总功率: {W_t_orc_total_MW:.2f} MW")

    # --- ORC冷凝器 (COND_ORC) ---
    # 进口: state_o4_turbine_out
    # 出口目标: 与泵进口 state_o1_pump_in 状态一致 (P, T, h)
    # 使用 model_cooler_set_T_out 来模拟，出口温度为 T_o1_K
    state_o1_cond_out_calc, Q_cond_orc_J_s = model_cooler_set_T_out(
        state_in=state_o4_turbine_out,
        T_out_K=state_o1_pump_in.T, # 目标是泵进口温度
        # 压力也应与泵进口压力一致，model_cooler_set_T_out 通常假设等压过程，
        # 但如果 T_out_K 导致饱和状态，则压力由饱和性质决定。
        # 这里需要确保冷凝器出口压力与 P_o1_Pa 一致。
        # model_cooler_set_T_out 内部会处理，如果 T_out_K 在给定 P_in 下是饱和温度，则出口是饱和液。
        # 如果 T_out_K 是过冷温度，则出口是过冷液。
        name_suffix="COND_ORC",
        target_state_is_saturated_liquid=True # 明确指出目标是饱和液体
    )

    if not state_o1_cond_out_calc:
        print("错误: ORC冷凝器计算失败。ORC仿真终止。")
        return None
    
    # 强制冷凝器出口压力与泵进口一致 (P_o1_Pa)
    # 并重新计算基于 (P_o1_Pa, T_o1_K) 的状态，以确保闭合
    _final_o1 = StatePoint(orc_fluid, "P_o1_CondOut_Final")
    _final_o1.props_from_PQ(P_o1_Pa, 0) # 使用P和Q=0定义饱和液体，确保与泵进口状态一致
    _final_o1.m_dot = state_o4_turbine_out.m_dot
    
    # Q_cond_orc_J_s 应该基于 _final_o1 和 state_o4_turbine_out 的焓差重新计算
    if _final_o1.h and state_o4_turbine_out.h and _final_o1.m_dot:
        Q_cond_orc_J_s_recalc = (_final_o1.h - state_o4_turbine_out.h) * _final_o1.m_dot
    else:
        Q_cond_orc_J_s_recalc = None

    orc_states["P_o1_CondOut_Calc"] = _final_o1 # 使用修正后的点
    
    print("\n计算得到的ORC冷凝器出口状态 (应接近初始点o1):")
    print(_final_o1)
    if Q_cond_orc_J_s_recalc is not None:
        print(f"ORC冷凝器放出热量 Q_COND_ORC: {abs(Q_cond_orc_J_s_recalc) / 1e6:.2f} MW")

    # ORC 性能计算
    W_net_orc_MW = None
    eta_orc_thermal = None
    if W_t_orc_total_MW is not None and W_p_orc_total_MW is not None:
        W_net_orc_MW = W_t_orc_total_MW - W_p_orc_total_MW
        print(f"\nORC净输出功: {W_net_orc_MW:.2f} MW")
        
        Q_in_orc_MW = Q_from_scbc_J_s / 1e6 # 这是ORC的吸热量
        if Q_in_orc_MW > 1e-6: # 避免除零
            eta_orc_thermal = W_net_orc_MW / Q_in_orc_MW
            print(f"ORC吸热量 (来自SCBC): {Q_in_orc_MW:.2f} MW")
            print(f"ORC热效率 (W_net_orc / Q_in_orc): {eta_orc_thermal*100:.2f}%")
        else:
            print("ORC吸热量为零，无法计算热效率。")

    print("\n--- ORC独立循环初步计算完成 ---")
    print("注意: ORC流量和蒸发压力为假设值，实际需要迭代优化以满足能量平衡和温差约束。")
    
    return {
        "orc_states": orc_states,
        "W_net_orc_MW": W_net_orc_MW,
        "eta_orc_thermal": eta_orc_thermal,
        "Q_cond_orc_MW": abs(Q_cond_orc_J_s_recalc / 1e6) if Q_cond_orc_J_s_recalc else None
    }


if __name__ == '__main__':
    cycle_params = load_cycle_parameters()
    if cycle_params:
        simulate_scbc_orc_cycle(cycle_params)