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

# 追赶法（Thomas算法）解三对角线性方程组
def thomas_algorithm(A, d):
    n = len(d)
    # 提取三对角元素
    a = np.zeros(n)  # 下对角线
    b = np.zeros(n)  # 主对角线
    c = np.zeros(n)  # 上对角线
    for i in range(n):
        b[i] = A[i, i]
        if i > 0:
            a[i] = A[i, i - 1]
        if i < n - 1:
            c[i] = A[i, i + 1]
    # 前向消元
    for i in range(1, n):
        m = a[i] / b[i - 1]
        b[i] = b[i] - m * c[i - 1]
        d[i] = d[i] - m * d[i - 1]
    # 回代
    x = np.zeros(n)
    x[-1] = d[-1] / b[-1]
    for i in reversed(range(n - 1)):
        x[i] = (d[i] - c[i] * x[i + 1]) / b[i]
    return x

if __name__ == "__main__":
    a, b = -1, 1
    n = 10
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)
    A, rhs = cubic_spline_system(x_nodes, y_nodes)

    # 用追赶法（Thomas算法）求解
    M = thomas_algorithm(A, rhs.copy())
    print("Thomas algorithm solution (second derivatives at nodes):")
    print(M)

# =========================
# 中文说明：
# 本代码实现了三次样条插值法中三对角线性方程组的追赶法（Thomas算法）求解。
# 1. cubic_spline_system函数构造自然边界三次样条插值的系数矩阵A和右端项b。
# 2. thomas_algorithm函数提取三对角矩阵的下、主、上对角线元素，进行前向消元和回代，得到方程组解。
# 3. 主程序部分给出节点、构造方程组并用追赶法求解，输出每个节点的二阶导数值。
# 4. 这些二阶导数可用于后续三次样条插值函数的构造。
# ========================= 