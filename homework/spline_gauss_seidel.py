import numpy as np
import matplotlib.pyplot as plt

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

# 判断Gauss-Seidel迭代是否收敛（严格对角占优或谱半径）
def is_gauss_seidel_convergent(A):
    # 严格对角占优判据
    diag = np.abs(np.diag(A))
    off_diag_sum = np.sum(np.abs(A), axis=1) - diag
    if np.all(diag > off_diag_sum):
        return True, "Strictly diagonally dominant"
    # 谱半径判据
    D = np.diag(np.diag(A))
    L = np.tril(A, -1)
    U = np.triu(A, 1)
    G = -np.linalg.inv(D + L) @ U
    eigvals = np.linalg.eigvals(G)
    spectral_radius = max(abs(eigvals))
    return spectral_radius < 1, f"Spectral radius = {spectral_radius:.4f}"

# Gauss-Seidel迭代
def gauss_seidel_iteration(A, b, x0=None, tol=1e-10, max_iter=500):
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    residuals = []
    for k in range(max_iter):
        x_new = x.copy()
        for i in range(n):
            s1 = np.dot(A[i, :i], x_new[:i])
            s2 = np.dot(A[i, i+1:], x[i+1:])
            x_new[i] = (b[i] - s1 - s2) / A[i, i]
        res = np.linalg.norm(np.dot(A, x_new) - b, ord=np.inf)
        residuals.append(res)
        if res < tol:
            break
        x = x_new
    return x, residuals

if __name__ == "__main__":
    a, b = -1, 1
    n = 10
    x_nodes = equidistant_nodes(a, b, n)
    y_nodes = f(x_nodes)
    A, rhs = cubic_spline_system(x_nodes, y_nodes)

    # 判断Gauss-Seidel迭代是否收敛
    convergent, reason = is_gauss_seidel_convergent(A)
    print("Gauss-Seidel convergence:", convergent, "| Reason:", reason)

    # Gauss-Seidel迭代
    x0 = np.zeros_like(rhs)
    sol, residuals = gauss_seidel_iteration(A, rhs, x0=x0, tol=1e-10, max_iter=500)
    print("Gauss-Seidel solution (second derivatives at nodes):")
    print(sol)

    # 绘制残差曲线
    plt.figure(figsize=(8, 5))
    plt.semilogy(residuals, marker='o')
    plt.xlabel("Iteration step")
    plt.ylabel("Residual (log scale)")
    plt.title("Gauss-Seidel iteration residuals")
    plt.grid(True)
    plt.show()

# =========================
# 中文说明：
# 本代码实现了三次样条插值法中三对角线性方程组的Gauss-Seidel迭代收敛性判断与迭代求解。
# 1. is_gauss_seidel_convergent函数先用严格对角占优判据判断收敛性，若不满足，再用谱半径判据判断。
# 2. gauss_seidel_iteration函数实现Gauss-Seidel迭代，记录每步残差（无穷范数），并返回解和残差序列。
# 3. 主程序部分输出Gauss-Seidel迭代是否收敛及原因，给出迭代解，并绘制残差随迭代步数的下降曲线（对数坐标）。
# 4. 你可以修改n的值，观察不同插值节点数下Gauss-Seidel迭代的收敛性和残差下降速度。
# ========================= 