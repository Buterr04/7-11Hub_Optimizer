class Location:
    """表示物流网络中的一个地点"""
    def __init__(self, id, name, type, x, y, capacity=None, product_categories=None):
        self.id = id
        self.name = name
        # 类型可以是: 'manufacturer', 'wholesaler', 'store' 或 'supplier', 'hub', 'demander'
        self.type = type  
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.capacity = capacity  # 容量
        self.product_categories = product_categories or []  # 产品类别

def load_default_locations():
    """加载默认的地点数据"""
    locations = []
    
    # 添加生产商
    locations.append(Location('M-A', '生产商A', 'manufacturer', 1, 8, capacity=1000, product_categories=['饮料']))
    locations.append(Location('M-B', '生产商B', 'manufacturer', 2, 9, capacity=1200, product_categories=['食品']))
    locations.append(Location('M-C', '生产商C', 'manufacturer', 3, 7, capacity=800, product_categories=['生活用品']))
    
    # 添加批发商
    locations.append(Location('W-A', '批发商A', 'wholesaler', 5, 8, capacity=1500))
    locations.append(Location('W-B', '批发商B', 'wholesaler', 6, 9, capacity=1800))
    locations.append(Location('W-C', '批发商C', 'wholesaler', 4, 7, capacity=1200))
    
    # 添加便利店
    locations.append(Location('S-A', '711便利店A', 'store', 8, 8))
    locations.append(Location('S-B', '711便利店B', 'store', 9, 9))
    locations.append(Location('S-C', '711便利店C', 'store', 7, 7))
    
    return locations

def load_hub_spoke_locations():
    """加载集线器-辐射模型的地点数据"""
    locations = []
    
    # 添加供应地
    locations.append(Location('S1', '供应地1', 'supplier', 1, 6))
    locations.append(Location('S2', '供应地2', 'supplier', 1, 5))
    locations.append(Location('S3', '供应地3', 'supplier', 1, 4))
    
    # 添加中转节点
    locations.append(Location('H1', '中转节点', 'hub', 5, 5))
    
    # 添加需求地
    locations.append(Location('D1', '需求地1', 'demander', 9, 6))
    locations.append(Location('D2', '需求地2', 'demander', 9, 5))
    locations.append(Location('D3', '需求地3', 'demander', 9, 4))
    
    return locations

def load_locations_from_file(filename):
    """从文件加载地点数据"""
    locations = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:  # 跳过标题行
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 5:
                        id = parts[0]
                        name = parts[1]
                        type = parts[2]
                        x = float(parts[3])
                        y = float(parts[4])
                        
                        capacity = None
                        if len(parts) > 5 and parts[5]:
                            capacity = float(parts[5])
                        
                        product_categories = []
                        if len(parts) > 6 and parts[6]:
                            product_categories = parts[6].split(';')
                        
                        locations.append(Location(id, name, type, x, y, capacity, product_categories))
    except Exception as e:
        print(f"加载文件时出错: {e}")
        return load_default_locations()
    
    return locations if locations else load_default_locations()

def save_locations_to_file(locations, filename):
    """将地点数据保存到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ID,名称,类型,X坐标,Y坐标,容量,产品类别\n")
            for loc in locations:
                product_categories = ';'.join(loc.product_categories) if loc.product_categories else ''
                capacity = str(loc.capacity) if loc.capacity is not None else ''
                f.write(f"{loc.id},{loc.name},{loc.type},{loc.x},{loc.y},{capacity},{product_categories}\n")
        print(f"地点数据已保存到 {filename}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False