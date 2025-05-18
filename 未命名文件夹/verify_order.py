import numpy as np
import sympy as sp

def verify_order():
    # 定义符号变量
    x, y, h = sp.symbols('x y h')
    
    # 定义微分方程 y' = f(x,y)
    f = y - 2*x/y
    
    # 定义(3.10)格式
    # y_{n+1} = y_n + h/2 * [f(x_n, y_n) + f(x_{n+1}, y_n + h*f(x_n, y_n))]
    
    # 计算局部截断误差
    # 1. 计算精确解在x_{n+1}处的值
    y_exact = sp.sqrt(1 + 2*(x + h))  # 精确解 y = sqrt(1 + 2x)
    
    # 2. 计算数值解在x_{n+1}处的值
    y_n = sp.sqrt(1 + 2*x)  # y_n
    f_n = f.subs([(x, x), (y, y_n)])  # f(x_n, y_n)
    y_pred = y_n + h*f_n  # 预测值
    f_pred = f.subs([(x, x + h), (y, y_pred)])  # f(x_{n+1}, y_pred)
    y_numerical = y_n + h/2 * (f_n + f_pred)  # 数值解
    
    # 3. 计算局部截断误差
    error = y_exact - y_numerical
    
    # 4. 对误差进行泰勒展开
    error_series = sp.series(error, h, 0, 3)
    
    print("局部截断误差的泰勒展开：")
    print(error_series)
    
    # 5. 判断阶数
    # 如果h^2项的系数不为0，则为二阶格式
    h2_coeff = error_series.coeff(h**2)
    print("\nh^2项的系数：", h2_coeff)
    
    if h2_coeff != 0:
        print("\n结论：该格式是二阶格式")
    else:
        print("\n结论：该格式不是二阶格式")

if __name__ == "__main__":
    verify_order() 