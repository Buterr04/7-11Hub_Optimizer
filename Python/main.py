import os
import sys
from locations import load_default_locations, load_locations_from_file, save_locations_to_file
from network_model import LogisticsNetwork
from optimizers.exhaustive_optimizer import ExhaustiveOptimizer
from optimizers.greedy_optimizer import GreedyOptimizer
from optimizers.simulated_annealing_optimizer import SimulatedAnnealingOptimizer

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
    print("1. 加载默认地点数据")
    print("2. 从文件加载地点数据")
    print("3. 保存地点数据到文件")
    print("4. 查看当前地点数据")
    print("5. 运行穷举法优化算法")
    print("6. 运行贪心算法优化")
    print("7. 运行模拟退火算法优化")
    print("8. 可视化当前网络")
    print("9. 退出")
    print("-" * 60)

def print_locations(locations):
    """打印地点数据"""
    if not locations:
        print("没有地点数据")
        return
    
    print("\n当前地点数据:")
    print("-" * 80)
    print(f"{'ID':<8} {'名称':<12} {'类型':<12} {'X坐标':<8} {'Y坐标':<8} {'容量':<8} {'产品类别'}")
    print("-" * 80)
    
    for loc in locations:
        capacity = str(loc.capacity) if loc.capacity is not None else 'N/A'
        product_categories = ', '.join(loc.product_categories) if loc.product_categories else 'N/A'
        print(f"{loc.id:<8} {loc.name:<12} {loc.type:<12} {loc.x:<8.2f} {loc.y:<8.2f} {capacity:<8} {product_categories}")
    
    print("-" * 80)

def print_optimization_results(network, algorithm_name, execution_time=None):
    """打印优化结果"""
    print(f"\n{algorithm_name}优化结果:")
    print("-" * 60)
    
    if execution_time:
        print(f"执行时间: {execution_time:.4f} 秒")
    
    print("\n生产商-批发商配对:")
    for m_id, w_id in network.manufacturer_wholesaler_pairs.items():
        m_name = network.locations[m_id].name
        w_name = network.locations[w_id].name
        distance = network.distance_matrix[m_id][w_id]
        print(f"{m_name} -> {w_name}, 距离: {distance:.2f}")
    
    print("\n便利店-批发商分配:")
    for s_id, w_ids in network.wholesaler_store_assignments.items():
        s_name = network.locations[s_id].name
        for w_id in w_ids:
            w_name = network.locations[w_id].name
            distance = network.distance_matrix[w_id][s_id]
            print(f"{s_name} <- {w_name}, 距离: {distance:.2f}")
    
    total_distance = network.calculate_total_network_distance()
    print(f"\n总距离: {total_distance:.2f}")
    print("-" * 60)

def main():
    """主函数"""
    locations = load_default_locations()
    network = LogisticsNetwork(locations)
    network.calculate_distances()
    
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = input("请输入选项 (1-9): ")
        
        if choice == '1':
            locations = load_default_locations()
            network = LogisticsNetwork(locations)
            network.calculate_distances()
            print("\n已加载默认地点数据")
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
                print(f"\n无法从 {filename} 加载数据，使用默认数据")
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
            except Exception as e:
                print(f"\n优化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '7':
            import time
            
            try:
                initial_temp = float(input("\n请输入初始温度 (默认: 1000): ") or 1000)
                cooling_rate = float(input("请输入冷却率 (0-1, 默认: 0.95): ") or 0.95)
                iterations = int(input("请输入迭代次数 (默认: 1000): ") or 1000)
                
                start_time = time.time()
                optimized_network = SimulatedAnnealingOptimizer.optimize(
                    network, initial_temp, cooling_rate, iterations)
                execution_time = time.time() - start_time
                
                print_optimization_results(optimized_network, "模拟退火算法", execution_time)
            except Exception as e:
                print(f"\n优化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '8':
            save_path = input("\n请输入保存图像的路径 (默认: network.png): ") or "network.png"
            title = input("请输入图像标题 (默认: 711便利店物流网络): ") or "711便利店物流网络"
            
            try:
                network.visualize_network(title, save_path)
            except Exception as e:
                print(f"\n可视化过程中出错: {e}")
            
            input("\n按Enter键继续...")
        
        elif choice == '9':
            print("\n感谢使用711便利店物流网络优化系统！")
            sys.exit(0)
        
        else:
            print("\n无效选项，请重新输入")
            input("\n按Enter键继续...")

if __name__ == "__main__":
    main()