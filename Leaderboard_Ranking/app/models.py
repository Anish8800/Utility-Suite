from typing import List

class Player:
    def __init__(self, name: str, points: List[int], spending: List[float]):
        self.name = name
        self.points = points
        self.spending = spending
        self.total_points = sum(points)
        self.total_spent = sum(spending)