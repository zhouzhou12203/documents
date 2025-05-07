import matplotlib.pyplot as plt

# 数据
phi = [0.6, 0.8, 1.0, 1.2]
b = [1.68, 1.65, 3.24, 4.64]

# 绘制图像
plt.figure(figsize=(8, 6))  # 设置图像大小
plt.plot(phi, b, marker='o', linestyle='-', color='blue')  # 绘制折线图，添加数据点

# 添加标题和标签
plt.title('Parameter b vs. Equivalence Ratio (Methane-Air)', fontsize=14)
plt.xlabel('Equivalence Ratio (Φ)', fontsize=12)
plt.ylabel('Parameter b', fontsize=12)

# 设置坐标轴范围
plt.xlim(0.5, 1.3)
plt.ylim(1.0, 5.0)

# 添加网格线
plt.grid(True)

# 显示图像
plt.tight_layout()  # 调整布局，防止标签重叠
plt.show()
