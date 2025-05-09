def calculate_efficiencies():
    # 输入质量流量
    m_dot = float(input("请输入质量流量 (kg/s): "))
    
    # 输热量（热源）焓值
    h_hot_in = float(input("请输入涡轮入口焓 (h3) (kJ/kg): "))
    h_cold_out = float(input("请输入涡轮出口焓 (h4) (kJ/kg): "))
    
    # 计算输入热量
    Q_in = m_dot * (h_hot_in - h_cold_out)
    print(f"输入热量 (Q_in): {Q_in:.2f} kJ/s")
    
    # 输出功
    h_hot_out = float(input("请输入压缩机出口焓 (h2) (kJ/kg): "))
    W_useful = m_dot * (h_hot_in - h_hot_out)
    print(f"输出功 (W_useful): {W_useful:.2f} kJ/s")

    # 计算热效率
    eta_thermal = W_useful / Q_in
    print(f"热效率 (η_thermal): {eta_thermal:.2%}")

    # 等熵焓值
    h_isentropic = float(input("请输入等熵焓 (h_isentropic) (kJ/kg): "))

    # 输出等熵功
    W_isentropic = m_dot * (h_hot_in - h_isentropic)
    print(f"等熵输出功 (W_isentropic): {W_isentropic:.2f} kJ/s")

    # 计算等熵效率
    eta_isentropic = W_useful / W_isentropic
    print(f"等熵效率 (η_isentropic): {eta_isentropic:.2%}")

if __name__ == "__main__":
    calculate_efficiencies()
