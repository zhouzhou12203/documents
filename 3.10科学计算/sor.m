% 方程组系数
A = [4 -1 0; -1 4 -1; 0 -1 4];
b = [1; 4; -3];

% 精确解
x_star = [0.5; 1; -0.5];

% 迭代参数
omega_values = [1.03, 1, 1.1];
tolerance = 5e-6;
max_iterations = 100;

for omega = omega_values
    % 初始化
    x = zeros(3, 1); % 初始向量为全零向量
    iterations = 0;

    % 迭代
    for k = 1:max_iterations
        % SOR迭代
        x_new = x;
        x_new(1) = (1-omega)*x(1) + omega*(1 + x(2)) / 4;
        x_new(2) = (1-omega)*x(2) + omega*(4 + x_new(1) + x(3)) / 4;
        x_new(3) = (1-omega)*x(3) + omega*(-3 + x_new(2)) / 4;

        % 检查终止条件
        error = norm(x_star - x_new, inf);
        if error < tolerance
            iterations = k;
            break;
        end

        x = x_new;
    end

    % 输出结果
    if iterations > 0
        fprintf('omega = %.2f, 迭代次数 = %d\n', omega, iterations);
    else
        fprintf('omega = %.2f, 迭代失败\n', omega);
    end
end
