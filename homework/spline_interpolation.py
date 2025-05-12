import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# 目标函数
def f(x):
    return 1 / (1 + 25 * x ** 2)

# 生成等分节点
def equidistant_nodes(a, b, n):
    return np.linspace(a, b, n + 1)

if __name__ == "__main__":
    a, b = -1, 1
    n = 10  # 插值节点数-1，可自行调整
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)

    # 构造三次样条插值（自然边界条件）
    cs = CubicSpline(x_nodes, y_nodes, bc_type='natural')

    # 生成用于绘图的点
    x_plot = np.linspace(a, b, 500)
    y_true = f(x_plot)
    y_spline = cs(x_plot)

    # 绘图
    plt.figure(figsize=(10, 6))
    plt.plot(x_plot, y_true, label="Original function", linewidth=2)
    plt.plot(x_plot, y_spline, '--', label="Cubic spline interpolation")
    plt.scatter(x_nodes, y_nodes, color='red', zorder=5, label="Interpolation nodes")
    plt.legend()
    plt.title(f"Cubic spline interpolation with equidistant nodes (n={n})")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)
    plt.show()

# =========================
# 中文说明：
# 本代码在区间[-1, 1]上，使用等分节点对函数f(x)=1/(1+25x^2)进行三次样条插值（自然边界）。
# 1. 首先生成n+1个等分节点，并计算对应的函数值。
# 2. 使用scipy库的CubicSpline类，构造三次样条插值函数。
# 3. 在较密集的x点上分别计算原函数值和样条插值值。
# 4. 绘制原函数曲线、三次样条插值曲线和插值节点，图像中的注释均为英文。
# 5. 通过对比两条曲线，可以观察三次样条插值对原函数的拟合效果。
# 6. 你可以修改n的值，观察不同插值节点数下的插值效果。
# ========================= 