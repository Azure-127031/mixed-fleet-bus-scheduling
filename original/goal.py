import pulp
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import Circle, Polygon, Wedge
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import random
import matplotlib
import traceback
from collections import defaultdict

# 设置 Matplotlib 中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# ======================
# 参数设置 (修改后)
# ======================
# 站点坐标 (增加了6个新站点)
coords = [
    (2, 8),    # s1 (索引0) - 大站点
    (6, 12),  # s2 (索引1) - 大站点
    (12, 9),    # s3 (索引2) - 大站点
    (4, 10),    # s4 (索引3) - 小站点
    (15, 8),   # s5 (索引4) - 小站点
    (8, 5),    # s6 (索引5) - 小站点
    (14, 6),    # s7 (索引6) - 大站点（新增）
    (10, 3),   # s8 (索引7) - 大站点（新增）
    (5, 6),   # s9 (索引8) - 大站点（新增）
    (11, 7),   # s10 (索引9) - 小站点（新增）
    (3, 5),   # s11 (索引10) - 小站点（新增）
    (12, 10)   # s12 (索引11) - 小站点（新增）
]

# 站点名称 (增加了6个新站点)
site_names = [
    'S1(Start station)', 'S2', 'S3', 'S4', 'S5', 'S6',
    'S7', 'S8', 'S9', 'S10', 'S11', 'S12'
]

# 站点类型 (0-大站点, 1-小站点) - 增加了6个
site_types = [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]

# 乘客需求矩阵 (扩展为12x12)
demand_matrix = [
    # s1 s2 s3  s4  s5 s6 s7 s8  s9  s10 s11 s12
    [0, 90, 50, 30, 8, 7, 65, 15, 20, 10, 15, 5],     # s1
    [80, 0, 70, 0, 10, 2, 58, 22, 12, 8, 6, 14],      # s2
    [75, 151, 0, 5, 5, 15, 30, 25, 18, 7, 12, 9],     # s3
    [30, 6, 11, 0, 21, 0, 15, 10, 8, 12, 5, 7],       # s4
    [20, 11, 9, 0, 0, 16, 10, 15, 7, 9, 11, 13],      # s5
    [15, 7, 3, 15, 0, 0, 8, 12, 6, 14, 9, 11],        # s6
    [22, 18, 25, 12, 15, 50, 0, 20, 25, 8, 12, 15],   # s7
    [15, 20, 22, 8, 12, 34, 18, 0, 30, 10, 8, 12],    # s8
    [18, 15, 20, 10, 8, 12, 22, 28, 0, 15, 10, 18],   # s9
    [10, 12, 8, 15, 10, 18, 9, 12, 16, 0, 20, 25],    # s10
    [12, 8, 10, 9, 12, 15, 11, 9, 12, 18, 0, 30],     # s11
    [8, 15, 12, 11, 14, 10, 13, 10, 15, 22, 28, 0]    # s12
]

# 车型参数 (索引0:大巴, 1:中巴, 2:小巴)
R = [50, 20, 10]  # 载客量
D = [3.0, 2.75, 2.7]  # 单位距离成本
e_consume = [3.0, 2.8, 2.7]  # 单位距离耗电量
k_val = [1.2, 0.9, 0.1]  # 交通影响因子
v = [68, 70, 72]  # 速度 (km/h)
c_e = 1.0  # 电价
vehicle_names = ['大巴', '中巴', '小巴']
vehicle_colors = ['#FF5733', '#33FF57', '#3357FF']  # 颜色

# 固定成本归一化常数
D_norm = max(D)  # 3.0
# 电耗归一化常数
E_norm = max(e_consume)  # 3.0
# 交通影响归一化常数
J_norm = max(k_val)  # 1.2

# 乘客最大等待时间 (分钟)
MAX_WAIT_TIME = 5

# 车辆可用数量 (增加车辆可用量以适应更多站点)
avail_vehicles = [50, 150, 250]

# 站点索引
all_stations = list(range(len(coords)))

# 固定路线定义 (保持不变)
fixed_route1 = [(0, 1), (1, 2), (2, 6), (6, 7), (7, 8), (8, 0)]  # S1->S2->S3->S1
fixed_route2 = [(0, 8), (8, 7), (7, 6), (6, 2), (2, 1), (1, 0)]  # S1->S3->S2->S1

# 所有固定路段
fixed_legs = set(fixed_route1 + fixed_route2)

# ======================
# 辅助函数 (保持不变)
# ======================
def calc_distance(coord1, coord2):
    """计算两点间距离"""
    dx = coord1[0] - coord2[0]
    dy = coord1[1] - coord2[1]
    return math.sqrt(dx * dx + dy * dy)

def calculate_distances(coords):
    """计算距离矩阵"""
    n_sites = len(coords)
    dist_matrix = [[0.0] * n_sites for _ in range(n_sites)]
    for i in range(n_sites):
        for j in range(n_sites):
            if i != j:
                dist_matrix[i][j] = calc_distance(coords[i], coords[j])
    return dist_matrix

def calc_route_distance(route):
    """计算路线总距离"""
    distance = 0
    for (i, j) in route:
        distance += calc_distance(coords[i], coords[j])
    return distance

def calculate_route_demand(route, demand_matrix):
    """
    计算整条固定路线的总需求
    返回: 整条路线的总乘客需求
    """
    total_demand = 0
    # 提取路线中的节点序列
    nodes = []
    for i, (start, end) in enumerate(route):
        if i == 0:
            nodes.append(start)
        nodes.append(end)

    # 计算整条路线的总需求
    n = len(nodes)
    for i in range(n - 1):
        for j in range(i + 1, n):
            start_node = nodes[i]
            end_node = nodes[j]
            total_demand += demand_matrix[start_node][end_node]

    return total_demand

def calculate_segment_passengers(route, demand_matrix):
    """
    计算固定路线各路段上的乘客数量
    返回: 各路段乘客量字典
    """
    # 提取路线中的节点序列
    nodes = []
    for i, (start, end) in enumerate(route):
        if i == 0:
            nodes.append(start)
        nodes.append(end)

    # 计算每个路段上的乘客量
    segment_passengers = {}
    n = len(nodes)

    # 创建节点到索引的映射
    node_to_idx = {node: idx for idx, node in enumerate(nodes)}

    # 初始化各路段乘客量为0
    for i in range(n - 1):
        segment_passengers[(nodes[i], nodes[i + 1])] = 0

    # 遍历所有OD对
    for i in range(n - 1):
        for j in range(i + 1, n):
            start_node = nodes[i]
            end_node = nodes[j]
            demand = demand_matrix[start_node][end_node]

            # 从起点到终点经过的所有路段
            for k in range(i, j):
                seg_start = nodes[k]
                seg_end = nodes[k + 1]
                segment_passengers[(seg_start, seg_end)] += demand

    return segment_passengers

# ======================
# 全局变量计算 (保持不变)
# ======================
dist_matrix = calculate_distances(coords)
fixed_route_distance1 = calc_route_distance(fixed_route1)
fixed_route_distance2 = calc_route_distance(fixed_route2)

# 计算整条固定路线的总需求和各路段乘客量
route1_total_demand = calculate_route_demand(fixed_route1, demand_matrix)
route2_total_demand = calculate_route_demand(fixed_route2, demand_matrix)
route1_segment_passengers = calculate_segment_passengers(fixed_route1, demand_matrix)
route2_segment_passengers = calculate_segment_passengers(fixed_route2, demand_matrix)

# 检查固定路段是否超时
fixed_legs_time_status = {}
for (i, j) in fixed_legs:
    travel_time = dist_matrix[i][j] / v[2] * 60  # 使用小巴速度
    fixed_legs_time_status[(i, j)] = (travel_time > MAX_WAIT_TIME, travel_time)

# 计算最大车辆需求
max_demand = max(max(row) for row in demand_matrix)  # 最大站点需求
L = [
    math.ceil(max_demand / (R[0] * 0.6)),  # 大巴最大数量
    math.ceil(max_demand / (R[1] * 0.4)),  # 中巴最大数量
    math.ceil(max_demand / R[2])  # 小巴最大数量
]

def objective(X):
    prob, *_ = solve_scheduling(X)  # 只取第一个返回值 prob
    status = pulp.LpStatus[prob.status]

    # 优化失败，返回大惩罚值
    if status != 'Optimal':
        return 1e5

    # Solve the problem (静默模式)
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    cost = pulp.value(prob.objective)
    return cost

# ======================
# 优化模型求解 (考虑站点乘客上下车) (保持不变)
# ======================
def solve_scheduling(X):

    X = [max(0, int(round(x))) for x in X]
    bus1, mid1, bus2, mid2 = X[0:4]

    prob = pulp.LpProblem("Route_Capacity_Constrained_Scheduling", pulp.LpMinimize)

    # === 1. 定义变量 ===
    x = {}
    for i in all_stations:
        for j in all_stations:
            if i != j:
                if (i, j) in fixed_legs and fixed_legs_time_status[(i, j)][0]:
                    # 禁用小巴
                    x[(i, j, 2)] = pulp.LpVariable(f'minibus_{i}_{j}', lowBound=0, upBound=0, cat='Integer')
                else:
                    # 启用小巴（可设置最大上限）
                    x[(i, j, 2)] = pulp.LpVariable(f'minibus_{i}_{j}', lowBound=0, cat='Integer')

    # 固定大巴中巴数量
    y_bus_route1 = pulp.LpVariable('bus_count_route1', lowBound=bus1, upBound=bus1, cat='Integer')
    y_mid_route1 = pulp.LpVariable('midbus_count_route1', lowBound=mid1, upBound=mid1, cat='Integer')
    y_bus_route2 = pulp.LpVariable('bus_count_route2', lowBound=bus2, upBound=bus2, cat='Integer')
    y_mid_route2 = pulp.LpVariable('midbus_count_route2', lowBound=mid2, upBound=mid2, cat='Integer')

    # === 2. 构建目标函数（使用归一化常数）===
    total_cost = 0

    # 固定路线部分
    for route, dist, bus_var, mid_var in [
        (fixed_route1, fixed_route_distance1, y_bus_route1, y_mid_route1),
        (fixed_route2, fixed_route_distance2, y_bus_route2, y_mid_route2)
    ]:
        # 固定成本部分 (归一化)
        fixed_term = dist * (
                bus_var * (D[0] / D_norm) +
                mid_var * (D[1] / D_norm)
        )

        # 电耗部分 (归一化)
        energy_term = dist * (
                bus_var * (e_consume[0] / E_norm) * c_e +
                mid_var * (e_consume[1] / E_norm) * c_e
        )

        # 交通影响部分 (归一化)
        traffic_term = (
                bus_var * (k_val[0] / J_norm) +
                mid_var * (k_val[1] / J_norm)
        )

        total_cost += fixed_term + energy_term - traffic_term  # 交通影响为负数

    # 小巴部分
    for (i, j, k), var in x.items():
        dij = dist_matrix[i][j]
        # 固定成本部分 (归一化)
        fixed_term = var * dij * (D[k] / D_norm)

        # 电耗部分 (归一化)
        energy_term = var * dij * (e_consume[k] / E_norm) * c_e

        # 交通影响部分 (归一化)
        traffic_term = var * (k_val[k] / J_norm)

        total_cost += fixed_term + energy_term - traffic_term  # 交通影响为负数

    prob += total_cost, "Total_Cost"

    # === 3. 添加约束 ===

    # 固定路线总需求
    prob += y_bus_route1 * R[0] * 0.6 + y_mid_route1 * R[1] * 0.4 >= route1_total_demand, "Route1_Demand"
    prob += y_bus_route2 * R[0] * 0.6 + y_mid_route2 * R[1] * 0.4 >= route2_total_demand, "Route2_Demand"

    # 固定路线分段容量
    for (i, j), p in route1_segment_passengers.items():
        prob += y_bus_route1 * R[0] * 0.6 + y_mid_route1 * R[1] * 0.4 >= p, f"Seg_R1_{i}_{j}"
    for (i, j), p in route2_segment_passengers.items():
        prob += y_bus_route2 * R[0] * 0.6 + y_mid_route2 * R[1] * 0.4 >= p, f"Seg_R2_{i}_{j}"

    # 小巴服务需求
    for i in all_stations:
        for j in all_stations:
            if i != j and demand_matrix[i][j] > 0:
                if (i, j) not in fixed_route1 and (i, j) not in fixed_route2:
                    prob += x[(i, j, 2)] * R[2] >= demand_matrix[i][j], f"OD_{i}_{j}"

    # 车辆数量限制
    prob += y_bus_route1 + y_bus_route2 <= avail_vehicles[0], "Bus_Limit"
    prob += y_mid_route1 + y_mid_route2 <= avail_vehicles[1], "Mid_Limit"
    prob += pulp.lpSum(var for (_, _, k), var in x.items() if k == 2) <= avail_vehicles[2], "Mini_Limit"

    # === 4. 求解 ===
    try:
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=10, gapRel=0.01)
        prob.solve(solver)
    except Exception as e:
        print(f"求解异常，尝试默认求解器: {e}")
        prob.solve()

    # === 5. 解析结果 ===
    results = {}
    for key, var in x.items():
        if var.varValue and var.varValue > 0:
            results[key] = int(round(var.varValue))

    def safe_value(var):
        return max(0, int(var.varValue)) if var.varValue is not None else 0

    bus1_val = safe_value(y_bus_route1)
    mid1_val = safe_value(y_mid_route1)
    bus2_val = safe_value(y_bus_route2)
    mid2_val = safe_value(y_mid_route2)

    # 将结果写入每条固定路段
    for (i, j) in fixed_route1:
        if bus1_val > 0:
            results[(i, j, 0)] = bus1_val
        if mid1_val > 0:
            results[(i, j, 1)] = mid1_val

    for (i, j) in fixed_route2:
        if bus2_val > 0:
            results[(i, j, 0)] = bus2_val
        if mid2_val > 0:
            results[(i, j, 1)] = mid2_val

    total_bus = bus1_val + bus2_val
    total_mid = mid1_val + mid2_val

    return prob, results, total_bus, total_mid, bus1_val, mid1_val, bus2_val, mid2_val

# ======================
# 可视化函数 (保持不变)
# ======================
def plot_scheduling_solution(coords, site_types, site_names, solution, bus_count_route1, mid_count_route1,
                             bus_count_route2, mid_count_route2):
    plt.figure(figsize=(16, 12))

    # 绘制站点
    for i, (x, y) in enumerate(coords):
        color = '#3498DB' if site_types[i] == 0 else '#E74C3C'
        size = 120 if site_types[i] == 0 else 80
        plt.scatter(x, y, s=size, c=color, zorder=5)
        offset = 0.5 if i < 6 else 0.7  # 新增站点偏移量更大
        plt.text(x, y + offset, site_names[i], fontsize=9, ha='center', va='bottom', zorder=6)

    # 绘制需求连接线
    for i in range(len(coords)):
        for j in range(len(coords)):
            if i != j and demand_matrix[i][j] > 0:
                x1, y1 = coords[i]
                x2, y2 = coords[j]
                plt.plot([x1, x2], [y1, y2], 'k--', alpha=0.2, lw=0.8)

                # 标注需求数量
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                plt.text(mid_x, mid_y, f'{demand_matrix[i][j]}人',
                         fontsize=8, color='purple', ha='center', va='center',
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.6))

    # 绘制车辆路径和分配
    vehicle_paths = {}

    # 收集所有路径
    for (i, j, k), count in solution.items():
        if count > 0:
            key = (i, j)
            if key not in vehicle_paths:
                vehicle_paths[key] = []
            vehicle_paths[key].append((k, int(count)))

    # 为相同路径的不同车型分配偏移量
    offset_angles = {}

    # 绘制路径
    for (i, j), vehicles in vehicle_paths.items():
        x1, y1 = coords[i]
        x2, y2 = coords[j]
        dx, dy = x2 - x1, y2 - y1
        angle = math.atan2(dy, dx)

        # 计算路径长度
        path_len = math.sqrt(dx * dx + dy * dy)

        # 为不同车型分配偏移角度
        if (i, j) not in offset_angles:
            offset_angles[(i, j)] = {}
        for idx, (k, count) in enumerate(vehicles):
            if k not in offset_angles[(i, j)]:
                offset_angle = (idx - len(vehicles) / 2 + 0.5) * 0.15
                offset_angles[(i, j)][k] = offset_angle
            else:
                offset_angle = offset_angles[(i, j)][k]

            # 计算偏移向量
            offset_x = math.sin(angle) * offset_angle
            offset_y = -math.cos(angle) * offset_angle

            # 路径起点和终点
            start_x = x1 + offset_x
            start_y = y1 + offset_y
            end_x = x2 + offset_x
            end_y = y2 + offset_y

            # 绘制路径
            color = vehicle_colors[k]

            # 绘制箭头
            plt.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                         arrowprops=dict(arrowstyle='->', lw=2, color=color, alpha=0.8, shrinkA=5, shrinkB=5))

            # 标注车型和数量
            label_x = (start_x * 0.6 + end_x * 0.4)
            label_y = (start_y * 0.6 + end_y * 0.4)

            # 特殊标注固定路线
            route_label = ""
            if (i, j) in fixed_route1 and k in [0, 1]:
                route_label = " (Fixed route1)"
            elif (i, j) in fixed_route2 and k in [0, 1]:
                route_label = " (Fixed route2)"

            # 车型标注
            if k == 0:
                label = f'Large bus: {count}{route_label}'
            elif k == 1:
                label = f'Medium bus: {count}{route_label}'
            else:
                # 小巴标注
                travel_time = dist_matrix[i][j] / v[2] * 60
                if (i, j) in fixed_legs and fixed_legs_time_status.get((i, j), (False, 0))[0]:
                    time_status = "禁用小巴"
                elif (i, j) in fixed_legs and travel_time <= MAX_WAIT_TIME:
                    time_status = "非高峰期"
                else:
                    time_status = "灵活调度"
                label = f'Mini bus: {count}'

            plt.text(label_x, label_y, label,
                     fontsize=9, color=color, ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8, ec=color))

    # 添加图例
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498DB', markersize=10, label='Large station'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#E74C3C', markersize=10, label='Small station'),
        Line2D([0], [0], color=vehicle_colors[0], lw=2, label='Large bus'),
        Line2D([0], [0], color=vehicle_colors[1], lw=2, label='Medium bus'),
        Line2D([0], [0], color=vehicle_colors[2], lw=2, label='Mini bus')
    ]

    plt.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # 设置标题和标签
    plt.title(f'Schematic diagram of traffic dispatching optimization', fontsize=14)
    plt.xlabel('X coordinates (km)', fontsize=12)
    plt.ylabel('Y coordinates (km)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    return plt

# ======================
# 结果输出函数 (保持不变)
# ======================
def print_solution(prob, solution, total_bus, total_mid, bus_count_route1, mid_count_route1, bus_count_route2,
                   mid_count_route2):
    print("=" * 60)
    print("站点容量约束交通调度优化结果")
    print(f"最大等待时间: {MAX_WAIT_TIME}分钟")
    print("=" * 60)

    # 求解状态和目标值
    print(f"求解状态: {pulp.LpStatus[prob.status]}")
    if prob.status == pulp.LpStatusOptimal:
        print(f"总运营成本: ¥{pulp.value(prob.objective):.2f}")
    else:
        print("未找到最优解，当前目标值: ", pulp.value(prob.objective))
    print("\n")

    # 车型统计
    minibus_count = 0
    for key, count in solution.items():
        if key[2] == 2 and count > 0:
            minibus_count += count

    print("车型调度统计:")
    print(f"  大巴(高峰人群): {int(total_bus)}辆 (可用: {avail_vehicles[0]})")
    print(f"    路线1: {int(bus_count_route1)}辆, 路线2: {int(bus_count_route2)}辆")
    print(f"  中巴(分散人群): {int(total_mid)}辆 (可用: {avail_vehicles[1]})")
    print(f"    路线1: {int(mid_count_route1)}辆, 路线2: {int(mid_count_route2)}辆")
    print(f"  小巴: {int(minibus_count)}辆 (可用: {avail_vehicles[2]})")
    print("\n")

    # 详细车辆分配
    print("固定路线1车辆调度 (S1->S2->S3->S7->S8->S9->S1):")
    print(f"  路线总需求: {route1_total_demand}人")
    if bus_count_route1 > 0:
        bus_capacity = bus_count_route1 * R[0] * 0.6
        print(
            f"  大巴(高峰人群): {int(bus_count_route1)}辆 (提供{int(bus_capacity)}运力, 占比: {bus_capacity / route1_total_demand * 100:.1f}%)")
    if mid_count_route1 > 0:
        mid_capacity = mid_count_route1 * R[1] * 0.4
        print(
            f"  中巴(分散人群): {int(mid_count_route1)}辆 (提供{int(mid_capacity)}运力, 占比: {mid_capacity / route1_total_demand * 100:.1f}%)")

    # 输出各路段乘客量和容量
    print("\n  路段容量验证:")
    for (i, j), passengers in route1_segment_passengers.items():
        seg_capacity = bus_count_route1 * R[0] * 0.6 + mid_count_route1 * R[1] * 0.4
        status = "满足" if seg_capacity >= passengers else "不满足"
        print(f"    {site_names[i]}→{site_names[j]}: {passengers}人, 容量{seg_capacity:.1f}人 - {status}")

    print("\n固定路线2车辆调度 (S1->S9->S8->S7->S3->S2->S1):")
    print(f"  路线总需求: {route2_total_demand}人")
    if bus_count_route2 > 0:
        bus_capacity = bus_count_route2 * R[0] * 0.6
        print(
            f"  大巴: {int(bus_count_route2)}辆 (提供{int(bus_capacity)}运力, 占比: {bus_capacity / route2_total_demand * 100:.1f}%)")
    if mid_count_route2 > 0:
        mid_capacity = mid_count_route2 * R[1] * 0.4
        print(
            f"  中巴: {int(mid_count_route2)}辆 (提供{int(mid_capacity)}运力, 占比: {mid_capacity / route2_total_demand * 100:.1f}%)")

    # 输出各路段乘客量和容量
    print("\n  路段容量验证:")
    for (i, j), passengers in route2_segment_passengers.items():
        seg_capacity = bus_count_route2 * R[0] * 0.6 + mid_count_route2 * R[1] * 0.4
        status = "满足" if seg_capacity >= passengers else "不满足"
        print(f"    {site_names[i]}→{site_names[j]}: {passengers}人, 容量{seg_capacity:.1f}人 - {status}")
    print("\n")

    # 小巴灵活调度路线
    print("小巴:")
    for (i, j, k), count in solution.items():
        if k == 2 and count > 0 and (i, j) not in fixed_route1 and (i, j) not in fixed_route2:
            travel_time = dist_matrix[i][j] / v[2] * 60
            capacity = count * R[2]
            status = "满足" if capacity >= demand_matrix[i][j] else "不满足"
            print(
                f"  {site_names[i]} → {site_names[j]}: {int(count)}辆 (需求: {demand_matrix[i][j]}人, 容量: {capacity}人 - {status})")
    print("\n")

    # 验证需求满足情况
    print("需求满足验证:")
    unmet_demand = False
    total_demand = 0
    total_provided = 0

    # 检查固定路线整体需求是否满足
    route1_cap = bus_count_route1 * R[0] * 0.6 + mid_count_route1 * R[1] * 0.4
    route1_status = "满足" if route1_cap >= route1_total_demand else "未满足"
    if route1_cap < route1_total_demand: unmet_demand = True
    print(f"  固定路线1: {route1_status} 总需求:{route1_total_demand}人, 提供运力:{route1_cap:.1f}")

    route2_cap = bus_count_route2 * R[0] * 0.6 + mid_count_route2 * R[1] * 0.4
    route2_status = "满足" if route2_cap >= route2_total_demand else "未满足"
    if route2_cap < route2_total_demand: unmet_demand = True
    print(f"  固定路线2: {route2_status} 总需求:{route2_total_demand}人, 提供运力:{route2_cap:.1f}")

    # 检查非固定路线需求是否满足
    for i in all_stations:
        for j in all_stations:
            if i != j and demand_matrix[i][j] > 0:
                # 检查是否为固定路线OD对
                is_fixed_od = False
                for (k, l) in fixed_route1 + fixed_route2:
                    if (i, j) == (k, l):
                        is_fixed_od = True
                        break

                if not is_fixed_od:
                    total_demand += demand_matrix[i][j]
                    cap = solution.get((i, j, 2), 0) * R[2]
                    total_provided += cap
                    status = "满足" if cap >= demand_matrix[i][j] else "未满足"
                    if cap < demand_matrix[i][j]: unmet_demand = True
                    print(f"  {site_names[i]}→{site_names[j]}: {status} 需要{demand_matrix[i][j]}人, 提供{cap:.1f}运力")

    # 计算资源利用率
    total_fixed_demand = route1_total_demand + route2_total_demand
    total_all_demand = total_fixed_demand + total_demand
    total_all_provided = route1_cap + route2_cap + total_provided
    utilization = total_all_provided / total_all_demand * 100 if total_all_demand > 0 else 0

    print(f"\n总需求: {total_all_demand}人, 总运力: {total_all_provided:.1f}人")
    print(f"资源利用率: {utilization:.2f}%")

    if unmet_demand:
        print("\n警告: 部分需求未完全满足! 建议增加车辆或调整路线")
    else:
        print("\n所有需求均已满足!")

    print("\n" + "=" * 60)

# ======================
# 主程序 (保持不变)
# ======================
if __name__ == "__main__":
    # 计算距离矩阵
    dist_matrix = calculate_distances(coords)

    # 计算固定路线总需求和各路段乘客量
    route1_total_demand = calculate_route_demand(fixed_route1, demand_matrix)
    route2_total_demand = calculate_route_demand(fixed_route2, demand_matrix)
    route1_segment_passengers = calculate_segment_passengers(fixed_route1, demand_matrix)
    route2_segment_passengers = calculate_segment_passengers(fixed_route2, demand_matrix)

    # 更新固定路段时间状态
    fixed_legs_time_status = {}
    for (i, j) in set(fixed_route1 + fixed_route2):
        travel_time = dist_matrix[i][j] / v[2] * 60
        fixed_legs_time_status[(i, j)] = (travel_time > MAX_WAIT_TIME, travel_time)

    # 打印路线分析
    print("=" * 60)
    print("站点容量约束交通调度优化")
    print("=" * 60)

    print("固定路线1 (S1->S2->S3->S1):")
    print(f"  路线总距离: {fixed_route_distance1:.1f}公里")
    print(f"  路线总需求: {route1_total_demand}人")
    for (i, j) in fixed_route1:
        start_name = site_names[i]
        end_name = site_names[j]
        travel_time = fixed_legs_time_status[(i, j)][1]
        if fixed_legs_time_status[(i, j)][0]:
            status = "超时 (禁用小巴)"
        elif travel_time <= MAX_WAIT_TIME:
            status = "未超时 (允许小巴)"
        else:
            status = "超时 (禁用小巴)"
        print(f"  {start_name}→{end_name}: {travel_time:.1f}分钟 {status}")

    print("\n  路段乘客量分析:")
    for (i, j), passengers in route1_segment_passengers.items():
        print(f"    {site_names[i]}→{site_names[j]}: {passengers}人")

    print("\n固定路线2 (S1->S3->S2->S1):")
    print(f"  路线总距离: {fixed_route_distance2:.1f}公里")
    print(f"  路线总需求: {route2_total_demand}人")
    for (i, j) in fixed_route2:
        start_name = site_names[i]
        end_name = site_names[j]
        travel_time = fixed_legs_time_status[(i, j)][1]
        if fixed_legs_time_status[(i, j)][0]:
            status = "超时 (禁用小巴)"
        elif travel_time <= MAX_WAIT_TIME:
            status = "未超时 (允许小巴)"
        else:
            status = "超时 (禁用小巴)"
        print(f"  {start_name}→{end_name}: {travel_time:.1f}分钟 {status}")

    print("\n  路段乘客量分析:")
    for (i, j), passengers in route2_segment_passengers.items():
        print(f"    {site_names[i]}→{site_names[j]}: {passengers}人")

    print("\n" + "=" * 60)

    # 求解优化问题
    try:
        print("\n正在求解优化问题...")
        # 根据需求计算初始车辆估计
        bus1_init = max(5, math.ceil(route1_total_demand * 0.5 / (R[0] * 0.6)))
        mid1_init = max(3, math.ceil(route1_total_demand * 0.5 / (R[1] * 0.4)))
        bus2_init = max(6, math.ceil(route2_total_demand * 0.5 / (R[0] * 0.6)))
        mid2_init = max(4, math.ceil(route2_total_demand * 0.5 / (R[1] * 0.4)))

        # 使用改进的初始解
        X = [bus1_init, mid1_init, bus2_init, mid2_init] + [1] * 36

        prob, solution, total_bus, total_mid, bus_count_route1, mid_count_route1, bus_count_route2, mid_count_route2 = solve_scheduling(X)
        # 输出结果
        print_solution(prob, solution, total_bus, total_mid, bus_count_route1, mid_count_route1, bus_count_route2,
                       mid_count_route2)

        # 绘制分配示意图
        plt = plot_scheduling_solution(coords, site_types, site_names, solution, bus_count_route1, mid_count_route1,
                                       bus_count_route2, mid_count_route2)

        # 保存并显示结果
        plt.savefig(f'capacity_constrained_scheduling_{MAX_WAIT_TIME}min.png', dpi=300)
        plt.show()

        result = objective(X)
        print("目标函数值:", result)

    except Exception as e:
        print(f"求解过程中发生错误: {str(e)}")
        traceback.print_exc()
        print("建议检查约束条件或增加可用资源")
