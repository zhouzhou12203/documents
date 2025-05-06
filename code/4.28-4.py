import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve  # 新增：用于隐式方程求解

# 定义微分方程的函数
def f(x, y):
    return y - 2 * x / y

# 定义步长和区间
h = 0.1
x = np.arange(0, 1.1, h)
y0 = 1

# 定义欧拉格式的计算方法（保持不变）
def euler_method(x, y0, h):
    y = np.zeros(len(x))
    y[0] = y0
    for n in range(len(x)-1):
        y[n+1] = y[n] + h * f(x[n], y[n])
    return y

# 定义后退欧拉格式的修正方法（使用隐式求解）
def backward_euler_method(x, y0, h):
    y = np.zeros(len(x))
    y[0] = y0
    for n in range(len(x)-1):
        x_next = x[n+1]
        # 使用fsolve解隐式方程 y_{n+1} = y_n + h*f(x_{n+1}, y_{n+1})
        y_next = fsolve(lambda y_next: y_next - y[n] - h * f(x_next, y_next), y[n])
        y[n+1] = y_next[0]  # 确保结果为标量
    return y

# 定义梯形格式的修正方法（使用隐式求解）
def trapezoidal_method(x, y0, h):
    y = np.zeros(len(x))
    y[0] = y0
    for n in range(len(x)-1):
        x_n = x[n]
        x_np1 = x[n+1]
        y_n = y[n]
        # 隐式方程：y_{n+1} = y_n + h/2 [f(x_n, y_n) + f(x_{n+1}, y_{n+1})]
        y_pred = y_n + h * f(x_n, y_n)  # 预测步（显式欧拉）
        # 使用fsolve解隐式方程
        y_next = fsolve(
            lambda y_next: y_next - y_n - h/2*(f(x_n, y_n) + f(x_np1, y_next)),
            y_pred
        )
        y[n+1] = y_next[0]
    return y

# 计算数值解
y_euler = euler_method(x, y0, h)
y_backward_euler = backward_euler_method(x, y0, h)
y_trapezoidal = trapezoidal_method(x, y0, h)

# 计算真实解（假设已知）
def y_true(x):
    return np.sqrt(x**4 + 4*x**3 + 4*x**2 + 1)

y_exact = y_true(x)

# 绘制结果比较（国际化标签）
plt.figure(figsize=(10, 6))
plt.plot(x, y_exact, 'k-', label='Exact Solution')
plt.plot(x, y_euler, 'r--', marker='o', label='Euler Method')
plt.plot(x, y_backward_euler, 'b--', marker='x', label='Backward Euler')
plt.plot(x, y_trapezoidal, 'g--', marker='s', label='Trapezoidal Method')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.title('Numerical Solutions Comparison (h=0.1)')
plt.grid(True)
plt.show()

# 打印误差表（国际化表头）
print("x\tEuler\t\tBackward Euler\tTrapezoidal\tExact\t\tError Euler\tError Backward Euler\tError Trapezoidal")
for i in range(len(x)):
    print(
        f"{x[i]:.1f}\t"
        f"{y_euler[i]:.6f}\t"
        f"{y_backward_euler[i]:.6f}\t"
        f"{y_trapezoidal[i]:.6f}\t"
        f"{y_exact[i]:.6f}\t"
        f"{y_exact[i]-y_euler[i]:.6f}\t"
        f"{y_exact[i]-y_backward_euler[i]:.6f}\t\t"
        f"{y_exact[i]-y_trapezoidal[i]:.6f}"
    )
