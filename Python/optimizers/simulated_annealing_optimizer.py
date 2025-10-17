import random
import math
import copy
from itertools import combinations
from network_model import LogisticsNetwork


class SimulatedAnnealingOptimizer:
    """使用聚类与模拟退火算法优化物流网络"""
    TARGET_WHOLESALER_COUNT = 3

    @staticmethod
    def optimize(network, manufacturer_clusters=3,
                 initial_temp=1000, cooling_rate=0.95, iterations=1000):
        """先对生产商聚类，再通过模拟退火优化物流网络"""
        if not isinstance(network, LogisticsNetwork):
            raise TypeError("network必须是LogisticsNetwork类型")

        if not network.distance_matrix:
            network.calculate_distances()

        if len(network.wholesalers) < SimulatedAnnealingOptimizer.TARGET_WHOLESALER_COUNT:
            raise ValueError("批发商数量不足，无法选择三个最优批发商")

        if len(network.manufacturers) < 1:
            raise ValueError("没有可优化的生产商")

        optimized_network = SimulatedAnnealingOptimizer._select_best_wholesalers(
            network,
            manufacturer_clusters,
            initial_temp,
            cooling_rate,
            iterations,
        )

        if optimized_network is None:
            raise RuntimeError("无法选出最优的批发商组合")

        return optimized_network

    @staticmethod
    def _select_best_wholesalers(network, manufacturer_clusters,
                                 initial_temp, cooling_rate, iterations):
        """从所有批发商中选择三个使总距离最小"""
        best_network = None
        best_distance = float('inf')

        for wholesaler_subset in combinations(network.wholesalers, SimulatedAnnealingOptimizer.TARGET_WHOLESALER_COUNT):
            candidate_network = network.create_filtered_network(wholesaler_subset)

            total_distance = SimulatedAnnealingOptimizer._run_clustered_simulated_annealing(
                candidate_network,
                manufacturer_clusters,
                initial_temp,
                cooling_rate,
                iterations,
            )

            if total_distance < best_distance:
                best_distance = total_distance
                best_network = candidate_network

        return best_network

    @staticmethod
    def _run_clustered_simulated_annealing(network, manufacturer_clusters,
                                           initial_temp, cooling_rate, iterations):
        manufacturer_assignments, store_assignments = (
            SimulatedAnnealingOptimizer._initialize_assignments_with_clustering(
                network, manufacturer_clusters)
        )

        best_manufacturers, best_stores, best_distance = (
            SimulatedAnnealingOptimizer._simulated_annealing_process(
                network,
                manufacturer_assignments,
                store_assignments,
                initial_temp,
                cooling_rate,
                iterations,
            )
        )

        network.manufacturer_wholesaler_pairs = best_manufacturers
        network.wholesaler_store_assignments = best_stores
        network.update_delivery_paths()

        return best_distance

    @staticmethod
    def _initialize_assignments_with_clustering(network, manufacturer_clusters):
        manufacturer_clusters = max(1, min(manufacturer_clusters, len(network.manufacturers)))

        manufacturer_clusters_map, manufacturer_centroids = network.cluster_entities(
            network.manufacturers,
            manufacturer_clusters,
        )

        manufacturer_assignments = SimulatedAnnealingOptimizer._assign_clusters_to_wholesalers(
            network,
            manufacturer_clusters_map,
            manufacturer_centroids,
        )

        store_assignments = SimulatedAnnealingOptimizer._assign_stores_to_nearest_wholesaler(
            network,
            manufacturer_assignments,
        )

        return manufacturer_assignments, store_assignments

    @staticmethod
    def _assign_clusters_to_wholesalers(network, clusters, centroids):
        assignments = {}
        available_wholesalers = list(network.wholesalers)
        remaining_wholesalers = set(available_wholesalers)

        for cluster_idx, entity_ids in clusters.items():
            centroid_point = centroids[cluster_idx]
            assigned_wholesaler = SimulatedAnnealingOptimizer._select_closest_wholesaler(
                network,
                centroid_point,
                remaining_wholesalers,
                available_wholesalers,
            )

            for entity_id in entity_ids:
                assignments[entity_id] = assigned_wholesaler

            if assigned_wholesaler in remaining_wholesalers:
                remaining_wholesalers.remove(assigned_wholesaler)

        return assignments

    @staticmethod
    def _select_closest_wholesaler(network, centroid_point, remaining_wholesalers, available_wholesalers):
        def distance_to_wholesaler(wholesaler_id):
            location = network.locations[wholesaler_id]
            return abs(centroid_point[0] - location.x) + abs(centroid_point[1] - location.y)

        if remaining_wholesalers:
            best_wholesaler = min(remaining_wholesalers, key=distance_to_wholesaler)
        else:
            best_wholesaler = min(available_wholesalers, key=distance_to_wholesaler)

        return best_wholesaler

    @staticmethod
    def _assign_stores_to_nearest_wholesaler(network, manufacturer_assignments):
        assignments = {}
        candidate_wholesalers = set(manufacturer_assignments.values())
        if not candidate_wholesalers:
            candidate_wholesalers = set(network.wholesalers)

        for store_id in network.stores:
            best_wholesaler = None
            best_distance = float('inf')

            for wholesaler_id in candidate_wholesalers:
                distance = network._ensure_distance(wholesaler_id, store_id)
                if distance < best_distance:
                    best_distance = distance
                    best_wholesaler = wholesaler_id

            if best_wholesaler is not None:
                assignments.setdefault(store_id, []).append(best_wholesaler)

        return assignments

    @staticmethod
    def _simulated_annealing_process(network, manufacturer_assignments, store_assignments,
                                     initial_temp, cooling_rate, iterations):
        current_manufacturers = copy.deepcopy(manufacturer_assignments)
        current_stores = copy.deepcopy(store_assignments)

        best_manufacturers = copy.deepcopy(current_manufacturers)
        best_stores = copy.deepcopy(current_stores)

        current_distance = SimulatedAnnealingOptimizer._calculate_total_distance_for_assignments(
            network,
            current_manufacturers,
            current_stores,
        )

        best_distance = current_distance
        temperature = initial_temp if initial_temp > 0 else 1e-6

        manufacturers = list(network.manufacturers)
        stores = list(network.stores)

        for _ in range(iterations):
            new_manufacturers = copy.deepcopy(current_manufacturers)
            new_stores = copy.deepcopy(current_stores)

            if len(manufacturers) > 1 and (not stores or random.random() < 0.5):
                m1, m2 = random.sample(manufacturers, 2)
                wh1 = new_manufacturers.get(m1)
                wh2 = new_manufacturers.get(m2)
                if wh1 is not None and wh2 is not None:
                    new_manufacturers[m1], new_manufacturers[m2] = wh2, wh1
            elif stores:
                store_id = random.choice(stores)
                candidate_wholesalers = list(set(new_manufacturers.values())) or list(network.wholesalers)
                wholesaler_id = random.choice(candidate_wholesalers)
                new_stores[store_id] = [wholesaler_id]

            new_distance = SimulatedAnnealingOptimizer._calculate_total_distance_for_assignments(
                network,
                new_manufacturers,
                new_stores,
            )

            if (new_distance < current_distance or
                    SimulatedAnnealingOptimizer._should_accept_worse(new_distance, current_distance, temperature)):
                current_manufacturers = new_manufacturers
                current_stores = new_stores
                current_distance = new_distance

                if new_distance < best_distance:
                    best_distance = new_distance
                    best_manufacturers = copy.deepcopy(new_manufacturers)
                    best_stores = copy.deepcopy(new_stores)

            temperature *= cooling_rate
            if temperature < 1e-6:
                temperature = 1e-6

        return best_manufacturers, best_stores, best_distance

    @staticmethod
    def _should_accept_worse(new_distance, current_distance, temperature):
        delta = new_distance - current_distance
        if delta <= 0:
            return True
        probability = math.exp(-delta / temperature)
        return random.random() < probability

    @staticmethod
    def _calculate_total_distance_for_assignments(network, manufacturer_assignments, store_assignments):
        total_distance = 0.0

        for manufacturer_id, wholesaler_id in manufacturer_assignments.items():
            total_distance += network._ensure_distance(manufacturer_id, wholesaler_id)

        for store_id, wholesalers in store_assignments.items():
            for wholesaler_id in wholesalers:
                total_distance += network._ensure_distance(wholesaler_id, store_id)

        return total_distance