import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial.legendre import leggauss

# 目标函数
def f(x):
    return 1 / (1 + 25 * x ** 2)

# 生成等分节点
def equidistant_nodes(a, b, n):
    return np.linspace(a, b, n + 1)

# 生成切比雪夫节点
def chebyshev_nodes(a, b, n):
    k = np.arange(0, n + 1)
    x_cheb = np.cos((2 * k + 1) * np.pi / (2 * n + 2))
    return 0.5 * (b - a) * x_cheb + 0.5 * (a + b)

# 生成勒让德节点
def legendre_nodes(a, b, n):
    x_leg, _ = leggauss(n + 1)
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

    # 生成三种节点
    x_equi = equidistant_nodes(a, b, n)
    x_cheb = chebyshev_nodes(a, b, n)
    x_leg = legendre_nodes(a, b, n)

    y_equi = f(x_equi)
    y_cheb = f(x_cheb)
    y_leg = f(x_leg)

    # 密集点
    x_dense = np.linspace(a, b, 1000)
    y_true = f(x_dense)

    # 三种插值
    y_interp_equi = lagrange_interpolation(x_equi, y_equi, x_dense)
    y_interp_cheb = lagrange_interpolation(x_cheb, y_cheb, x_dense)
    y_interp_leg = lagrange_interpolation(x_leg, y_leg, x_dense)

    # 误差
    error_equi = np.abs(y_true - y_interp_equi)
    error_cheb = np.abs(y_true - y_interp_cheb)
    error_leg = np.abs(y_true - y_interp_leg)

    # 最大误差
    max_error_equi = np.max(error_equi)
    max_error_cheb = np.max(error_cheb)
    max_error_leg = np.max(error_leg)

    # 均方误差
    mse_equi = np.mean(error_equi ** 2)
    mse_cheb = np.mean(error_cheb ** 2)
    mse_leg = np.mean(error_leg ** 2)

    # 输出误差指标
    print("Max error (Equidistant nodes):", max_error_equi)
    print("Max error (Chebyshev nodes):", max_error_cheb)
    print("Max error (Legendre nodes):", max_error_leg)
    print("MSE (Equidistant nodes):", mse_equi)
    print("MSE (Chebyshev nodes):", mse_cheb)
    print("MSE (Legendre nodes):", mse_leg)

    # 绘制误差曲线
    plt.figure(figsize=(10, 6))
    plt.plot(x_dense, error_equi, label="Equidistant nodes")
    plt.plot(x_dense, error_cheb, label="Chebyshev nodes")
    plt.plot(x_dense, error_leg, label="Legendre nodes")
    plt.yscale('log')
    plt.legend()
    plt.title(f"Interpolation error comparison (n={n})")
    plt.xlabel("x")
    plt.ylabel("Absolute error (log scale)")
    plt.grid(True)
    plt.show()

# =========================
# 中文说明与分析：
# 本代码比较了等分节点、切比雪夫节点、勒让德节点三种Lagrange插值的误差，并给出了最大误差和均方误差的数值指标。
# 1. 最大误差（max error）反映了插值多项式与原函数在整个区间内最不精确的点的误差。
# 2. 均方误差（MSE）反映了插值多项式与原函数在整个区间内的整体拟合优劣。
# 3. 从输出结果和误差曲线可以看出：
#    - 等分节点的插值在区间两端误差较大，最大误差和均方误差通常也较大，容易出现龙格现象。
#    - 切比雪夫节点和勒让德节点的插值误差明显小于等分节点，尤其在区间两端表现更好，最大误差和均方误差都更低。
#    - 切比雪夫节点和勒让德节点的插值精度相近，均优于等分节点。
# 4. 你可以修改n的值，观察不同插值次数下的误差对比和数值指标变化。
# =========================