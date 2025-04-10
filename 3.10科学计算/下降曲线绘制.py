import matplotlib.pyplot as plt
import numpy as np

def plot_error_curve(filename, ax, title, label):
    """
    绘制误差下降曲线到指定的子图。

    参数:
        filename (str): 包含误差数据的文件名。
        ax (matplotlib.axes.Axes): 要绘制到的子图对象。
        title (str): 子图的标题。
        label (str): 曲线的标签。
    """
    try:
        # 从文件中读取数据
        data = np.loadtxt(filename)
        iterations = data[:, 0].astype(float)  # 第一列是迭代次数，确保是浮点数
        errors = data[:, 1].astype(float)      # 第二列是误差值，确保是浮点数

        # 绘制曲线
        ax.plot(iterations, errors, label=label)

        # 添加标签和标题 (英文)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Error")
        ax.set_title(title)

        ax.set_yscale('log')  # 使用对数刻度显示 y 轴
        ax.grid(True)  # 添加网格线
        ax.legend()  # 显示图例

    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # 创建一个包含 2x2 子图的图表
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 解决负号显示为方块的问题 (可选)
    plt.rcParams['axes.unicode_minus'] = False

    # 绘制 Jacobi 方法的误差下降曲线 (方程组 1)
    plot_error_curve("target/jacobi_error_1.dat", axes[0, 0], "Jacobi Method (System 1)", "Jacobi")

    # 绘制 Gauss-Seidel 方法的误差下降曲线 (方程组 1)
    plot_error_curve("target/gauss_seidel_error_1.dat", axes[0, 1], "Gauss-Seidel Method (System 1)", "Gauss-Seidel")

    # 绘制 Jacobi 方法的误差下降曲线 (方程组 2)
    plot_error_curve("target/jacobi_error_2.dat", axes[1, 0], "Jacobi Method (System 2)", "Jacobi")

    # 绘制 Gauss-Seidel 方法的误差曲线 (方程组 2)
    plot_error_curve("target/gauss_seidel_error_2.dat", axes[1, 1], "Gauss-Seidel Method (System 2)", "Gauss-Seidel")

    # 调整子图之间的间距
    plt.tight_layout()

    # 显示图表
    plt.show()
