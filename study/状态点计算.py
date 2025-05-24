import numpy as np
from CoolProp.CoolProp import PropsSI

# --- 环境参考状态 (用于㶲计算) ---
T0_CELSIUS = 25.0
P0_KPA = 101.325

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

# 假设你的 StatePoint 类定义，to_pascal, to_kelvin 函数，以及 T0_K, P0_Pa 已经定义好了
# from your_module import StatePoint, to_pascal, to_kelvin, T0_K, P0_Pa
# 例如：
# T0_K = to_kelvin(25)
# P0_Pa = to_pascal(101.325, 'kpa')

print("--- 正在验证表10中的所有状态点 (假设P,T或P,Q已知) ---")

# --- SCBC 工质: CO2 ---
fluid_co2 = 'CO2'

# 点1
P1_Pa = to_pascal(7400.00, 'kpa')
T1_K = to_kelvin(35.00)
state1 = StatePoint(fluid_name=fluid_co2, name="SCBC点1 (主压气机入口)")
state1.props_from_PT(P1_Pa, T1_K)
state1.m_dot = 1945.09 # kg/s
print(state1)
print(f"表10预期: P=7400.00 kPa, T=35.00 C, h=402.40 kJ/kg, s=1.66 kJ/kgK, e=200.84 kJ/kg, q_m=1945.09 kg/s\n")

# 点2 (已在你的示例中)
P2_Pa = to_pascal(24198.00, 'kpa')
T2_K = to_kelvin(121.73)
state2 = StatePoint(fluid_name=fluid_co2, name="SCBC点2 (主压气机出口)")
state2.props_from_PT(P2_Pa, T2_K)
state2.m_dot = 1945.09
print(state2)
print(f"表10预期: P=24198.00 kPa, T=121.73 C, h=453.36 kJ/kg, s=1.68 kJ/kgK, e=246.29 kJ/kg, q_m=1945.09 kg/s\n")

# 点3
P3_Pa = to_pascal(24198.00, 'kpa')
T3_K = to_kelvin(281.92)
state3 = StatePoint(fluid_name=fluid_co2, name="SCBC点3 (再压气机出口/HTR冷端入口)")
state3.props_from_PT(P3_Pa, T3_K)
state3.m_dot = 2641.42 # 注意流量变化
print(state3)
print(f"表10预期: P=24198.00 kPa, T=281.92 C, h=696.46 kJ/kg, s=2.21 kJ/kgK, e=341.30 kJ/kg, q_m=2641.42 kg/s\n")

# 点4
P4_Pa = to_pascal(24198.00, 'kpa')
T4_K = to_kelvin(417.94)
state4 = StatePoint(fluid_name=fluid_co2, name="SCBC点4 (HTR冷端出口/ER入口)")
state4.props_from_PT(P4_Pa, T4_K)
state4.m_dot = 2641.42
print(state4)
print(f"表10预期: P=24198.00 kPa, T=417.94 C, h=867.76 kJ/kg, s=2.48 kJ/kgK, e=434.43 kJ/kg, q_m=2641.42 kg/s\n")

# 点5
P5_Pa = to_pascal(24198.00, 'kpa')
T5_K = to_kelvin(599.85)
state5 = StatePoint(fluid_name=fluid_co2, name="SCBC点5 (ER出口/透平入口)")
state5.props_from_PT(P5_Pa, T5_K)
state5.m_dot = 2641.42
print(state5)
print(f"表10预期: P=24198.00 kPa, T=599.85 C, h=1094.91 kJ/kg, s=2.77 kJ/kgK, e=579.03 kJ/kg, q_m=2641.42 kg/s\n")

# 点6
P6_Pa = to_pascal(7400.00, 'kpa')
T6_K = to_kelvin(455.03)
state6 = StatePoint(fluid_name=fluid_co2, name="SCBC点6 (透平出口/HTR热端入口)")
state6.props_from_PT(P6_Pa, T6_K)
state6.m_dot = 2641.42
print(state6)
print(f"表10预期: P=7400.00 kPa, T=455.03 C, h=932.38 kJ/kg, s=2.80 kJ/kgK, e=409.40 kJ/kg, q_m=2641.42 kg/s\n")

# 点7
P7_Pa = to_pascal(7400.00, 'kpa')
T7_K = to_kelvin(306.16)
state7 = StatePoint(fluid_name=fluid_co2, name="SCBC点7 (HTR热端出口/LTR热端入口)")
state7.props_from_PT(P7_Pa, T7_K)
state7.m_dot = 2641.42
print(state7)
print(f"表10预期: P=7400.00 kPa, T=306.16 C, h=761.08 kJ/kg, s=2.54 kJ/kgK, e=312.52 kJ/kg, q_m=2641.42 kg/s\n")

# 点8
P8_Pa = to_pascal(7400.00, 'kpa')
T8_K = to_kelvin(147.55)
state8 = StatePoint(fluid_name=fluid_co2, name="SCBC点8 (LTR热端出口/再压气机入口)")
state8.props_from_PT(P8_Pa, T8_K)
state8.m_dot = 1945.09 # 注意流量变化 (分流点之后)
print(state8)
print(f"表10预期: P=7400.00 kPa, T=147.55 C, h=582.06 kJ/kg, s=2.17 kJ/kgK, e=235.75 kJ/kg, q_m=1945.09 kg/s\n")

# 点9
P9_Pa = to_pascal(7400.00, 'kpa')
T9_K = to_kelvin(84.26)
state9 = StatePoint(fluid_name=fluid_co2, name="SCBC点9 (LTR冷端出口/混合点)") # 也可能是GO入口
state9.props_from_PT(P9_Pa, T9_K)
state9.m_dot = 1945.09 # TODO: 这里的流量 q_m 在表中点9是1945.09，但这点应该是从LTR冷端流向GO的流量
                       # 或者是 LTR 热端出口分流后去往 GO 的那部分？
                       # 查图3a: 点9是LTR热端出口流向GO的。点8是LTR热端出口流向RC的。
                       # 表10中点8和点9的q_m是不同的，这点需要注意，似乎与图不完全对应。
                       # 假设点9是CO2流经GO之前的状态
                       # 表10的点9 (CO2): P=7400 kPa, T=84.26 C, h=503.44, s=1.97, e=214.69, qm=1945.09
                       # 这应该是CO2在GO（气体冷却器/ORC蒸发器）的入口状态
print(state9)
print(f"表10预期 (CO2点9): P=7400.00 kPa, T=84.26 C, h=503.44 kJ/kg, s=1.97 kJ/kgK, e=214.69 kJ/kg, q_m=1945.09 kg/s\n")


# --- ORC 工质: R245fa ---
fluid_r245fa = 'R245fa'

# 点09 (已在你的示例中)
P09_Pa = to_pascal(1500.00, 'kpa')
T09_K = to_kelvin(127.76)
state09_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点09 (ORC透平入口)")
state09_orc.props_from_PT(P09_Pa, T09_K)
state09_orc.m_dot = 677.22
print(state09_orc)
print(f"表10预期: P=1500.00 kPa, T=127.76 C, h=505.35 kJ/kg, s=1.86 kJ/kgK, e=61.21 kJ/kg, q_m=677.22 kg/s\n")

# 点010
P010_Pa = to_pascal(445.10, 'kpa')
T010_K = to_kelvin(94.67)
state010_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点010 (ORC透平出口)")
state010_orc.props_from_PT(P010_Pa, T010_K)
state010_orc.m_dot = 677.22
print(state010_orc)
print(f"表10预期: P=445.10 kPa, T=94.67 C, h=485.51 kJ/kg, s=1.88 kJ/kgK, e=37.52 kJ/kg, q_m=677.22 kg/s\n")

# 点011 (已在你的示例中, 但这里用P,T)
P011_Pa = to_pascal(445.10, 'kpa')
T011_K = to_kelvin(58.66) # 表中直接给了温度
state011_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点011 (ORC冷凝器出口)")
# 验证是否接近饱和液体
# state011_orc_PQ = StatePoint(fluid_name=fluid_r245fa, name="ORC点011 (PQ法)")
# state011_orc_PQ.props_from_PQ(P011_Pa, 0)
# print("PQ法计算011:", state011_orc_PQ) # 输出 T 应该是 58.66 C 左右
state011_orc.props_from_PT(P011_Pa, T011_K) # 使用表中的P,T
state011_orc.m_dot = 677.22
print(state011_orc)
print(f"表10预期: P=445.10 kPa, T=58.66 C, h=278.39 kJ/kg, s=1.26 kJ/kgK, e=5.40 kJ/kg, q_m=677.22 kg/s\n")

# 点012
P012_Pa = to_pascal(1500.00, 'kpa')
T012_K = to_kelvin(59.37)
state012_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点012 (ORC泵出口)")
state012_orc.props_from_PT(P012_Pa, T012_K)
state012_orc.m_dot = 677.22
print(state012_orc)
print(f"表10预期: P=1500.00 kPa, T=59.37 C, h=279.52 kJ/kg, s=1.26 kJ/kgK, e=6.29 kJ/kg, q_m=677.22 kg/s\n")

# 假设你的 StatePoint 类定义，to_pascal, to_kelvin 函数，以及 T0_K, P0_Pa 已经定义好了
# from your_module import StatePoint, to_pascal, to_kelvin, T0_K, P0_Pa
# 例如：
# T0_K = to_kelvin(25)
# P0_Pa = to_pascal(101.325, 'kpa')

print("--- 正在验证表10中的所有状态点 (假设P,T或P,Q已知) ---")

# --- SCBC 工质: CO2 ---
fluid_co2 = 'CO2'

# 点1
P1_Pa = to_pascal(7400.00, 'kpa')
T1_K = to_kelvin(35.00)
state1 = StatePoint(fluid_name=fluid_co2, name="SCBC点1 (主压气机入口)")
state1.props_from_PT(P1_Pa, T1_K)
state1.m_dot = 1945.09 # kg/s
print(state1)
print(f"表10预期: P=7400.00 kPa, T=35.00 C, h=402.40 kJ/kg, s=1.66 kJ/kgK, e=200.84 kJ/kg, q_m=1945.09 kg/s\n")

# 点2 (已在你的示例中)
P2_Pa = to_pascal(24198.00, 'kpa')
T2_K = to_kelvin(121.73)
state2 = StatePoint(fluid_name=fluid_co2, name="SCBC点2 (主压气机出口)")
state2.props_from_PT(P2_Pa, T2_K)
state2.m_dot = 1945.09
print(state2)
print(f"表10预期: P=24198.00 kPa, T=121.73 C, h=453.36 kJ/kg, s=1.68 kJ/kgK, e=246.29 kJ/kg, q_m=1945.09 kg/s\n")

# 点3
P3_Pa = to_pascal(24198.00, 'kpa')
T3_K = to_kelvin(281.92)
state3 = StatePoint(fluid_name=fluid_co2, name="SCBC点3 (再压气机出口/HTR冷端入口)")
state3.props_from_PT(P3_Pa, T3_K)
state3.m_dot = 2641.42 # 注意流量变化
print(state3)
print(f"表10预期: P=24198.00 kPa, T=281.92 C, h=696.46 kJ/kg, s=2.21 kJ/kgK, e=341.30 kJ/kg, q_m=2641.42 kg/s\n")

# 点4
P4_Pa = to_pascal(24198.00, 'kpa')
T4_K = to_kelvin(417.94)
state4 = StatePoint(fluid_name=fluid_co2, name="SCBC点4 (HTR冷端出口/ER入口)")
state4.props_from_PT(P4_Pa, T4_K)
state4.m_dot = 2641.42
print(state4)
print(f"表10预期: P=24198.00 kPa, T=417.94 C, h=867.76 kJ/kg, s=2.48 kJ/kgK, e=434.43 kJ/kg, q_m=2641.42 kg/s\n")

# 点5
P5_Pa = to_pascal(24198.00, 'kpa')
T5_K = to_kelvin(599.85)
state5 = StatePoint(fluid_name=fluid_co2, name="SCBC点5 (ER出口/透平入口)")
state5.props_from_PT(P5_Pa, T5_K)
state5.m_dot = 2641.42
print(state5)
print(f"表10预期: P=24198.00 kPa, T=599.85 C, h=1094.91 kJ/kg, s=2.77 kJ/kgK, e=579.03 kJ/kg, q_m=2641.42 kg/s\n")

# 点6
P6_Pa = to_pascal(7400.00, 'kpa')
T6_K = to_kelvin(455.03)
state6 = StatePoint(fluid_name=fluid_co2, name="SCBC点6 (透平出口/HTR热端入口)")
state6.props_from_PT(P6_Pa, T6_K)
state6.m_dot = 2641.42
print(state6)
print(f"表10预期: P=7400.00 kPa, T=455.03 C, h=932.38 kJ/kg, s=2.80 kJ/kgK, e=409.40 kJ/kg, q_m=2641.42 kg/s\n")

# 点7
P7_Pa = to_pascal(7400.00, 'kpa')
T7_K = to_kelvin(306.16)
state7 = StatePoint(fluid_name=fluid_co2, name="SCBC点7 (HTR热端出口/LTR热端入口)")
state7.props_from_PT(P7_Pa, T7_K)
state7.m_dot = 2641.42
print(state7)
print(f"表10预期: P=7400.00 kPa, T=306.16 C, h=761.08 kJ/kg, s=2.54 kJ/kgK, e=312.52 kJ/kg, q_m=2641.42 kg/s\n")

# 点8
P8_Pa = to_pascal(7400.00, 'kpa')
T8_K = to_kelvin(147.55)
state8 = StatePoint(fluid_name=fluid_co2, name="SCBC点8 (LTR热端出口/再压气机入口)")
state8.props_from_PT(P8_Pa, T8_K)
state8.m_dot = 1945.09 # 注意流量变化 (分流点之后)
print(state8)
print(f"表10预期: P=7400.00 kPa, T=147.55 C, h=582.06 kJ/kg, s=2.17 kJ/kgK, e=235.75 kJ/kg, q_m=1945.09 kg/s\n")

# 点9
P9_Pa = to_pascal(7400.00, 'kpa')
T9_K = to_kelvin(84.26)
state9 = StatePoint(fluid_name=fluid_co2, name="SCBC点9 (LTR冷端出口/混合点)") # 也可能是GO入口
state9.props_from_PT(P9_Pa, T9_K)
state9.m_dot = 1945.09 # TODO: 这里的流量 q_m 在表中点9是1945.09，但这点应该是从LTR冷端流向GO的流量
                       # 或者是 LTR 热端出口分流后去往 GO 的那部分？
                       # 查图3a: 点9是LTR热端出口流向GO的。点8是LTR热端出口流向RC的。
                       # 表10中点8和点9的q_m是不同的，这点需要注意，似乎与图不完全对应。
                       # 假设点9是CO2流经GO之前的状态
                       # 表10的点9 (CO2): P=7400 kPa, T=84.26 C, h=503.44, s=1.97, e=214.69, qm=1945.09
                       # 这应该是CO2在GO（气体冷却器/ORC蒸发器）的入口状态
print(state9)
print(f"表10预期 (CO2点9): P=7400.00 kPa, T=84.26 C, h=503.44 kJ/kg, s=1.97 kJ/kgK, e=214.69 kJ/kg, q_m=1945.09 kg/s\n")


# --- ORC 工质: R245fa ---
fluid_r245fa = 'R245fa'

# 点09 (已在你的示例中)
P09_Pa = to_pascal(1500.00, 'kpa')
T09_K = to_kelvin(127.76)
state09_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点09 (ORC透平入口)")
state09_orc.props_from_PT(P09_Pa, T09_K)
state09_orc.m_dot = 677.22
print(state09_orc)
print(f"表10预期: P=1500.00 kPa, T=127.76 C, h=505.35 kJ/kg, s=1.86 kJ/kgK, e=61.21 kJ/kg, q_m=677.22 kg/s\n")

# 点010
P010_Pa = to_pascal(445.10, 'kpa')
T010_K = to_kelvin(94.67)
state010_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点010 (ORC透平出口)")
state010_orc.props_from_PT(P010_Pa, T010_K)
state010_orc.m_dot = 677.22
print(state010_orc)
print(f"表10预期: P=445.10 kPa, T=94.67 C, h=485.51 kJ/kg, s=1.88 kJ/kgK, e=37.52 kJ/kg, q_m=677.22 kg/s\n")

# 点011 (已在你的示例中, 但这里用P,T)
P011_Pa = to_pascal(445.10, 'kpa')
T011_K = to_kelvin(58.66) # 表中直接给了温度
state011_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点011 (ORC冷凝器出口)")
# 验证是否接近饱和液体
# state011_orc_PQ = StatePoint(fluid_name=fluid_r245fa, name="ORC点011 (PQ法)")
# state011_orc_PQ.props_from_PQ(P011_Pa, 0)
# print("PQ法计算011:", state011_orc_PQ) # 输出 T 应该是 58.66 C 左右
state011_orc.props_from_PT(P011_Pa, T011_K) # 使用表中的P,T
state011_orc.m_dot = 677.22
print(state011_orc)
print(f"表10预期: P=445.10 kPa, T=58.66 C, h=278.39 kJ/kg, s=1.26 kJ/kgK, e=5.40 kJ/kg, q_m=677.22 kg/s\n")

# 点012
P012_Pa = to_pascal(1500.00, 'kpa')
T012_K = to_kelvin(59.37)
state012_orc = StatePoint(fluid_name=fluid_r245fa, name="ORC点012 (ORC泵出口)")
state012_orc.props_from_PT(P012_Pa, T012_K)
state012_orc.m_dot = 677.22
print(state012_orc)
print(f"表10预期: P=1500.00 kPa, T=59.37 C, h=279.52 kJ/kg, s=1.26 kJ/kgK, e=6.29 kJ/kg, q_m=677.22 kg/s\n")

