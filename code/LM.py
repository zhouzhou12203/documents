import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

# ------------------------- 步骤1: 数据定义 -------------------------
x_data = np.array([1.00, 1.25, 1.50, 1.75, 2.00])
y_data = np.array([5.10, 5.79, 6.53, 7.45, 8.46])

# ------------------------- 步骤2: 线性化方法获取初始猜测值 -------------------------
log_y = np.log(y_data)
X = np.vstack([np.ones_like(x_data), x_data]).T
A, B = np.linalg.lstsq(X, log_y, rcond=None)[0]
a_initial, b_initial = np.exp(A), B
print(f"初始猜测值: a = {a_initial:.4f}, b = {b_initial:.4f}")

# ------------------------- 步骤3: 定义非线性模型和残差函数 -------------------------
def exponential_model(params, x):
    a, b = params
    return a * np.exp(b * x)

def residuals(params, x, y):
    return exponential_model(params, x) - y

# ------------------------- 步骤4: 自定义收敛条件 -------------------------
# 设置收敛条件参数
convergence_config = {
    "xtol": 1e-10,     # 参数变化容忍度 (默认1e-8)
    "ftol": 1e-10,     # 残差变化容忍度 (默认1e-8)
    "max_nfev": 100   # 最大函数评估次数
}

# 使用最小二乘法优化
result = least_squares(
    fun=residuals,
    x0=[a_initial, b_initial],
    args=(x_data, y_data),
    **convergence_config
)

# 提取优化结果
a_fit, b_fit = result.x
print(f"\n优化结果:")
print(f"a = {a_fit:.4f}, b = {b_fit:.4f}")
print(f"迭代次数: {result.nfev}, 终止原因: {result.message}")

# ------------------------- 步骤5: 结果验证与可视化 -------------------------
y_pred = exponential_model([a_fit, b_fit], x_data)
sse = np.sum((y_data - y_pred)**2)
print(f"\n残差平方和 (SSE) = {sse:.6f}")

plt.figure(figsize=(8, 5))
plt.scatter(x_data, y_data, color='red', label='Original Data')
x_smooth = np.linspace(1.0, 2.0, 100)
plt.plot(x_smooth, exponential_model([a_fit, b_fit], x_smooth), '--', 
         label=f'Fitted: $S(x)={a_fit:.3f}e^{{{b_fit:.3f}x}}$')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Nonlinear Fitting with Convergence Criteria')
plt.legend()
plt.grid(True)
plt.show()