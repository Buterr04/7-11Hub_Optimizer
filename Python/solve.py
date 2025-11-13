import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams
def set_matplotlib_chinese_font_to_pingfang():
    # 字体路径
    pingfang_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"

    if not os.path.exists(pingfang_path):
        raise FileNotFoundError("找不到字体文件，请检查路径。")

    # 创建字体对象
    font_prop = FontProperties(fname=pingfang_path)

    # 设置全局字体（覆盖默认字体族）
    rcParams['font.family'] = font_prop.get_name()

    # 防止中文负号显示为方块
    rcParams['axes.unicode_minus'] = False

    print(f"matplotlib 已设置为中文字体：{font_prop.get_name()}")


set_matplotlib_chinese_font_to_pingfang()
# plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def create_data_model():
    """创建问题数据"""
    data = {}
    try:
        # 读取仓库坐标
        warehouse_df = pd.read_excel('optimized_hubs.xlsx')
        warehouse_coords = list(zip(warehouse_df['横坐标 (X)'], warehouse_df['纵坐标 (Y)']))

        # 读取车辆信息
        car_df = pd.read_excel('car.xlsx')
        data['vehicle_capacities'] = car_df['容量'].astype(float).tolist()
        data['num_vehicles'] = len(car_df)

        # 从 locations.csv 中提取所有 store 节点
        locations_df = pd.read_csv('locations.csv', encoding='utf-8')
        type_series = locations_df['类型'].astype(str).str.lower()
        store_df = locations_df[type_series == 'store'].copy()
        if store_df.empty:
            raise ValueError('locations.csv 未找到类型为 store 的节点')

        # 坐标和需求转换
        store_df['X坐标'] = pd.to_numeric(store_df['X坐标'], errors='coerce')
        store_df['Y坐标'] = pd.to_numeric(store_df['Y坐标'], errors='coerce')

        demand_column = '需求' if '需求' in store_df.columns else '容量'
        store_df[demand_column] = pd.to_numeric(store_df[demand_column], errors='coerce')
        store_df[demand_column] = store_df[demand_column].fillna(0.0)

        if store_df[['X坐标', 'Y坐标']].isna().any().any():
            raise ValueError('locations.csv 中存在坐标缺失的 store 节点')

        store_coords = list(zip(store_df['X坐标'], store_df['Y坐标']))
        store_demands = store_df[demand_column].tolist()

        if all(demand == 0 for demand in store_demands):
            print('警告：所有便利店节点的需求为0，请确认 locations.csv 中的容量/需求配置。')

        # 组合坐标与需求
        data['coordinates'] = warehouse_coords + store_coords
        data['demands'] = [0.0] * len(warehouse_coords) + store_demands

        # 记录仓库与门店索引映射
        data['depots'] = list(range(len(warehouse_coords)))
        data['store_ids'] = store_df['ID'].tolist()

        print(f"读取到{len(warehouse_coords)}个仓库和{len(store_df)}个便利店节点的数据")

        # 计算曼哈顿距离矩阵
        data['distance_matrix'] = []
        for i in range(len(data['coordinates'])):
            row = []
            for j in range(len(data['coordinates'])):
                x1, y1 = data['coordinates'][i]
                x2, y2 = data['coordinates'][j]
                distance = abs(x1 - x2) + abs(y1 - y2)
                row.append(distance)
            data['distance_matrix'].append(row)

        # 配送单价（元/吨·公里）
        data['unit_price'] = 3  # 假设每吨每公里价格

        # 车辆固定使用成本（元）
        data['vehicle_fixed_cost'] = 500

        print('成功从文件导入数据')

    except Exception as e:
        print(f"读取输入数据失败: {e}")

    return data

def split_route(data, route, depot_index=0, max_vehicles=None, reorder_by_angle=False):
    "按原始顺序拆分路径，必要时可选择角度重排"
    if max_vehicles is None:
        max_vehicles = data['num_vehicles']
    vehicle_capacity = data['vehicle_capacities'][0]

    if not route:
        return []

    # 可选：用于初始化时的角度分组，迭代优化阶段保持原始顺序
    groups = split_by_angle_simple(data, route, depot_index) if reorder_by_angle else [route]

    vehicle_routes = []
    for group in groups:
        current_route = []
        current_load = 0

        for node in group:
            demand = data['demands'][node]
            if demand > vehicle_capacity:
                return None  # 单节点需求超载，直接判为无解

            if current_load + demand <= vehicle_capacity:
                current_route.append(node)
                current_load += demand
                continue

            if current_route:
                vehicle_routes.append((depot_index, current_route))

            if len(vehicle_routes) >= max_vehicles:
                assigned = False
                for _, existing_route in vehicle_routes:
                    existing_load = sum(data['demands'][n] for n in existing_route)
                    if existing_load + demand <= vehicle_capacity:
                        existing_route.append(node)
                        assigned = True
                        break
                if not assigned:
                    return None
                current_route = []
                current_load = 0
            else:
                current_route = [node]
                current_load = demand

        if current_route:
            vehicle_routes.append((depot_index, current_route))

        if len(vehicle_routes) > max_vehicles:
            return None

    for _, vr in vehicle_routes:
        total_load = sum(data['demands'][node] for node in vr)
        if total_load > vehicle_capacity:
            return None

    return vehicle_routes


def build_vehicle_plan(data, depot_routes):
    """为所有仓库构建车辆执行计划，确保总车辆数不超过全局上限"""
    total_vehicles = 0
    plan = {}

    for depot in sorted(depot_routes.keys()):
        route = depot_routes[depot]
        vehicle_routes = split_route(data, route, depot)
        if vehicle_routes is None:
            return None

        total_vehicles += len(vehicle_routes)
        if total_vehicles > data['num_vehicles']:
            return None

        plan[depot] = [(depot_idx, vr.copy()) for depot_idx, vr in vehicle_routes]

    return plan


def clone_vehicle_plan(plan):
    """深拷贝车辆执行计划，避免后续操作影响原始记录"""
    return {
        depot: [(depot_idx, route.copy()) for depot_idx, route in routes]
        for depot, routes in plan.items()
    }


def evaluate_solution(data, depot_routes):
    """评估给定仓库-节点分配的成本，若违反车辆上限则返回None"""
    plan = build_vehicle_plan(data, depot_routes)
    if plan is None:
        return None, None

    total_cost = 0
    for depot, vehicle_routes in plan.items():
        depot_cost = calculate_route_cost(data, vehicle_routes)
        vehicle_cost = len(vehicle_routes) * data['vehicle_fixed_cost']

        if has_crossing_paths_simple(data, vehicle_routes):
            depot_cost += 20000

        total_cost += depot_cost + vehicle_cost

    return total_cost, plan

def split_by_angle_simple(data, route, depot_index=0):
    """基于角度将节点分配到不同区域，智能分组避免交叉
    支持多仓库"""
    if len(route) <= 1:
        return [route] if route else []
    
    depot_x, depot_y = data['coordinates'][depot_index]
    
    # 计算每个节点相对于仓库的角度和距离
    node_info = []
    for node in route:
        x, y = data['coordinates'][node]
        angle = math.atan2(y - depot_y, x - depot_x)
        distance = math.sqrt((x - depot_x)**2 + (y - depot_y)**2)
        node_info.append((node, angle, distance))
    
    # 按角度排序
    node_info.sort(key=lambda x: x[1])
    
    # 智能确定分组数量
    vehicle_capacity = data['vehicle_capacities'][0]
    total_demand = sum(data['demands'][node] for node in route)
    min_vehicles_needed = math.ceil(total_demand / vehicle_capacity)
    
    # 平衡车辆数量和路径质量
    if len(route) <= 6:  # 节点较少时，每个节点一辆车
        num_groups = min(len(route), data['num_vehicles'])
    else:  # 节点较多时，基于容量需求
        num_groups = min(min_vehicles_needed + 1, data['num_vehicles'], len(route))
    
    # 如果只需要一辆车，直接返回
    if num_groups <= 1:
        return [route]
    
    # 智能分组：考虑角度分布和容量平衡
    angle_routes = []
    nodes_per_group = len(route) / num_groups
    
    current_group = []
    current_demand = 0
    target_demand = total_demand / num_groups
    
    for i, (node, angle, distance) in enumerate(node_info):
        node_demand = data['demands'][node]
        
        # 检查是否应该开始新组
        should_start_new = (
            len(current_group) >= nodes_per_group and 
            len(angle_routes) < num_groups - 1 and
            current_demand >= target_demand * 0.7  # 至少达到目标需求的70%
        )
        
        if should_start_new and current_group:
            angle_routes.append(current_group)
            current_group = []
            current_demand = 0
        
        current_group.append(node)
        current_demand += node_demand
    
    # 添加最后一组
    if current_group:
        angle_routes.append(current_group)
    
    # 确保不超过车辆数量限制
    while len(angle_routes) > data['num_vehicles']:
        # 合并最小的两组
        smallest_idx = min(range(len(angle_routes)), key=lambda i: len(angle_routes[i]))
        if smallest_idx < len(angle_routes) - 1:
            angle_routes[smallest_idx + 1].extend(angle_routes[smallest_idx])
        else:
            angle_routes[smallest_idx - 1].extend(angle_routes[smallest_idx])
        angle_routes.pop(smallest_idx)
    
    return angle_routes

def calculate_route_cost(data, vehicle_routes):
    "计算路径总成本：成本 = 距离×单价×载重"
    total_cost = 0
    unit_price = data['unit_price']
    
    for route_info in vehicle_routes:
        if isinstance(route_info, tuple) and len(route_info) == 2:
            depot_index, v_route = route_info
        else:
            depot_index = 0  # 默认仓库索引
            v_route = route_info
        
        prev_node = depot_index
        current_load = 0
        
        for node in v_route:
            # 计算当前段的距离
            segment_distance = data['distance_matrix'][prev_node][node]
            # 更新当前载重
            current_load += data['demands'][node]
            # 计算当前段的成本：距离 × 单价 × 当前载重
            segment_cost = segment_distance * unit_price * current_load
            total_cost += segment_cost
            prev_node = node
        
        # 返回仓库段的成本
        return_distance = data['distance_matrix'][prev_node][depot_index]
        return_cost = return_distance * unit_price * current_load
        total_cost += return_cost
    
    return total_cost


def generate_neighbor_solution(current_solution, data, attempts=50):
    """生成邻域解：尝试多种局部操作并返回第一个可行解或None
    操作包括：仓库间交换、仓库内交换、迁移节点、仓库内2-opt。
    为保证可行性，对每个候选解调用 split_route 验证。
    """
    depots = list(current_solution.keys())
    for _ in range(attempts):
        neighbor = {d: current_solution[d].copy() for d in depots}
        op = random.choice(['swap_between', 'swap_within', 'relocate', '2opt'])

        if op == 'swap_between' and len(depots) > 1:
            d1, d2 = random.sample(depots, 2)
            if neighbor[d1] and neighbor[d2]:
                i = random.randrange(len(neighbor[d1]))
                j = random.randrange(len(neighbor[d2]))
                neighbor[d1][i], neighbor[d2][j] = neighbor[d2][j], neighbor[d1][i]

        elif op == 'swap_within':
            d = random.choice(depots)
            if len(neighbor[d]) >= 2:
                i, j = random.sample(range(len(neighbor[d])), 2)
                neighbor[d][i], neighbor[d][j] = neighbor[d][j], neighbor[d][i]

        elif op == 'relocate' and len(depots) > 1:
            d_from, d_to = random.sample(depots, 2)
            if neighbor[d_from]:
                i = random.randrange(len(neighbor[d_from]))
                node = neighbor[d_from].pop(i)
                insert_pos = random.randrange(len(neighbor[d_to]) + 1)
                neighbor[d_to].insert(insert_pos, node)

        elif op == '2opt':
            d = random.choice(depots)
            if len(neighbor[d]) >= 4:
                i = random.randrange(0, len(neighbor[d]) - 2)
                j = random.randrange(i + 1, len(neighbor[d]))
                neighbor[d][i:j+1] = list(reversed(neighbor[d][i:j+1]))

        # 可行性验证：需满足容量及全局车辆上限
        plan = build_vehicle_plan(data, neighbor)
        if plan is not None:
            return neighbor

    return None

def solve_cvrp():
    """使用模拟退火算法解决多仓库CVRP问题"""
    data = create_data_model()
    
    # 模拟退火参数
    initial_temp = 100
    cooling_rate = 0.995
    min_temp = 1
    iterations_per_temp = 30  # 每个温度尝试次数，提高探索能力
    max_iterations = 20000    # 保护性上限，防止无限循环
    
    # 生成初始解（为每个仓库生成初始路径）
    all_nodes = list(range(len(data['depots']), len(data['distance_matrix'])))
    
    # 按最近仓库分配节点
    depot_routes = {depot: [] for depot in data['depots']}
    for node in all_nodes:
        closest_depot = min(data['depots'], 
                           key=lambda d: data['distance_matrix'][d][node])
        depot_routes[closest_depot].append(node)
    
    # 对每个仓库的节点按角度排序
    current_solution = {}
    for depot in data['depots']:
        depot_x, depot_y = data['coordinates'][depot]
        node_angles = []
        for node in depot_routes[depot]:
            x, y = data['coordinates'][node]
            angle = math.atan2(y - depot_y, x - depot_x)
            node_angles.append((node, angle))
        
        # 按角度排序
        node_angles.sort(key=lambda x: x[1])
        current_solution[depot] = [node for node, _ in node_angles]
    
    best_solution = {}
    best_plan = {}
    current_cost, current_plan = evaluate_solution(data, current_solution)

    if current_plan is None:
        # 尝试通过邻域扰动修复初始解
        repaired = generate_neighbor_solution(current_solution, data, attempts=1000)
        if repaired is not None:
            current_solution = {d: r.copy() for d, r in repaired.items()}
            current_cost, current_plan = evaluate_solution(data, current_solution)

    if current_plan is None:
        print("初始解不可行（容量/车辆限制），请检查数据或增加车辆数量。")
        return {}, {}

    best_solution = {depot: route.copy() for depot, route in current_solution.items()}
    best_plan = clone_vehicle_plan(current_plan)
    best_cost = current_cost
    
    # 记录每一代的成本数据
    iteration_costs = [current_cost]  # 记录每一代的当前成本
    best_costs = [best_cost]  # 记录每一代的最优成本
    temperatures = [initial_temp]  # 记录每一代的温度
    iteration_count = 0
    
    # 模拟退火主循环
    temp = initial_temp
    total_iterations = 0
    while temp > min_temp and total_iterations < max_iterations:
        for _ in range(iterations_per_temp):
            total_iterations += 1
            iteration_count += 1

            neighbor_solution = generate_neighbor_solution(current_solution, data, attempts=100)
            if neighbor_solution is None:
                # 无法生成有效邻域解，跳过本次尝试
                continue

            neighbor_cost, neighbor_plan = evaluate_solution(data, neighbor_solution)
            if neighbor_plan is None:
                continue

            # 计算成本差
            cost_diff = neighbor_cost - current_cost

            # 接受准则
            accept = False
            if neighbor_cost < current_cost:
                accept = True
            else:
                try:
                    prob = math.exp(-cost_diff / temp)
                except OverflowError:
                    prob = 0.0
                if random.random() < prob:
                    accept = True

            if accept:
                current_solution = {d: r.copy() for d, r in neighbor_solution.items()}
                current_plan = clone_vehicle_plan(neighbor_plan)
                current_cost = neighbor_cost

                # 更新最优解
                if current_cost < best_cost:
                    best_solution = {depot: route.copy() for depot, route in current_solution.items()}
                    best_plan = clone_vehicle_plan(neighbor_plan)
                    best_cost = current_cost

            # 记录当前迭代的成本数据
            iteration_costs.append(current_cost)
            best_costs.append(best_cost)
            temperatures.append(temp)

            if total_iterations >= max_iterations:
                break

        # 降温
        temp *= cooling_rate
    
    # 绘制模拟退火算法收敛图
    plot_sa_convergence(iteration_costs, best_costs, temperatures, iteration_count)
    
    # 输出最优解
    total_vehicles = 0
    total_cost = 0
    
    if not best_plan:
        print("未找到满足车辆限制的可行解。")
        return best_solution, best_plan

    for depot, vehicle_routes in best_plan.items():
        print(f"=== 仓库 {depot} 的最优路线 ===")
        print(f"使用车辆数量: {len(vehicle_routes)}/{data['num_vehicles']}")
        
        # 计算并显示总成本
        depot_cost = calculate_route_cost(data, vehicle_routes)
        print(f"配送成本: {depot_cost:.2f}元")
        
        # 验证容量约束并显示详细成本
        for i, (route_depot, vehicle_route) in enumerate(vehicle_routes):
            total_load = sum(data['demands'][node] for node in vehicle_route)
            route_cost = calculate_route_cost(data, [(route_depot, vehicle_route)])
            print(f"车辆 {i+1} 载重: {total_load}/{data['vehicle_capacities'][0]}, 成本: {route_cost:.2f}元")
        
        total_vehicles += len(vehicle_routes)
        total_cost += depot_cost
    
    print(f"总使用车辆: {total_vehicles}/{data['num_vehicles']}")
    print(f"总配送成本: {total_cost:.2f}元")
    
    return best_solution, best_plan

def has_crossing_paths_simple(data, vehicle_routes):
    "简化版交叉检测：只检查主要路径段"
    if len(vehicle_routes) < 2:
        return False
    
    coordinates = data['coordinates']
    
    # 只检查从仓库出发的第一段和返回仓库的最后一段
    main_segments = []
    for depot_index, route in vehicle_routes:
        if route:
            depot_coord = coordinates[depot_index]
            # 仓库到第一个节点
            first_seg = (depot_coord, coordinates[route[0]])
            # 最后一个节点到仓库
            last_seg = (coordinates[route[-1]], depot_coord)
            main_segments.extend([first_seg, last_seg])
    
    # 检查主要路径段是否交叉
    for i in range(len(main_segments)):
        for j in range(i + 1, len(main_segments)):
            if do_segments_intersect_simple(main_segments[i], main_segments[j]):
                return True
    
    return False

def do_segments_intersect_simple(seg1, seg2):
    """线段相交检测"""
    p1, p2 = seg1
    p3, p4 = seg2
    
    # 如果线段共享端点，不算交叉
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def print_solution(data, vehicle_routes):
    """打印多辆车解决方案"""
    total_distance = 0
    total_load = 0
    
    for vehicle_id, route in enumerate(vehicle_routes, 1):
        plan_output = f'车辆 {vehicle_id} 的路线:\n'
        route_distance = 0
        route_load = 0
        prev_node = data['depots'][0]  # 使用第一个仓库
        
        # 从仓库出发
        plan_output += f' {data["depots"][0]} (载重: 0) ->'
        
        for node in route:
            route_distance += data['distance_matrix'][prev_node][node]
            route_load += data['demands'][node]
            plan_output += f' {node} (载重: {route_load}) ->'
            prev_node = node
        
        # 返回仓库
        route_distance += data['distance_matrix'][prev_node][data['depots'][0]]
        plan_output += f' {data["depots"][0]} (载重: {route_load})\n'
        plan_output += f'该路线距离: {route_distance}m\n'
        plan_output += f'该路线载重: {route_load}\n'
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    
    print(f'总行驶距离: {total_distance}m')
    print(f'总配送量: {total_load}')

def visualize_solution(data, solution, vehicle_plan=None):
    """优化后的可视化函数，支持多仓库"""
    # 提取节点坐标
    coordinates = data['coordinates']
    x = [coord[0] for coord in coordinates]
    y = [coord[1] for coord in coordinates]
    
    # 创建正方形图形
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 设置更密集的网格线
    ax.grid(True, which='both', linestyle='--', linewidth=1, alpha=1)
    
    # 绘制仓库和门店
    for i, (xi, yi) in enumerate(zip(x, y)):
        if i in data['depots']:
            ax.scatter(xi, yi, c='red', marker='s', s=200, label='仓库' if i == data['depots'][0] else "", zorder=5)
        else:
            ax.scatter(xi, yi, c='blue', marker='o', s=100, label='门店' if i == len(data['depots']) else "", zorder=5)
    
    # 标注所有节点编号
    for i, (xi, yi) in enumerate(zip(x, y)):
        ax.text(xi, yi + 0.2, str(i), ha='center', fontsize=10, 
               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'), zorder=10)
    
    # 定义颜色列表
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b','#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # 绘制每辆车的路径
    vehicle_count = 0
    for depot, route in solution.items():
        # 复用已构造的车辆计划，避免违反全局车辆上限
        if vehicle_plan and depot in vehicle_plan:
            vehicle_routes = vehicle_plan[depot]
        else:
            vehicle_routes = split_route(data, route, depot)
            if vehicle_routes is None:
                continue
            
        for route_info in vehicle_routes:
            if isinstance(route_info, tuple) and len(route_info) == 2:
                depot_index, v_route = route_info
            else:
                depot_index = depot
                v_route = route_info
                
            color = colors[vehicle_count % len(colors)]
            path_x = []
            path_y = []
            
            # 从仓库出发
            path_x.append(coordinates[depot_index][0])
            path_y.append(coordinates[depot_index][1])
            
            for node in v_route:
                path_x.append(coordinates[node][0])
                path_y.append(coordinates[node][1])
            
            # 返回仓库
            path_x.append(coordinates[depot_index][0])
            path_y.append(coordinates[depot_index][1])
            
            # 绘制路径
            ax.plot(path_x, path_y, '-', linewidth=2, color=color, alpha=0.8, 
                   label=f'车辆 {vehicle_count + 1} 路径', zorder=5)
            vehicle_count += 1
    
    # 设置坐标轴为正方形比例
    ax.set_aspect('equal', adjustable='datalim')
    
    # 计算坐标范围
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    range_x = x_max - x_min
    range_y = y_max - y_min
    
    # 统一坐标范围
    margin = max(range_x, range_y) * 0.1
    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)
    
    # 添加图例和标题
    ax.legend(loc='upper right', fontsize=10)
    ax.set_title('多仓库车辆路径规划', fontsize=14, pad=20)
    ax.set_xlabel('X坐标', fontsize=12)
    ax.set_ylabel('Y坐标', fontsize=12)
    
    plt.tight_layout()
    plt.show()

def calculate_vehicle_utilization(data, vehicle_routes):
    """计算车辆利用率"""
    utilizations = []
    for i, route in enumerate(vehicle_routes):
        total_load = sum(data['demands'][node] for node in route)
        vehicle_capacity = data['vehicle_capacities'][0]  # 假设所有车辆容量相同
        utilization = total_load / vehicle_capacity * 100  # 百分比
        utilizations.append((i + 1, utilization))  # (车辆序号, 利用率)
    return utilizations

def plot_vehicle_utilization(data, vehicle_routes):
    """绘制车辆利用率的横向柱状图"""
    utilizations = calculate_vehicle_utilization(data, vehicle_routes)
    
    # 提取数据
    vehicle_numbers = [item[0] for item in utilizations]
    utilization_rates = [item[1] for item in utilizations]
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制横向柱状图
    bars = ax.barh(vehicle_numbers, utilization_rates, 
                   color='skyblue', edgecolor='navy', alpha=0.8)
    
    # 设置标题和标签
    ax.set_title('车辆利用率分布', fontsize=14, fontweight='bold')
    ax.set_xlabel('车辆利用率 (%)', fontsize=12)
    ax.set_ylabel('车辆序号', fontsize=12)
    
    # 设置Y轴刻度为车辆序号
    ax.set_yticks(vehicle_numbers)
    ax.set_yticklabels([f'车辆 {i}' for i in vehicle_numbers])
    
    # 在柱状图上显示数值
    for bar, util in zip(bars, utilization_rates):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{util:.1f}%', ha='left', va='center', fontsize=10)
    
    # 设置网格线
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # 设置X轴范围
    ax.set_xlim(0, max(utilization_rates) * 1.15)
    
    # 美化图形
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.show()
    
    # 打印统计信息
    print("=== 车辆利用率 ===")
    for vehicle_num, util in utilizations:
        print(f"车辆 {vehicle_num}: {util:.1f}%")
    
    avg_utilization = sum(utilization_rates) / len(utilization_rates)
    max_utilization = max(utilization_rates)
    min_utilization = min(utilization_rates)
    
    print(f"平均利用率: {avg_utilization:.1f}%")
    print(f"最高利用率: {max_utilization:.1f}% (车辆 {utilization_rates.index(max_utilization) + 1})")
    print(f"最低利用率: {min_utilization:.1f}% (车辆 {utilization_rates.index(min_utilization) + 1})")

def plot_sa_convergence(iteration_costs, best_costs, temperatures, iteration_count):
    """绘制模拟退火算法成本收敛图"""
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制成本收敛图
    iterations = range(len(iteration_costs))
    ax.plot(iterations, iteration_costs, 'b-', linewidth=1, alpha=0.7, label='当前成本')
    ax.plot(iterations, best_costs, 'r-', linewidth=2, label='最优成本')
    
    ax.set_title('模拟退火算法成本收敛图', fontsize=14, fontweight='bold')
    ax.set_xlabel('迭代次数', fontsize=12)
    ax.set_ylabel('成本 (元)', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # 设置Y轴为科学计数法显示大数字
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    
    # 添加统计信息
    final_cost = best_costs[-1]
    initial_cost = iteration_costs[0]
    if initial_cost and math.isfinite(initial_cost) and math.isfinite(final_cost):
        improvement = ((initial_cost - final_cost) / initial_cost) * 100
    else:
        improvement = 0.0
    
    # 在图上添加统计信息
    ax.text(0.02, 0.98, f'总迭代次数: {iteration_count}\n'
                        f'初始成本: {initial_cost:.2e}元\n'
                        f'最终成本: {final_cost:.2e}元\n'
                        f'优化幅度: {improvement:.1f}%', 
             transform=ax.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    # 打印详细统计信息
    print("=== 模拟退火算法收敛分析 ===")
    print(f"总迭代次数: {iteration_count}")
    print(f"初始成本: {initial_cost:.2f}元")
    print(f"最终成本: {final_cost:.2f}元")
    print(f"成本优化幅度: {improvement:.1f}%")

if __name__ == '__main__':
    data = create_data_model()
    solution, vehicle_plan = solve_cvrp()

    # 从最优执行计划提取车辆路径用于打印和利用率分析
    vehicle_routes = []
    if vehicle_plan:
        for routes in vehicle_plan.values():
            for _, v_route in routes:
                vehicle_routes.append(v_route)

    if vehicle_routes:
        print_solution(data, vehicle_routes)
        plot_vehicle_utilization(data, vehicle_routes)
    else:
        print("未生成满足条件的车辆路径，跳过打印与利用率分析。")

    visualize_solution(data, solution, vehicle_plan)