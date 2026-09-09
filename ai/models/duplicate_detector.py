import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from backend.app.models.entities import DuplicateStatus

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class SpatioTemporalDuplicateDetector:
    """
    Detects duplicate complaints using multimodal spatial, temporal,
    categorical, textual, and visual feature scoring.
    """
    def __init__(
        self,
        max_geo_radius_meters: float = 200.0,
        threshold_score: float = 0.70,
        model_version: str = "1.2.0"
    ):
        self.max_geo_radius_meters = max_geo_radius_meters
        self.threshold_score = threshold_score
        self.model_name = "civiclens-duplicate-detector"
        self.model_version = model_version

    def _text_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.20
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return float(len(intersection)) / float(len(union))

    def _geo_similarity(self, distance_meters: float) -> float:
        if distance_meters <= 10.0:
            return 1.0
        if distance_meters >= self.max_geo_radius_meters:
            return 0.0
        # Linear decay within radius
        return max(0.0, 1.0 - (distance_meters / self.max_geo_radius_meters))

    def _temporal_similarity(self, time1: datetime, time2: datetime) -> float:
        delta_days = abs((time1 - time2).total_seconds()) / 86400.0
        # Exponential decay: e^(-days / 30) -> High similarity if within 30 days
        return float(math.exp(-delta_days / 30.0))

    def _embedding_similarity(self, vec1: Optional[List[float]], vec2: Optional[List[float]]) -> Optional[float]:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return None
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 > 0 and norm2 > 0:
            return max(0.0, min(1.0, dot / (norm1 * norm2)))
        return None

    def compute_similarity(
        self,
        new_lat: float,
        new_lng: float,
        new_category: str,
        new_text: str,
        new_created_at: datetime,
        cand_lat: float,
        cand_lng: float,
        cand_category: str,
        cand_text: str,
        cand_created_at: datetime,
        cand_image_hash: Optional[str] = None,
        new_image_hash: Optional[str] = None,
        new_embedding: Optional[List[float]] = None,
        cand_embedding: Optional[List[float]] = None,
    ) -> Tuple[float, float, float, float, float]:
        """
        Returns: (composite_score, geo_distance_meters, geo_sim, text_sim, image_sim)
        """
        distance_m = haversine_distance_meters(new_lat, new_lng, cand_lat, cand_lng)

        # If beyond max radius, early return 0.0 similarity
        if distance_m > self.max_geo_radius_meters:
            return 0.0, distance_m, 0.0, 0.0, 0.0

        geo_sim = self._geo_similarity(distance_m)
        text_sim = self._text_similarity(new_text, cand_text)
        time_sim = self._temporal_similarity(new_created_at, cand_created_at)
        cat_sim = 1.0 if new_category == cand_category else 0.20

        # Learned image embedding similarity (when available) or perceptual hash fallback
        embed_sim = self._embedding_similarity(new_embedding, cand_embedding)
        if embed_sim is not None:
            img_sim = embed_sim
        elif new_image_hash and cand_image_hash and new_image_hash == cand_image_hash:
            img_sim = 1.0
        else:
            img_sim = 0.50 if cat_sim == 1.0 else 0.10

        # Weighted formula:
        # Geo (40%) + Category (25%) + Text (15%) + Temporal (10%) + Image (10%)
        composite_score = (
            0.40 * geo_sim +
            0.25 * cat_sim +
            0.15 * text_sim +
            0.10 * time_sim +
            0.10 * img_sim
        )

        return round(composite_score, 4), round(distance_m, 1), round(geo_sim, 4), round(text_sim, 4), round(img_sim, 4)

    def find_duplicates(
        self,
        new_complaint_dict: Dict[str, Any],
        active_complaints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates new complaint against a list of active complaints.
        """
        candidates = []
        new_lat = new_complaint_dict["latitude"]
        new_lng = new_complaint_dict["longitude"]
        new_cat = new_complaint_dict.get("category", "")
        new_text = new_complaint_dict.get("description", "") or new_complaint_dict.get("title", "")
        new_time = new_complaint_dict.get("created_at") or datetime.now(timezone.utc)
        new_hash = new_complaint_dict.get("image_hash")

        for cand in active_complaints:
            cand_id = cand["id"]
            if cand_id == new_complaint_dict.get("id"):
                continue

            comp_score, dist_m, geo_sim, text_sim, img_sim = self.compute_similarity(
                new_lat, new_lng, new_cat, new_text, new_time,
                cand["latitude"], cand["longitude"], cand.get("category", ""),
                cand.get("description", "") or cand.get("title", ""),
                cand.get("created_at") or datetime.now(timezone.utc),
                cand.get("image_hash"),
                new_hash
            )

            if comp_score >= self.threshold_score:
                candidates.append({
                    "candidate_complaint_id": cand_id,
                    "candidate_complaint_number": cand.get("complaint_number", ""),
                    "candidate_title": cand.get("title", ""),
                    "candidate_status": cand.get("status", "SUBMITTED"),
                    "candidate_image_url": cand.get("primary_image_url"),
                    "similarity_score": comp_score,
                    "image_similarity": img_sim,
                    "text_similarity": text_sim,
                    "geo_distance_meters": dist_m,
                    "status": DuplicateStatus.POTENTIAL
                })

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates

duplicate_detector = SpatioTemporalDuplicateDetector()
