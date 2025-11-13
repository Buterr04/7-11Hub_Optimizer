class Location:
    """表示物流网络中的一个地点"""
    def __init__(self, id, name, type, x, y, capacity=None, product_categories=None, build_cost=0.0):
        self.id = id
        self.name = name
        # 类型可以是: 'manufacturer', 'wholesaler', 'store' 或 'supplier', 'hub', 'demander'
        self.type = type  
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.capacity = capacity  # 容量
        self.product_categories = product_categories or []  # 产品类别
        self.build_cost = float(build_cost) if build_cost is not None else 0.0

def load_default_locations():
    """默认从 locations.csv 加载地点数据"""
    return load_locations_from_file("locations.csv")


def load_locations_from_file(filename):
    """从文件加载地点数据"""
    locations = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:  # 跳过标题行
                if not line.strip():
                    continue

                parts = [part.strip() for part in line.strip().split(',')]
                if len(parts) < 5:
                    continue

                id = parts[0]
                name = parts[1]
                type = parts[2]
                x = float(parts[3])
                y = float(parts[4])

                capacity = float(parts[5]) if len(parts) > 5 and parts[5] else None

                product_categories = []
                if len(parts) > 6 and parts[6]:
                    product_categories = [item for item in parts[6].split(';') if item]

                build_cost = float(parts[7]) if len(parts) > 7 and parts[7] else 0.0

                locations.append(Location(
                    id, name, type, x, y, capacity, product_categories, build_cost))
    except FileNotFoundError:
        print(f"未找到文件: {filename}")
    except Exception as e:
        print(f"加载文件时出错: {e}")
    
    return locations

def save_locations_to_file(locations, filename):
    """将地点数据保存到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ID,名称,类型,X坐标,Y坐标,容量,产品类别,建设成本\n")
            for loc in locations:
                product_categories = ';'.join(loc.product_categories) if loc.product_categories else ''
                capacity = str(loc.capacity) if loc.capacity is not None else ''
                build_cost = f"{loc.build_cost}" if getattr(loc, 'build_cost', 0.0) else ''
                f.write(
                    f"{loc.id},{loc.name},{loc.type},{loc.x},{loc.y},{capacity},{product_categories},{build_cost}\n"
                )
        print(f"地点数据已保存到 {filename}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False