from itertools import permutations, combinations
from network_model import LogisticsNetwork

class ExhaustiveOptimizer:
    """使用穷举法优化物流网络"""
    TARGET_WHOLESALER_COUNT = 3
    
    @staticmethod
    def optimize(network):
        """优化物流网络"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network必须是LogisticsNetwork类型")
        
        # 确保距离矩阵已计算
        if not network.distance_matrix:
            network.calculate_distances()

        if len(network.wholesalers) < ExhaustiveOptimizer.TARGET_WHOLESALER_COUNT:
            raise ValueError("批发商数量不足，无法选择三个最优批发商")

        if len(network.manufacturers) != ExhaustiveOptimizer.TARGET_WHOLESALER_COUNT:
            raise ValueError("当前实现要求存在三个生产商，以便与三个批发商配对")

        optimized_network = ExhaustiveOptimizer._select_best_wholesalers(network)
        if optimized_network is None:
            raise RuntimeError("无法选出最优的批发商组合")

        return optimized_network

    @staticmethod
    def _select_best_wholesalers(network):
        """从所有批发商中选择三个使总距离最小"""
        best_network = None
        best_distance = float('inf')

        for wholesaler_subset in combinations(network.wholesalers, ExhaustiveOptimizer.TARGET_WHOLESALER_COUNT):
            candidate_network = network.create_filtered_network(wholesaler_subset)

            ExhaustiveOptimizer._optimize_manufacturer_wholesaler_pairs(candidate_network)
            ExhaustiveOptimizer._optimize_wholesaler_store_assignments(candidate_network)
            candidate_network.update_delivery_paths()

            total_distance = candidate_network.calculate_total_network_distance()
            if total_distance < best_distance:
                best_distance = total_distance
                best_network = candidate_network

        return best_network
    
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