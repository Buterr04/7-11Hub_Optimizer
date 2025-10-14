from network_model import LogisticsNetwork

class GreedyOptimizer:
    """使用贪心算法优化物流网络"""
    
    @staticmethod
    def optimize(network):
        """优化物流网络"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network必须是LogisticsNetwork类型")
        
        # 确保距离矩阵已计算
        if not network.distance_matrix:
            network.calculate_distances()
        
        # 优化生产商和批发商的配对
        GreedyOptimizer._optimize_manufacturer_wholesaler_pairs(network)
        
        # 优化批发商到便利店的分配
        GreedyOptimizer._optimize_wholesaler_store_assignments(network)
        
        return network
    
    @staticmethod
    def _optimize_manufacturer_wholesaler_pairs(network):
        """使用贪心算法优化生产商和批发商的配对"""
        if len(network.manufacturers) != len(network.wholesalers):
            raise ValueError("生产商和批发商的数量必须相等")
        
        # 创建所有可能的生产商-批发商对及其距离
        pairs = []
        for m_id in network.manufacturers:
            for w_id in network.wholesalers:
                pairs.append((m_id, w_id, network.distance_matrix[m_id][w_id]))
        
        # 按距离排序
        pairs.sort(key=lambda x: x[2])
        
        # 贪心选择
        used_manufacturers = set()
        used_wholesalers = set()
        pairings = {}
        
        for m_id, w_id, distance in pairs:
            if m_id not in used_manufacturers and w_id not in used_wholesalers:
                pairings[m_id] = w_id
                used_manufacturers.add(m_id)
                used_wholesalers.add(w_id)
                
                # 如果所有生产商或批发商都已分配，则停止
                if len(used_manufacturers) == len(network.manufacturers) or len(used_wholesalers) == len(network.wholesalers):
                    break
        
        network.manufacturer_wholesaler_pairs = pairings
        return pairings
    
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