% ������ϵ��
A = [4 -1 0; -1 4 -1; 0 -1 4];
b = [1; 4; -3];

% ��ȷ��
x_star = [0.5; 1; -0.5];

% ��������
omega_values = [1.03, 1, 1.1];
tolerance = 5e-6;
max_iterations = 100;

for omega = omega_values
    % ��ʼ��
    x = zeros(3, 1); % ��ʼ����Ϊȫ������
    iterations = 0;

    % ����
    for k = 1:max_iterations
        % SOR����
        x_new = x;
        x_new(1) = (1-omega)*x(1) + omega*(1 + x(2)) / 4;
        x_new(2) = (1-omega)*x(2) + omega*(4 + x_new(1) + x(3)) / 4;
        x_new(3) = (1-omega)*x(3) + omega*(-3 + x_new(2)) / 4;

        % �����ֹ����
        error = norm(x_star - x_new, inf);
        if error < tolerance
            iterations = k;
            break;
        end

        x = x_new;
    end

    % ������
    if iterations > 0
        fprintf('omega = %.2f, �������� = %d\n', omega, iterations);
    else
        fprintf('omega = %.2f, ����ʧ��\n', omega);
    end
end
