#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <sys/stat.h>
#include <cerrno>
#include <algorithm>
#include <limits> // 用于 numeric_limits
#include <Eigen/Eigenvalues>  // 包含 Eigenvalue 解算器
#include <Eigen/Dense>

using namespace std;
using namespace Eigen; // 添加 Eigen 命名空间

// 函数：Jacobi 迭代法
vector<double> jacobi(const vector<vector<double>>& A, const vector<double>& b, vector<double> x0, int max_iterations, double tolerance, vector<vector<double>>& x_history, vector<double>& error_history, bool& converged) {
    int n = A.size();
    vector<double> x = x0;
    vector<double> x_new(n);

    x_history.push_back(x);

    for (int iter = 0; iter < max_iterations; ++iter) {
        for (int i = 0; i < n; ++i) {
            double sum = 0.0;
            for (int j = 0; j < n; ++j) {
                if (i != j) {
                    sum += A[i][j] * x[j];
                }
            }
            x_new[i] = (b[i] - sum) / A[i][i];
        }

        double error = 0.0;
        for (int i = 0; i < n; ++i) {
            error = max(error, abs(x_new[i] - x[i]));
        }
        error_history.push_back(error);

        x = x_new;
        x_history.push_back(x);

        if (error < tolerance) {
            cout << "Jacobi 方法在 " << iter + 1 << " 次迭代后收敛。" << endl;
            converged = true;
            return x;
        }
    }

    cout << "Jacobi 方法在 " << max_iterations << " 次迭代内未收敛。" << endl;
    converged = false;
    return x;
}

// 函数：Gauss-Seidel 迭代法
vector<double> gauss_seidel(const vector<vector<double>>& A, const vector<double>& b, vector<double> x0, int max_iterations, double tolerance, vector<vector<double>>& x_history, vector<double>& error_history, bool& converged) {
    int n = A.size();
    vector<double> x = x0;

    x_history.push_back(x);

    for (int iter = 0; iter < max_iterations; ++iter) {
        vector<double> x_prev = x;
        for (int i = 0; i < n; ++i) {
            double sum = 0.0;
            for (int j = 0; j < n; ++j) {
                if (i != j) {
                    sum += A[i][j] * x[j];
                }
            }
            x[i] = (b[i] - sum) / A[i][i];
        }

        double error = 0.0;
        for (int i = 0; i < n; ++i) {
            error = max(error, abs(x[i] - x_prev[i]));
        }
        error_history.push_back(error);

        x_history.push_back(x);  // 记录更新后的 x

        if (error < tolerance) {
            cout << "Gauss-Seidel 方法在 " << iter + 1 << " 次迭代后收敛。" << endl;
            converged = true;
            return x;
        }
    }

    cout << "Gauss-Seidel 方法在 " << max_iterations << " 次迭代内未收敛。" << endl;
    converged = false;
    return x;
}

// 函数：高斯消元法求精确解
vector<double> gaussian_elimination(vector<vector<double>> A, vector<double> b) {
    int n = A.size();

    // 前向消元
    for (int i = 0; i < n; ++i) {
        // 寻找主元
        int max_row = i;
        for (int k = i + 1; k < n; ++k) {
            if (abs(A[k][i]) > abs(A[max_row][i])) {
                max_row = k;
            }
        }

        // 交换行
        if (max_row != i) {
            swap(A[i], A[max_row]);
            swap(b[i], b[max_row]);
        }

        // 消元
        for (int k = i + 1; k < n; ++k) {
            double factor = A[k][i] / A[i][i];
            for (int j = i; j < n; ++j) {
                A[k][j] -= factor * A[i][j];
            }
            b[k] -= factor * b[i];
        }
    }

    // 回代
    vector<double> x(n);
    for (int i = n - 1; i >= 0; --i) {
        x[i] = b[i];
        for (int j = i + 1; j < n; ++j) {
            x[i] -= A[i][j] * x[j];
        }
        x[i] /= A[i][i];
    }

    return x;
}

// Jacobi 迭代矩阵 (D^-1 * (L+U))
vector<vector<double>> create_jacobi_iteration_matrix(const vector<vector<double>>& A) {
    int n = A.size();
    vector<vector<double>> Bj(n, vector<double>(n, 0.0));
    vector<double> D_inv(n);
    for (int i = 0; i < n; ++i) {
        D_inv[i] = 1.0 / A[i][i];
    }

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i != j) {
                Bj[i][j] = -D_inv[i] * A[i][j];
            }
        }
    }
    return Bj;
}

// Gauss-Seidel 迭代矩阵 (D-L)^-1 * U
vector<vector<double>> create_gauss_seidel_iteration_matrix(const vector<vector<double>>& A) {
    int n = A.size();
    vector<vector<double>> L(n, vector<double>(n, 0.0));
    vector<vector<double>> U(n, vector<double>(n, 0.0));
    vector<vector<double>> D(n, vector<double>(n, 0.0));

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i > j) {
                L[i][j] = A[i][j];
            } else if (i < j) {
                U[i][j] = A[i][j];
            } else {
                D[i][j] = A[i][j];
            }
        }
    }

    // 计算 (D-L)^-1
    vector<vector<double>> DL_inv(n, vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        DL_inv[i][i] = 1.0 / D[i][i];
        for (int j = i + 1; j < n; ++j) {
            double sum = 0.0;
            for (int k = i; k < j; ++k) {
                sum += L[j][k] * DL_inv[k][i];
            }
            DL_inv[j][i] = -(sum / D[j][j]);
        }
    }

    // 计算 (D-L)^-1 * U
    vector<vector<double>> Bg(n, vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            for (int k = 0; k < n; ++k) {
                Bg[i][j] += DL_inv[i][k] * U[k][j]; // 注意这里的加号，之前是减号
            }
        }
    }
    return Bg;
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

// 近似计算谱半径 (使用幂迭代法和绝对值矩阵, 改进精度)  这个函数不再使用
double approximate_spectral_radius(const vector<vector<double>>& A, int max_iter, double tolerance) {
    int n = A.size();
    vector<double> v(n, 1.0); // 初始向量
    double rho_approx = 0.0;
    double prev_rho_approx = 0.0;

    // 创建绝对值矩阵
    vector<vector<double>> abs_A(n, vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            abs_A[i][j] = abs(A[i][j]);
        }
    }

    for (int iter = 0; iter < max_iter; ++iter) {
        vector<double> Av(n, 0.0);
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                Av[i] += abs_A[i][j] * v[j]; // 使用绝对值矩阵
            }
        }

        // 计算向量的范数
        double norm = 0.0;
        for (int i = 0; i < n; ++i) {
            norm = max(norm, abs(Av[i]));
        }

        // 归一化向量
        for (int i = 0; i < n; ++i) {
            v[i] = Av[i] / norm;
        }

        prev_rho_approx = rho_approx;
        rho_approx = norm; // 当前迭代的谱半径估计

        // 提前停止机制
        if (abs(rho_approx - prev_rho_approx) < tolerance) {
            cout << "谱半径在 " << iter << " 次迭代后收敛。" << endl;
            break;
        }
    }

    return rho_approx;
}

int main() {
    // 方程组 1
    vector<vector<double>> A1 = {{2, -1, -1}, {2, 2, 2}, {-1, -1, 2}};
    vector<double> b1 = {-1, 4, 5};
    vector<double> x0_1 = {0, 0, 0};

    // 方程组 2
    vector<vector<double>> A2 = {{1, 2, -2}, {1, 1, 1}, {2, 2, 1}};
    vector<double> b2 = {7, 2, 5};
    vector<double> x0_2 = {0, 0, 0};

    int max_iterations = 1000; // 增加迭代次数
    double tolerance = 1e-6;
    double rho_tolerance = 1e-8; // 谱半径计算的容差

    // 存储迭代历史和误差
    vector<vector<double>> jacobi_x_history_1, gauss_seidel_x_history_1;
    vector<double> jacobi_error_history_1, gauss_seidel_error_history_1;

    vector<vector<double>> jacobi_x_history_2, gauss_seidel_x_history_2;
    vector<double> jacobi_error_history_2, gauss_seidel_error_history_2;

    bool jacobi_converged_1, gauss_seidel_converged_1;
    bool jacobi_converged_2, gauss_seidel_converged_2;

    cout << "求解方程组 1:" << endl;
    cout << "-----------------" << endl;

    // 高斯消元法求解精确解
    vector<double> x_exact_1 = gaussian_elimination(A1, b1);
    cout << "精确解: x1 = " << x_exact_1[0] << ", x2 = " << x_exact_1[1] << ", x3 = " << x_exact_1[2] << endl;

    cout << "Jacobi 方法:" << endl;
    vector<double> x_jacobi_1 = jacobi(A1, b1, x0_1, max_iterations, tolerance, jacobi_x_history_1, jacobi_error_history_1, jacobi_converged_1);
    cout << "解: x1 = " << x_jacobi_1[0] << ", x2 = " << x_jacobi_1[1] << ", x3 = " << x_jacobi_1[2] << endl;
    cout << "是否收敛: " << (jacobi_converged_1 ? "是" : "否") << endl;

    cout << "Gauss-Seidel 方法:" << endl;
    vector<double> x_gauss_seidel_1 = gauss_seidel(A1, b1, x0_1, max_iterations, tolerance, gauss_seidel_x_history_1, gauss_seidel_error_history_1, gauss_seidel_converged_1);
    cout << "解: x1 = " << x_gauss_seidel_1[0] << ", x2 = " << x_gauss_seidel_1[1] << ", x3 = " << x_gauss_seidel_1[2] << endl;
    cout << "是否收敛: " << (gauss_seidel_converged_1 ? "是" : "否") << endl;

    cout << endl;

    cout << "求解方程组 2:" << endl;
    cout << "-----------------" << endl;

    // 高斯消元法求解精确解
    vector<double> x_exact_2 = gaussian_elimination(A2, b2);
    cout << "精确解: x1 = " << x_exact_2[0] << ", x2 = " << x_exact_2[1] << ", x3 = " << x_exact_2[2] << endl;

    cout << "Jacobi 方法:" << endl;
    vector<double> x_jacobi_2 = jacobi(A2, b2, x0_2, max_iterations, tolerance, jacobi_x_history_2, jacobi_error_history_2, jacobi_converged_2);
    cout << "解: x1 = " << x_jacobi_2[0] << ", x2 = " << x_jacobi_2[1] << ", x3 = " << x_jacobi_2[2] << endl;
    cout << "是否收敛: " << (jacobi_converged_2 ? "是" : "否") << endl;

    cout << "Gauss-Seidel 方法:" << endl;
    vector<double> x_gauss_seidel_2 = gauss_seidel(A2, b2, x0_2, max_iterations, tolerance, gauss_seidel_x_history_2, gauss_seidel_error_history_2, gauss_seidel_converged_2);
    cout << "解: x1 = " << x_gauss_seidel_2[0] << ", x2 = " << x_gauss_seidel_2[1] << ", x3 = " << x_gauss_seidel_2[2] << endl;
    cout << "是否收敛: " << (gauss_seidel_converged_2 ? "是" : "否") << endl;

    cout << endl;

    // 创建 target 目录 (如果不存在)
    const string target_dir = "target";
    if (mkdir(target_dir.c_str(), 0777) == -1) {
        if (errno != EEXIST) {
            cerr << "无法创建目录 " << target_dir << endl;
            return 1;
        }
    }

    // 输出下降曲线数据到文件
    ofstream jacobi_data_1(target_dir + "/jacobi_error_1.dat");
    ofstream gauss_seidel_data_1(target_dir + "/gauss_seidel_error_1.dat");
    ofstream jacobi_data_2(target_dir + "/jacobi_error_2.dat");
    ofstream gauss_seidel_data_2(target_dir + "/gauss_seidel_error_2.dat");

    if (jacobi_data_1.is_open() && gauss_seidel_data_1.is_open() && jacobi_data_2.is_open() && gauss_seidel_data_2.is_open()) {
        for (size_t i = 0; i < jacobi_error_history_1.size(); ++i) {
            jacobi_data_1 << i << " " << jacobi_error_history_1[i] << endl;
        }

        for (size_t i = 0; i < gauss_seidel_error_history_1.size(); ++i) {
            gauss_seidel_data_1 << i << " " << gauss_seidel_error_history_1[i] << endl;
        }

        for (size_t i = 0; i < jacobi_error_history_2.size(); ++i) {
            jacobi_data_2 << i << " " << jacobi_error_history_2[i] << endl;
        }

        for (size_t i = 0; i < gauss_seidel_error_history_2.size(); ++i) {
            gauss_seidel_data_2 << i << " " << gauss_seidel_error_history_2[i] << endl;
        }

        jacobi_data_1.close();
        gauss_seidel_data_1.close();
        jacobi_data_2.close();
        gauss_seidel_data_2.close();

        cout << "误差数据已输出到 " << target_dir << "/jacobi_error_1.dat, " << target_dir << "/gauss_seidel_error_1.dat, "
             << target_dir << "/jacobi_error_2.dat, " << target_dir << "/gauss_seidel_error_2.dat 文件。" << endl;
        cout << "可以使用 gnuplot 等工具绘制下降曲线。" << endl;
    } else {
        cout << "无法打开文件以写入误差数据。" << endl;
    }

    // 计算方程组 1 的 rho(Bj) 和 rho(Bg)
    cout << "计算方程组 1 的谱半径:" << endl;
    vector<vector<double>> Bj_1 = create_jacobi_iteration_matrix(A1);
    vector<vector<double>> Bg_1 = create_gauss_seidel_iteration_matrix(A1);

    //double rho_Bj_1 = approximate_spectral_radius(Bj_1, max_iterations, rho_tolerance); // 传递 max_iterations 和容差
    //double rho_Bg_1 = approximate_spectral_radius(Bg_1, max_iterations, rho_tolerance); // 传递 max_iterations 和容差
    double rho_Bj_1 = calculate_spectral_radius_eigen(Bj_1);
    double rho_Bg_1 = calculate_spectral_radius_eigen(Bg_1);


    cout << "rho(Bj) 对于方程组 1 = " << rho_Bj_1 << endl;
    cout << "rho(Bg) 对于方程组 1 = " << rho_Bg_1 << endl;

    // 计算方程组 2 的 rho(Bj) 和 rho(Bg)
    cout << "计算方程组 2 的谱半径:" << endl;
    vector<vector<double>> Bj_2 = create_jacobi_iteration_matrix(A2);
    vector<vector<double>> Bg_2 = create_gauss_seidel_iteration_matrix(A2);

    //double rho_Bj_2 = approximate_spectral_radius(Bj_2, max_iterations, rho_tolerance); // 传递 max_iterations 和容差
    //double rho_Bg_2 = approximate_spectral_radius(Bg_2, max_iterations, rho_tolerance); // 传递 max_iterations 和容差
    double rho_Bj_2 = calculate_spectral_radius_eigen(Bj_2);
    double rho_Bg_2 = calculate_spectral_radius_eigen(Bg_2);

    cout << "rho(Bj) 对于方程组 2 = " << rho_Bj_2 << endl;
    cout << "rho(Bg) 对于方程组 2 = " << rho_Bg_2 << endl;

    return 0;
}
