import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial.legendre import leggauss

# 目标函数
def f(x):
    return 1 / (1 + 25 * x ** 2)

# 生成勒让德多项式的根（高斯-勒让德节点）
def legendre_nodes(a, b, n):
    # leggauss返回n个节点和权重，节点在[-1,1]区间
    x_leg, _ = leggauss(n + 1)
    # 节点映射到[a, b]
    return 0.5 * (b - a) * x_leg + 0.5 * (a + b)

# Lagrange插值
def lagrange_interpolation(x, y, x_eval):
    n = len(x)
    L = np.zeros_like(x_eval)
    for k in range(n):
        l = np.ones_like(x_eval)
        for j in range(n):
            if j != k:
                l *= (x_eval - x[j]) / (x[k] - x[j])
        L += y[k] * l
    return L

if __name__ == "__main__":
    a, b = -1, 1
    n = 10  # 插值次数，可自行调整
    x_nodes = legendre_nodes(a, b, n)
    y_nodes = f(x_nodes)

    # 计算插值
    x_plot = np.linspace(a, b, 500)
    y_true = f(x_plot)
    y_lagrange = lagrange_interpolation(x_nodes, y_nodes, x_plot)

    # 绘图
    plt.figure(figsize=(10, 6))
    plt.plot(x_plot, y_true, label="Original function", linewidth=2)
    plt.plot(x_plot, y_lagrange, '--', label="Lagrange interpolation (Legendre nodes)")
    plt.scatter(x_nodes, y_nodes, color='red', zorder=5, label="Interpolation nodes")
    plt.legend()
    plt.title(f"Lagrange interpolation with Legendre nodes (n={n})")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)
    plt.show()

# =========================
# 中文说明：
# 本代码在区间[-1, 1]上，使用勒让德多项式的根（高斯-勒让德节点）作为插值节点，对函数f(x)=1/(1+25x^2)进行Lagrange插值。
# 1. 通过legendre_nodes函数生成n+1个勒让德节点，并计算对应的函数值。
# 2. 使用Lagrange插值法构造插值多项式。
# 3. 在较密集的x点上分别计算原函数值和插值多项式的值。
# 4. 绘制原函数曲线、Lagrange插值曲线和插值节点，图像中的注释均为英文。
# 5. 通过对比两条曲线，可以观察勒让德节点下插值多项式对原函数的拟合效果。
# 6. 你可以修改n的值，观察不同插值次数下的插值效果。
# ========================= 