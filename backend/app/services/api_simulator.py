"""
API Simulator — simulates 16 APIs across 5 categories with realistic latency/cost/success.
"""
import logging
import random
from typing import Any

from app.utils.helpers import InvalidAPIError

logger = logging.getLogger(__name__)

API_CONFIG: dict[str, dict[str, Any]] = {
    # E-commerce
    "payment_A":         {"latency": (100, 300), "success_prob": 0.95, "cost": 5.0},
    "payment_B":         {"latency": (150, 400), "success_prob": 0.92, "cost": 4.0},
    "inventory":         {"latency": (50,  200), "success_prob": 0.98, "cost": 1.5},
    "cart":              {"latency": (40,  150), "success_prob": 0.99, "cost": 1.0},
    "order":             {"latency": (80,  250), "success_prob": 0.96, "cost": 2.5},
    "recommendation":    {"latency": (200, 600), "success_prob": 0.90, "cost": 3.0},
    # User Services
    "authentication":    {"latency": (30,  100), "success_prob": 0.99, "cost": 0.5},
    "profile":           {"latency": (40,  120), "success_prob": 0.98, "cost": 0.8},
    "preferences":       {"latency": (35,  110), "success_prob": 0.97, "cost": 0.7},
    # Logistics
    "delivery":          {"latency": (100, 350), "success_prob": 0.93, "cost": 3.5},
    "tracking":          {"latency": (60,  200), "success_prob": 0.96, "cost": 2.0},
    "warehouse":         {"latency": (80,  300), "success_prob": 0.94, "cost": 2.8},
    # Financial
    "fraud_detection":   {"latency": (200, 500), "success_prob": 0.97, "cost": 6.0},
    "billing":           {"latency": (100, 300), "success_prob": 0.95, "cost": 4.5},
    # External
    "external_payment":  {"latency": (300, 800), "success_prob": 0.88, "cost": 7.0},
    "external_shipping": {"latency": (250, 700), "success_prob": 0.87, "cost": 6.5},
}


def simulate_api(api_name: str, retry: bool = False) -> dict[str, Any]:
    """
    Simulate an API call and return performance metrics.

    Raises:
        InvalidAPIError: Unknown api_name.
    """
    if api_name not in API_CONFIG:
        raise InvalidAPIError(
            f"Unknown API: '{api_name}'. Valid: {list(API_CONFIG.keys())}"
        )

    cfg = API_CONFIG[api_name]
    lat_min, lat_max = cfg["latency"]
    system_load = random.uniform(0.8, 1.5)

    latency = random.uniform(lat_min, lat_max) * system_load
    if retry:
        latency *= 1.1   # +10% latency on retry (per spec)
        latency += 20.0

    # Retry boosts success probability by 0.05 (per spec)
    success_prob = min(1.0, cfg["success_prob"] + (0.05 if retry else 0.0))
    success = random.random() < success_prob

    result = {
        "api_name": api_name,
        "latency": round(latency, 3),
        "cost": round(cfg["cost"] * (1.5 if retry else 1.0), 4),
        "success": success,
        "system_load": round(system_load, 4),
    }
    logger.debug("simulate_api: %s", result)
    return result
