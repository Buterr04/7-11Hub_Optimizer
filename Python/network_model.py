import numpy as np
import matplotlib.pyplot as plt
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
        
        if locations:
            for location in locations:
                self.add_location(location)
    
    def add_location(self, location):
        """添加一个地点到网络中"""
        self.locations[location.id] = location
        if location.type == 'manufacturer':
            self.manufacturers.append(location.id)
        elif location.type == 'wholesaler':
            self.wholesalers.append(location.id)
        elif location.type == 'store':
            self.stores.append(location.id)
    
    def calculate_distance(self, loc1, loc2):
        """计算两个地点之间的欧几里得距离"""
        return np.sqrt((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)
    
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
        for manufacturer_id, wholesaler_id in self.manufacturer_wholesaler_pairs.items():
            total_distance += self.distance_matrix[manufacturer_id][wholesaler_id]
        
        # 计算批发商到便利店的距离
        for store_id, wholesalers in self.wholesaler_store_assignments.items():
            for wholesaler_id in wholesalers:
                total_distance += self.distance_matrix[wholesaler_id][store_id]
        
        return total_distance
    
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
        
        # 绘制生产商到批发商的连接
        for manufacturer_id, wholesaler_id in self.manufacturer_wholesaler_pairs.items():
            m_loc = self.locations[manufacturer_id]
            w_loc = self.locations[wholesaler_id]
            plt.plot([m_loc.x, w_loc.x], [m_loc.y, w_loc.y], 'b-', linewidth=2)
        
        # 绘制批发商到便利店的连接
        for store_id, wholesalers in self.wholesaler_store_assignments.items():
            s_loc = self.locations[store_id]
            for wholesaler_id in wholesalers:
                w_loc = self.locations[wholesaler_id]
                plt.plot([w_loc.x, s_loc.x], [w_loc.y, s_loc.y], 'g--', linewidth=1.5)
        
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