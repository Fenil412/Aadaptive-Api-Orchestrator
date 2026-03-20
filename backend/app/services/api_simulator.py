import random

API_ECOSYSTEM = {
    "ecommerce": {
        "payment_A": {"latency_range": (50, 200), "success_prob": 0.95, "cost": 0.05},
        "payment_B": {"latency_range": (100, 300), "success_prob": 0.99, "cost": 0.10},
        "inventory": {"latency_range": (20, 100), "success_prob": 0.98, "cost": 0.01},
        "cart": {"latency_range": (10, 50), "success_prob": 0.99, "cost": 0.01},
        "order": {"latency_range": (150, 400), "success_prob": 0.90, "cost": 0.05},
        "recommendation": {"latency_range": (200, 800), "success_prob": 0.85, "cost": 0.08},
    },
    "user": {
        "authentication": {"latency_range": (50, 150), "success_prob": 0.99, "cost": 0.02},
        "profile": {"latency_range": (20, 80), "success_prob": 0.99, "cost": 0.01},
        "preferences": {"latency_range": (10, 50), "success_prob": 0.99, "cost": 0.01},
    },
    "logistics": {
        "delivery": {"latency_range": (200, 500), "success_prob": 0.92, "cost": 0.10},
        "tracking": {"latency_range": (100, 300), "success_prob": 0.95, "cost": 0.02},
        "warehouse": {"latency_range": (50, 200), "success_prob": 0.98, "cost": 0.03},
    },
    "financial": {
        "fraud_detection": {"latency_range": (300, 1000), "success_prob": 0.99, "cost": 0.15},
        "billing": {"latency_range": (150, 400), "success_prob": 0.95, "cost": 0.05},
    },
    "external": {
        "external_payment": {"latency_range": (400, 1200), "success_prob": 0.85, "cost": 0.20},
        "external_shipping": {"latency_range": (300, 900), "success_prob": 0.80, "cost": 0.15},
    }
}

class APISimulator:
    @staticmethod
    def call_api(category: str, api_name: str, system_load: float = 1.0, is_retry: bool = False):
        if category not in API_ECOSYSTEM or api_name not in API_ECOSYSTEM[category]:
            return {"api_name": api_name, "latency": 0, "cost": 0, "success": False, "error": "API not found"}
        
        profile = API_ECOSYSTEM[category][api_name]
        
        min_lat, max_lat = profile["latency_range"]
        base_latency = random.uniform(min_lat, max_lat)
        latency = base_latency * (1 + (system_load - 1) * 0.5)
        
        success_prob = profile["success_prob"]
        if system_load > 1.5:
            success_prob -= 0.1
            
        if is_retry:
            latency *= 1.1
            success_prob += 0.05
            
        success_prob = max(0.01, min(0.99, success_prob))
        success = random.random() < success_prob
        
        if not success:
            latency = max_lat * system_load
            
        cost = profile["cost"]
        if is_retry:
            cost *= 1.5
            
        return {
            "api_name": api_name,
            "latency": round(latency, 2),
            "cost": round(cost, 4),
            "success": success
        }
