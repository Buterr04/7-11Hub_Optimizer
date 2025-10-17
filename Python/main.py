import os
import sys
from locations import load_default_locations, load_locations_from_file, save_locations_to_file
from network_model import LogisticsNetwork
from optimizers.exhaustive_optimizer import ExhaustiveOptimizer
from optimizers.greedy_optimizer import GreedyOptimizer
from optimizers.simulated_annealing_optimizer import SimulatedAnnealingOptimizer
from optimizers.kmeans_sa_optimizer import KMeansSimulatedAnnealingOptimizer

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印标题"""
    print("=" * 60)
    print("                711便利店物流网络优化系统")
    print("=" * 60)

def print_menu():
    """打印主菜单"""
    print("\n请选择操作:")
    print("1. 从 locations.csv 重新加载地点数据")
    print("2. 从文件加载地点数据")
    print("3. 保存地点数据到文件")
    print("4. 查看当前地点数据")
    print("5. 运行穷举法优化算法")
    print("6. 运行贪心算法优化")
    print("7. 运行模拟退火算法优化")
    print("8. 运行K-means+模拟退火优化")
    print("9. 可视化当前网络")
    print("10. 退出")
    print("-" * 60)

def print_locations(locations):
    """打印地点数据"""
    if not locations:
        print("没有地点数据")
        return
    
    print("\n当前地点数据:")
    print("-" * 100)
    print(f"{'ID':<8} {'名称':<12} {'类型':<12} {'X坐标':<8} {'Y坐标':<8} {'容量':<8} {'建设成本':<10} {'产品类别'}")
    print("-" * 100)
    
    for loc in locations:
        capacity = str(loc.capacity) if loc.capacity is not None else 'N/A'
        product_categories = ', '.join(loc.product_categories) if loc.product_categories else 'N/A'
        build_cost = getattr(loc, 'build_cost', 0.0)
        build_cost_str = f"{build_cost:.2f}" if build_cost else 'N/A'
        print(f"{loc.id:<8} {loc.name:<12} {loc.type:<12} {loc.x:<8.2f} {loc.y:<8.2f} {capacity:<8} {build_cost_str:<10} {product_categories}")
    
    print("-" * 80)

def print_optimization_results(network, algorithm_name, execution_time=None):
    """打印优化结果"""
    print(f"\n{algorithm_name}优化结果:")
    print("-" * 60)
    
    if execution_time:
        print(f"执行时间: {execution_time:.4f} 秒")
    
    print("\n生产商-批发商配对:")
    for m_id, hubs in network.manufacturer_wholesaler_pairs.items():
        hub_ids = hubs if isinstance(hubs, (list, tuple, set)) else [hubs]
        for w_id in hub_ids:
            if w_id is None:
                continue
            m_name = network.locations[m_id].name
            w_name = network.locations[w_id].name
            distance = network.distance_matrix[m_id][w_id]
            print(f"{m_name} -> {w_name}, 曼哈顿距离: {distance:.2f}")
    
    print("\n便利店-批发商分配:")
    for s_id, w_ids in network.wholesaler_store_assignments.items():
        s_name = network.locations[s_id].name
        for w_id in w_ids:
            w_name = network.locations[w_id].name
            distance = network.distance_matrix[w_id][s_id]
            print(f"{s_name} <- {w_name}, 曼哈顿距离: {distance:.2f}")

    if getattr(network, "store_delivery_paths", None):
        print("\n完整配送路径:")
        for store_id, path_infos in network.store_delivery_paths.items():
            store_name = network.locations[store_id].name
            for path_info in path_infos:
                manufacturer_id = path_info.get('manufacturer_id')
                wholesaler_id = path_info.get('wholesaler_id')
                manufacturer_name = network.locations[manufacturer_id].name if manufacturer_id else '未知生产商'
                wholesaler_name = network.locations[wholesaler_id].name if wholesaler_id else '未知批发商'
                mw_distance = path_info.get('segment_distances', {}).get('manufacturer_to_wholesaler', 0.0)
                ws_distance = path_info.get('segment_distances', {}).get('wholesaler_to_store', 0.0)
                total_path_distance = path_info.get('total_distance', mw_distance + ws_distance)
                print(
                    f"{manufacturer_name} -> {wholesaler_name} -> {store_name}, "
                    f"曼哈顿距离: {mw_distance:.2f} + {ws_distance:.2f} = {total_path_distance:.2f}"
                )
    
    total_distance = network.calculate_total_network_distance()
    print(f"\n总曼哈顿距离: {total_distance:.2f}")
    print("-" * 60)

def main():
    """主函数"""
    locations = load_default_locations()
    network = LogisticsNetwork(locations)
    network.calculate_distances()
    if not locations:
        print("警告: locations.csv 中没有有效的地点数据，请先加载或导入数据。")
        input("\n按Enter键继续...")
    
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = input("请输入选项 (1-10): ")
        
        if choice == '1':
            locations = load_default_locations()
            network = LogisticsNetwork(locations)
            network.calculate_distances()
            if locations:
                print("\n已从 locations.csv 加载地点数据")
            else:
                print("\nlocations.csv 未包含有效地点，请检查文件内容")
            input("\n按Enter键继续...")
        
        elif choice == '2':
            filename = input("\n请输入文件名 (默认: locations.csv): ") or "locations.csv"
            loaded_locations = load_locations_from_file(filename)
            if loaded_locations:
                locations = loaded_locations
                network = LogisticsNetwork(locations)
                network.calculate_distances()
                print(f"\n已从 {filename} 加载地点数据")
            else:
                print(f"\n未能从 {filename} 加载有效地点数据")
            input("\n按Enter键继续...")
        
        elif choice == '3':
            filename = input("\n请输入文件名 (默认: locations.csv): ") or "locations.csv"
            if save_locations_to_file(locations, filename):
                print(f"\n地点数据已保存到 {filename}")
            else:
                print(f"\n保存到 {filename} 失败")
            input("\n按Enter键继续...")
        
        elif choice == '4':
            print_locations(locations)
            input("\n按Enter键继续...")
        
        elif choice == '5':
            import time
            start_time = time.time()
            
            try:
                optimized_network = ExhaustiveOptimizer.optimize(network)
                execution_time = time.time() - start_time
                print_optimization_results(optimized_network, "穷举法", execution_time)
                network = optimized_network
                locations = list(network.locations.values())
            except Exception as e:
                print(f"\n优化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '6':
            import time
            start_time = time.time()
            
            try:
                optimized_network = GreedyOptimizer.optimize(network)
                execution_time = time.time() - start_time
                print_optimization_results(optimized_network, "贪心算法", execution_time)
                network = optimized_network
                locations = list(network.locations.values())
            except Exception as e:
                print(f"\n优化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '7':
            import time
            
            try:
                manufacturer_clusters = int(input("\n请输入生产商聚类数 (默认: 3): ") or 3)
                initial_temp = float(input("\n请输入初始温度 (默认: 1000): ") or 1000)
                cooling_rate = float(input("请输入冷却率 (0-1, 默认: 0.95): ") or 0.95)
                iterations = int(input("请输入迭代次数 (默认: 1000): ") or 1000)
                
                start_time = time.time()
                optimized_network = SimulatedAnnealingOptimizer.optimize(
                    network,
                    manufacturer_clusters=manufacturer_clusters,
                    initial_temp=initial_temp,
                    cooling_rate=cooling_rate,
                    iterations=iterations)
                execution_time = time.time() - start_time
                
                print_optimization_results(optimized_network, "模拟退火算法", execution_time)
                network = optimized_network
                locations = list(network.locations.values())
            except Exception as e:
                print(f"\n优化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '8':
            import time

            try:
                hub_counts_input = input("\n请输入启用中转点数量集合 (例如: 1,2,3，默认: 1-所有): ").strip()
                if hub_counts_input:
                    hub_counts = sorted({int(x) for x in hub_counts_input.split(',') if x.strip().isdigit()})
                else:
                    hub_counts = None

                unit_cost = float(input("请输入单位距离运输成本c (默认: 1.0): ") or 1.0)
                initial_temp = float(input("请输入初始温度 (默认: 500): ") or 500)
                cooling_rate = float(input("请输入冷却率 (0-1, 默认: 0.9): ") or 0.9)
                iterations = int(input("请输入模拟退火迭代次数 (默认: 800): ") or 800)
                kmeans_restarts = int(input("请输入K-means重启次数 (默认: 5): ") or 5)

                start_time = time.time()
                best_solution, evaluated = KMeansSimulatedAnnealingOptimizer.optimize(
                    network,
                    hub_counts=hub_counts,
                    unit_transport_cost=unit_cost,
                    initial_temp=initial_temp,
                    cooling_rate=cooling_rate,
                    iterations=iterations,
                    kmeans_restarts=kmeans_restarts,
                )
                execution_time = time.time() - start_time

                print(f"\nK-means+模拟退火优化结果 (耗时 {execution_time:.2f} 秒):")
                print("-" * 60)
                print(f"启用中转点数量: {best_solution['hub_count']}")
                print(f"启用的中转点: {', '.join(best_solution['active_hubs'])}")
                print(f"建设成本: {best_solution['build_cost']:.2f}")
                print(f"供应商到中转点运输成本: {best_solution['supplier_cost']:.2f}")
                print(f"中转点到末端节点运输成本: {best_solution['store_cost']:.2f}")
                print(f"总成本: {best_solution['total_cost']:.2f}")

                print("\n供应商-中转点连接:")
                for supplier_id in network.manufacturers:
                    supplier_name = network.locations[supplier_id].name
                    for hub_id in best_solution['active_hubs']:
                        hub_name = network.locations[hub_id].name
                        distance = network._ensure_distance(supplier_id, hub_id)
                        print(f"{supplier_name} -> {hub_name}, 曼哈顿距离: {distance:.2f}")

                print("\n便利店分配方案:")
                for store_id, hub_id in best_solution['store_assignments'].items():
                    store_name = network.locations[store_id].name
                    hub_name = network.locations[hub_id].name
                    distance = network._ensure_distance(hub_id, store_id)
                    print(f"{store_name} <- {hub_name}, 曼哈顿距离: {distance:.2f}")

                # 更新网络状态以便可视化使用
                network.manufacturer_wholesaler_pairs = {
                    supplier_id: list(best_solution['active_hubs'])
                    for supplier_id in network.manufacturers
                }
                network.wholesaler_store_assignments = {}
                for store_id, hub_id in best_solution['store_assignments'].items():
                    network.wholesaler_store_assignments.setdefault(store_id, []).append(hub_id)
                network.update_delivery_paths()
                locations = list(network.locations.values())

            except Exception as e:
                print(f"\n优化过程中出错: {e}")

            input("\n按Enter键继续...")

        elif choice == '9':
            save_path = input("\n请输入保存图像的路径 (默认: network.png): ") or "network.png"
            title = input("请输入图像标题 (默认: 711便利店物流网络): ") or "711便利店物流网络"
            
            try:
                network.visualize_network(title, save_path)
            except Exception as e:
                print(f"\n可视化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '10':
            print("\n感谢使用711便利店物流网络优化系统！")
            sys.exit(0)
        
        else:
            print("\n无效选项，请重新输入")
            input("\n按Enter键继续...")

if __name__ == "__main__":
    main()