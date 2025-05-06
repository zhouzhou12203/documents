import numpy as np

def f(x, y):
    """被积函数: ln(x + 2y)"""
    return np.log(x + 2 * y)


def simpson_double_integral(func, x_lim, y_lim, n=100, m=100):
    """
    二维复合辛普森积分
    :param func: 被积函数 f(x, y)
    :param x_lim: x积分区间 [x_min, x_max]
    :param y_lim: y积分区间 [y_min, y_max]
    :param n: x方向子区间数（需为偶数）
    :param m: y方向子区间数（需为偶数）
    :return: 积分近似值
    """
    # 检查n和m是否为偶数
    if n % 2 != 0 or m % 2 != 0:
        raise ValueError("n和m必须为偶数")
    
    # 计算x方向的步长和网格
    a, b = x_lim
    h_x = (b - a) / n
    x_points = np.linspace(a, b, n + 1)
    
    # 计算y方向的步长和网格
    c, d = y_lim
    h_y = (d - c) / m
    y_points = np.linspace(c, d, m + 1)
    
    # 生成x和y的权重系数 (辛普森公式系数: 1,4,2,4,...,1)
    weights_x = np.array([4 if i % 2 == 1 else 2 for i in range(n + 1)])
    weights_x[0] = weights_x[-1] = 1  # 首尾为1
    
    weights_y = np.array([4 if i % 2 == 1 else 2 for i in range(m + 1)])
    weights_y[0] = weights_y[-1] = 1  # 首尾为1
    
    # 计算所有网格点处的函数值（向量化计算）
    X, Y = np.meshgrid(x_points, y_points, indexing='ij')
    Z = func(X, Y)
    
    # 先对y方向积分（对每个x计算积分）
    integral_y = h_y / 3 * np.dot(Z, weights_y)  # 结果是一个长度为n+1的向量
    
    # 再对x方向积分
    integral_total = h_x / 3 * np.dot(integral_y, weights_x)
    
    return integral_total


# 积分参数设置
x_limits = [1.4, 2.0]
y_limits = [1.0, 1.5]
n = 200  # x方向子区间数（必须为偶数）
m = 200  # y方向子区间数（必须为偶数）

# 计算积分
result = simpson_double_integral(f, x_limits, y_limits, n, m)
print(f"辛普森二重积分结果: {result:.8f}")

# 蒙特卡洛积分验证（对比参考）
np.random.seed(0)  # 固定随机种子
N_samples = 10**7  # 采样数
x_rand = np.random.uniform(x_limits[0], x_limits[1], N_samples)
y_rand = np.random.uniform(y_limits[0], y_limits[1], N_samples)
area = (x_limits[1] - x_limits[0]) * (y_limits[1] - y_limits[0])
mc_result = area * np.mean(f(x_rand, y_rand))
print(f"蒙特卡洛验证结果: {mc_result:.8f} (N={N_samples})")
