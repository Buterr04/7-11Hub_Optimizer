from itertools import permutations
from network_model import LogisticsNetwork

class ExhaustiveOptimizer:
    """使用穷举法优化物流网络"""
    
    @staticmethod
    def optimize(network):
        """优化物流网络"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network必须是LogisticsNetwork类型")
        
        # 确保距离矩阵已计算
        if not network.distance_matrix:
            network.calculate_distances()
        
        # 优化生产商和批发商的配对
        ExhaustiveOptimizer._optimize_manufacturer_wholesaler_pairs(network)
        
        # 优化批发商到便利店的分配
        ExhaustiveOptimizer._optimize_wholesaler_store_assignments(network)
        
        return network
    
    @staticmethod
    def _optimize_manufacturer_wholesaler_pairs(network):
        """优化生产商和批发商的配对，使总距离最小"""
        if len(network.manufacturers) != len(network.wholesalers):
            raise ValueError("生产商和批发商的数量必须相等")
        
        # 生成所有可能的批发商排列
        best_distance = float('inf')
        best_pairing = None
        
        for wholesaler_perm in permutations(network.wholesalers):
            total_distance = 0
            current_pairing = {}
            
            for i, manufacturer_id in enumerate(network.manufacturers):
                wholesaler_id = wholesaler_perm[i]
                total_distance += network.distance_matrix[manufacturer_id][wholesaler_id]
                current_pairing[manufacturer_id] = wholesaler_id
            
            if total_distance < best_distance:
                best_distance = total_distance
                best_pairing = current_pairing
        
        network.manufacturer_wholesaler_pairs = best_pairing
        return best_pairing, best_distance
    
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