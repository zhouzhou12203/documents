import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 设置中文字体
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac使用支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用支持中文的字体（Windows 推荐）
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def euler_method(f, x0, y0, h, n):
    """原Euler格式"""
    x = np.zeros(n+1)
    y = np.zeros(n+1)
    x[0] = x0
    y[0] = y0
    
    for i in range(n):
        x[i+1] = x[i] + h
        y[i+1] = y[i] + h * f(x[i], y[i])
    
    return x, y

def improved_euler_method(f, x0, y0, h, n):
    """改进的Euler格式"""
    x = np.zeros(n+1)
    y = np.zeros(n+1)
    x[0] = x0
    y[0] = y0
    
    for i in range(n):
        x[i+1] = x[i] + h
        k1 = f(x[i], y[i])
        k2 = f(x[i+1], y[i] + h * k1)
        y[i+1] = y[i] + h/2 * (k1 + k2)
    
    return x, y

def two_step_euler_method(f, x0, y0, h, n):
    """欧拉两步格式"""
    x = np.zeros(n+1)
    y = np.zeros(n+1)
    x[0] = x0
    y[0] = y0
    
    # 使用Euler方法计算第一步
    x[1] = x[0] + h
    y[1] = y[0] + h * f(x[0], y[0])
    
    for i in range(1, n):
        x[i+1] = x[i] + h
        y[i+1] = y[i-1] + 2*h * f(x[i], y[i])
    
    return x, y

def predictor_corrector_method(f, x0, y0, h, n):
    """预测-改进-校正6步格式"""
    x = np.zeros(n+1)
    y = np.zeros(n+1)
    x[0] = x0
    y[0] = y0
    
    # 使用Euler方法计算前5步
    for i in range(5):
        x[i+1] = x[i] + h
        y[i+1] = y[i] + h * f(x[i], y[i])
    
    # 使用6步预测-校正格式
    for i in range(5, n):
        x[i+1] = x[i] + h
        # 预测步
        y_pred = y[i] + h/720 * (1901*f(x[i], y[i]) - 2774*f(x[i-1], y[i-1]) + 
                                2616*f(x[i-2], y[i-2]) - 1274*f(x[i-3], y[i-3]) + 
                                251*f(x[i-4], y[i-4]))
        # 校正步
        y[i+1] = y[i] + h/720 * (251*f(x[i+1], y_pred) + 646*f(x[i], y[i]) - 
                                264*f(x[i-1], y[i-1]) + 106*f(x[i-2], y[i-2]) - 
                                19*f(x[i-3], y[i-3]))

    return x, y

def trapezoidal_method(f, x0, y0, h, n):
    """梯形格式"""
    x = np.zeros(n+1)
    y = np.zeros(n+1)
    x[0] = x0
    y[0] = y0
    
    for i in range(n):
        x[i+1] = x[i] + h
        # 使用简单迭代求解隐式方程
        y_new = y[i] + h/2 * f(x[i], y[i])
        for _ in range(5):  # 迭代5次
            y_new = y[i] + h/2 * (f(x[i], y[i]) + f(x[i+1], y_new))
        y[i+1] = y_new
    
    return x, y

# 定义微分方程
def f(x, y):
    return y - 2*x/y

# 初始条件
x0 = 0
y0 = 1
h = 0.1
n = 10  # 计算10步

# 计算各种方法的结果
x_euler, y_euler = euler_method(f, x0, y0, h, n)
x_improved, y_improved = improved_euler_method(f, x0, y0, h, n)
x_two_step, y_two_step = two_step_euler_method(f, x0, y0, h, n)
x_pc, y_pc = predictor_corrector_method(f, x0, y0, h, n)
x_trap, y_trap = trapezoidal_method(f, x0, y0, h, n)

# 计算精确解
x_exact = np.linspace(x0, x0 + n*h, n+1)
y_exact = np.sqrt(1 + 2*x_exact)

# 打印结果
print("步长 h =", h)
print("\n计算结果比较：")
print("x\t\t精确解\t\tEuler\t\t改进Euler\t两步Euler\t预测校正\t梯形格式")
print("-" * 100)
for i in range(n+1):
    print(f"{x_euler[i]:.1f}\t\t{y_exact[i]:.6f}\t\t{y_euler[i]:.6f}\t\t{y_improved[i]:.6f}\t\t{y_two_step[i]:.6f}\t\t{y_pc[i]:.6f}\t\t{y_trap[i]:.6f}")

# 绘制结果
plt.figure(figsize=(12, 8))
plt.plot(x_exact, y_exact, 'k-', label='Exact Solution')
plt.plot(x_euler, y_euler, 'r--', label='Euler Method')
plt.plot(x_improved, y_improved, 'g--', label='Improved Euler')
plt.plot(x_two_step, y_two_step, 'b--', label='Two-step Euler')
plt.plot(x_pc, y_pc, 'm--', label='Predictor-Corrector')
plt.plot(x_trap, y_trap, 'c--', label='Trapezoidal')

plt.xlabel('x')
plt.ylabel('y')
plt.title('Comparison of Numerical Methods')
plt.legend()
plt.grid(True)
plt.savefig('numerical_methods_comparison.png')
plt.close()

# 计算误差
error_euler = np.abs(y_euler - y_exact)
error_improved = np.abs(y_improved - y_exact)
error_two_step = np.abs(y_two_step - y_exact)
error_pc = np.abs(y_pc - y_exact)
error_trap = np.abs(y_trap - y_exact)

print("\n最大误差比较：")
print(f"Euler格式最大误差: {np.max(error_euler):.6f}")
print(f"改进Euler格式最大误差: {np.max(error_improved):.6f}")
print(f"两步Euler格式最大误差: {np.max(error_two_step):.6f}")
print(f"预测-校正格式最大误差: {np.max(error_pc):.6f}")
print(f"梯形格式最大误差: {np.max(error_trap):.6f}") 