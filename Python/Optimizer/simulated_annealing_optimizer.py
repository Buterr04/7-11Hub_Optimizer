import random
import math
import copy
from network_model import LogisticsNetwork

class SimulatedAnnealingOptimizer:
    """使用模拟退火算法优化物流网络"""
    
    @staticmethod
    def optimize(network, initial_temp=1000, cooling_rate=0.95, iterations=1000):
        """优化物流网络"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network必须是LogisticsNetwork类型")
        
        # 确保距离矩阵已计算
        if not network.distance_matrix:
            network.calculate_distances()
        
        # 优化生产商和批发商的配对
        SimulatedAnnealingOptimizer._optimize_manufacturer_wholesaler_pairs(
            network, initial_temp, cooling_rate, iterations)
        
        # 优化批发商到便利店的分配
        SimulatedAnnealingOptimizer._optimize_wholesaler_store_assignments(network)
        
        return network
    
    @staticmethod
    def _optimize_manufacturer_wholesaler_pairs(network, initial_temp, cooling_rate, iterations):
        """使用模拟退火算法优化生产商和批发商的配对"""
        if len(network.manufacturers) != len(network.wholesalers):
            raise ValueError("生产商和批发商的数量必须相等")
        
        # 初始解：随机配对
        current_solution = {}
        wholesalers_list = list(network.wholesalers)
        random.shuffle(wholesalers_list)
        
        for i, m_id in enumerate(network.manufacturers):
            current_solution[m_id] = wholesalers_list[i]
        
        # 计算初始解的总距离
        current_distance = SimulatedAnnealingOptimizer._calculate_total_distance(
            network, current_solution)
        
        best_solution = copy.deepcopy(current_solution)
        best_distance = current_distance
        
        # 模拟退火过程
        temp = initial_temp
        
        for i in range(iterations):
            # 生成新解：交换两个批发商的分配
            new_solution = copy.deepcopy(current_solution)
            
            # 随机选择两个生产商
            m1, m2 = random.sample(network.manufacturers, 2)
            
            # 交换它们的批发商
            new_solution[m1], new_solution[m2] = new_solution[m2], new_solution[m1]
            
            # 计算新解的总距离
            new_distance = SimulatedAnnealingOptimizer._calculate_total_distance(
                network, new_solution)
            
            # 决定是否接受新解
            if new_distance < current_distance:
                # 如果新解更好，总是接受
                current_solution = new_solution
                current_distance = new_distance
                
                # 更新最佳解
                if new_distance < best_distance:
                    best_solution = copy.deepcopy(new_solution)
                    best_distance = new_distance
            else:
                # 如果新解更差，以一定概率接受
                delta = new_distance - current_distance
                acceptance_probability = math.exp(-delta / temp)
                
                if random.random() < acceptance_probability:
                    current_solution = new_solution
                    current_distance = new_distance
            
            # 降低温度
            temp *= cooling_rate
        
        network.manufacturer_wholesaler_pairs = best_solution
        return best_solution, best_distance
    
    @staticmethod
    def _calculate_total_distance(network, solution):
        """计算给定配对方案的总距离"""
        total_distance = 0
        for m_id, w_id in solution.items():
            total_distance += network.distance_matrix[m_id][w_id]
        return total_distance
    
    @staticmethod
    def _optimize_wholesaler_store_assignments(network):
        """为每个便利店分配最近的批发商"""
        assignments = {}
        
        for store_id in network.stores:
            min_distance = float('inf')
            best_wholesaler = None
            
            for wholesaler_id in network.wholesalers:
                distance = network.distance_matrix[wholesaler_id][store_id]
                if distance < min_distance:
                    min_distance = distance
                    best_wholesaler = wholesaler_id
            
            if store_id not in assignments:
                assignments[store_id] = []
            assignments[store_id].append(best_wholesaler)
        
        network.wholesaler_store_assignments = assignments
        return assignments