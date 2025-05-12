import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

# Target function
def f(x):
    return 1 / (1 + 25 * x ** 2)

# Generate equidistant nodes
def equidistant_nodes(a, b, n):
    return np.linspace(a, b, n + 1)

# Lagrange interpolation
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

# Newton interpolation
def divided_differences(x, y):
    n = len(x)
    coef = np.copy(y)
    for j in range(1, n):
        coef[j:n] = (coef[j:n] - coef[j-1:n-1]) / (x[j:n] - x[0:n-j])
    return coef

def newton_interpolation(x, coef, x_eval):
    n = len(coef)
    p = np.zeros_like(x_eval)
    for i in range(len(x_eval)):
        temp = coef[-1]
        for k in range(n-2, -1, -1):
            temp = temp * (x_eval[i] - x[k]) + coef[k]
        p[i] = temp
    return p

if __name__ == "__main__":
    a, b = -1, 1
    n = 10  # Interpolation degree, can be adjusted
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)

    # Interpolation
    x_plot = np.linspace(a, b, 500)
    y_true = f(x_plot)
    y_lagrange = lagrange_interpolation(x_nodes, y_nodes, x_plot)
    coef_newton = divided_differences(x_nodes, y_nodes)
    y_newton = newton_interpolation(x_nodes, coef_newton, x_plot)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(x_plot, y_true, label="Original function", linewidth=2)
    plt.plot(x_plot, y_lagrange, '--', label="Lagrange interpolation")
    plt.plot(x_plot, y_newton, ':', label="Newton interpolation")
    plt.scatter(x_nodes, y_nodes, color='red', zorder=5, label="Interpolation nodes")
    plt.legend()
    plt.title(f"Lagrange and Newton interpolation with equidistant nodes (n={n})")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)
    plt.show()

# =========================
# 中文注释说明：
# 本代码实现了在区间[-1, 1]上，使用等分节点对函数f(x)=1/(1+25x^2)进行插值。
# 1. 通过Lagrange插值法和Newton插值法分别构造插值多项式。
# 2. 绘制了原函数曲线、Lagrange插值曲线、Newton插值曲线，以及插值节点。
# 3. 图像中，Original function为原函数，Lagrange interpolation为拉格朗日插值，Newton interpolation为牛顿插值，Interpolation nodes为插值节点。
# 4. 通过对比三条曲线，可以观察插值多项式与原函数的拟合效果。
# 5. 你可以修改n的值，观察不同插值次数下的插值效果。
# ========================= 