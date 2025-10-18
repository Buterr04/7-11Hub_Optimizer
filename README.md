# 7-11Hub Optimizer
<p align="center">
  <a href="README_CN.md">简体中文</a> ｜ <a href="README.md">English</a>
</p>

A comprehensive logistics network optimization tool for 7-11 convenience stores, built with clean object-oriented design and powerful optimization algorithms.

## 📋 Overview

This project provides an intelligent solution for optimizing 7-11's transportation and logistics network. Through a clear object-oriented approach, it separates data models, network structures, and optimization algorithms, making the system maintainable, extensible, and easy to use.


## 🏗️ Architecture

The system follows a clean separation of concerns with three main components:

### 1. **Data Layer - `Location`**
- Represents physical locations (stores, warehouses, distribution centers)
- Stores geographical coordinates, capacity, demand, and other location-specific data
- Provides data validation and serialization methods

### 2. **Model Layer - `LogisticsNetwork`**
- Represents the entire logistics network as a graph structure
- Manages relationships between locations (routes, distances, costs)
- Handles network-wide operations and queries
- Provides methods for network analysis and evaluation

### 3. **Algorithm Layer - `Optimizers`**
Multiple optimization algorithms to solve different aspects of the logistics problem:
- **Route Optimizer**: Finds optimal delivery routes (TSP/VRP solutions)
- **Hub Location Optimizer**: Determines optimal warehouse/hub locations
- **Capacity Optimizer**: Balances load across the network
- **Cost Optimizer**: Minimizes overall transportation costs
- **Multi-objective Optimizer**: Balances multiple optimization goals

## ✨ Features

- **🎯 Multiple Optimization Strategies**: Choose from various algorithms based on your specific needs
- **📊 Data-Driven Decisions**: Load and analyze real-world location and demand data
- **🖥️ Simple CLI Interface**: Easy-to-use command-line interface for all operations
- **📈 Visualization**: Generate visual representations of the network and optimization results
- **🔧 Extensible Design**: Easy to add new optimizers or modify existing ones
- **⚡ Efficient Algorithms**: Optimized for performance on real-world scale problems

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Buterr04/7-11Hub_Optimizer.git
cd 7-11Hub_Optimizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Quick Start

Run the optimizer with default settings:
```bash
python main.py
```

## 📖 Usage

### Example Workflow

You can also follow the instructions in the app

1. **Load your location data**

2. **Run optimization**

3. **View and export results**

## 📊 Data Format

Location data can only be provided in CSV files.

CSV
- File must be UTF-8 encoded and contain a header row. The loader skips the first line.
- Header (order must match):
  ID,名称,类型,X坐标,Y坐标,容量,产品类别
- Columns:
  - ID (string)
  - 名称 (string)
  - 类型 (string) — one of: `manufacturer`, `wholesaler`, `store`, `supplier`, `hub`, `demander`
  - X坐标, Y坐标 (numeric)
  - 容量 (optional numeric; leave empty if not used)
  - 产品类别 (optional; multiple categories separated by `;`)
- Minimum valid row: first five columns (ID,名称,类型,X坐标,Y坐标) must exist.
- Example:
```csv
ID,名称,类型,X坐标,Y坐标,容量,产品类别
M-A,生产商A,manufacturer,1,8,1000,饮料
W-A,批发商A,wholesaler,5,8,1500,
S-A,711便利店A,store,8,8,,
```


## 🎨 Visualization

The system generates various visualizations:
- **Network Maps**: Geographic representation of locations and routes
- **Route Diagrams**: Optimized delivery routes
- **Performance Metrics**: Charts showing optimization improvements
- **Comparison Graphs**: Before/after optimization comparisons

## 🛠️ Development

### Project Structure

```
7-11Hub_Optimizer/
├── Python/
│   ├── locations.py                          *location definitions
│   ├── main.py                               *main entrypoint
│   ├── network_model.py                      *logistics network model
│   └── optimizers/
│       ├── exhaustive_optimizer.py           *exhaustive search
│       ├── greedy_optimizer.py               *greedy algorithm
│       └── simulated_annealing_optimizer.py  *simulated annealing
├── requirements.txt                          *project dependencies
├── LICENSE
├── README.md                                 *English readme (this file)
└── README_CN.md                              *Chinese readme
```

### Adding New Optimizers

To add a new optimizer:

1. Create a new class inheriting from `BaseOptimizer`
2. Implement the `optimize()` method
3. Register the optimizer in the CLI

```python
from optimizers.base_optimizer import BaseOptimizer

class CustomOptimizer(BaseOptimizer):
    def optimize(self, network):
        # Your optimization logic here
        return optimized_network
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run with coverage:
```bash
python -m pytest --cov=src tests/
```

## 📈 Performance

The system is designed to handle:
- 1,000+ store locations
- Multiple distribution centers
- Complex route constraints
- Real-time optimization updates

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Buterr.**

## 🙏 Acknowledgments

- Inspired by real-world logistics optimization problems
- Built for the 7-11 convenience store network
- Utilizes modern optimization algorithms and techniques

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Check the documentation
- Review example use cases in the `examples/` directory

---

**Made with ❤️ for optimizing 7-11 logistics networks**
