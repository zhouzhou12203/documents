import numpy as np
import sympy

# 定义权函数
def weight_function(x):
    return sympy.sqrt(x)

# 构造正交多项式 P_2(x) = x^2 + a*x + b
# 需要满足条件: 积分(P_2(x) * x^k * w(x), (x, 0, 1)) = 0  对于 k = 0, 1

x = sympy.Symbol('x')
a, b = sympy.symbols('a b')

# 定义正交多项式
P_2 = x**2 + a*x + b

# 计算正交性条件
eq1 = sympy.integrate(P_2 * weight_function(x), (x, 0, 1))
eq2 = sympy.integrate(P_2 * x * weight_function(x), (x, 0, 1))

# 求解a和b
sol = sympy.solve([eq1, eq2], [a, b])
a_val = sol[a]
b_val = sol[b]

print(f"a = {a_val}, b = {b_val}")

# 求解P_2(x) = 0，得到高斯点
P_2_final = x**2 + a_val*x + b_val
roots = sympy.solve(P_2_final, x)

x0_sym = roots[0]
x1_sym = roots[1]
x0 = float(x0_sym)
x1 = float(x1_sym)

print(f"符号解x0 = {x0_sym:.4f}, x1 = {x1_sym:.4f}")

print(f"数值解x0 = {x0:.4f}, x1 = {x1:.4f}")


#  以下部分使用符号求解，可以更精确
# 计算求积系数A0和A1
# 需要满足条件:
# A0 + A1 = 积分(w(x), (x, 0, 1))
# A0*x0 + A1*x1 = 积分(x*w(x), (x, 0, 1))

A0_sym, A1_sym = sympy.symbols('A0 A1')
eq3 = A0_sym + A1_sym - sympy.integrate(weight_function(x), (x, 0, 1))
eq4 = A0_sym*x0_sym + A1_sym*x1_sym - sympy.integrate(x*weight_function(x), (x, 0, 1))

# 求解 A0 和 A1
sol_A = sympy.solve([eq3, eq4], [A0_sym, A1_sym])
A0_sym = sol_A[A0_sym]
A1_sym = sol_A[A1_sym]
A0 = float(A0_sym)
A1 = float(A1_sym)

print(f"符号解A0 = {A0_sym:.4f}, A1 = {A1_sym:.4f}")

print(f"数值解A0 = {A0:.4f}, A1 = {A1:.4f}")

# 定义验证函数
def verify_quadrature(n):
    """
    验证求积公式对x^n的精确性。
    """
    exact_integral = sympy.integrate(weight_function(x) * x**n, (x, 0, 1))
    approximate_integral = A0 * x0**n + A1 * x1**n
    print(f"当 f(x) = x^{n} 时: ")
    print(f"  精确积分值: {float(exact_integral):.6f}")
    print(f"  求积公式结果: {float(approximate_integral):.6f}")


# 验证求积公式对不同多项式的精确性
verify_quadrature(0)  # f(x) = 1
verify_quadrature(1)  # f(x) = x
verify_quadrature(2)  # f(x) = x^2
verify_quadrature(3)  # f(x) = x^3
verify_quadrature(4)  # f(x) = x^4
