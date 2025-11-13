import copy
import math
import random
from itertools import combinations, permutations
from typing import Dict, Iterable, List, Optional, Tuple

from network_model import LogisticsNetwork


class KMeansSimulatedAnnealingOptimizer:
    """K-means 聚类 + 模拟退火 的中转点选择与配送优化算法"""

    @staticmethod
    def optimize(
        network: LogisticsNetwork,
        hub_counts: Optional[Iterable[int]] = None,
        unit_transport_cost: float = 1.0,
        initial_temp: float = 500.0,
        cooling_rate: float = 0.9,
        iterations: int = 1000,
        kmeans_restarts: int = 5,
    ):
        """执行优化，返回最佳方案及所有尝试的方案列表"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network 必须是 LogisticsNetwork 类型")

        if unit_transport_cost < 0:
            raise ValueError("unit_transport_cost 必须为非负数")

        if not network.distance_matrix:
            network.calculate_distances()

        candidate_hubs = list(network.wholesalers)
        suppliers = list(network.manufacturers)
        stores = [
            store_id
            for store_id in network.stores
            if getattr(network.locations.get(store_id), "type", "").lower() == "store"
        ]

        if not candidate_hubs:
            raise ValueError("网络中缺少可用的中转点候选")

        if not stores:
            raise ValueError("网络中缺少末端节点 (便利店)")

        if not suppliers:
            raise ValueError("网络中缺少供应商")

        if hub_counts is None:
            hub_counts = range(1, len(candidate_hubs) + 1)

        best_solution = None
        best_cost = float("inf")
        evaluated_solutions = []

        for hub_count in hub_counts:
            if hub_count <= 0 or hub_count > len(candidate_hubs):
                continue

            result = KMeansSimulatedAnnealingOptimizer._evaluate_hub_count(
                network,
                hub_count,
                candidate_hubs,
                suppliers,
                unit_transport_cost,
                initial_temp,
                cooling_rate,
                iterations,
                kmeans_restarts,
            )

            if result is None:
                continue

            evaluated_solutions.append(result)

            if result["total_cost"] < best_cost:
                best_cost = result["total_cost"]
                best_solution = result

        if best_solution is None:
            raise RuntimeError("在给定参数下未能找到可行方案")

        return best_solution, evaluated_solutions

    @staticmethod
    def _evaluate_hub_count(
        network: LogisticsNetwork,
        hub_count: int,
        candidate_hubs: List[str],
        suppliers: List[str],
        unit_transport_cost: float,
        initial_temp: float,
        cooling_rate: float,
        iterations: int,
        kmeans_restarts: int,
    ) -> Optional[Dict]:
        best_for_count = None
        best_cost = float("inf")

        for hub_subset in combinations(candidate_hubs, hub_count):
            initial_assignments = None
            initial_cost = float("inf")

            for _ in range(max(1, kmeans_restarts)):
                cluster_result = KMeansSimulatedAnnealingOptimizer._cluster_stores(
                    network,
                    hub_count,
                )

                if cluster_result is None:
                    continue

                clusters, centroids = cluster_result

                assignments = KMeansSimulatedAnnealingOptimizer._match_clusters_to_hubs(
                    network,
                    clusters,
                    centroids,
                    hub_subset,
                )

                cost_breakdown = KMeansSimulatedAnnealingOptimizer._calculate_total_cost(
                    network,
                    hub_subset,
                    assignments,
                    suppliers,
                    unit_transport_cost,
                )

                if cost_breakdown["total_cost"] < initial_cost:
                    initial_cost = cost_breakdown["total_cost"]
                    initial_assignments = assignments

            if initial_assignments is None:
                continue

            sa_assignments, sa_cost_breakdown = KMeansSimulatedAnnealingOptimizer._simulated_annealing(
                network,
                hub_subset,
                initial_assignments,
                suppliers,
                unit_transport_cost,
                initial_temp,
                cooling_rate,
                iterations,
            )

            if sa_cost_breakdown["total_cost"] < best_cost:
                best_cost = sa_cost_breakdown["total_cost"]
                best_for_count = {
                    "hub_count": hub_count,
                    "active_hubs": list(hub_subset),
                    "store_assignments": sa_assignments,
                    "suppliers": suppliers,
                    "unit_transport_cost": unit_transport_cost,
                    **sa_cost_breakdown,
                }

        return best_for_count

    @staticmethod
    def _cluster_stores(network: LogisticsNetwork, k: int) -> Optional[Tuple[Dict[int, List[str]], List[List[float]]]]:
        store_ids = [
            store_id
            for store_id in network.stores
            if getattr(network.locations.get(store_id), "type", "").lower() == "store"
        ]

        if k <= 0 or not store_ids:
            return None

        clusters, centroids = network.cluster_entities(store_ids, k)
        return clusters, centroids.tolist()

    @staticmethod
    def _match_clusters_to_hubs(
        network: LogisticsNetwork,
        clusters: Dict[int, List[str]],
        centroids: List[List[float]],
        hub_subset: Tuple[str, ...],
    ) -> Dict[str, str]:
        best_mapping = None
        best_score = float("inf")

        cluster_indices = list(clusters.keys())

        for perm in permutations(hub_subset, len(cluster_indices)):
            score = 0.0
            store_to_hub = {}

            for cluster_idx, hub_id in zip(cluster_indices, perm):
                centroid = centroids[cluster_idx]
                hub_loc = network.locations[hub_id]
                score += abs(hub_loc.x - centroid[0]) + abs(hub_loc.y - centroid[1])

                for store_id in clusters[cluster_idx]:
                    store_to_hub[store_id] = hub_id

            if score < best_score:
                best_score = score
                best_mapping = store_to_hub

        if best_mapping is None:
            raise RuntimeError("无法将聚类结果匹配到中转点")

        return best_mapping

    @staticmethod
    def _simulated_annealing(
        network: LogisticsNetwork,
        hubs: Tuple[str, ...],
        initial_assignments: Dict[str, str],
        suppliers: List[str],
        unit_transport_cost: float,
        initial_temp: float,
        cooling_rate: float,
        iterations: int,
    ) -> Tuple[Dict[str, str], Dict[str, float]]:
        hubs = tuple(hubs)
        current_assignments = copy.deepcopy(initial_assignments)
        best_assignments = copy.deepcopy(current_assignments)

        current_cost_breakdown = KMeansSimulatedAnnealingOptimizer._calculate_total_cost(
            network,
            hubs,
            current_assignments,
            suppliers,
            unit_transport_cost,
        )
        current_cost = current_cost_breakdown["total_cost"]
        best_cost_breakdown = dict(current_cost_breakdown)

        temperature = initial_temp if initial_temp > 0 else 1e-6
        store_ids = list(current_assignments.keys())

        for _ in range(iterations):
            if not store_ids:
                break

            store_id = random.choice(store_ids)
            current_hub = current_assignments[store_id]
            candidate_hubs = [hub for hub in hubs if hub != current_hub]

            if not candidate_hubs:
                continue

            # 确保不会将当前中转点的最后一个门店移走
            stores_served_by_current = sum(1 for h in current_assignments.values() if h == current_hub)
            if stores_served_by_current <= 1:
                continue

            new_assignments = copy.deepcopy(current_assignments)
            new_assignments[store_id] = random.choice(candidate_hubs)

            new_cost_breakdown = KMeansSimulatedAnnealingOptimizer._calculate_total_cost(
                network,
                hubs,
                new_assignments,
                suppliers,
                unit_transport_cost,
            )
            new_cost = new_cost_breakdown["total_cost"]

            if (new_cost < current_cost or
                    KMeansSimulatedAnnealingOptimizer._accept_worse(current_cost, new_cost, temperature)):
                current_assignments = new_assignments
                current_cost = new_cost
                current_cost_breakdown = new_cost_breakdown

                if new_cost < best_cost_breakdown["total_cost"]:
                    best_assignments = copy.deepcopy(new_assignments)
                    best_cost_breakdown = new_cost_breakdown

            temperature *= cooling_rate
            if temperature < 1e-6:
                temperature = 1e-6

        return best_assignments, best_cost_breakdown

    @staticmethod
    def _accept_worse(current_cost: float, new_cost: float, temperature: float) -> bool:
        delta = new_cost - current_cost
        if delta <= 0:
            return True
        probability = math.exp(-delta / max(temperature, 1e-6))
        return random.random() < probability

    @staticmethod
    def _calculate_total_cost(
        network: LogisticsNetwork,
        hubs: Iterable[str],
        store_assignments: Dict[str, str],
        suppliers: List[str],
        unit_transport_cost: float,
    ) -> Dict[str, float]:
        active_hubs = list(hubs)

        build_cost = 0.0
        for hub_id in active_hubs:
            location = network.locations[hub_id]
            build_cost += getattr(location, "build_cost", 0.0)

        supplier_cost = 0.0
        for hub_id in active_hubs:
            for supplier_id in suppliers:
                supplier_cost += unit_transport_cost * network._ensure_distance(supplier_id, hub_id)

        store_cost = 0.0
        for store_id, hub_id in store_assignments.items():
            store_cost += unit_transport_cost * network._ensure_distance(hub_id, store_id)

        total_cost = build_cost + supplier_cost + store_cost

        return {
            "total_cost": total_cost,
            "build_cost": build_cost,
            "supplier_cost": supplier_cost,
            "store_cost": store_cost,
        }