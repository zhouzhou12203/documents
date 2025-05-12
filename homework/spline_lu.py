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

# LU分解：L为单位下三角，U为上三角
def lu_decomposition_unit_lower(A):
    n = A.shape[0]
    L = np.eye(n)
    U = np.zeros_like(A)
    for i in range(n):
        for j in range(i, n):
            U[i, j] = A[i, j] - np.dot(L[i, :i], U[:i, j])
        for j in range(i + 1, n):
            L[j, i] = (A[j, i] - np.dot(L[j, :i], U[:i, i])) / U[i, i]
    return L, U

# LU分解：U为单位上三角，L为下三角
def lu_decomposition_unit_upper(A):
    n = A.shape[0]
    L = np.zeros_like(A)
    U = np.eye(n)
    for i in range(n):
        for j in range(i + 1):
            L[i, j] = A[i, j] - np.dot(L[i, :j], U[:j, j])
        for j in range(i + 1, n):
            U[i, j] = (A[i, j] - np.dot(L[i, :i], U[:i, j])) / L[i, i]
    return L, U

# 利用LU分解解方程组
def lu_solve(L, U, b, unit_lower=True):
    n = len(b)
    # 先解Ly = b
    y = np.zeros_like(b)
    if unit_lower:
        for i in range(n):
            y[i] = b[i] - np.dot(L[i, :i], y[:i])
    else:
        for i in range(n):
            y[i] = (b[i] - np.dot(L[i, :i], y[:i])) / L[i, i]
    # 再解Ux = y
    x = np.zeros_like(b)
    if unit_lower:
        for i in reversed(range(n)):
            x[i] = (y[i] - np.dot(U[i, i + 1:], x[i + 1:])) / U[i, i]
    else:
        for i in reversed(range(n)):
            x[i] = y[i] - np.dot(U[i, i + 1:], x[i + 1:])
    return x

if __name__ == "__main__":
    a, b = -1, 1
    n = 10
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)
    A, rhs = cubic_spline_system(x_nodes, y_nodes)

    # 第一种LU分解
    L1, U1 = lu_decomposition_unit_lower(A)
    x1 = lu_solve(L1, U1, rhs, unit_lower=True)
    print("Solution with L unit lower, U upper:")
    print(x1)

    # 第二种LU分解
    L2, U2 = lu_decomposition_unit_upper(A)
    x2 = lu_solve(L2, U2, rhs, unit_lower=False)
    print("Solution with L lower, U unit upper:")
    print(x2)

# =========================
# 中文说明：
# 本代码实现了三次样条插值法中三对角线性方程组的两种LU分解与求解。
# 1. 第一种LU分解：L为单位下三角矩阵，U为上三角矩阵。
# 2. 第二种LU分解：L为下三角矩阵，U为单位上三角矩阵。
# 3. lu_solve函数分别适配两种分解方式，先解Ly=b，再解Ux=y。
# 4. 主程序部分给出节点、构造方程组并用两种LU分解法求解，输出每个节点的二阶导数值。
# 5. 这些二阶导数可用于后续三次样条插值函数的构造。
# ========================= 