import numpy as np
from CoolProp.CoolProp import PropsSI
import json
import scipy.optimize

# --- 环境参考状态 (用于㶲计算) ---
T0_CELSIUS = 9.56
P0_KPA = 101.382

T0_K = T0_CELSIUS + 273.15
P0_PA = P0_KPA * 1000

# --- 辅助函数 ---
def to_kelvin(T_celsius):
    """将摄氏度转换为开尔文温度"""
    return T_celsius + 273.15

def to_pascal(P_bar_or_kpa, unit='kpa'):
    """将不同单位的压力转换为帕斯卡"""
    if unit.lower() == 'kpa':
        return P_bar_or_kpa * 1000
    elif unit.lower() == 'mpa':
        return P_bar_or_kpa * 1e6
    elif unit.lower() == 'bar':
        return P_bar_or_kpa * 1e5
    return P_bar_or_kpa

# --- 核心物性计算类 ---
class StatePoint:
    def __init__(self, fluid_name, name=""):
        self.fluid = fluid_name
        self.name = name
        self.P = None; self.T = None; self.h = None; self.s = None
        self.d = None; self.e = None; self.q = None; self.m_dot = None
        try:
            self._h0 = PropsSI('H', 'T', T0_K, 'P', P0_PA, self.fluid)
            self._s0 = PropsSI('S', 'T', T0_K, 'P', P0_PA, self.fluid)
        except ValueError:
            self._h0 = None
            self._s0 = None

    def _calculate_exergy(self):
        if self.h is not None and self.s is not None and self._h0 is not None and self._s0 is not None:
            self.e = (self.h - self._h0) - T0_K * (self.s - self._s0)
        else:
            self.e = None

    def props_from_PT(self, P_Pa, T_K):
        self.P = P_Pa; self.T = T_K
        try:
            self.h = PropsSI('H', 'P', self.P, 'T', self.T, self.fluid)
            self.s = PropsSI('S', 'P', self.P, 'T', self.T, self.fluid)
            self.d = PropsSI('D', 'P', self.P, 'T', self.T, self.fluid)
            self._calculate_exergy()
        except Exception as err:
            print(f"计算P,T物性时出错 {self.name} ({self.fluid}): {err}")
            self.h, self.s, self.d, self.e = None, None, None, None
        return self

    def props_from_PH(self, P_Pa, h_J_kg):
        self.P = P_Pa; self.h = h_J_kg
        try:
            self.T = PropsSI('T', 'P', self.P, 'H', self.h, self.fluid)
            self.s = PropsSI('S', 'P', self.P, 'H', self.h, self.fluid)
            self.d = PropsSI('D', 'P', self.P, 'H', self.h, self.fluid)
            try: self.q = PropsSI('Q', 'P', self.P, 'H', self.h, self.fluid)
            except: self.q = None
            self._calculate_exergy()
        except Exception as err:
            print(f"计算P,H物性时出错 {self.name} ({self.fluid}): {err}")
            self.T, self.s, self.d, self.e, self.q = None, None, None, None, None
        return self

    def props_from_PS(self, P_Pa, s_J_kgK):
        self.P = P_Pa; self.s = s_J_kgK
        try:
            self.T = PropsSI('T', 'P', self.P, 'S', self.s, self.fluid)
            self.h = PropsSI('H', 'P', self.P, 'S', self.s, self.fluid)
            self.d = PropsSI('D', 'P', self.P, 'S', self.s, self.fluid)
            try: self.q = PropsSI('Q', 'P', self.P, 'S', self.s, self.fluid)
            except: self.q = None
            self._calculate_exergy()
        except Exception as err:
            print(f"计算P,S物性时出错 {self.name} ({self.fluid}): {err}")
            self.T, self.h, self.d, self.e, self.q = None, None, None, None, None
        return self

    def props_from_PQ(self, P_Pa, Q_frac):
        self.P = P_Pa; self.q = Q_frac
        try:
            self.T = PropsSI('T', 'P', self.P, 'Q', self.q, self.fluid)
            self.h = PropsSI('H', 'P', self.P, 'Q', self.q, self.fluid)
            self.s = PropsSI('S', 'P', self.P, 'Q', self.q, self.fluid)
            self.d = PropsSI('D', 'P', self.P, 'Q', self.q, self.fluid)
            self._calculate_exergy()
        except Exception as err:
            print(f"计算P,Q物性时出错 {self.name} ({self.fluid}): {err}")
            self.T, self.h, self.s, self.d, self.e = None, None, None, None, None
        return self

    def __str__(self):
        return (f"状态点: {self.name} ({self.fluid})\n"
                f"  P = {self.P/1e6 if self.P else 'N/A':.3f} MPa\n"
                f"  T = {self.T - 273.15 if self.T else 'N/A':.2f} °C\n"
                f"  h = {self.h/1e3 if self.h else 'N/A':.2f} kJ/kg\n"
                f"  s = {self.s/1e3 if self.s else 'N/A':.4f} kJ/kgK\n"
                f"  d = {self.d if self.d else 'N/A':.2f} kg/m³\n"
                f"  e = {self.e/1e3 if self.e else 'N/A':.2f} kJ/kg\n"
                f"  Q = {self.q if self.q is not None else 'N/A'}\n"
                f"  m_dot = {self.m_dot if self.m_dot is not None else 'N/A'} kg/s")

# --- T0/P0反推相关函数定义 (全局作用域) ---
table10_data_for_fitting = [
    ("SCBC 1", "CO2", 7400.00, 35.00, 402.40, 1.66, 200.84),
    ("SCBC 2", "CO2", 24198.00, 121.73, 453.36, 1.68, 246.29),
    ("SCBC 3", "CO2", 24198.00, 281.92, 696.46, 2.21, 341.30),
    ("SCBC 4", "CO2", 24198.00, 417.94, 867.76, 2.48, 434.43),
    ("SCBC 5", "CO2", 24198.00, 599.85, 1094.91, 2.77, 579.03),
    ("SCBC 6", "CO2", 7400.00, 455.03, 932.38, 2.80, 409.40),
    ("SCBC 7", "CO2", 7400.00, 306.16, 761.08, 2.54, 312.52),
    ("SCBC 8", "CO2", 7400.00, 147.55, 582.06, 2.17, 235.75),
    ("SCBC 9", "CO2", 7400.00, 84.26, 503.44, 1.97, 214.69),
    ("ORC 09", "R245fa", 1500.00, 127.76, 505.35, 1.86, 61.21),
    ("ORC 010", "R245fa", 445.10, 94.67, 485.51, 1.88, 37.52),
    ("ORC 011", "R245fa", 445.10, 58.66, 278.39, 1.26, 5.40),
    ("ORC 012", "R245fa", 1500.00, 59.37, 279.52, 1.26, 6.29),
]

def exergy_error_func(params_T0_P0, data_points):
    T0_K_fit, P0_Pa_fit = params_T0_P0
    errors = []
    if T0_K_fit <= 0 or P0_Pa_fit <= 0: return [1e6] * len(data_points)
    for _, fluid, _, _, h_kJ_kg, s_kJ_kgK, e_kJ_kg_paper in data_points:
        try:
            _h0 = PropsSI('H', 'T', T0_K_fit, 'P', P0_Pa_fit, fluid)
            _s0 = PropsSI('S', 'T', T0_K_fit, 'P', P0_Pa_fit, fluid)
            h_J_paper = h_kJ_kg * 1000
            s_J_paper = s_kJ_kgK * 1000
            e_calc_J = (h_J_paper - _h0) - T0_K_fit * (s_J_paper - _s0)
            errors.append(e_calc_J / 1000 - e_kJ_kg_paper)
        except Exception: errors.append(1e6)
    return errors

def run_t0_p0_fitting():
    print("\n--- 开始反推参考状态 T0 和 P0 ---")
    initial_params = [298.15, 101325.0]
    bounds = ([273.15, 80000.0], [323.15, 120000.0])
    try:
        result = scipy.optimize.least_squares(
            exergy_error_func, initial_params, args=(table10_data_for_fitting,), bounds=bounds, verbose=0
        )
        if result.success:
            T0_fit_K, P0_fit_Pa = result.x
            print(f"  优化成功! 反推 T0 = {T0_fit_K - 273.15:.2f} °C, P0 = {P0_fit_Pa / 1000:.3f} kPa")
        else: print(f"  优化未成功: {result.message}")
    except Exception as e_fit: print(f"  运行反推时发生错误: {e_fit}")

# --- 主程序块 ---
if __name__ == "__main__":
    print("--- 脚本开始执行 ---")
    print(f"当前使用的全局参考状态: T0 = {T0_CELSIUS:.2f} °C ({T0_K:.2f} K), P0 = {P0_KPA:.3f} kPa ({P0_PA:.0f} Pa)")
    print("--- 正在验证表10中的所有状态点 (基于论文给定的P,T) ---")

    validation_data = [
        ("SCBC 1", "CO2", 7400.00, 35.00, 402.40, 1.66, 200.84, 1945.09),
        ("SCBC 2", "CO2", 24198.00, 121.73, 453.36, 1.68, 246.29, 1945.09),
        ("SCBC 3", "CO2", 24198.00, 281.92, 696.46, 2.21, 341.30, 2641.42),
        ("SCBC 4", "CO2", 24198.00, 417.94, 867.76, 2.48, 434.43, 2641.42),
        ("SCBC 5", "CO2", 24198.00, 599.85, 1094.91, 2.77, 579.03, 2641.42),
        ("SCBC 6", "CO2", 7400.00, 455.03, 932.38, 2.80, 409.40, 2641.42),
        ("SCBC 7", "CO2", 7400.00, 306.16, 761.08, 2.54, 312.52, 2641.42),
        ("SCBC 8", "CO2", 7400.00, 147.55, 582.06, 2.17, 235.75, 1945.09),
        ("SCBC 9", "CO2", 7400.00, 84.26, 503.44, 1.97, 214.69, 1945.09),
        ("ORC 09", "R245fa", 1500.00, 127.76, 505.35, 1.86, 61.21, 677.22),
        ("ORC 010", "R245fa", 445.10, 94.67, 485.51, 1.88, 37.52, 677.22),
        ("ORC 011", "R245fa", 445.10, 58.66, 278.39, 1.26, 5.40, 677.22),
        ("ORC 012", "R245fa", 1500.00, 59.37, 279.52, 1.26, 6.29, 677.22),
    ]

    output_csv_data = []
    csv_header = [
        "PointName", "Fluid", "P_kPa_paper", "T_C_paper", "h_kJ_kg_paper", 
        "s_kJ_kgK_paper", "e_kJ_kg_paper", "m_dot_kg_s", "P_Pa_calc", "T_K_calc", 
        "h_J_kg_calc", "s_J_kgK_calc", "d_kg_m3_calc", "e_J_kg_calc",
        "e_kJ_kg_calc", "e_diff_kJ_kg"
    ]
    output_csv_data.append(csv_header)

    print("\n详细状态点验证 (㶲对比):")
    print("="*120)
    print(f"{'状态点名':<18} {'流体':<6} {'P(kPa)':>8} {'T(C)':>7} {'h(kJ/kg)':>10} {'s(kJ/kgK)':>10} {'m_dot(kg/s)':>12} {'e_calc(kJ/kg)':>14} {'e_paper(kJ/kg)':>14} {'e_diff(kJ/kg)':>14}")
    print("-"*120)

    for name, fluid, p_kpa, t_c, h_kj_kg_paper, s_kj_kgk_paper, e_kj_kg_paper, m_dot_kg_s in validation_data:
        P_Pa = to_pascal(p_kpa, 'kpa')
        T_K = to_kelvin(t_c)
        current_state = StatePoint(fluid_name=fluid, name=name)
        current_state.props_from_PT(P_Pa, T_K)
        current_state.m_dot = m_dot_kg_s
        e_calc_kj = current_state.e / 1000 if current_state.e is not None else float('nan')
        e_diff_kj = e_calc_kj - e_kj_kg_paper if current_state.e is not None else float('nan')
        print(f"{name:<18} {fluid:<6} {p_kpa:>8.2f} {t_c:>7.2f} {current_state.h/1000 if current_state.h else 'N/A':>10.2f} {current_state.s/1000 if current_state.s else 'N/A':>10.4f} {m_dot_kg_s:>12.2f} {e_calc_kj:>14.2f} {e_kj_kg_paper:>14.2f} {e_diff_kj:>14.2f}")
        csv_row = [
            name, fluid, p_kpa, t_c, h_kj_kg_paper, s_kj_kgk_paper, e_kj_kg_paper, m_dot_kg_s,
            current_state.P, current_state.T, current_state.h, current_state.s, 
            current_state.d, current_state.e, e_calc_kj, e_diff_kj
        ]
        output_csv_data.append(csv_row)
    print("="*120)

    csv_filename = "calculated_state_points_from_table10.csv"
    try:
        import csv # Already imported at top
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(output_csv_data)
        print(f"\n状态点数据已成功导出到: {csv_filename}")
    except Exception as e_csv:
        print(f"\n导出到CSV文件时出错: {e_csv}")

    # --- (可选) 调用T0/P0反推函数 ---
    # print("\n尝试执行T0/P0反推...")
    # run_t0_p0_fitting() 

    # --- 输出循环设定参数到JSON文件 ---
    print("\n--- 正在输出循环设定参数到 cycle_setup_parameters.json ---")
    cycle_parameters = {
        "fluids": {"scbc": "CO2", "orc": "R245fa"},
        "reference_conditions": {"T0_C": T0_CELSIUS, "P0_kPa": P0_KPA},
        "scbc_parameters": {
            "p1_compressor_inlet_kPa": 7400.0, "T1_compressor_inlet_C": 35.0,
            "T5_turbine_inlet_C": 550.0, "PR_main_cycle_pressure_ratio": 3.0,
            "eta_T_turbine": 0.9, "eta_C_compressor": 0.85,
            "eta_H_HTR_effectiveness": 0.86, "eta_L_LTR_effectiveness": 0.86
        },
        "orc_parameters": {
            "T_turbine_inlet_C": 120.0, "PR_turbine_expansion_ratio": 3.0,
            "eta_TO_turbine": 0.8, "eta_PO_pump": 0.75
        },
        "heat_exchangers_common": {"min_temp_diff_pinch_C": 10.0},
        "notes": {
            "phi_ER_MW_heat_input": 600.0,
            "cost_fuel_cQ_dollar_per_MWh": 7.4 
        }
    }
    params_filename = "cycle_setup_parameters.json"
    try:
        with open(params_filename, 'w', encoding='utf-8') as f:
            json.dump(cycle_parameters, f, ensure_ascii=False, indent=4)
        print(f"循环设定参数已成功导出到: {params_filename}")
    except Exception as e_json:
        print(f"\n导出循环设定参数到JSON文件时出错: {e_json}")

    print("\n--- 脚本执行完毕 ---")
