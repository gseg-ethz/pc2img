from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import Delaunay

class TriangulationStrategy(ABC):
    @abstractmethod
    def triangulate(
        self,
        points: NDArray[np.float32],
        xi:    NDArray[np.float32],
        batch_size: Optional[int] = None,
    ) -> tuple[
        tuple[NDArray[np.float32], ...],
        NDArray[np.int32],
        NDArray[np.float32]
        ]:
        """Return (simplices, indices, distances)."""
        ...


class DelaunayTriangulation(TriangulationStrategy):
    def triangulate(self, points, xi, **_):
        tri = Delaunay(points)
        simplex_idx = tri.find_simplex(xi)
        indices = tri.simplices[simplex_idx]
        simplices = (
            tri.points[indices[:, 0]],
            tri.points[indices[:, 1]],
            tri.points[indices[:, 2]],
        )

        # compute euclidean distances per vertex
        XA = tri.points[indices].reshape(-1, 2).astype(np.float32)
        XB = np.repeat(xi, repeats=3, axis=0)
        distances = np.linalg.norm(XA - XB, axis=1).reshape(-1, 3)
        distances[simplex_idx == -1] = np.inf

        return simplices, indices, distances