import numpy as np
from CoolProp.CoolProp import PropsSI

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
    """将不同单位的压力转换为帕斯卡
    
    参数:
        P_bar_or_kpa: float, 压力值
        unit: str, 单位类型 ('kpa', 'mpa', 'bar')
    返回:
        float: 帕斯卡单位的压力值
    """
    if unit.lower() == 'kpa':
        return P_bar_or_kpa * 1000
    elif unit.lower() == 'mpa':
        return P_bar_or_kpa * 1e6
    elif unit.lower() == 'bar':
        return P_bar_or_kpa * 1e5
    return P_bar_or_kpa # 如果没有指定单位或未知单位，假设输入已经是帕斯卡

# --- 核心物性计算类 ---
class StatePoint:
    def __init__(self, fluid_name, name=""):
        """初始化状态点
        
        参数:
            fluid_name: str, 工质名称
            name: str, 状态点名称（如"压缩机入口"、"涡轮出口"等）
        """
        self.fluid = fluid_name
        self.name = name
        self.P = None  # 压力 (Pa)
        self.T = None  # 温度 (K)
        self.h = None  # 焓 (J/kg)
        self.s = None  # 熵 (J/kg/K)
        self.d = None  # 密度 (kg/m^3)
        self.e = None  # 比㶲 (J/kg)
        self.q = None  # 干度（如果适用）
        self.m_dot = None # 质量流量 (kg/s)（由系统模型设置）

        # 用于㶲计算的参考状态属性
        self._h0 = PropsSI('H', 'T', T0_K, 'P', P0_PA, self.fluid)
        self._s0 = PropsSI('S', 'T', T0_K, 'P', P0_PA, self.fluid)

    def _calculate_exergy(self):
        """计算比㶲"""
        if self.h is not None and self.s is not None:
            self.e = (self.h - self._h0) - T0_K * (self.s - self._s0)
        else:
            self.e = None

    def props_from_PT(self, P_Pa, T_K):
        """根据压力和温度计算其他物性参数"""
        self.P = P_Pa
        self.T = T_K
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
        """根据压力和焓计算其他物性参数"""
        self.P = P_Pa
        self.h = h_J_kg
        try:
            self.T = PropsSI('T', 'P', self.P, 'H', self.h, self.fluid)
            self.s = PropsSI('S', 'P', self.P, 'H', self.h, self.fluid)
            self.d = PropsSI('D', 'P', self.P, 'H', self.h, self.fluid)
            # 检查是否在两相区
            try: self.q = PropsSI('Q', 'P', self.P, 'H', self.h, self.fluid)
            except: self.q = None # 不在两相区或不支持干度计算
            self._calculate_exergy()
        except Exception as err:
            print(f"计算P,H物性时出错 {self.name} ({self.fluid}): {err}")
            self.T, self.s, self.d, self.e, self.q = None, None, None, None, None
        return self

    def props_from_PS(self, P_Pa, s_J_kgK):
        """根据压力和熵计算其他物性参数"""
        self.P = P_Pa
        self.s = s_J_kgK
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
        """根据压力和干度计算其他物性参数
        
        参数:
            P_Pa: float, 压力 (Pa)
            Q_frac: float, 干度 (0表示饱和液体，1表示饱和蒸汽)
        """
        self.P = P_Pa
        self.q = Q_frac
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
        """返回状态点的字符串表示"""
        return (f"状态点: {self.name} ({self.fluid})\n"
                f"  P = {self.P/1e6 if self.P else 'N/A':.3f} MPa\n"
                f"  T = {self.T - 273.15 if self.T else 'N/A':.2f} °C\n"
                f"  h = {self.h/1e3 if self.h else 'N/A':.2f} kJ/kg\n"
                f"  s = {self.s/1e3 if self.s else 'N/A':.4f} kJ/kgK\n"
                f"  d = {self.d if self.d else 'N/A':.2f} kg/m³\n"
                f"  e = {self.e/1e3 if self.e else 'N/A':.2f} kJ/kg\n"
                f"  Q = {self.q if self.q is not None else 'N/A'}\n"
                f"  m_dot = {self.m_dot if self.m_dot is not None else 'N/A'} kg/s")

# (之前的 StatePoint 类定义等保持不变)

# --- 主程序块 ---
if __name__ == "__main__":
    print("--- 脚本开始执行 ---")
    print(f"当前使用的全局参考状态: T0 = {T0_CELSIUS:.2f} °C ({T0_K:.2f} K), P0 = {P0_KPA:.3f} kPa ({P0_PA:.0f} Pa)")
    print("--- 正在验证表10中的所有状态点 (基于论文给定的P,T) ---")

    # 表10 SCBC/ORC系统优化后的状态点数据 (与 run_t0_p0_fitting 中的 table10_data 结构一致)
    # (name, fluid, P_kPa, T_C, h_kJ_kg_paper, s_kJ_kgK_paper, e_kJ_kg_paper, m_dot_kg_s)
    # 注意：为清晰起见，这里重新定义，并增加了质量流量 m_dot
    validation_data = [
        ("SCBC 1", "CO2", 7400.00, 35.00, 402.40, 1.66, 200.84, 1945.09),
        ("SCBC 2", "CO2", 24198.00, 121.73, 453.36, 1.68, 246.29, 1945.09),
        ("SCBC 3", "CO2", 24198.00, 281.92, 696.46, 2.21, 341.30, 2641.42),
        ("SCBC 4", "CO2", 24198.00, 417.94, 867.76, 2.48, 434.43, 2641.42),
        ("SCBC 5", "CO2", 24198.00, 599.85, 1094.91, 2.77, 579.03, 2641.42),
        ("SCBC 6", "CO2", 7400.00, 455.03, 932.38, 2.80, 409.40, 2641.42),
        ("SCBC 7", "CO2", 7400.00, 306.16, 761.08, 2.54, 312.52, 2641.42),
        ("SCBC 8", "CO2", 7400.00, 147.55, 582.06, 2.17, 235.75, 1945.09), # m_dot from table 10 for point 8
        ("SCBC 9", "CO2", 7400.00, 84.26, 503.44, 1.97, 214.69, 1945.09), # m_dot from table 10 for point 9
        ("ORC 09", "R245fa", 1500.00, 127.76, 505.35, 1.86, 61.21, 677.22),
        ("ORC 010", "R245fa", 445.10, 94.67, 485.51, 1.88, 37.52, 677.22),
        ("ORC 011", "R245fa", 445.10, 58.66, 278.39, 1.26, 5.40, 677.22),
        ("ORC 012", "R245fa", 1500.00, 59.37, 279.52, 1.26, 6.29, 677.22),
    ]

    output_csv_data = []
    csv_header = [
        "PointName", "Fluid",
        "P_kPa_paper", "T_C_paper",
        "h_kJ_kg_paper", "s_kJ_kgK_paper", "e_kJ_kg_paper",
        "m_dot_kg_s",
        "P_Pa_calc", "T_K_calc",
        "h_J_kg_calc", "s_J_kgK_calc", "d_kg_m3_calc", "e_J_kg_calc",
        "e_kJ_kg_calc", "e_diff_kJ_kg"
    ]
    output_csv_data.append(csv_header)

    print("\n详细状态点验证 (㶲对比):")
    print("="*120) # 增加了宽度以容纳新列
    print(f"{'状态点名':<18} {'流体':<6} {'P(kPa)':>8} {'T(C)':>7} {'h(kJ/kg)':>10} {'s(kJ/kgK)':>10} {'m_dot(kg/s)':>12} {'e_calc(kJ/kg)':>14} {'e_paper(kJ/kg)':>14} {'e_diff(kJ/kg)':>14}")
    print("-"*120) # 增加了宽度

    for name, fluid, p_kpa, t_c, h_kj_kg_paper, s_kj_kgk_paper, e_kj_kg_paper, m_dot_kg_s in validation_data:
        P_Pa = to_pascal(p_kpa, 'kpa')
        T_K = to_kelvin(t_c)
        
        current_state = StatePoint(fluid_name=fluid, name=name)
        current_state.props_from_PT(P_Pa, T_K)
        current_state.m_dot = m_dot_kg_s # 确保StatePoint对象也记录了m_dot

        e_calc_kj = current_state.e / 1000 if current_state.e is not None else float('nan')
        e_diff_kj = e_calc_kj - e_kj_kg_paper if current_state.e is not None else float('nan')

        # 增加了 m_dot_kg_s 的打印
        print(f"{name:<18} {fluid:<6} {p_kpa:>8.2f} {t_c:>7.2f} {current_state.h/1000 if current_state.h else 'N/A':>10.2f} {current_state.s/1000 if current_state.s else 'N/A':>10.4f} {m_dot_kg_s:>12.2f} {e_calc_kj:>14.2f} {e_kj_kg_paper:>14.2f} {e_diff_kj:>14.2f}")
        
        # 准备CSV行数据
        # csv_row 的内容已经包含了 m_dot_kg_s，无需更改
        csv_row = [
            name, fluid,
            p_kpa, t_c,
            h_kj_kg_paper, s_kj_kgk_paper, e_kj_kg_paper,
            m_dot_kg_s,
            current_state.P, current_state.T,
            current_state.h, current_state.s, current_state.d, current_state.e,
            e_calc_kj, e_diff_kj
        ]
        output_csv_data.append(csv_row)
    print("="*100)

    # 输出到CSV文件
    csv_filename = "calculated_state_points_from_table10.csv"
    try:
        import csv
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(output_csv_data)
        print(f"\n状态点数据已成功导出到: {csv_filename}")
    except Exception as e_csv:
        print(f"\n导出到CSV文件时出错: {e_csv}")

    # --- 以下是用于反推参考状态 T0 和 P0 的代码 ---
    # (这部分代码保持不变，但其 table10_data 定义与上面的 validation_data 重复，可以考虑复用)
    # (为了本次修改的聚焦，暂时不改动 run_t0_p0_fitting 内部的 table10_data)
import scipy.optimize

# 表10 SCBC/ORC系统优化后的状态点数据
# 结构: (name, fluid, P_kPa, T_C, h_kJ_kg, s_kJ_kgK, e_kJ_kg_paper)
table10_data = [
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
    """
    计算给定参考状态 T0, P0 时，各状态点计算㶲与论文㶲的误差。
    params_T0_P0: 包含 [T0_K, P0_Pa] 的数组
    data_points: 包含多个状态点数据的列表
    """
    T0_K_fit, P0_Pa_fit = params_T0_P0
    errors = []

    if T0_K_fit <= 0 or P0_Pa_fit <= 0: # 避免无效的物理参数
        return [1e6] * len(data_points) # 返回一个较大的误差值

    for point_name, fluid, P_kPa, T_C, h_kJ_kg, s_kJ_kgK, e_kJ_kg_paper in data_points:
        try:
            h0_J_kg = PropsSI('H', 'T', T0_K_fit, 'P', P0_Pa_fit, fluid)
            s0_J_kgK = PropsSI('S', 'T', T0_K_fit, 'P', P0_Pa_fit, fluid)

            # 将论文中的h和s转换为J/kg和J/kgK
            h_J_kg_paper = h_kJ_kg * 1000
            s_J_kgK_paper = s_kJ_kgK * 1000

            e_calc_J_kg = (h_J_kg_paper - h0_J_kg) - T0_K_fit * (s_J_kgK_paper - s0_J_kgK)
            e_calc_kJ_kg = e_calc_J_kg / 1000
            
            errors.append(e_calc_kJ_kg - e_kJ_kg_paper)
        except Exception as e:
            # print(f"Error calculating for {point_name} with T0={T0_K_fit-273.15:.2f}C, P0={P0_Pa_fit/1000:.2f}kPa: {e}")
            errors.append(1e6) # 如果计算出错，也返回一个较大的误差
    return errors

def run_t0_p0_fitting():
    print("\n--- 开始反推参考状态 T0 和 P0 ---")
    
    # 初始猜测值 (T0 in Kelvin, P0 in Pascal)
    initial_T0_K = 25.0 + 273.15
    initial_P0_Pa = 101.325 * 1000
    initial_params = [initial_T0_K, initial_P0_Pa]

    # 参数边界 (T0: 0C to 50C, P0: 80kPa to 120kPa)
    bounds_T0_P0 = ([273.15, 80000], [273.15 + 50, 120000])

    try:
        result = scipy.optimize.least_squares(
            exergy_error_func,
            initial_params,
            args=(table10_data,),
            bounds=bounds_T0_P0,
            verbose=1 # 0 for no output, 1 for termination report, 2 for detailed progress
        )

        if result.success:
            T0_fit_K, P0_fit_Pa = result.x
            print(f"\n优化成功!")
            print(f"  反推得到的参考温度 T0 = {T0_fit_K - 273.15:.2f} °C ({T0_fit_K:.2f} K)")
            print(f"  反推得到的参考压力 P0 = {P0_fit_Pa / 1000:.3f} kPa ({P0_fit_Pa:.0f} Pa)")

            print("\n使用反推的T0, P0重新计算各点㶲值与论文值的对比:")
            print("状态点名\t\t流体\t论文e (kJ/kg)\t计算e (kJ/kg)\t差值 (kJ/kg)")
            # 需要重新获取PropsSI，因为 exergy_error_func 内部的 T0_K, P0_Pa 是局部变量
            # 或者直接使用 result.fun (即误差)
            final_errors = result.fun # exergy_error_func([T0_fit_K, P0_fit_Pa], table10_data)
            for i, (point_name, fluid, _, _, _, _, e_kJ_kg_paper) in enumerate(table10_data):
                # 确保 final_errors[i] 是 e_calc - e_paper
                # 如果 exergy_error_func 返回的是这个差值，那么 e_calc = e_paper + final_errors[i]
                calc_e = e_kJ_kg_paper + final_errors[i] 
                print(f"{point_name:<18}\t{fluid:<6}\t{e_kJ_kg_paper:<12.2f}\t{calc_e:<14.2f}\t{final_errors[i]:<12.2f}")
            
            avg_abs_error = np.mean(np.abs(final_errors)) # 需要 import numpy as np
            print(f"\n平均绝对误差: {avg_abs_error:.3f} kJ/kg")
            print(f"均方根误差 (RMSE): {np.sqrt(np.mean(np.array(final_errors)**2)):.3f} kJ/kg")


        else:
            print(f"\n优化未成功: {result.message}")
    except ImportError:
        print("\n错误: 需要安装 scipy 库才能运行此反推功能。请运行 'pip install scipy'")
        print("您也可能需要 'pip install numpy' (如果脚本中其他地方未导入numpy)")
    except Exception as e_fit:
        print(f"\n运行反推时发生错误: {e_fit}")

# 为了使上面的平均绝对误差和RMSE计算工作，确保numpy已导入
# 如果脚本其他地方没有 import numpy as np，可以在文件顶部添加
# import numpy as np # 这一行已在脚本开头存在

# 修改 __main__ 部分以包含新的函数调用
# 找到原有的 if __name__ == "__main__": 部分并修改，或者确保它是这样调用的：
# (假设原有的验证代码在 if __name__ == "__main__": 块内或被一个main函数调用)

# 这是一个示例，说明如何修改或确保 __main__ 调用了新函数
# 如果脚本末尾没有 if __name__ == "__main__":，则可以直接添加：
# if __name__ == "__main__": (此行已被上面的新 __main__ 块替换)
    # ... (原有的状态点验证代码已被新的验证和CSV输出逻辑替换) ...
    
    # 之前的 run_t0_p0_fitting() 函数定义依然存在于文件末尾
    # 如果需要再次运行拟合，可以取消下面这行的注释：
    # run_t0_p0_fitting()
    print("\n--- 脚本执行完毕 ---")
