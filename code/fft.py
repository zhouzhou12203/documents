import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

def find_feature_frequency(freq, amplitude):
    """
    找出幅值最大的峰值对应的频率，作为特征频率
    输入:
        freq: 频率数组 (Hz)
        amplitude: 对应的幅值数组
    返回:
        peak_freq: 特征频率 (峰值频率)
        peak_amp: 峰值幅值
        peak_idx: 峰值索引
    """
    peak_idx = np.argmax(amplitude)
    peak_freq = freq[peak_idx]
    peak_amp = amplitude[peak_idx]
    return peak_freq, peak_amp, peak_idx

def main():
    # 弹出文件选择对话框（隐藏主窗口）
    Tk().withdraw()
    file_path = askopenfilename(title="Select the microphone data file",
                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not file_path:
        print("No file selected.")
        return

    # 读取数据，假设文件中是多行或单行浮点数（空格或制表符分隔均支持）
    with open(file_path, 'r') as f:
        content = f.read().strip()
    data_strs = content.replace('\t',' ').split()
    data = np.array(list(map(float, data_strs)))

    # 去除直流分量（均值），避免0Hz峰值过大影响判断
    data = data - np.mean(data)

    # 假设采样频率，需根据实际设备修改
    fs = 48000  # Hz

    N = len(data)
    print(f"Number of sampling points: {N}")

    # 计算FFT
    fft_data = np.fft.fft(data)
    freq = np.fft.fftfreq(N, d=1/fs)

    # 只取非负频率部分
    pos_mask = freq >= 0
    freq = freq[pos_mask]
    fft_data = fft_data[pos_mask]

    # 幅度归一化
    # 对于实信号，正频率成分幅值乘2/N，直流和奈奎斯特频率点除外
    amplitude = np.abs(fft_data) * 2 / N
    amplitude[0] /= 2  # 直流分量不乘2
    if N % 2 == 0:
        amplitude[-1] /= 2  # 如果点数是偶数，奈奎斯特频率不乘2

    # 计算特征频率（频谱峰值）
    peak_freq, peak_amp, peak_idx = find_feature_frequency(freq, amplitude)

    print(f"特征频率 (峰值频率): {peak_freq:.2f} Hz")
    print(f"对应的峰值幅度: {peak_amp:.4f}")

    # 绘制频谱图
    plt.figure(figsize=(10,6))
    plt.plot(freq, amplitude, label='Amplitude Spectrum')
    plt.title(f"FFT Spectrum of {os.path.basename(file_path)}", fontsize=14)
    plt.xlabel("Frequency (Hz)", fontsize=12)
    plt.ylabel("Amplitude", fontsize=12)
    plt.grid(True)

    # 标注峰值点（特征频率）
    plt.plot(peak_freq, peak_amp, 'ro', label='Feature Frequency Peak')
    plt.text(peak_freq, peak_amp * 1.1,
             f'{peak_freq:.2f} Hz\nAmp: {peak_amp:.4f}',
             color='red', fontsize=10, ha='center')

    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
