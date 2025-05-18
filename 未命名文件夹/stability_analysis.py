import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 设置中文字体
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac使用支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def analyze_stability():
    # 模型问题：y' = λy
    # 改进的Euler格式的稳定性函数
    def stability_function(z):
        return 1 + z + z**2/2
    
    # 生成复平面上的点
    theta = np.linspace(0, 2*np.pi, 1000)
    z = np.exp(1j * theta)
    
    # 计算稳定性函数的值
    R = stability_function(z)
    
    # 绘制稳定性区域
    plt.figure(figsize=(10, 10))
    plt.plot(np.real(z), np.imag(z), 'k--', label='Unit Circle')
    plt.plot(np.real(R), np.imag(R), 'r-', label='Stability Region Boundary')
    
    # 填充稳定性区域
    plt.fill(np.real(R), np.imag(R), 'r', alpha=0.2)
    
    plt.grid(True)
    plt.axis('equal')
    plt.xlabel('Re(z)')
    plt.ylabel('Im(z)')
    plt.title('Improved Euler Method Stability Region')
    plt.legend()
    
    # 计算稳定性区间
    real_axis = np.linspace(-3, 1, 1000)
    stability_values = stability_function(real_axis)
    stability_interval = real_axis[np.abs(stability_values) <= 1]
    
    print(f"Stability interval: [{stability_interval[0]:.4f}, {stability_interval[-1]:.4f}]")
    
    plt.savefig('stability_region.png')
    plt.close()

if __name__ == "__main__":
    analyze_stability() 