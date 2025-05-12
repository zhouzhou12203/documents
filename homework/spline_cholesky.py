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
    # 构造系数矩阵A和右端项b
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

# Cholesky分解
def cholesky_decomposition(A):
    n = A.shape[0]
    L = np.zeros_like(A)
    for i in range(n):
        for j in range(i + 1):
            temp_sum = np.dot(L[i, :j], L[j, :j])
            if i == j:
                L[i, j] = np.sqrt(A[i, i] - temp_sum)
            else:
                L[i, j] = (A[i, j] - temp_sum) / L[j, j]
    return L

# 利用Cholesky分解解方程组
def cholesky_solve(A, b):
    L = cholesky_decomposition(A)
    # 先解Ly = b
    y = np.zeros_like(b)
    for i in range(len(b)):
        y[i] = (b[i] - np.dot(L[i, :i], y[:i])) / L[i, i]
    # 再解L^T x = y
    x = np.zeros_like(b)
    LT = L.T
    for i in reversed(range(len(b))):
        x[i] = (y[i] - np.dot(LT[i, i + 1:], x[i + 1:])) / LT[i, i]
    return x

if __name__ == "__main__":
    a, b = -1, 1
    n = 10  # 节点数-1
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)

    # 构造三次样条方程组
    A, rhs = cubic_spline_system(x_nodes, y_nodes)

    # Cholesky分解求解
    M = cholesky_solve(A, rhs)

    print("Cholesky decomposition solution (second derivatives at nodes):")
    print(M)

# =========================
# 中文说明：
# 本代码实现了三次样条插值法中三对角线性方程组的Cholesky分解与求解。
# 1. cubic_spline_system函数构造自然边界三次样条插值的系数矩阵A和右端项b。
# 2. cholesky_decomposition函数实现了对称正定矩阵的Cholesky分解，返回下三角矩阵L。
# 3. cholesky_solve函数利用Cholesky分解，先解Ly=b，再解L^T x=y，得到方程组解。
# 4. 主程序部分给出节点、构造方程组并用Cholesky分解法求解，输出每个节点的二阶导数值。
# 5. 这些二阶导数可用于后续三次样条插值函数的构造。
# ========================= 