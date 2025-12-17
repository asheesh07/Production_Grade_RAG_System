from typing import List
import math

class ScoreNormalizer:
    
    def min_max(self, scores: List[float]) -> List[float]:
        if not scores:
            return []

        min_s = min(scores)
        max_s = max(scores)

        if max_s == min_s:
            return [1.0 for _ in scores]

        return [(s - min_s) / (max_s - min_s) for s in scores]


    def z_score(self, scores: List[float]) -> List[float]:
        if not scores:
            return []

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance) if variance > 0 else 1.0

        return [(s - mean) / std for s in scores]


    def softmax(self, scores: List[float]) -> List[float]:
        if not scores:
            return []

        max_score = max(scores)
        exps = [math.exp(s - max_score) for s in scores]
        total = sum(exps)

        return [e / total for e in exps]


    def distance_to_similarity(self, distances: List[float]) -> List[float]:
        """
        Converts L2 distances into similarity scores.
        """
        return [1 / (1 + d) for d in distances]
