#include <iostream>
#include <vector>
#include <Eigen/Eigenvalues>  // 包含 Eigenvalue 解算器

using namespace std;
using namespace Eigen;

//  <--  添加 create_jacobi_iteration_matrix 函数的定义  -->
vector<vector<double>> create_jacobi_iteration_matrix(const vector<vector<double>>& A) {
    int n = A.size();
    vector<vector<double>> Bj(n, vector<double>(n, 0.0));
    vector<double> D_inv(n, 0.0);  // 用于存储 D 的逆矩阵的对角线元素

    // 计算 D 的逆矩阵的对角线元素
    for (int i = 0; i < n; ++i) {
        if (A[i][i] != 0) {
            D_inv[i] = 1.0 / A[i][i];
        } else {
            // 如果对角线元素为 0，则 Jacobi 迭代可能不收敛
            cerr << "Error: Diagonal element is zero. Jacobi method may not converge." << endl;
            return Bj; // 或者采取其他错误处理策略
        }
    }

    // 构造 Jacobi 迭代矩阵
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i != j) {
                Bj[i][j] = -D_inv[i] * A[i][j];
            }
        }
    }

    return Bj;
}

// 使用 Eigen 库计算谱半径
double calculate_spectral_radius_eigen(const vector<vector<double>>& A) {
    int n = A.size();
    MatrixXd eigen_matrix(n, n);

    // 将 vector<vector<double>> 转换为 Eigen::MatrixXd
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            eigen_matrix(i, j) = A[i][j];
        }
    }

    // 使用 Eigen 的 EigenSolver 计算特征值
    EigenSolver<MatrixXd> es(eigen_matrix);
    VectorXcd eigenvalues = es.eigenvalues();

    // 找到绝对值最大的特征值，即谱半径
    double spectral_radius = 0.0;
    for (int i = 0; i < eigenvalues.size(); ++i) {
        spectral_radius = max(spectral_radius, abs(eigenvalues(i)));
    }

    return spectral_radius;
}

int main() {
    // 方程组 1
    vector<vector<double>> A1 = {{2, -1, -1}, {2, 2, 2}, {-1, -1, 2}};

    // 创建 Jacobi 迭代矩阵
    vector<vector<double>> Bj_1 = create_jacobi_iteration_matrix(A1);

    // 使用 Eigen 库计算谱半径
    double rho_Bj_1 = calculate_spectral_radius_eigen(Bj_1);

    cout << "rho(Bj) 对于方程组 1 (使用 Eigen) = " << rho_Bj_1 << endl;

    // 方程组 2
    vector<vector<double>> A2 = {{1, 2, -2}, {1, 1, 1}, {2, 2, 1}};

    // 创建 Jacobi 迭代矩阵
    vector<vector<double>> Bj_2 = create_jacobi_iteration_matrix(A2);

    // 使用 Eigen 库计算谱半径
    double rho_Bj_2 = calculate_spectral_radius_eigen(Bj_2);

    cout << "rho(Bj) 对于方程组 2 (使用 Eigen) = " << rho_Bj_2 << endl;

    return 0;
}
