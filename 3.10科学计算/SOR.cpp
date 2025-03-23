#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <sys/stat.h>
#include <cerrno>
#include <algorithm>
#include <limits>
#include <Eigen/Eigenvalues>
#include <Eigen/Dense>

using namespace std;
using namespace Eigen;

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

// 函数：SOR 迭代法
vector<double> sor(const vector<vector<double>>& A, const vector<double>& b, vector<double> x0, double omega, int max_iterations, double tolerance, vector<vector<double>>& x_history, vector<double>& error_history, bool& converged) {
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
            // 检查 A[i][i] 是否为零
            if (abs(A[i][i]) < 1e-12) {
                cout << "警告: A[" << i << "][" << i << "] 接近零，可能导致数值不稳定。" << endl;
                converged = false;
                return x; // 返回当前解
            }
            double new_x = (1 - omega) * x[i] + omega * (b[i] - sum) / A[i][i];

            // 检查 new_x 是否为 NaN 或 Inf
            if (isnan(new_x) || isinf(new_x)) {
                cout << "警告: 计算结果为 NaN 或 Inf，数值不稳定。" << endl;
                converged = false;
                return x; // 返回当前解
            }

            x[i] = new_x;
        }

        double error = 0.0;
        for (int i = 0; i < n; ++i) {
            error = max(error, abs(x[i] - x_prev[i]));
        }
        error_history.push_back(error);

        x_history.push_back(x);

        if (error < tolerance) {
            cout << "SOR 方法在 " << iter + 1 << " 次迭代后收敛 (omega = " << omega << ")。" << endl;
            converged = true;
            return x;
        }
    }

    cout << "SOR 方法在 " << max_iterations << " 次迭代内未收敛 (omega = " << omega << ")。" << endl;
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
    MatrixXd L = MatrixXd::Zero(n, n);
    MatrixXd U = MatrixXd::Zero(n, n);
    MatrixXd D = MatrixXd::Zero(n, n);

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i > j) {
                L(i, j) = A[i][j];
            } else if (i < j) {
                U(i, j) = A[i][j];
            } else {
                D(i, j) = A[i][j];
            }
        }
    }

    MatrixXd DL = D + L;
    MatrixXd Bg = DL.inverse() * U;

    vector<vector<double>> Bg_vec(n, vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            // 增加索引检查
            if (i >= 0 && i < n && j >= 0 && j < n) {
                Bg_vec[i][j] = Bg(i, j);
            } else {
                cerr << "错误: 访问 Bg_vec[" << i << "][" << j << "] 时索引越界。" << endl;
                // 可以选择抛出异常或者返回一个空矩阵
                return vector<vector<double>>(); // 返回空矩阵
            }
        }
    }

    return Bg_vec;
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
    vector<double> b1 = {-1, 4, 5};
    vector<double> x0_1 = {0, 0, 0};

    // 方程组 2
    vector<vector<double>> A2 = {{1, 2, -2}, {1, 1, 1}, {2, 2, 1}};
    vector<double> b2 = {7, 2, 5};
    vector<double> x0_2 = {0, 0, 0};

    int max_iterations = 1000;
    double tolerance = 1e-6;
    double rho_tolerance = 1e-8;

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

    // 在使用Bg_1之前检查它是否为空
    if (!Bg_1.empty()) {
        double rho_Bg_1 = calculate_spectral_radius_eigen(Bg_1);
        cout << "rho(Bg) 对于方程组 1 = " << rho_Bg_1 << endl;
    } else {
        cout << "警告: Bg_1 为空，无法计算谱半径。" << endl;
    }

    double rho_Bj_1 = calculate_spectral_radius_eigen(Bj_1);
    cout << "rho(Bj) 对于方程组 1 = " << rho_Bj_1 << endl;


    // 计算方程组 2 的 rho(Bj) 和 rho(Bg)
    cout << "计算方程组 2 的谱半径:" << endl;
    vector<vector<double>> Bj_2 = create_jacobi_iteration_matrix(A2);
    vector<vector<double>> Bg_2 = create_gauss_seidel_iteration_matrix(A2);

     // 在使用Bg_2之前检查它是否为空
    if (!Bg_2.empty()) {
        double rho_Bg_2 = calculate_spectral_radius_eigen(Bg_2);
        cout << "rho(Bg) 对于方程组 2 = " << rho_Bg_2 << endl;
    } else {
        cout << "警告: Bg_2 为空，无法计算谱半径。" << endl;
    }

    double rho_Bj_2 = calculate_spectral_radius_eigen(Bj_2);
    cout << "rho(Bj) 对于方程组 2 = " << rho_Bj_2 << endl;

    // 测试不同的 omega 值
    cout << "\n测试 SOR 方法 (方程组 1):" << endl;
    for (double omega : {0.5 , 0.6 , 0.7 , 0.8 , 0.9 , 1.0 , 1.05 ,1.1 , 1.15 , 1.2  }) {
        vector<vector<double>> sor_x_history_1;
        vector<double> sor_error_history_1;
        bool sor_converged_1;

        cout << "omega = " << omega << ":" << endl;
        vector<double> x_sor_1 = sor(A1, b1, x0_1, omega, max_iterations, tolerance, sor_x_history_1, sor_error_history_1, sor_converged_1);
        cout << "解: x1 = " << x_sor_1[0] << ", x2 = " << x_sor_1[1] << ", x3 = " << x_sor_1[2] << endl;
        cout << "是否收敛: " << (sor_converged_1 ? "是" : "否") << endl;

        // 将 SOR 的误差数据输出到文件
        ofstream sor_data_1(target_dir + "/sor_error_1_omega_" + to_string(omega) + ".dat");
        if (sor_data_1.is_open()) {
            for (size_t i = 0; i < sor_error_history_1.size(); ++i) {
                sor_data_1 << i << " " << sor_error_history_1[i] << endl;
            }
            sor_data_1.close();
            cout << "omega = " << omega << " 的误差数据已输出到 target/sor_error_1_omega_" << omega << ".dat" << endl;
        } else {
            cout << "无法打开文件以写入 SOR 误差数据 (omega = " << omega << ")" << endl;
        }
    }

    cout << "\n测试 SOR 方法 (方程组 2):" << endl;
    for (double omega : {0.5 , 0.6 , 0.7 , 0.8 , 0.9 , 1.0 , 1.05 ,1.1 , 1.15 , 1.2 }) {
        vector<vector<double>> sor_x_history_2;
        vector<double> sor_error_history_2;
        bool sor_converged_2;

        cout << "omega = " << omega << ":" << endl;
        vector<double> x_sor_2 = sor(A2, b2, x0_2, omega, max_iterations, tolerance, sor_x_history_2, sor_error_history_2, sor_converged_2);
        cout << "解: x1 = " << x_sor_2[0] << ", x2 = " << x_sor_2[1] << ", x3 = " << x_sor_2[2] << endl;
        cout << "是否收敛: " << (sor_converged_2 ? "是" : "否") << endl;

        // 将 SOR 的误差数据输出到文件
        ofstream sor_data_2("target/sor_error_2_omega_" + to_string(omega) + ".dat");
        if (sor_data_2.is_open()) {
            for (size_t i = 0; i < sor_error_history_2.size(); ++i) {
                sor_data_2 << i << " " << sor_error_history_2[i] << endl;
            }
            sor_data_2.close();
            cout << "omega = " << omega << " 的误差数据已输出到 target/sor_error_2_omega_" << omega << ".dat" << endl;
        } else {
            cout << "无法打开文件以写入 SOR 误差数据 (omega = " << omega << ")" << endl;
        }
    }

    return 0;
}
