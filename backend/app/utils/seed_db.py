"""
Seed script — inserts 100 synthetic api_logs + 20 rl_decisions.
Run from backend/ directory:
    python -m app.utils.seed_db
"""
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

API_NAMES = [
    "payment_A", "payment_B", "inventory", "cart", "order", "recommendation",
    "authentication", "profile", "preferences",
    "delivery", "tracking", "warehouse",
    "fraud_detection", "billing",
    "external_payment", "external_shipping",
]
ACTION_LABELS = ["call_api", "retry", "skip", "switch_provider"]


async def seed_api_logs(db, n: int = 100) -> None:
    from app.services.db_service import insert_api_log

    for _ in range(n):
        result = {
            "api_name": random.choice(API_NAMES),
            "latency": round(random.uniform(30, 800), 2),
            "cost": round(random.uniform(0.5, 7.0), 2),
            "success": random.random() > 0.1,
            "system_load": round(random.uniform(0.8, 1.5), 4),
            "action_taken": random.choice(ACTION_LABELS),
        }
        await insert_api_log(db, result)

    logger.info("Seeded %d api_log records.", n)


async def seed_rl_decisions(db, n: int = 20) -> None:
    from app.services.db_service import insert_rl_decision

    for _ in range(n):
        state = [round(random.uniform(0, 1), 4) for _ in range(5)]
        action = random.randint(0, 3)
        reward = round(random.uniform(-60, 100), 4)
        api_name = random.choice(API_NAMES)
        await insert_rl_decision(db, state, action, reward, api_name)

    logger.info("Seeded %d rl_decision records.", n)


async def main() -> None:
    from app.config.database import AsyncSessionLocal, create_all_tables

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Creating tables if needed...")
    await create_all_tables()

    async with AsyncSessionLocal() as db:
        await seed_api_logs(db, n=100)
        await seed_rl_decisions(db, n=20)
        await db.commit()

    logger.info("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
