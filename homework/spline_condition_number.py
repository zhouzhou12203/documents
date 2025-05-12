import numpy as np

# 目标函数
def f(x):
    return 1 / (1 + 25 * x ** 2)

# 生成等分节点
def equidistant_nodes(a, b, n):
    return np.linspace(a, b, n + 1)

# 构造三次样条插值的三对角线性方程组（自然边界条件）
def cubic_spline_system(x, y):
    n = len(x) - 1
    h = np.diff(x)
    A = np.zeros((n + 1, n + 1))
    b = np.zeros(n + 1)
    A[0, 0] = 1
    A[n, n] = 1
    for i in range(1, n):
        A[i, i - 1] = h[i - 1]
        A[i, i] = 2 * (h[i - 1] + h[i])
        A[i, i + 1] = h[i]
        b[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    return A, b

if __name__ == "__main__":
    a, b = -1, 1
    n = 10
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)
    A, rhs = cubic_spline_system(x_nodes, y_nodes)

    # 计算不同范数下的条件数
    cond_inf = np.linalg.cond(A, np.inf)
    cond_1 = np.linalg.cond(A, 1)
    cond_2 = np.linalg.cond(A, 2)

    print("Condition number (infinity norm):", cond_inf)
    print("Condition number (1-norm):", cond_1)
    print("Condition number (2-norm):", cond_2)

# =========================
# 中文说明：
# 本代码计算了三次样条插值法中三对角线性方程组系数矩阵A在不同范数下的条件数。
# 1. cond_inf为无穷范数（行和范数）下的条件数。
# 2. cond_1为1-范数（列和范数）下的条件数。
# 3. cond_2为2-范数（谱范数）下的条件数。
# 4. 条件数越大，说明矩阵越接近奇异，数值解的稳定性越差。
# 5. 你可以修改n的值，观察不同插值节点数下条件数的变化。
# ========================= 