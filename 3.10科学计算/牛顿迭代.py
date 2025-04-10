def newton_iteration_with_output(x0, tol=1e-6, max_iter=100):
    """
    牛顿迭代法求平方根 (带过程输出).

    Args:
        x0: 初始值 (float).
        tol: 容差 (float).
        max_iter: 最大迭代次数 (int).

    Returns:
        tuple: (迭代结果, 迭代次数, 是否收敛).
    """
    x = x0
    print(f"Initial value: x0 = {x0}")
    for i in range(max_iter):
        x_next = (x + 25 / x) / 2
        print(f"Iteration {i+1}: x = {x:.8f}, x_next = {x_next:.8f}")
        if abs(x_next - x) < tol:
            print("Converged!")
            return x_next, i + 1, True  # 收敛
        x = x_next
    print("Not converged within max iterations.")
    return x, max_iter, False  # 未收敛

# 设置初始值
x0 = 3.0  # 或者其他接近 5 的值

# 进行牛顿迭代
print("\n牛顿迭代法求 √25:")
result, iterations, converged = newton_iteration_with_output(x0)

print("\n牛顿迭代法求 √25:")
print(f"  迭代结果: {result}")
print(f"  迭代次数: {iterations}")
print(f"  是否收敛: {converged}")
