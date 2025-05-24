# cycle_components.py

from state_point_calculator import StatePoint # 假设 'state_point_calculator.py' 在同一目录或Python路径中
# 如果 StatePoint 类依赖全局的 T0_K, P0_PA 进行㶲计算，
# 确保 '状态点计算.py' 中的这些值是您希望使用的。

def model_compressor_MC(state_in: StatePoint, P_out_Pa: float, eta_isen: float):
    """
    模拟主压缩机 (MC) 的性能。

    参数:
        state_in (StatePoint): 压缩机进口状态。
        P_out_Pa (float): 压缩机出口压力 (Pa)。
        eta_isen (float): 压缩机的等熵效率 (0 到 1 之间)。

    返回:
        tuple: (state_out_actual, W_consumed_J_kg)
            state_out_actual (StatePoint): 实际出口状态。
            W_consumed_J_kg (float): 单位质量工质消耗的功 (J/kg)，正值。
    """
    if not (0 < eta_isen <= 1):
        raise ValueError("等熵效率必须在 (0, 1] 范围内。")

    fluid = state_in.fluid
    name_out = state_in.name.replace("入口", "出口") if state_in.name else "压缩机出口" # 尝试生成一个有意义的出口名称

    # 1. 理想压缩（等熵过程）
    # 创建一个临时状态点用于计算理想出口
    ideal_state_out = StatePoint(fluid_name=fluid, name=f"{name_out}_ideal")
    ideal_state_out.props_from_PS(P_out_Pa, state_in.s) # s_in = s_out_ideal

    if ideal_state_out.h is None or state_in.h is None:
        print(f"错误: 无法计算压缩机 {state_in.name} 的理想或实际焓。")
        return None, None

    h_out_ideal_J_kg = ideal_state_out.h

    # 2. 实际出口焓
    # W_isen = h_out_ideal - h_in
    # W_actual = W_isen / eta_isen
    # h_out_actual = h_in + W_actual
    h_in_J_kg = state_in.h
    h_out_actual_J_kg = h_in_J_kg + (h_out_ideal_J_kg - h_in_J_kg) / eta_isen

    # 3. 实际出口状态
    state_out_actual = StatePoint(fluid_name=fluid, name=name_out)
    state_out_actual.props_from_PH(P_out_Pa, h_out_actual_J_kg)
    state_out_actual.m_dot = state_in.m_dot # 传递质量流量

    if state_out_actual.h is None:
        print(f"错误: 无法计算压缩机 {state_in.name} 的实际出口状态。")
        return None, None
        
    W_consumed_J_kg = h_out_actual_J_kg - h_in_J_kg

    return state_out_actual, W_consumed_J_kg


def model_turbine_T(state_in: StatePoint, P_out_Pa: float, eta_isen: float):
    """
    模拟SCBC透平 (T) 的性能。

    参数:
        state_in (StatePoint): 透平进口状态。
        P_out_Pa (float): 透平出口压力 (Pa)。
        eta_isen (float): 透平的等熵效率 (0 到 1 之间)。

    返回:
        tuple: (state_out_actual, W_produced_J_kg)
            state_out_actual (StatePoint): 实际出口状态。
            W_produced_J_kg (float): 单位质量工质产生的功 (J/kg)，正值。
    """
    if not (0 < eta_isen <= 1):
        raise ValueError("等熵效率必须在 (0, 1] 范围内。")

    fluid = state_in.fluid
    name_out = state_in.name.replace("入口", "出口") if state_in.name else "透平出口"

    # 1. 理想膨胀（等熵过程）
    ideal_state_out = StatePoint(fluid_name=fluid, name=f"{name_out}_ideal")
    ideal_state_out.props_from_PS(P_out_Pa, state_in.s) # s_in = s_out_ideal

    if ideal_state_out.h is None or state_in.h is None:
        print(f"错误: 无法计算透平 {state_in.name} 的理想或实际焓。")
        return None, None

    h_out_ideal_J_kg = ideal_state_out.h
    h_in_J_kg = state_in.h

    # 2. 实际出口焓
    # W_isen_produced = h_in - h_out_ideal
    # W_actual_produced = W_isen_produced * eta_isen
    # h_out_actual = h_in - W_actual_produced
    h_out_actual_J_kg = h_in_J_kg - (h_in_J_kg - h_out_ideal_J_kg) * eta_isen

    # 3. 实际出口状态
    state_out_actual = StatePoint(fluid_name=fluid, name=name_out)
    state_out_actual.props_from_PH(P_out_Pa, h_out_actual_J_kg)
    state_out_actual.m_dot = state_in.m_dot # 传递质量流量
    
    if state_out_actual.h is None:
        print(f"错误: 无法计算透平 {state_in.name} 的实际出口状态。")
        return None, None

    W_produced_J_kg = h_in_J_kg - h_out_actual_J_kg

    return state_out_actual, W_produced_J_kg


def model_pump_ORC(state_in: StatePoint, P_out_Pa: float, eta_isen: float):
    """
    模拟ORC泵 (PO) 的性能。

    参数:
        state_in (StatePoint): 泵进口状态。
        P_out_Pa (float): 泵出口压力 (Pa)。
        eta_isen (float): 泵的等熵效率 (0 到 1 之间)。

    返回:
        tuple: (state_out_actual, W_consumed_J_kg)
            state_out_actual (StatePoint): 实际出口状态。
            W_consumed_J_kg (float): 单位质量工质消耗的功 (J/kg)，正值。
    """
    if not (0 < eta_isen <= 1):
        raise ValueError("等熵效率必须在 (0, 1] 范围内。")

    fluid = state_in.fluid
    name_out = state_in.name.replace("入口", "出口") if state_in.name else "泵出口"

    # 1. 理想加压（等熵过程）
    ideal_state_out = StatePoint(fluid_name=fluid, name=f"{name_out}_ideal")
    ideal_state_out.props_from_PS(P_out_Pa, state_in.s)

    if ideal_state_out.h is None or state_in.h is None:
        print(f"错误: 无法计算泵 {state_in.name} 的理想或实际焓。")
        return None, None

    h_out_ideal_J_kg = ideal_state_out.h
    h_in_J_kg = state_in.h

    # 2. 实际出口焓
    h_out_actual_J_kg = h_in_J_kg + (h_out_ideal_J_kg - h_in_J_kg) / eta_isen

    # 3. 实际出口状态
    state_out_actual = StatePoint(fluid_name=fluid, name=name_out)
    state_out_actual.props_from_PH(P_out_Pa, h_out_actual_J_kg)
    state_out_actual.m_dot = state_in.m_dot # 传递质量流量
    
    if state_out_actual.h is None:
        print(f"错误: 无法计算泵 {state_in.name} 的实际出口状态。")
        return None, None

    W_consumed_J_kg = h_out_actual_J_kg - h_in_J_kg

    return state_out_actual, W_consumed_J_kg


def model_heat_exchanger_effectiveness(
    state_hot_in: StatePoint,
    state_cold_in: StatePoint,
    effectiveness: float,
    hot_fluid_is_C_min_side: bool, # True if hot fluid side determines Q_actual via effectiveness, False if cold fluid side
    pressure_drop_hot_Pa: float = 0.0,
    pressure_drop_cold_Pa: float = 0.0,
    name_suffix: str = ""
):
    """
    模拟基于效能定义的换热器（如回热器）。
    假设等质量流量或质量流量已在StatePoint对象中设置。
    如果 hot_fluid_is_C_min_side is True, T_hot_out is calculated based on effectiveness.
    If hot_fluid_is_C_min_side is False, T_cold_out is calculated based on effectiveness.
    然后另一侧的出口通过能量平衡确定。

    参数:
        state_hot_in: 热流体进口状态。
        state_cold_in: 冷流体进口状态。
        effectiveness: 换热器效能 (0 到 1)。
        hot_fluid_is_C_min_side: 布尔值，指示效能定义是基于热侧还是冷侧的温差潜力。
                                  对于HTR/LTR的eta_H/eta_L定义，通常是基于C_min侧。
                                  根据验算，对HTR，设为True (热侧温度变化由eff决定)可以匹配论文。
        pressure_drop_hot_Pa: 热流体侧压降 (Pa)。
        pressure_drop_cold_Pa: 冷流体侧压降 (Pa)。
        name_suffix: 用于命名出口状态点的后缀。

    返回:
        tuple: (state_hot_out, state_cold_out, Q_exchanged_J)
            state_hot_out: 热流体出口状态。
            state_cold_out: 冷流体出口状态。
            Q_exchanged_J: 交换的总热量 (J)，从热流体到冷流体为正。
    """
    if not (0 <= effectiveness <= 1):
        raise ValueError("换热器效能必须在 [0, 1] 范围内。")

    # 获取进口参数
    T_hot_in_K = state_hot_in.T
    h_hot_in_J_kg = state_hot_in.h
    P_hot_in_Pa = state_hot_in.P
    m_dot_hot = state_hot_in.m_dot
    fluid_hot = state_hot_in.fluid

    T_cold_in_K = state_cold_in.T
    h_cold_in_J_kg = state_cold_in.h
    P_cold_in_Pa = state_cold_in.P
    m_dot_cold = state_cold_in.m_dot
    fluid_cold = state_cold_in.fluid

    if m_dot_hot is None or m_dot_cold is None:
        # 对于HTR/LTR, m_dot_hot == m_dot_cold. 如果一个未知，另一个也未知。
        # 如果后续需要支持不同流量，这里需要调整。目前假设调用者已设置。
        print(f"警告: 换热器 {name_suffix} 的热侧或冷侧质量流量未设置。")
        # 尝试从另一个流获取，假设它们相等 (适用于HTR/LTR)
        if m_dot_hot is None and m_dot_cold is not None: m_dot_hot = m_dot_cold
        elif m_dot_cold is None and m_dot_hot is not None: m_dot_cold = m_dot_hot
        else: # 两者都未知，无法计算总换热量，但可以计算单位质量焓变
            print(f"错误: 换热器 {name_suffix} 两侧质量流量均未知。无法计算总换热量。")
            # 或者可以假设单位质量流量进行计算，但Q_exchanged_J会是单位质量的
            return None, None, None


    # 计算出口压力
    P_hot_out_Pa = P_hot_in_Pa - pressure_drop_hot_Pa
    P_cold_out_Pa = P_cold_in_Pa - pressure_drop_cold_Pa

    Q_exchanged_J = 0
    state_hot_out = StatePoint(fluid_hot, name=f"{state_hot_in.name}_out_{name_suffix}")
    state_cold_out = StatePoint(fluid_cold, name=f"{state_cold_in.name}_out_{name_suffix}")
    state_hot_out.m_dot = m_dot_hot
    state_cold_out.m_dot = m_dot_cold

    if hot_fluid_is_C_min_side: # 假设效能定义是针对热流体温度变化
        # T_hot_out = T_hot_in - effectiveness * (T_hot_in - T_cold_in)
        T_hot_out_K = T_hot_in_K - effectiveness * (T_hot_in_K - T_cold_in_K)
        state_hot_out.props_from_PT(P_hot_out_Pa, T_hot_out_K)
        if state_hot_out.h is None: return None, None, None
        h_hot_out_J_kg = state_hot_out.h
        
        Q_exchanged_J = m_dot_hot * (h_hot_in_J_kg - h_hot_out_J_kg)
        
        h_cold_out_J_kg = h_cold_in_J_kg + Q_exchanged_J / m_dot_cold
        state_cold_out.props_from_PH(P_cold_out_Pa, h_cold_out_J_kg)
        if state_cold_out.h is None: return None, None, None
    else: # 假设效能定义是针对冷流体温度变化
        # T_cold_out = T_cold_in + effectiveness * (T_hot_in - T_cold_in)
        T_cold_out_K = T_cold_in_K + effectiveness * (T_hot_in_K - T_cold_in_K)
        state_cold_out.props_from_PT(P_cold_out_Pa, T_cold_out_K)
        if state_cold_out.h is None: return None, None, None
        h_cold_out_J_kg = state_cold_out.h

        Q_exchanged_J = m_dot_cold * (h_cold_out_J_kg - h_cold_in_J_kg)

        h_hot_out_J_kg = h_hot_in_J_kg - Q_exchanged_J / m_dot_hot
        state_hot_out.props_from_PH(P_hot_out_Pa, h_hot_out_J_kg)
        if state_hot_out.h is None: return None, None, None
        
    return state_hot_out, state_cold_out, Q_exchanged_J

if __name__ == '__main__':
    # --- 测试 model_compressor_MC ---
    # (此部分测试代码保持不变)
    print("--- 测试主压缩机 (MC) 模型 ---")
    from state_point_calculator import to_kelvin, to_pascal

    P1_Pa_test_mc = to_pascal(7400.00, 'kpa') # Renamed for clarity
    T1_K_test_mc = to_kelvin(35.00)    # Renamed for clarity
    m_dot1_mc = 1945.09 # kg/s, from Table 10, point 1 for SCBC/ORC
    eta_mc_test = 0.85
    P2_Pa_test_mc = to_pascal(24198.00, 'kpa') # Renamed for clarity

    state1_test_mc = StatePoint(fluid_name="CO2", name="测试用SCBC点1_MC")
    state1_test_mc.props_from_PT(P1_Pa_test_mc, T1_K_test_mc)
    state1_test_mc.m_dot = m_dot1_mc # 设置质量流量

    if state1_test_mc.h is not None:
        print("\n进口状态 (点1 测试 MC):")
        print(state1_test_mc)
        state2_calc_mc, W_mc_calc = model_compressor_MC(state1_test_mc, P2_Pa_test_mc, eta_mc_test)
        if state2_calc_mc and W_mc_calc is not None:
            print("\n计算得到的MC出口状态 (点2 计算):")
            print(state2_calc_mc)
            print(f"MC单位质量压缩功: {W_mc_calc/1000:.2f} kJ/kg")
            print("\n与论文表10 SCBC点2 对比 (MC):")
            print(f"  计算MC出口温度 T: {state2_calc_mc.T - 273.15:.2f} °C (论文: 121.73 °C)")
            print(f"  计算MC出口焓 h: {state2_calc_mc.h / 1000:.2f} kJ/kg (论文: 453.36 kJ/kg)")
            h1_paper_kj_mc = 402.40
            w_mc_paper_kj = 453.36 - h1_paper_kj_mc
            print(f"  计算MC压缩功: {W_mc_calc/1000:.2f} kJ/kg (论文近似值: {w_mc_paper_kj:.2f} kJ/kg)")
    else:
        print("创建MC测试用进口状态点1失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试 model_turbine_T ---
    print("--- 测试SCBC透平 (T) 模型 ---")
    # SCBC 点5 (透平入口) 数据来自表10: P=24198.00 kPa, T=599.85 C, fluid='CO2'
    # 论文中 ηT = 0.9 (来自表6)
    # 论文中点6 (出口) P=7400.00 kPa, T=455.03 C, h=932.38 kJ/kg
    
    P5_Pa_test_t = to_pascal(24198.00, 'kpa') # Renamed for clarity
    T5_K_test_t = to_kelvin(599.85)    # Renamed for clarity
    m_dot5_t = 2641.42 # kg/s, from Table 10, point 5 for SCBC/ORC
    eta_t_test = 0.90 # 来自论文表6, η_T
    P6_Pa_test_t = to_pascal(7400.00, 'kpa') # Renamed for clarity

    state5_test_t = StatePoint(fluid_name="CO2", name="测试用SCBC点5_T")
    state5_test_t.props_from_PT(P5_Pa_test_t, T5_K_test_t)
    state5_test_t.m_dot = m_dot5_t # 设置质量流量

    if state5_test_t.h is not None:
        print("\n进口状态 (点5 测试 T):")
        print(state5_test_t)

        state6_calc_t, W_t_calc = model_turbine_T(state5_test_t, P6_Pa_test_t, eta_t_test)

        if state6_calc_t and W_t_calc is not None:
            print("\n计算得到的透平出口状态 (点6 计算):")
            print(state6_calc_t)
            print(f"透平单位质量做功: {W_t_calc/1000:.2f} kJ/kg")

            # 与表10中的点6进行对比
            print("\n与论文表10 SCBC点6 对比 (T):")
            print(f"  计算透平出口温度 T: {state6_calc_t.T - 273.15:.2f} °C (论文: 455.03 °C)")
            print(f"  计算透平出口焓 h: {state6_calc_t.h / 1000:.2f} kJ/kg (论文: 932.38 kJ/kg)")
            
            # 透平功对比: 论文 h5-h6 = 1094.91 - 932.38 = 162.53 kJ/kg
            h5_paper_kj_t = 1094.91 # from table10_data for SCBC 5
            w_t_paper_kj = h5_paper_kj_t - 932.38 # 162.53 kJ/kg
            print(f"  计算透平做功: {W_t_calc/1000:.2f} kJ/kg (论文近似值: {w_t_paper_kj:.2f} kJ/kg)")
    else:
        print("创建透平测试用进口状态点5失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 反算并测试 ORC泵 (PO) 模型 (使用论文点011的h,s为基准进行效率反算) ---
    print("--- 反算并测试ORC泵 (PO) 模型 (新反算逻辑) ---")
    
    # --- 步骤1: 定义论文中点011和点012的关键参数 ---
    P011_kPa_paper_po = 445.10                # 论文点011压力 (kPa)
    T011_C_paper_po = 58.66                 # 论文点011温度 (C) - 用于CoolProp计算实际模型输入点
    h011_kJ_kg_paper_po = 278.39            # 论文点011焓 (kJ/kg) - 用于新效率反算
    s011_kJ_kgK_paper_po = 1.26             # 论文点011熵 (kJ/kgK) - 用于新效率反算
    m_dot011_po = 677.22                    # 论文点011质量流量 (kg/s)

    P012_kPa_paper_po = 1500.00             # 论文点012压力 (kPa)
    h012_kJ_kg_paper_target_po = 279.52     # 论文点012焓 (kJ/kg) - 我们的目标实际出口焓

    # --- 步骤2: 反算ORC泵等熵效率，基于论文点011的h,s和论文焓差 ---
    eta_po_recalculated = None
    
    # 2a. 计算理想出口焓 h012_ideal_based_on_paper_s
    #     (出口压力P012_kPa_paper, 进口熵s011_kJ_kgK_paper)
    ideal_state_out_for_eta_calc = StatePoint(fluid_name="R245fa", name="ORC点012_Ideal_ForEtaRecalc")
    # 使用论文中的熵值 (kJ/kgK -> J/kgK) 和论文中的出口压力
    ideal_state_out_for_eta_calc.props_from_PS(to_pascal(P012_kPa_paper_po, 'kpa'), s011_kJ_kgK_paper_po * 1000)
    h_out_ideal_for_eta_calc_J_kg = ideal_state_out_for_eta_calc.h

    if h_out_ideal_for_eta_calc_J_kg is not None:
        # 2b. 计算理想功 W_ideal (基于论文点011的h,s)
        W_ideal_kJ_kg_recalc = (h_out_ideal_for_eta_calc_J_kg / 1000) - h011_kJ_kg_paper_po
        
        # 2c. 计算实际功 W_actual (基于论文点011和点012的h差)
        W_actual_kJ_kg_paper_diff = h012_kJ_kg_paper_target_po - h011_kJ_kg_paper_po
                                     # This is approx 1.13 kJ/kg

        if W_actual_kJ_kg_paper_diff > 1e-3 and abs(W_ideal_kJ_kg_recalc) > 1e-9: # 避免除零或无效计算
            # 2d. 反算等熵效率
            eta_po_recalculated = W_ideal_kJ_kg_recalc / W_actual_kJ_kg_paper_diff
            print(f"新反算得到的ORC泵等熵效率 (基于论文点011的h,s和论文焓差): {eta_po_recalculated:.4f}")
        else:
            print(f"警告: 无法有效进行新反算泵效率 (W_ideal_recalc={W_ideal_kJ_kg_recalc:.4f} kJ/kg, W_actual_paper_diff={W_actual_kJ_kg_paper_diff:.4f} kJ/kg)。")
    else:
        print("警告: 计算理想出口焓失败(基于论文s011)，无法进行新反算泵效率。")

    # --- 步骤3: 使用新反算出的效率（如果成功）或默认值进行ORC泵模型测试 ---
    eta_po_test_final = 0.75 # Default, if recalculation fails or is out of bounds
    if eta_po_recalculated is not None and 0 < eta_po_recalculated <= 1.0:
        eta_po_test_final = eta_po_recalculated
        print(f"测试将使用新反算出的效率: {eta_po_test_final:.4f}")
    elif eta_po_recalculated is not None: #反算出的效率不合理
        print(f"警告: 新反算出的泵效率 {eta_po_recalculated:.4f} 不在(0,1]合理范围内。将使用默认测试效率 {eta_po_test_final:.2f}。")
    else: # 反算过程失败
         print(f"警告: 新的泵效率反算失败。将使用默认测试效率 {eta_po_test_final:.2f}。")

    # 模型的实际进口状态仍然由CoolProp根据P,T计算 (与之前一致)
    # 这是因为 model_pump_ORC 函数期望一个 StatePoint 对象，其内部的 h,s 是自洽的
    state011_test_po_model_input = StatePoint(fluid_name="R245fa", name="测试用ORC点011_PO_ModelIn")
    state011_test_po_model_input.props_from_PT(to_pascal(P011_kPa_paper_po, 'kpa'), to_kelvin(T011_C_paper_po))
    state011_test_po_model_input.m_dot = m_dot011_po

    if state011_test_po_model_input.h is not None:
        print("\n泵模型实际进口状态 (点011 CoolProp计算):")
        print(state011_test_po_model_input)

        state012_calc_po, W_po_calc = model_pump_ORC(state011_test_po_model_input, to_pascal(P012_kPa_paper_po, 'kpa'), eta_po_test_final)

        if state012_calc_po and W_po_calc is not None:
            print("\n计算得到的泵出口状态 (点012 计算):")
            print(state012_calc_po)
            print(f"泵单位质量消耗功: {W_po_calc/1000:.2f} kJ/kg (使用效率: {eta_po_test_final:.4f})")

            # 与表10中的点012进行对比
            print("\n与论文表10 ORC点012 对比 (PO):")
            # For T_paper_012, we use the direct value from the paper.
            T012_C_paper_po = 59.37
            print(f"  计算泵出口温度 T: {state012_calc_po.T - 273.15:.2f} °C (论文: {T012_C_paper_po:.2f} °C)")
            print(f"  计算泵出口焓 h: {state012_calc_po.h / 1000:.2f} kJ/kg (论文: {h012_kJ_kg_paper_target_po:.2f} kJ/kg)")
            
            w_po_paper_kj = h012_kJ_kg_paper_target_po - h011_kJ_kg_paper_po
            print(f"  计算泵功: {W_po_calc/1000:.2f} kJ/kg (论文焓差近似值: {w_po_paper_kj:.2f} kJ/kg)")
    else:
        print("创建泵测试用进口状态点011 (模型输入) 失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试高温回热器 (HTR) 模型 ---
    print("--- 测试高温回热器 (HTR) 模型 ---")
    # HTR: 热流 SCBC 点6 -> 点7; 冷流 SCBC 点3 -> 点4
    # eta_H = 0.86 from Table 6
    # m_dot = 2641.42 kg/s for all these points

    # 进口状态 (基于论文表10)
    # 点6 (热进口)
    P6_htr_in_Pa = to_pascal(7400.00, 'kpa')
    T6_htr_in_K = to_kelvin(455.03)
    m_dot_htr = 2641.42
    state6_htr_in = StatePoint("CO2", "HTR_HotIn(P6)")
    state6_htr_in.props_from_PT(P6_htr_in_Pa, T6_htr_in_K)
    state6_htr_in.m_dot = m_dot_htr
    
    # 点3 (冷进口)
    P3_htr_in_Pa = to_pascal(24198.00, 'kpa')
    T3_htr_in_K = to_kelvin(281.92)
    state3_htr_in = StatePoint("CO2", "HTR_ColdIn(P3)")
    state3_htr_in.props_from_PT(P3_htr_in_Pa, T3_htr_in_K)
    state3_htr_in.m_dot = m_dot_htr # 质量流量相同

    eta_H_test = 0.86

    if state6_htr_in.h and state3_htr_in.h:
        print("\nHTR 热流进口 (点6):")
        print(state6_htr_in)
        print("HTR 冷流进口 (点3):")
        print(state3_htr_in)

        # 根据我们对HTR效率定义的验算，hot_fluid_is_C_min_side=True (即热侧温度变化由eff决定)
        state7_htr_out_calc, state4_htr_out_calc, Q_htr_calc = model_heat_exchanger_effectiveness(
            state_hot_in=state6_htr_in,
            state_cold_in=state3_htr_in,
            effectiveness=eta_H_test,
            hot_fluid_is_C_min_side=True,
            name_suffix="HTR"
        )

        if state7_htr_out_calc and state4_htr_out_calc:
            print("\n计算得到的HTR热流出口 (点7):")
            print(state7_htr_out_calc)
            print("计算得到的HTR冷流出口 (点4):")
            print(state4_htr_out_calc)
            print(f"HTR换热量 Q: {Q_htr_calc / (1000*1000) if Q_htr_calc is not None else 'N/A'} MW") # MW

            # 与论文表10对比
            # 点7: T=306.16 C, h=761.08 kJ/kg
            # 点4: T=417.94 C, h=867.76 kJ/kg
            print("\n与论文表10对比 (HTR):")
            print(f"  热出口(点7) 计算T: {state7_htr_out_calc.T - 273.15:.2f}°C (论文: 306.16°C)")
            print(f"  热出口(点7) 计算h: {state7_htr_out_calc.h / 1000:.2f} kJ/kg (论文: 761.08 kJ/kg)")
            print(f"  冷出口(点4) 计算T: {state4_htr_out_calc.T - 273.15:.2f}°C (论文: 417.94°C)")
            print(f"  冷出口(点4) 计算h: {state4_htr_out_calc.h / 1000:.2f} kJ/kg (论文: 867.76 kJ/kg)")
    else:
        print("创建HTR测试用进口状态点失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试低温回热器 (LTR) 模型 ---
    print("--- 测试低温回热器 (LTR) 模型 ---")
    # LTR: 热流 SCBC 点7 -> 点8; 冷流 SCBC 点2 -> 点3''(混合前)
    # eta_L = 0.86 from Table 6
    
    # 进口状态 (基于论文表10或之前计算的出口)
    # 点7 (热进口) - P, T, m_dot from paper
    P7_ltr_in_Pa_test = to_pascal(7400.00, 'kpa')
    T7_ltr_in_K_test = to_kelvin(306.16)
    m_dot_hot_ltr_test = 2641.42 # kg/s (论文点7 q_m)
    state7_ltr_in_test = StatePoint("CO2", "LTR_HotIn(P7)")
    state7_ltr_in_test.props_from_PT(P7_ltr_in_Pa_test, T7_ltr_in_K_test)
    state7_ltr_in_test.m_dot = m_dot_hot_ltr_test
    
    # 点2 (冷进口) - P, T, m_dot from paper
    P2_ltr_in_Pa_test = to_pascal(24198.00, 'kpa')
    T2_ltr_in_K_test = to_kelvin(121.73)
    m_dot_cold_ltr_test = 1945.09 # kg/s (论文点2 q_m)
    state2_ltr_in_test = StatePoint("CO2", "LTR_ColdIn(P2)")
    state2_ltr_in_test.props_from_PT(P2_ltr_in_Pa_test, T2_ltr_in_K_test)
    state2_ltr_in_test.m_dot = m_dot_cold_ltr_test

    eta_L_test = 0.86

    if state7_ltr_in_test.h and state2_ltr_in_test.h:
        print("\nLTR 热流进口 (点7):")
        print(state7_ltr_in_test)
        print("LTR 冷流进口 (点2):")
        print(state2_ltr_in_test)

        # 假设 ηL 的定义方式与 ηH 类似，基于热侧温度变化
        state8_ltr_out_calc, state3_prime_ltr_out_calc, Q_ltr_calc = model_heat_exchanger_effectiveness(
            state_hot_in=state7_ltr_in_test,
            state_cold_in=state2_ltr_in_test,
            effectiveness=eta_L_test,
            hot_fluid_is_C_min_side=True,
            name_suffix="LTR"
        )

        if state8_ltr_out_calc and state3_prime_ltr_out_calc:
            print("\n计算得到的LTR热流出口 (应为点8状态):")
            print(state8_ltr_out_calc)
            print("计算得到的LTR冷流出口 (点3'' - 主压气机流路在与RC混合前):")
            print(state3_prime_ltr_out_calc)
            print(f"LTR换热量 Q: {Q_ltr_calc / (1000*1000) if Q_ltr_calc is not None else 'N/A'} MW")

            # 与论文表10对比 - 点8
            # 论文点8: T=147.55 C, h=582.06 kJ/kg
            T8_paper_ltr = 147.55
            h8_paper_ltr_kJ = 582.06
            print("\n与论文表10对比 (LTR 热出口 - 点8):")
            print(f"  热出口(点8) 计算T: {state8_ltr_out_calc.T - 273.15:.2f}°C (论文: {T8_paper_ltr:.2f}°C)")
            print(f"  热出口(点8) 计算h: {state8_ltr_out_calc.h / 1000:.2f} kJ/kg (论文: {h8_paper_ltr_kJ:.2f} kJ/kg)")
            
            # 论文中的点3是混合后的状态，所以 state3_prime_ltr_out_calc 不能直接对比。
            # 但我们可以打印出来供参考。
            h3_mixed_paper_kJ = 696.46 # 论文点3的焓
            print(f"  供参考: LTR冷出口(点3'') 计算h: {state3_prime_ltr_out_calc.h/1000:.2f} kJ/kg (论文混合后点3的h: {h3_mixed_paper_kJ:.2f} kJ/kg)")
    else:
        print("创建LTR测试用进口状态点失败。")
    print("\n" + "="*50 + "\n") # Separator

    # --- 测试再压缩机 (RC) 模型 ---
    print("--- 测试再压缩机 (RC) 模型 ---")
    # RC进口: 状态与点8相同 (P=7.4MPa, T=147.55C)
    # RC流量: m_dot_rc = m_dot_H_cold_in (m3_paper) - m_dot_L_cold_out (m_dot_MC_main_flow)
    # m_dot_rc = 2641.42 - 1945.09 = 696.33 kg/s
    # RC出口压力: 与MC出口压力相同 (P_点2 = 24.198 MPa)
    # RC效率: eta_C = 0.85

    P8_rc_in_Pa_test = to_pascal(7400.00, 'kpa')
    T8_rc_in_K_test = to_kelvin(147.55)
    m_dot_rc_test = 696.33 # kg/s (calculated for flow balance at node 3)
    eta_rc_test = 0.85     # Same as MC

    state8_rc_in_test = StatePoint("CO2", "RC_In(P8_state)")
    state8_rc_in_test.props_from_PT(P8_rc_in_Pa_test, T8_rc_in_K_test)
    state8_rc_in_test.m_dot = m_dot_rc_test
    
    # RC出口压力应与MC出口压力相同，即P2 (24.198 MPa)
    P_rc_out_Pa_test = to_pascal(24198.00, 'kpa') 

    if state8_rc_in_test.h:
        print("\nRC 进口状态 (基于点8参数,流量调整):")
        print(state8_rc_in_test)

        state_rc_out_calc, W_rc_calc = model_compressor_MC(
            state_in=state8_rc_in_test, 
            P_out_Pa=P_rc_out_Pa_test, 
            eta_isen=eta_rc_test
        )

        if state_rc_out_calc and W_rc_calc:
            print("\n计算得到的RC出口状态 (点3'_rc - RC单独出口):")
            print(state_rc_out_calc)
            print(f"RC单位质量压缩功: {W_rc_calc/1000:.2f} kJ/kg")
            print(f"RC总消耗功率: {W_rc_calc * m_dot_rc_test / (1000*1000):.2f} MW")

            # --- 验证混合点3的焓和温度 ---
            # 为了验证，我们需要LTR的冷出口状态 (state3_prime_ltr_out_calc)
            # LTR冷进口是点2, LTR热进口是点7
            
            # LTR冷进口 (点2) - 参数来自之前的LTR测试或直接定义
            P2_for_mix_Pa = to_pascal(24198.00, 'kpa')
            T2_for_mix_K = to_kelvin(121.73)
            m_dot_ltr_cold_val = 1945.09 # kg/s (MC主流路流量)
            state2_for_mix_val = StatePoint("CO2", "LTR_ColdIn_for_mix_val(P2)")
            state2_for_mix_val.props_from_PT(P2_for_mix_Pa, T2_for_mix_K)
            state2_for_mix_val.m_dot = m_dot_ltr_cold_val

            # LTR热进口 (点7) - 参数来自之前的LTR测试或直接定义
            P7_for_mix_Pa = to_pascal(7400.00, 'kpa')
            T7_for_mix_K = to_kelvin(306.16)
            m_dot_ltr_hot_val = 2641.42 # kg/s (总流量在LTR热侧)
            state7_for_mix_val = StatePoint("CO2", "LTR_HotIn_for_mix_val(P7)")
            state7_for_mix_val.props_from_PT(P7_for_mix_Pa, T7_for_mix_K)
            state7_for_mix_val.m_dot = m_dot_ltr_hot_val
            
            # 调用LTR模型获取其冷出口状态
            _, ltr_cold_out_for_mix_calc, _ = model_heat_exchanger_effectiveness(
                state_hot_in=state7_for_mix_val,
                state_cold_in=state2_for_mix_val,
                effectiveness=0.86, # eta_L
                hot_fluid_is_C_min_side=True, # Based on previous LTR test matching
                name_suffix="LTR_for_RC_mix_val"
            )

            if ltr_cold_out_for_mix_calc and ltr_cold_out_for_mix_calc.h:
                h_ltr_c_out_J_kg = ltr_cold_out_for_mix_calc.h
                m_ltr_c_out_kg_s = ltr_cold_out_for_mix_calc.m_dot # Should be 1945.09

                h_rc_out_J_kg = state_rc_out_calc.h
                m_rc_out_kg_s = state_rc_out_calc.m_dot # Should be 696.33

                # 混合点3的计算焓
                m3_mixed_calc_kg_s = m_ltr_c_out_kg_s + m_rc_out_kg_s
                if abs(m3_mixed_calc_kg_s) < 1e-6: # Avoid division by zero if流量为0
                    print("错误: 混合流量为零，无法计算混合焓。")
                    h3_mixed_calc_J_kg = None
                else:
                    h3_mixed_calc_J_kg = (m_ltr_c_out_kg_s * h_ltr_c_out_J_kg + m_rc_out_kg_s * h_rc_out_J_kg) / m3_mixed_calc_kg_s
                
                # 论文中点3的参数
                h3_paper_kJ_kg = 696.46 
                m3_paper_kg_s = 2641.42 
                T3_paper_C = 281.92
                
                print(f"\n混合点3 (RC出口 + LTR冷出口) 验证:")
                print(f"  计算得到的混合流量: {m3_mixed_calc_kg_s:.2f} kg/s (论文点3流量: {m3_paper_kg_s:.2f} kg/s)")
                if h3_mixed_calc_J_kg is not None:
                    print(f"  计算得到的混合焓h3_calc: {h3_mixed_calc_J_kg / 1000:.2f} kJ/kg (论文点3焓h3_paper: {h3_paper_kJ_kg:.2f} kJ/kg)")
                
                    P3_mixed_Pa = to_pascal(24198.00, 'kpa') # 假设混合后压力与RC出口/MC出口相同
                    state3_mixed_calc_obj = StatePoint("CO2", "Mixed_Point3_Calc")
                    state3_mixed_calc_obj.props_from_PH(P3_mixed_Pa, h3_mixed_calc_J_kg)
                    state3_mixed_calc_obj.m_dot = m3_mixed_calc_kg_s
                    if state3_mixed_calc_obj.T:
                        print(f"  计算得到的混合温度T3_calc: {state3_mixed_calc_obj.T - 273.15:.2f} °C (论文点3温度T3_paper: {T3_paper_C:.2f} °C)")
                else:
                    print("  未能计算混合焓。")
            else:
                print("错误：无法获取LTR冷出口状态用于混合点验证。")
        else:
            print("错误：RC模型计算失败。")
    else:
        print("创建RC测试用进口状态点失败。")

    print("\n" + "="*50 + "\n") # Separator

def model_evaporator_GO(
    state_hot_in: StatePoint,   # SCBC side (e.g., point 8m)
    state_cold_in: StatePoint,  # ORC side (e.g., point 012)
    # Specify one of the outlet conditions to define the heat exchange
    T_hot_out_K: float = None,
    h_hot_out_J_kg: float = None,
    T_cold_out_K: float = None,
    h_cold_out_J_kg: float = None,
    pressure_drop_hot_Pa: float = 0.0,
    pressure_drop_cold_Pa: float = 0.0,
    name_suffix: str = "GO"
):
    """
    模拟蒸发器/气体冷却器 (GO)。
    需要指定一侧的出口条件（温度或焓）来确定换热量。
    """
    P_hot_out_Pa = state_hot_in.P - pressure_drop_hot_Pa
    P_cold_out_Pa = state_cold_in.P - pressure_drop_cold_Pa

    state_hot_out = StatePoint(state_hot_in.fluid, name=f"{state_hot_in.name}_out_{name_suffix}")
    state_cold_out = StatePoint(state_cold_in.fluid, name=f"{state_cold_in.name}_out_{name_suffix}")
    state_hot_out.m_dot = state_hot_in.m_dot
    state_cold_out.m_dot = state_cold_in.m_dot
    
    Q_exchanged_J = None

    if h_hot_out_J_kg is not None: # Hot side outlet enthalpy is given
        state_hot_out.props_from_PH(P_hot_out_Pa, h_hot_out_J_kg)
    elif T_hot_out_K is not None: # Hot side outlet temperature is given
        state_hot_out.props_from_PT(P_hot_out_Pa, T_hot_out_K)
    # Add similar conditions if cold side outlet is specified instead
    elif h_cold_out_J_kg is not None: # Cold side outlet enthalpy is given
        state_cold_out.props_from_PH(P_cold_out_Pa, h_cold_out_J_kg)
    elif T_cold_out_K is not None: # Cold side outlet temperature is given
        state_cold_out.props_from_PT(P_cold_out_Pa, T_cold_out_K)
    else:
        print(f"错误: 蒸发器 {name_suffix} 未指定任何出口条件。")
        return None, None, None

    if state_hot_out.h and state_cold_in.h and state_hot_in.h: # If hot side outlet was determined
        if Q_exchanged_J is None: # Calculate Q based on hot side if not already set
             Q_exchanged_J = state_hot_in.m_dot * (state_hot_in.h - state_hot_out.h)
        
        # Calculate cold side outlet
        if state_cold_out.h is None: # If cold side outlet was not the one specified
            _h_cold_out_J_kg = state_cold_in.h + Q_exchanged_J / state_cold_in.m_dot
            state_cold_out.props_from_PH(P_cold_out_Pa, _h_cold_out_J_kg)

    elif state_cold_out.h and state_hot_in.h and state_cold_in.h: # If cold side outlet was determined
        if Q_exchanged_J is None: # Calculate Q based on cold side if not already set
            Q_exchanged_J = state_cold_in.m_dot * (state_cold_out.h - state_cold_in.h)

        # Calculate hot side outlet
        if state_hot_out.h is None: # If hot side outlet was not the one specified
            _h_hot_out_J_kg = state_hot_in.h - Q_exchanged_J / state_hot_in.m_dot
            state_hot_out.props_from_PH(P_hot_out_Pa, _h_hot_out_J_kg)
            
    if not (state_hot_out.h and state_cold_out.h and Q_exchanged_J is not None):
        print(f"错误: 蒸发器 {name_suffix} 计算失败。")
        return None, None, None
        
    return state_hot_out, state_cold_out, Q_exchanged_J

def model_cooler_set_T_out(
    state_in: StatePoint, 
    T_out_K: float, 
    pressure_drop_Pa: float = 0.0,
    name_suffix: str = "Cooler"
):
    """
    模拟冷却器，将工质冷却到指定的出口温度。
    (适用于 SCBC主冷却器CS 和 ORC次冷却器CO)

    参数:
        state_in (StatePoint): 进口状态。
        T_out_K (float): 目标出口温度 (K)。
        pressure_drop_Pa (float): 冷却器内压降 (Pa)，默认为0。
        name_suffix (str): 用于命名出口状态点的后缀。

    返回:
        tuple: (state_out, Q_rejected_J)
            state_out (StatePoint): 出口状态。
            Q_rejected_J (float): 排出的总热量 (J)，正值。
    """
    # Allow T_in to be very close to T_out, in which case Q_rejected is near zero.
    # A more significant T_in < T_out would be a logical issue for a cooler.
    if state_in.T < T_out_K and not (-1e-3 < (state_in.T - T_out_K) < 1e-3): # If T_in is meaningfully less than T_out
        print(f"警告: 冷却器 {name_suffix} 进口温度 {state_in.T-273.15:.2f}C 低于目标出口温度 {T_out_K-273.15:.2f}C。")

    P_out_Pa = state_in.P - pressure_drop_Pa
    
    state_out = StatePoint(fluid_name=state_in.fluid, name=f"{state_in.name}_out_{name_suffix}")
    state_out.props_from_PT(P_out_Pa, T_out_K)
    state_out.m_dot = state_in.m_dot # 传递质量流量

    if state_out.h is None or state_in.h is None:
        print(f"错误: 无法计算冷却器 {name_suffix} 的进口或出口焓。")
        return None, None

    Q_rejected_J = state_in.m_dot * (state_in.h - state_out.h) # h_in > h_out for cooling
    
    # For a cooler, we expect Q_rejected_J to be positive.
    # Negative Q might occur if T_out_K was set higher than T_in, or due to complex fluid behavior.
    if Q_rejected_J < -1e-9: # Allow for very small negative due to precision, but flag larger ones.
         print(f"警告: 冷却器 {name_suffix} 计算得到的排出热量为负 ({Q_rejected_J/(state_in.m_dot*1000) if state_in.m_dot and state_in.m_dot > 1e-9 else Q_rejected_J:.2f} kJ/kg or J)。检查进口和目标出口温度。")

    return state_out, Q_rejected_J

def model_heater_set_T_out(
    state_in: StatePoint,
    T_out_K: float,
    pressure_drop_Pa: float = 0.0,
    name_suffix: str = "Heater"
):
    """
    模拟加热器 (如SCBC吸热器ER)，将工质加热到指定的出口温度。

    参数:
        state_in (StatePoint): 进口状态。
        T_out_K (float): 目标出口温度 (K)。
        pressure_drop_Pa (float): 加热器内压降 (Pa)，默认为0。
        name_suffix (str): 用于命名出口状态点的后缀。

    返回:
        tuple: (state_out, Q_absorbed_J)
            state_out (StatePoint): 出口状态。
            Q_absorbed_J (float): 吸收的总热量 (J)，正值。
    """
    if state_in.T >= T_out_K and not (-1e-3 < (state_in.T - T_out_K) < 1e-3): # If T_in is meaningfully greater than T_out
        print(f"警告: 加热器 {name_suffix} 进口温度 {state_in.T-273.15:.2f}C 高于或等于目标出口温度 {T_out_K-273.15:.2f}C。")

    P_out_Pa = state_in.P - pressure_drop_Pa
    
    state_out = StatePoint(fluid_name=state_in.fluid, name=f"{state_in.name}_out_{name_suffix}")
    state_out.props_from_PT(P_out_Pa, T_out_K)
    state_out.m_dot = state_in.m_dot # 传递质量流量

    if state_out.h is None or state_in.h is None:
        print(f"错误: 无法计算加热器 {name_suffix} 的进口或出口焓。")
        return None, None

    Q_absorbed_J = state_in.m_dot * (state_out.h - state_in.h) # h_out > h_in for heating
    
    if Q_absorbed_J < -1e-9: # Allow for very small negative due to precision
         print(f"警告: 加热器 {name_suffix} 计算得到的吸收热量为负 ({Q_absorbed_J/(state_in.m_dot*1000) if state_in.m_dot and state_in.m_dot > 1e-9 else Q_absorbed_J:.2f} kJ/kg or J)。检查进口和目标出口温度。")

    return state_out, Q_absorbed_J

if __name__ == '__main__':
    # ... (之前的测试代码保持不变) ...
    print("\n" + "="*50 + "\n") # Separator

    # --- 测试蒸发器 (GO) 模型 ---
    print("--- 测试蒸发器 (GO) / 气体冷却器 模型 ---")
    # SCBC侧 (热): 点8m (同点8状态) -> 点9
    # ORC侧 (冷): 点012 -> 点09

    # 点8m (热进口 - CO2)
    P8m_go_in_Pa = to_pascal(7400.00, 'kpa')
    T8m_go_in_K = to_kelvin(147.55)
    m_dot_8m_go = 1945.09 # kg/s (m_total - m_rc = 2641.42 - 696.33)
    state8m_go_in = StatePoint("CO2", "GO_HotIn(P8m)")
    state8m_go_in.props_from_PT(P8m_go_in_Pa, T8m_go_in_K)
    state8m_go_in.m_dot = m_dot_8m_go
    h8m_kJ_kg_paper = 582.06 # 论文点8焓

    # 点9 (热出口 - CO2) - 目标状态
    P9_go_out_Pa_target = to_pascal(7400.00, 'kpa') # 假设无压降
    T9_go_out_K_target = to_kelvin(84.26)
    h9_kJ_kg_paper_target = 503.44 # 论文点9焓

    # 点012 (冷进口 - R245fa)
    P012_go_in_Pa = to_pascal(1500.00, 'kpa')
    T012_go_in_K = to_kelvin(59.37) # 使用论文点012温度
    m_dot_012_go = 677.22 # kg/s
    state012_go_in = StatePoint("R245fa", "GO_ColdIn(P012)")
    # 为获得与论文焓值更接近的进口点，我们用P,h初始化（如果论文h已知）
    # 或者坚持P,T然后接受CoolProp的h。这里用P,T。
    state012_go_in.props_from_PT(P012_go_in_Pa, T012_go_in_K)
    state012_go_in.m_dot = m_dot_012_go
    h012_kJ_kg_paper = 279.52 # 论文点012焓

    # 点09 (冷出口 - R245fa) - 目标状态
    P09_go_out_Pa_target = to_pascal(1500.00, 'kpa') # 假设无压降
    T09_go_out_K_target = to_kelvin(127.76)
    h09_kJ_kg_paper_target = 505.35 # 论文点09焓

    if state8m_go_in.h and state012_go_in.h:
        print("\nGO 热流进口 (点8m):")
        print(state8m_go_in)
        print("GO 冷流进口 (点012):")
        print(state012_go_in)

        # 测试1: 给定热侧出口焓，计算冷侧出口
        print("\n--- 测试1: 给定热侧出口焓 (h9_paper) ---")
        go_hot_out_1, go_cold_out_1, Q_go_1 = model_evaporator_GO(
            state_hot_in=state8m_go_in,
            state_cold_in=state012_go_in,
            h_hot_out_J_kg=h9_kJ_kg_paper_target * 1000
        )
        if go_hot_out_1 and go_cold_out_1:
            print("计算得到的GO热流出口 (点9):")
            print(go_hot_out_1)
            print("计算得到的GO冷流出口 (点09):")
            print(go_cold_out_1)
            print(f"GO换热量 Q1: {Q_go_1 / (1000*1000) if Q_go_1 is not None else 'N/A'} MW")
            print(f"  对比冷出口焓: 计算 {go_cold_out_1.h/1000:.2f} kJ/kg vs 论文点09 {h09_kJ_kg_paper_target:.2f} kJ/kg")
            print(f"  对比冷出口温度: 计算 {go_cold_out_1.T-273.15:.2f} °C vs 论文点09 {T09_go_out_K_target-273.15:.2f} °C")

        # 测试2: 给定冷侧出口焓，计算热侧出口
        print("\n--- 测试2: 给定冷侧出口焓 (h09_paper) ---")
        go_hot_out_2, go_cold_out_2, Q_go_2 = model_evaporator_GO(
            state_hot_in=state8m_go_in,
            state_cold_in=state012_go_in,
            h_cold_out_J_kg=h09_kJ_kg_paper_target * 1000
        )
        if go_hot_out_2 and go_cold_out_2:
            print("计算得到的GO热流出口 (点9):")
            print(go_hot_out_2)
            print("计算得到的GO冷流出口 (点09):")
            print(go_cold_out_2)
            print(f"GO换热量 Q2: {Q_go_2 / (1000*1000) if Q_go_2 is not None else 'N/A'} MW")
            print(f"  对比热出口焓: 计算 {go_hot_out_2.h/1000:.2f} kJ/kg vs 论文点9 {h9_kJ_kg_paper_target:.2f} kJ/kg")
            print(f"  对比热出口温度: 计算 {go_hot_out_2.T-273.15:.2f} °C vs 论文点9 {T9_go_out_K_target-273.15:.2f} °C")
            
            # 验证热平衡
            Q_released_scbc_calc = state8m_go_in.m_dot * (state8m_go_in.h - go_hot_out_2.h) if state8m_go_in.h and go_hot_out_2.h else 0
            Q_absorbed_orc_calc = state012_go_in.m_dot * (go_cold_out_2.h - state012_go_in.h) if state012_go_in.h and go_cold_out_2.h else 0
            print(f"  热平衡校验: Q_hot_side={Q_released_scbc_calc/(1e6):.2f} MW, Q_cold_side={Q_absorbed_orc_calc/(1e6):.2f} MW")

    else:
        print("创建GO测试用进口状态点失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试ORC透平 (TO) 模型 ---
    print("--- 测试ORC透平 (TO) 模型 ---")
    # ORC透平进口: 点09 (P=1500 kPa, T=127.76C, R245fa, m_dot=677.22 kg/s)
    # ORC透平出口: 点010 (P=445.10 kPa)
    # ORC透平效率: eta_TO = 0.8 (来自论文表6)

    P09_to_in_Pa = to_pascal(1500.00, 'kpa')
    T09_to_in_K = to_kelvin(127.76)
    m_dot09_to = 677.22 # kg/s
    eta_to_test = 0.80  # 来自论文表6

    state09_to_in_test = StatePoint("R245fa", "TO_In(P09)")
    state09_to_in_test.props_from_PT(P09_to_in_Pa, T09_to_in_K)
    state09_to_in_test.m_dot = m_dot09_to
    
    P010_to_out_Pa_test = to_pascal(445.10, 'kpa')
    if state09_to_in_test.h:
        print("\nORC透平 进口状态 (点09):")
        print(state09_to_in_test)

        state010_to_out_calc, W_to_calc = model_turbine_T( # 复用透平模型
            state_in=state09_to_in_test,
            P_out_Pa=P010_to_out_Pa_test,
            eta_isen=eta_to_test
        )

        if state010_to_out_calc and W_to_calc:
            print("\n计算得到的ORC透平出口状态 (点010):")
            print(state010_to_out_calc)
            print(f"ORC透平单位质量做功: {W_to_calc/1000:.2f} kJ/kg")
            print(f"ORC透平总输出功率: {W_to_calc * m_dot09_to / (1000*1000):.2f} MW")

            # 与论文表10中点010对比
            T010_paper_C = 94.67
            h010_paper_kJ = 485.51
            print("\n与论文表10 ORC点010 对比:")
            print(f"  计算出口温度 T: {state010_to_out_calc.T - 273.15:.2f}°C (论文: {T010_paper_C:.2f}°C)")
            print(f"  计算出口焓 h: {state010_to_out_calc.h / 1000:.2f} kJ/kg (论文: {h010_paper_kJ:.2f} kJ/kg)")

            # 论文做功: h09_paper - h010_paper = 505.35 - 485.51 = 19.84 kJ/kg
            h09_paper_kJ = 505.35
            w_to_paper_kj = h09_paper_kJ - h010_paper_kJ
            print(f"  计算ORC透平做功: {W_to_calc/1000:.2f} kJ/kg (论文焓差近似值: {w_to_paper_kj:.2f} kJ/kg)")
        else:
            print("错误: ORC透平模型计算失败。")
    else:
        print("创建ORC透平测试用进口状态点09失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试SCBC主冷却器 (CS) 模型 ---
    print("--- 测试SCBC主冷却器 (CS) 模型 ---")
    # CS进口: 点9 (P=7.4MPa, T=84.26C, m_dot=1945.09 kg/s, CO2)
    # CS出口: 点1 (P=7.4MPa, T=35.00C)
    
    P9_cs_in_Pa = to_pascal(7400.00, 'kpa')
    T9_cs_in_K = to_kelvin(84.26)
    m_dot_cs = 1945.09 # kg/s
    
    state9_cs_in_test = StatePoint("CO2", "CS_In(P9)")
    state9_cs_in_test.props_from_PT(P9_cs_in_Pa, T9_cs_in_K)
    state9_cs_in_test.m_dot = m_dot_cs

    T1_cs_out_K_target = to_kelvin(35.00) # 论文点1温度

    if state9_cs_in_test.h:
        print("\n主冷却器CS 进口状态 (点9):")
        print(state9_cs_in_test)

        state1_cs_out_calc, Q_cs_calc = model_cooler_set_T_out(
            state_in=state9_cs_in_test,
            T_out_K=T1_cs_out_K_target,
            name_suffix="CS"
        )

        if state1_cs_out_calc and Q_cs_calc is not None:
            print("\n计算得到的主冷却器CS出口状态 (点1):")
            print(state1_cs_out_calc)
            print(f"主冷却器CS排出的总热量 Q_CS: {Q_cs_calc / (1000*1000):.2f} MW")

            # 与论文表10中点1对比
            T1_paper_C_cs = 35.00 
            h1_paper_kJ_cs = 402.40
            # 论文中排出热量 Q_CS_paper = m_dot_cs * (h9_paper - h1_paper)
            # h9_paper (来自表10点9) = 503.44 kJ/kg 
            h9_paper_kJ_cs = 503.44 
            Q_cs_paper_MW = m_dot_cs * (h9_paper_kJ_cs - h1_paper_kJ_cs) / 1000

            print("\n与论文表10 SCBC点1 对比:")
            print(f"  计算出口温度 T: {state1_cs_out_calc.T - 273.15:.2f}°C (论文: {T1_paper_C_cs:.2f}°C)")
            print(f"  计算出口焓 h: {state1_cs_out_calc.h / 1000:.2f} kJ/kg (论文: {h1_paper_kJ_cs:.2f} kJ/kg)")
            print(f"  计算排出热量 Q_CS: {Q_cs_calc / (1000*1000):.2f} MW (论文近似值: {Q_cs_paper_MW:.2f} MW)")
        else:
            print("错误: 主冷却器CS模型计算失败。")
    else:
        print("创建主冷却器CS测试用进口状态点9失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试ORC次冷却器 (CO) / 冷凝器 模型 ---
    print("--- 测试ORC次冷却器 (CO) / 冷凝器 模型 ---")
    # CO进口: 点010 (P=445.10 kPa, T=94.67C, m_dot=677.22 kg/s, R245fa)
    # CO出口: 点011 (P=445.10 kPa, T=58.66C)
    
    P010_co_in_Pa = to_pascal(445.10, 'kpa')
    T010_co_in_K = to_kelvin(94.67)
    m_dot_co = 677.22 # kg/s
    
    state010_co_in_test = StatePoint("R245fa", "CO_In(P010)")
    state010_co_in_test.props_from_PT(P010_co_in_Pa, T010_co_in_K)
    state010_co_in_test.m_dot = m_dot_co

    T011_co_out_K_target = to_kelvin(58.66) # 论文点011温度

    if state010_co_in_test.h:
        print("\nORC次冷却器CO 进口状态 (点010):")
        print(state010_co_in_test)

        state011_co_out_calc, Q_co_calc = model_cooler_set_T_out(
            state_in=state010_co_in_test,
            T_out_K=T011_co_out_K_target,
            name_suffix="CO"
        )

        if state011_co_out_calc and Q_co_calc is not None:
            print("\n计算得到的ORC次冷却器CO出口状态 (点011):")
            print(state011_co_out_calc)
            print(f"ORC次冷却器CO排出的总热量 Q_CO: {Q_co_calc / (1000*1000):.2f} MW")

            # 与论文表10中点011对比
            T011_paper_C_co = 58.66 
            h011_paper_kJ_co = 278.39 # 注意：这是论文值，CoolProp在P,T下算出的点011焓可能略有不同
            
            # 论文中排出热量 Q_CO_paper = m_dot_co * (h010_paper - h011_paper)
            # h010_paper (来自表10点010) = 485.51 kJ/kg 
            h010_paper_kJ_co = 485.51
            Q_co_paper_MW = m_dot_co * (h010_paper_kJ_co - h011_paper_kJ_co) / 1000

            print("\n与论文表10 ORC点011 对比:")
            print(f"  计算出口温度 T: {state011_co_out_calc.T - 273.15:.2f}°C (论文: {T011_paper_C_co:.2f}°C)")
            print(f"  计算出口焓 h: {state011_co_out_calc.h / 1000:.2f} kJ/kg (论文: {h011_paper_kJ_co:.2f} kJ/kg)")
            print(f"  计算排出热量 Q_CO: {Q_co_calc / (1000*1000):.2f} MW (论文近似值: {Q_co_paper_MW:.2f} MW)")
        else:
            print("错误: ORC次冷却器CO模型计算失败。")
    else:
        print("创建ORC次冷却器CO测试用进口状态点010失败。")

    print("\n" + "="*50 + "\n") # Separator

    # --- 测试SCBC吸热器 (ER) 模型 ---
    print("--- 测试SCBC吸热器 (ER) 模型 ---")
    # ER进口: 点4 (P=24.198MPa, T=417.94C, m_dot=2641.42 kg/s, CO2)
    # ER出口: 点5 (P=24.198MPa, T=599.85C)
    
    P4_er_in_Pa = to_pascal(24198.00, 'kpa')
    T4_er_in_K = to_kelvin(417.94)
    m_dot_er = 2641.42 # kg/s
    
    state4_er_in_test = StatePoint("CO2", "ER_In(P4)")
    state4_er_in_test.props_from_PT(P4_er_in_Pa, T4_er_in_K)
    state4_er_in_test.m_dot = m_dot_er

    T5_er_out_K_target = to_kelvin(599.85) # 论文点5温度

    if state4_er_in_test.h:
        print("\n吸热器ER 进口状态 (点4):")
        print(state4_er_in_test)

        state5_er_out_calc, Q_er_calc = model_heater_set_T_out(
            state_in=state4_er_in_test,
            T_out_K=T5_er_out_K_target,
            name_suffix="ER"
        )

        if state5_er_out_calc and Q_er_calc is not None:
            print("\n计算得到的吸热器ER出口状态 (点5):")
            print(state5_er_out_calc)
            print(f"吸热器ER吸收的总热量 Q_ER: {Q_er_calc / (1000*1000):.2f} MW")

            # 与论文表10中点5对比
            T5_paper_C_er = 599.85
            h5_paper_kJ_er = 1094.91
            # 论文中吸热量 Q_ER_paper = m_dot_er * (h5_paper - h4_paper)
            # h4_paper (来自表10点4) = 867.76 kJ/kg
            h4_paper_kJ_er = 867.76
            Q_er_paper_MW = m_dot_er * (h5_paper_kJ_er - h4_paper_kJ_er) / 1000

            print("\n与论文表10 SCBC点5 对比:")
            print(f"  计算出口温度 T: {state5_er_out_calc.T - 273.15:.2f}°C (论文: {T5_paper_C_er:.2f}°C)")
            print(f"  计算出口焓 h: {state5_er_out_calc.h / 1000:.2f} kJ/kg (论文: {h5_paper_kJ_er:.2f} kJ/kg)")
            print(f"  计算吸收热量 Q_ER: {Q_er_calc / (1000*1000):.2f} MW (论文近似值: {Q_er_paper_MW:.2f} MW)")
        else:
            print("错误: 吸热器ER模型计算失败。")
    else:
        print("创建吸热器ER测试用进口状态点4失败。")
