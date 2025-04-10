import numpy as np
from scipy.linalg import qr, rq

def qr_iteration(A, tol=1e-6, max_iter=100):
    """
    使用 QR 迭代计算特征值。

    参数：
    A (numpy.ndarray): 要计算特征值的矩阵。
    tol (float): 收敛容差。
    max_iter (int): 最大迭代次数。

    返回值：
    numpy.ndarray: 特征值（对角线元素）。
    int: 实际迭代次数。
    """
    A_k = A.copy()
    for k in range(max_iter):
        Q, R = qr(A_k)
        A_k = R @ Q
        # 检查下三角是否收敛
        off_diag_sum = np.sum(np.abs(np.tril(A_k, k=-1)))
        print(f"QR Iteration {k+1}:\n{A_k}\nOff-diagonal sum: {off_diag_sum}\n")
        if off_diag_sum < tol:
            print("QR converged!")
            return np.diag(A_k), k + 1
    print("QR did not converge within the maximum number of iterations.")
    return np.diag(A_k), max_iter

def rq_iteration(A, tol=1e-6, max_iter=100):
    """
    使用 RQ 迭代计算特征值。

    参数：
    A (numpy.ndarray): 要计算特征值的矩阵。
    tol (float): 收敛容差。
    max_iter (int): 最大迭代次数。

    返回值：
    numpy.ndarray: 特征值（对角线元素）。
    int: 实际迭代次数。
    """
    A_k = A.copy()
    for k in range(max_iter):
        R, Q = rq(A_k)
        A_k = Q @ R
        # 检查下三角是否收敛
        off_diag_sum = np.sum(np.abs(np.tril(A_k, k=-1)))
        print(f"RQ Iteration {k+1}:\n{A_k}\nOff-diagonal sum: {off_diag_sum}\n")

        if off_diag_sum < tol:
            print("RQ converged!")
            return np.diag(A_k), k + 1
    print("RQ did not converge within the maximum number of iterations.")
    return np.diag(A_k), max_iter


# 初始矩阵
A = np.array([[1, 2, 0], [2, -1, 1], [0, 1, 3]], dtype=float)

# QR 迭代
print("QR Iteration:\n")
eigenvalues_qr, num_iterations_qr = qr_iteration(A)
print(f"Eigenvalues (QR): {eigenvalues_qr}")
print(f"Number of iterations (QR): {num_iterations_qr}\n")

# RQ 迭代
print("RQ Iteration:\n")
eigenvalues_rq, num_iterations_rq = rq_iteration(A)
print(f"Eigenvalues (RQ): {eigenvalues_rq}")
print(f"Number of iterations (RQ): {num_iterations_rq}")
