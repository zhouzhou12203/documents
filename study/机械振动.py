import numpy as np
import matplotlib.pyplot as plt

# 定义函数
def delta_omega(r, zeta, N):
    """计算 Delta(omega)"""
    return np.sqrt((1 - r**2)**2 + (2 * zeta * r * (1 + 1/N - r**2 / N))**2)

def X_X0(r, zeta, N):
    """计算 X/X0"""
    delta = delta_omega(r, zeta, N)
    return (1 / delta) * np.sqrt(1 + (2 * zeta * r / N)**2)

def absX_Y0(r, zeta, N):
    """计算 |X|/Y0"""
    delta = delta_omega(r, zeta, N)
    return (1 / delta) * np.sqrt(1 + (2 * zeta *  (1 + 1/N) * r)**2)

def damped_sDOF(r, zeta):
    """有阻尼单自由度系统的幅频响应"""
    return 1 / np.sqrt((1 - r**2)**2 + (2 * zeta * r)**2)

# 参数设置
N = 5  # 可以修改 N 值
zeta_values = [0, 0.1, 0.3,1]  # 阻尼比
r_values = np.linspace(0.1, 5, 200)  # 频率比范围

# 绘图：X/X0 随频率比变化
plt.figure(figsize=(10, 10))
for zeta in zeta_values:
    X_X0_values = X_X0(r_values, zeta, N)
    plt.plot(r_values, X_X0_values, label=f'ζ = {zeta}')
    sDOF_values = damped_sDOF(r_values, zeta)
    plt.plot(r_values, sDOF_values, label=f'SDOF ζ = {zeta}', linestyle='--') # 用虚线区分

plt.xlabel('Frequency Ratio r (ω/ωn)') # 横坐标：频率比
plt.ylabel('X/X0')
plt.title('X/X0 vs Frequency Ratio (Different Damping Ratios)')
plt.grid(True)
plt.legend()
plt.xlim(0, 5)  # 设置 x 轴范围
plt.ylim(0, 10)  # 设置 y 轴范围
plt.show()

# 绘图：|X|/Y0 随频率比变化
plt.figure(figsize=(10, 6))
for zeta in zeta_values:
    absX_Y0_values = absX_Y0(r_values, zeta, N)
    plt.plot(r_values, absX_Y0_values, label=f'ζ = {zeta}')
    sDOF_values = damped_sDOF(r_values, zeta)
    plt.plot(r_values, sDOF_values, label=f'SDOF ζ = {zeta}', linestyle='--') # 用虚线区分

plt.xlabel('Frequency Ratio r (ω/ωn)') # 横坐标：频率比
plt.ylabel('|X|/Y0')
plt.title('|X|/Y0 vs Frequency Ratio (Different Damping Ratios)')
plt.grid(True)
plt.legend()
plt.xlim(0, 5)  # 设置 x 轴范围
plt.ylim(0, 10)  # 设置 y 轴范围
plt.show()
