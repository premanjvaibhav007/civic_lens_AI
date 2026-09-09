"""
Hotspot Service — Stage 5 Geographic Intelligence
Detects areas with unusually high infrastructure problems using
spatial clustering. Results cached in-memory with TTL.
"""
import math
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from backend.app.models.entities import CivicIncident, IncidentStatus, Category
from backend.app.core.config import settings

logger = logging.getLogger("civiclens.hotspot")

# ── Simple in-memory TTL cache (replaces Redis for dev) ──────────────────────
_hotspot_cache: Dict[str, Tuple[float, List]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class HotspotArea:
    centroid_lat: float
    centroid_lng: float
    radius_meters: float
    incident_count: int
    dominant_category: str
    risk_level: str
    avg_impact_score: float
    ward: Optional[str]
    city: Optional[str]
    category_breakdown: Dict[str, int] = field(default_factory=dict)


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class HotspotService:
    """
    Geographic hotspot detection using DBSCAN-lite spatial clustering.
    Uses actual incident locations — never invents hotspots from thin air.
    """

    @staticmethod
    def _get_cached(cache_key: str) -> Optional[List[HotspotArea]]:
        if cache_key in _hotspot_cache:
            ts, data = _hotspot_cache[cache_key]
            if time.time() - ts < CACHE_TTL_SECONDS:
                return data
            del _hotspot_cache[cache_key]
        return None

    @staticmethod
    def _set_cache(cache_key: str, data: List[HotspotArea]) -> None:
        _hotspot_cache[cache_key] = (time.time(), data)

    @staticmethod
    async def detect_hotspots(
        db: AsyncSession,
        radius_m: Optional[float] = None,
        min_incidents: Optional[int] = None,
        days_lookback: int = 90,
        force_refresh: bool = False,
    ) -> List[HotspotArea]:
        """
        DBSCAN-lite: group incidents within radius_m of each other.
        Returns groups with >= min_incidents as hotspots.
        Results are cached for CACHE_TTL_SECONDS to avoid repeated heavy queries.
        """
        radius_m = radius_m or settings.HOTSPOT_DETECTION_RADIUS_METERS
        min_incidents = min_incidents or settings.INCIDENT_MIN_REPORTS_FOR_HOTSPOT
        cache_key = f"hotspots:{int(radius_m)}:{min_incidents}:{days_lookback}"

        if not force_refresh:
            cached = HotspotService._get_cached(cache_key)
            if cached is not None:
                return cached

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_lookback)
        stmt = (
            select(CivicIncident)
            .options(selectinload(CivicIncident.category))
            .where(
                CivicIncident.centroid_lat.isnot(None),
                CivicIncident.centroid_lng.isnot(None),
                CivicIncident.first_reported_at >= cutoff,
            )
        )
        result = await db.execute(stmt)
        incidents = result.scalars().all()

        if not incidents:
            HotspotService._set_cache(cache_key, [])
            return []

        # ── DBSCAN-lite ──────────────────────────────────────────────────────
        visited = set()
        clusters: List[List[CivicIncident]] = []

        for i, inc in enumerate(incidents):
            if i in visited:
                continue
            cluster = [inc]
            visited.add(i)
            for j, other in enumerate(incidents):
                if j in visited:
                    continue
                dist = _haversine_meters(
                    inc.centroid_lat, inc.centroid_lng,
                    other.centroid_lat, other.centroid_lng,
                )
                if dist <= radius_m:
                    cluster.append(other)
                    visited.add(j)
            if len(cluster) >= min_incidents:
                clusters.append(cluster)

        hotspots: List[HotspotArea] = []
        for cluster in clusters:
            lats = [i.centroid_lat for i in cluster]
            lngs = [i.centroid_lng for i in cluster]
            centroid_lat = sum(lats) / len(lats)
            centroid_lng = sum(lngs) / len(lngs)

            # Compute actual radius (max distance from centroid)
            actual_radius = max(
                _haversine_meters(centroid_lat, centroid_lng, i.centroid_lat, i.centroid_lng)
                for i in cluster
            )
            actual_radius = max(100.0, actual_radius)  # minimum 100m visual radius

            # Category breakdown
            cat_counts: Dict[str, int] = {}
            for inc in cluster:
                cat = inc.category.code if inc.category else "OTHER"
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            dominant_cat = max(cat_counts, key=cat_counts.get)
            avg_impact = sum(i.civic_impact_score for i in cluster) / len(cluster)

            # Risk level based on cluster size and avg impact
            if len(cluster) >= 10 or avg_impact >= 70:
                risk_level = "CRITICAL"
            elif len(cluster) >= 6 or avg_impact >= 50:
                risk_level = "HIGH"
            elif len(cluster) >= 4 or avg_impact >= 30:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            ward = cluster[0].ward
            city = cluster[0].city

            hotspots.append(HotspotArea(
                centroid_lat=round(centroid_lat, 6),
                centroid_lng=round(centroid_lng, 6),
                radius_meters=round(actual_radius, 1),
                incident_count=len(cluster),
                dominant_category=dominant_cat,
                risk_level=risk_level,
                avg_impact_score=round(avg_impact, 1),
                ward=ward,
                city=city,
                category_breakdown=cat_counts,
            ))

        hotspots.sort(key=lambda h: h.incident_count, reverse=True)
        HotspotService._set_cache(cache_key, hotspots)
        logger.info(f"[HotspotService] Detected {len(hotspots)} hotspots from {len(incidents)} incidents")
        return hotspots

    @staticmethod
    def hotspots_to_geojson(hotspots: List[HotspotArea]) -> Dict:
        """Convert hotspot list to GeoJSON FeatureCollection for the map."""
        features = []
        for h in hotspots:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [h.centroid_lng, h.centroid_lat],
                },
                "properties": {
                    "incident_count": h.incident_count,
                    "dominant_category": h.dominant_category,
                    "risk_level": h.risk_level,
                    "avg_impact_score": h.avg_impact_score,
                    "radius_meters": h.radius_meters,
                    "ward": h.ward,
                    "city": h.city,
                    "category_breakdown": h.category_breakdown,
                },
            })
        return {"type": "FeatureCollection", "features": features}


hotspot_service = HotspotService()
