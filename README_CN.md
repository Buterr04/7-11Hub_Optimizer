# 7-11Hub 优化器

一个为 7-11 便利店打造的综合物流网络优化工具，采用清晰的面向对象设计和强大的优化算法。

## 📋 概述

本项目为 7-11 的运输与物流网络优化提供智能解决方案。通过清晰的面向对象方法，将数据模型、网络结构和优化算法分离，使系统易于维护、扩展和使用。

## 🏗️ 架构

系统采用关注点分离，包含三大核心组件：

### 1. **数据层 - `Location`**
- 表示物理位置（门店、仓库、配送中心）
- 存储地理坐标、容量、需求等位置相关数据
- 提供数据校验和序列化方法

### 2. **模型层 - `LogisticsNetwork`**
- 将整个物流网络表示为图结构
- 管理位置之间的关系（路线、距离、成本）
- 处理网络级操作和查询
- 提供网络分析与评估方法

### 3. **算法层 - `Optimizers`**
多种优化算法解决物流问题的不同方面：
- **路线优化器**：寻找最优配送路线（TSP/VRP 解法）
- **枢纽选址优化器**：确定最优仓库/枢纽位置
- **容量优化器**：平衡网络负载
- **成本优化器**：最小化整体运输成本
- **多目标优化器**：平衡多种优化目标

## ✨ 功能特性

- **🎯 多种优化策略**：可根据需求选择不同算法
- **📊 数据驱动决策**：加载并分析真实位置与需求数据
- **🖥️ 简洁 CLI 界面**：所有操作均可通过命令行完成
- **📈 可视化**：生成网络与优化结果的可视化图表
- **🔧 可扩展设计**：便于添加新优化器或修改现有算法
- **⚡ 高效算法**：针对实际规模问题优化性能

## 🚀 快速开始

### 前置条件

- Python 3.8 及以上
- pip 包管理器

### 安装

1. 克隆仓库：
```bash
git clone https://github.com/Buterr04/7-11Hub_Optimizer.git
cd 7-11Hub_Optimizer
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 快速运行

使用默认设置运行优化器：
```bash
python main.py
```

## 📖 使用方法

### 示例流程

1. **加载位置数据**：

2. **运行优化**：

3. **查看并导出结果**：

## 📊 数据格式

位置数据需为 JSON 格式：

```json
{
    "locations": [
        {
            "id": "store_001",
            "name": "7-11 Main Street",
            "type": "store",
            "latitude": 25.0330,
            "longitude": 121.5654,
            "demand": 150,
            "capacity": 200
        },
        ...
    ]
}
```

## 🎨 可视化

系统可生成多种可视化内容：
- **网络地图**：地理位置与路线展示
- **路线图**：优化后的配送路线
- **性能指标**：优化提升的图表
- **对比图**：优化前后对比

## 🛠️ 开发

### 项目结构

```
7-11Hub_Optimizer/
├── src/
│   ├── models/
│   │   ├── location.py          # 位置数据模型
│   │   └── logistics_network.py # 网络模型
│   ├── optimizers/
│   │   ├── base_optimizer.py    # 优化器基类
│   │   ├── route_optimizer.py   # 路线优化算法
│   │   ├── hub_optimizer.py     # 枢纽选址算法
│   │   └── cost_optimizer.py    # 成本最小化算法
│   ├── utils/
│   │   ├── data_loader.py       # 数据加载工具
│   │   └── visualizer.py        # 可视化函数
│   └── cli.py                   # 命令行接口
├── data/                        # 示例数据文件
├── tests/                       # 单元测试
├── main.py                      # 主入口
├── requirements.txt             # 依赖列表
└── README.md                    # 本文件
```

### 添加新优化器

添加新优化器步骤：

1. 创建继承自 `BaseOptimizer` 的新类
2. 实现 `optimize()` 方法
3. 在 CLI 注册优化器

```python
from optimizers.base_optimizer import BaseOptimizer

class CustomOptimizer(BaseOptimizer):
        def optimize(self, network):
                # 在此实现优化逻辑
                return optimized_network
```

## 🧪 测试

运行测试套件：
```bash
python -m pytest tests/
```

带覆盖率运行：
```bash
python -m pytest --cov=src tests/
```

## 📈 性能

系统可支持：
- 1000+ 门店位置
- 多个配送中心
- 复杂路线约束
- 实时优化更新

## 🤝 贡献

欢迎贡献！如有重大更改，请先提交 issue 讨论。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 👤 作者

**Buterr.**

## 🙏 鸣谢

- 灵感来源于真实物流优化问题
- 专为 7-11 便利店网络打造
- 应用现代优化算法与技术

## 📞 支持

如有疑问或需要帮助，请：
- 在 GitHub 提交 issue
- 查阅文档
- 查看 `examples/` 目录下的示例用例

---

**用 ❤️ 优化 7-11 物流网络**