import numpy as np
import matplotlib.pyplot as plt
import math
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams
import os

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

class LogisticsNetwork:
    """物流网络基础类"""
    def __init__(self, locations=None):
        self.locations = {}
        self.manufacturers = []
        self.wholesalers = []
        self.stores = []
        self.distance_matrix = {}
        self.manufacturer_wholesaler_pairs = {}
        self.wholesaler_store_assignments = {}
        self.store_delivery_paths = {}
        
        if locations:
            for location in locations:
                self.add_location(location)

    def create_filtered_network(self, selected_wholesaler_ids):
        """基于选定批发商创建新的物流网络副本"""
        new_network = LogisticsNetwork()

        for manufacturer_id in self.manufacturers:
            new_network.add_location(self.locations[manufacturer_id])

        for wholesaler_id in selected_wholesaler_ids:
            if wholesaler_id in self.locations:
                new_network.add_location(self.locations[wholesaler_id])

        for store_id in self.stores:
            new_network.add_location(self.locations[store_id])

        new_network.calculate_distances()
        return new_network

    def cluster_entities(self, entity_ids, num_clusters, max_iterations=100, tolerance=1e-4):
        """使用简单KMeans对给定实体进行聚类"""
        if not entity_ids:
            raise ValueError("没有可聚类的实体")

        if num_clusters <= 0:
            raise ValueError("聚类数必须大于0")

        num_clusters = min(num_clusters, len(entity_ids))

        points = np.array([[self.locations[e_id].x, self.locations[e_id].y] for e_id in entity_ids])

        rng = np.random.default_rng()
        initial_indices = rng.choice(len(entity_ids), size=num_clusters, replace=False)
        centroids = points[initial_indices].copy()

        labels = np.zeros(len(entity_ids), dtype=int)

        for _ in range(max_iterations):
            distances = np.abs(points[:, np.newaxis, :] - centroids[np.newaxis, :, :]).sum(axis=2)
            new_labels = np.argmin(distances, axis=1)

            if np.array_equal(labels, new_labels):
                break

            labels = new_labels

            for cluster_idx in range(num_clusters):
                cluster_points = points[labels == cluster_idx]
                if len(cluster_points) == 0:
                    centroids[cluster_idx] = points[rng.choice(len(points))]
                else:
                    centroids[cluster_idx] = cluster_points.mean(axis=0)

        clusters = {idx: [] for idx in range(num_clusters)}
        for entity_idx, cluster_idx in enumerate(labels):
            clusters[cluster_idx].append(entity_ids[entity_idx])

        return clusters, centroids
    
    def add_location(self, location):
        """添加一个地点到网络中"""
        self.locations[location.id] = location

        location_type = (location.type or '').lower()
        if location_type == 'manufacturer':
            self.manufacturers.append(location.id)
        elif location_type == 'wholesaler':
            self.wholesalers.append(location.id)
        elif location_type == 'store':
            self.stores.append(location.id)
    
    def calculate_distance(self, loc1, loc2):
        """计算两个地点之间的曼哈顿距离"""
        return abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y)
    
    def calculate_distances(self):
        """计算所有地点之间的距离"""
        for loc1_id, loc1 in self.locations.items():
            if loc1_id not in self.distance_matrix:
                self.distance_matrix[loc1_id] = {}
            for loc2_id, loc2 in self.locations.items():
                if loc1_id != loc2_id:
                    self.distance_matrix[loc1_id][loc2_id] = self.calculate_distance(loc1, loc2)
    
    def calculate_total_network_distance(self):
        """计算整个网络的总距离"""
        total_distance = 0
        
        # 计算生产商到批发商的距离
        for manufacturer_id, wholesaler_id in self._iter_manufacturer_wholesaler_pairs():
            total_distance += self._ensure_distance(manufacturer_id, wholesaler_id)
        
        # 计算批发商到便利店的距离
        for store_id, wholesalers in self.wholesaler_store_assignments.items():
            for wholesaler_id in wholesalers:
                total_distance += self._ensure_distance(wholesaler_id, store_id)
        
        return total_distance

    def _iter_manufacturer_wholesaler_pairs(self):
        """遍历所有生产商-批发商连接，兼容一对多的配置"""
        for manufacturer_id, value in self.manufacturer_wholesaler_pairs.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple, set)):
                for wholesaler_id in value:
                    if wholesaler_id is not None:
                        yield manufacturer_id, wholesaler_id
            else:
                yield manufacturer_id, value

    def _ensure_distance(self, from_id, to_id):
        """确保距离矩阵中包含指定地点的距离并返回该距离"""
        if from_id == to_id:
            return 0.0

        if from_id not in self.distance_matrix:
            self.distance_matrix[from_id] = {}

        if to_id not in self.distance_matrix:
            self.distance_matrix[to_id] = {}

        if to_id not in self.distance_matrix[from_id]:
            loc_from = self.locations.get(from_id)
            loc_to = self.locations.get(to_id)
            if loc_from is None or loc_to is None:
                raise ValueError("距离计算失败：网络中缺少指定的地点")
            distance = self.calculate_distance(loc_from, loc_to)
            self.distance_matrix[from_id][to_id] = distance
            self.distance_matrix[to_id][from_id] = distance

        return self.distance_matrix[from_id][to_id]

    def _build_delivery_path(self, manufacturer_id, wholesaler_id, store_id):
        """构建单条完整配送路径及其距离信息"""
        if manufacturer_id not in self.locations or wholesaler_id not in self.locations or store_id not in self.locations:
            return None

        mw_distance = self._ensure_distance(manufacturer_id, wholesaler_id)
        ws_distance = self._ensure_distance(wholesaler_id, store_id)

        return {
            'manufacturer_id': manufacturer_id,
            'wholesaler_id': wholesaler_id,
            'store_id': store_id,
            'path': [manufacturer_id, wholesaler_id, store_id],
            'segment_distances': {
                'manufacturer_to_wholesaler': mw_distance,
                'wholesaler_to_store': ws_distance,
            },
            'total_distance': mw_distance + ws_distance,
        }

    def update_delivery_paths(self):
        """根据当前分配结果生成完整的生产商-批发商-便利店路径"""
        self.store_delivery_paths = {}

        if not self.manufacturer_wholesaler_pairs or not self.wholesaler_store_assignments:
            return self.store_delivery_paths

        # 创建批发商到生产商的反向映射，方便查询完整路径
        wholesaler_to_manufacturer = {}
        for manufacturer_id, wholesaler_id in self._iter_manufacturer_wholesaler_pairs():
            wholesalers = wholesaler_to_manufacturer.setdefault(wholesaler_id, [])
            wholesalers.append(manufacturer_id)

        for store_id, wholesaler_ids in self.wholesaler_store_assignments.items():
            if not wholesaler_ids:
                continue

            if not isinstance(wholesaler_ids, (list, tuple, set)):
                wholesaler_ids = [wholesaler_ids]

            store_paths = []
            for wholesaler_id in wholesaler_ids:
                manufacturer_candidates = wholesaler_to_manufacturer.get(wholesaler_id, [])
                manufacturer_id = None
                if manufacturer_candidates:
                    manufacturer_id = min(
                        manufacturer_candidates,
                        key=lambda mid: self._ensure_distance(mid, wholesaler_id)
                    )
                elif self.manufacturers:
                    manufacturer_id = self.manufacturers[0]

                path_info = self._build_delivery_path(manufacturer_id, wholesaler_id, store_id)
                if path_info:
                    store_paths.append(path_info)

            if store_paths:
                self.store_delivery_paths[store_id] = store_paths

        return self.store_delivery_paths
    
    def visualize_network(self, title="物流网络", save_path=None):
        """可视化物流网络"""
        plt.figure(figsize=(12, 8))
        
        # 绘制地点
        for location_id, location in self.locations.items():
            if location.type == 'manufacturer':
                plt.scatter(location.x, location.y, color='blue', s=100, marker='s')
                plt.text(location.x, location.y + 0.1, location.name, ha='center')
            elif location.type == 'wholesaler':
                plt.scatter(location.x, location.y, color='green', s=100, marker='^')
                plt.text(location.x, location.y + 0.1, location.name, ha='center')
            elif location.type == 'store':
                plt.scatter(location.x, location.y, color='red', s=100, marker='o')
                plt.text(location.x, location.y + 0.1, location.name, ha='center')
        
        # 绘制生产商到批发商的连接（欧式直线）
        for manufacturer_id, wholesaler_id in self._iter_manufacturer_wholesaler_pairs():
            m_loc = self.locations[manufacturer_id]
            w_loc = self.locations[wholesaler_id]
            # 使用欧氏距离绘制直线并标注距离
            plt.plot([m_loc.x, w_loc.x], [m_loc.y, w_loc.y], 'b-', linewidth=2)
            midpoint_x = (m_loc.x + w_loc.x) / 2
            midpoint_y = (m_loc.y + w_loc.y) / 2
            euclidean_distance = math.hypot(m_loc.x - w_loc.x, m_loc.y - w_loc.y)
            plt.text(midpoint_x, midpoint_y + 0.1, f"{euclidean_distance:.1f}", color='blue', fontsize=8, ha='center')
        
        # 绘制批发商到便利店的连接（欧式直线）
        for store_id, wholesalers in self.wholesaler_store_assignments.items():
            s_loc = self.locations[store_id]
            for wholesaler_id in wholesalers:
                w_loc = self.locations[wholesaler_id]
            # 使用欧氏距离绘制直线并标注距离
            plt.plot([w_loc.x, s_loc.x], [w_loc.y, s_loc.y], 'g--', linewidth=1.5)
            midpoint_x = (w_loc.x + s_loc.x) / 2
            midpoint_y = (w_loc.y + s_loc.y) / 2
            euclidean_distance = math.hypot(w_loc.x - s_loc.x, w_loc.y - s_loc.y)
            plt.text(midpoint_x, midpoint_y + 0.1, f"{euclidean_distance:.1f}", color='green', fontsize=8, ha='center')
        
        # 添加图例
        manufacturer_patch = plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='blue', markersize=10, label='生产商')
        wholesaler_patch = plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10, label='批发商')
        store_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='711便利店')
        m_to_w_line = plt.Line2D([0], [0], color='blue', linewidth=2, label='生产商到批发商')
        w_to_s_line = plt.Line2D([0], [0], color='green', linestyle='--', linewidth=1.5, label='批发商到便利店')
        
        plt.legend(handles=[manufacturer_patch, wholesaler_patch, store_patch, m_to_w_line, w_to_s_line], loc='upper right')
        
        # 设置标题和坐标轴
        plt.title(title, fontsize=16)
        plt.xlabel('X坐标', fontsize=12)
        plt.ylabel('Y坐标', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 保存图像
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"网络图已保存为 '{save_path}'")
        
        # 显示图像
        plt.show()