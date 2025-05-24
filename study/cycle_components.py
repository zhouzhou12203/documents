# cycle_components.py

from 状态点计算 import StatePoint # 假设 '状态点计算.py' 在同一目录或Python路径中
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
    from 状态点计算 import to_kelvin, to_pascal

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