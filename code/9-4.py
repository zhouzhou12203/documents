import numpy as np
import matplotlib.pyplot as plt

# 设置雷诺数
Re_values = [2.37, 16.7, 267]  # 不同雷诺数值

# x/R的范围
x_over_R = np.logspace(0, 3, 100)  # 从10^0到10^3，共100个点

# 定义速度衰减函数
def velocity_decay_gaussian(Re, x_over_R):
    return 0.375 * Re / x_over_R

def velocity_decay_parabolic(Re, x_over_R):
    return 0.5 * Re / x_over_R

# 创建图像
plt.figure(figsize=(8, 6))
plt.loglog(x_over_R, velocity_decay_gaussian(Re_values[0],x_over_R), linestyle='-', label=f'Gaussian Re={Re_values[0]}') # 绘制高斯分布
plt.loglog(x_over_R, velocity_decay_gaussian(Re_values[1],x_over_R), linestyle='-', label=f'Gaussian Re={Re_values[1]}') # 绘制高斯分布
plt.loglog(x_over_R, velocity_decay_gaussian(Re_values[2],x_over_R), linestyle='-', label=f'Gaussian Re={Re_values[2]}') # 绘制高斯分布
plt.loglog(x_over_R, velocity_decay_parabolic(Re_values[0],x_over_R), linestyle='-', label=f'Parabolic Re={Re_values[0]}') # 绘制抛物线分布
plt.loglog(x_over_R, velocity_decay_parabolic(Re_values[1],x_over_R), linestyle='-', label=f'Parabolic Re={Re_values[1]}') # 绘制抛物线分布
plt.loglog(x_over_R, velocity_decay_parabolic(Re_values[2],x_over_R), linestyle='-', label=f'Parabolic Re={Re_values[2]}') # 绘制抛物线分布

# 添加标签和标题
plt.xlabel('x/R', fontsize=12)
plt.ylabel('v_x0 / v_c', fontsize=12)
plt.title('Velocity Decay vs. Distance', fontsize=14)

# 设置坐标轴范围
plt.xlim(1, 1000) # x轴范围

# 添加图例
plt.legend()

# 添加网格
plt.grid(True, which="both", ls="-")
plt.tight_layout()
# 显示图像
plt.show()
