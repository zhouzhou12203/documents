import numpy as np

def fixed_point_iteration_with_output(phi, x0, tol=1e-6, max_iter=100):
    """
    不动点迭代法 (带过程输出，检查负平方根).

    Args:
        phi: 迭代函数 (callable).
        x0: 初始值 (float).
        tol: 容差 (float).
        max_iter: 最大迭代次数 (int).

    Returns:
        tuple: (迭代结果, 迭代次数, 是否收敛). 如果遇到负平方根，返回 None, None, False
    """
    x = x0
    print(f"Initial value: x0 = {x0}")
    for i in range(max_iter):
        try:
            x_next = phi(x)
        except RuntimeWarning as e:  # 捕获 numpy 的 warning，可以更精确地定位问题
            print(f"Iteration {i+1}: Encountered a negative square root. Stopping.")
            return None, None, False

        print(f"Iteration {i+1}: x = {x:.8f}, phi(x) = {x_next:.8f}")

        if np.isnan(x_next): #如果已经计算得到nan，直接停止
             print(f"Iteration {i+1}: Encountered a nan. Stopping.")
             return None, None, False

        if abs(x_next - x) < tol:
            print("Converged!")
            return x_next, i + 1, True  # 收敛
        x = x_next
    print("Not converged within max iterations.")
    return x, max_iter, False  # 未收敛

# 定义迭代函数
phi1 = lambda x: (x**2 + 21) / 10
phi2 = lambda x: np.sqrt(10*x - 21)

# 设置初始值
x0 = 2.5

# 在区间 [2.5, 3.5] 上进行迭代
print("φ₁(x) = (x² + 21) / 10:")
result1, iterations1, converged1 = fixed_point_iteration_with_output(phi1, x0)

print("\nφ₂(x) = √(10x - 21):")
result2, iterations2, converged2 = fixed_point_iteration_with_output(phi2, x0)
