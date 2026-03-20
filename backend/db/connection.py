"""
Database connection and operations for PostgreSQL (Supabase).

Provides connection management and CRUD operations for:
- API logs
- RL decisions
- Training runs
- Evaluation results
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def init_database():
    """Initialize database tables from schema.sql."""
    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "schema.sql"
    )
    try:
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
        print("✅ Database tables initialized")
        return True
    except FileNotFoundError:
        print("⚠️  schema.sql not found, skipping DB initialization")
        return False
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        return False


# ── API Logs ──

def insert_api_log(action, provider, latency, cost, success, reward, state):
    """Insert a new API log entry."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO api_logs (action, provider, latency, cost, success, reward, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (action, provider, latency, cost, success, reward, Json(state)),
                )
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"⚠️  Failed to insert API log: {e}")
        return None


def get_api_logs(limit=100, offset=0):
    """Fetch recent API logs."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, timestamp, action, provider, latency, cost,
                           success, reward, state
                    FROM api_logs
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                rows = cur.fetchall()
                # Convert datetime to string
                for row in rows:
                    row["timestamp"] = row["timestamp"].isoformat()
                return rows
    except Exception as e:
        print(f"⚠️  Failed to fetch API logs: {e}")
        return []


def get_api_logs_count():
    """Get total count of API logs."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM api_logs")
                return cur.fetchone()[0]
    except Exception:
        return 0


# ── RL Decisions ──

def insert_rl_decision(
    episode, step, state, action, provider,
    result_latency, result_cost, result_success,
    reward, cumulative_reward=0
):
    """Insert an RL decision record."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rl_decisions
                    (episode, step, state_latency, state_cost, state_success,
                     state_load, state_time, state_error,
                     action, provider, result_latency, result_cost,
                     result_success, reward, cumulative_reward)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        episode, step,
                        state[0], state[1], state[2],
                        state[3], state[4], state[5],
                        action, provider,
                        result_latency, result_cost,
                        result_success, reward, cumulative_reward,
                    ),
                )
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"⚠️  Failed to insert RL decision: {e}")
        return None


def get_rl_decisions(limit=100):
    """Fetch recent RL decisions."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM rl_decisions
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                for row in rows:
                    row["timestamp"] = row["timestamp"].isoformat()
                    row["created_at"] = row["created_at"].isoformat()
                return rows
    except Exception as e:
        print(f"⚠️  Failed to fetch RL decisions: {e}")
        return []


# ── Training Runs ──

def insert_training_run(total_timesteps, learning_rate):
    """Start a new training run record."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO training_runs (total_timesteps, learning_rate, status)
                    VALUES (%s, %s, 'running')
                    RETURNING id
                    """,
                    (total_timesteps, learning_rate),
                )
                return cur.fetchone()[0]
    except Exception as e:
        print(f"⚠️  Failed to insert training run: {e}")
        return None


def complete_training_run(run_id, final_avg_reward, final_success_rate, model_path):
    """Mark a training run as completed."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE training_runs
                    SET completed_at = NOW(),
                        final_avg_reward = %s,
                        final_success_rate = %s,
                        model_path = %s,
                        status = 'completed'
                    WHERE id = %s
                    """,
                    (final_avg_reward, final_success_rate, model_path, run_id),
                )
    except Exception as e:
        print(f"⚠️  Failed to complete training run: {e}")


# ── Evaluation Results ──

def insert_evaluation_result(strategy, avg_reward, avg_latency, avg_cost, success_rate, num_episodes):
    """Insert an evaluation result."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evaluation_results
                    (strategy, avg_episode_reward, avg_latency, avg_cost, success_rate, num_episodes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (strategy, avg_reward, avg_latency, avg_cost, success_rate, num_episodes),
                )
                return cur.fetchone()[0]
    except Exception as e:
        print(f"⚠️  Failed to insert evaluation result: {e}")
        return None


def get_evaluation_results():
    """Fetch the latest evaluation results."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (strategy)
                        strategy, avg_episode_reward, avg_latency,
                        avg_cost, success_rate, num_episodes, timestamp
                    FROM evaluation_results
                    ORDER BY strategy, timestamp DESC
                    """
                )
                rows = cur.fetchall()
                for row in rows:
                    row["timestamp"] = row["timestamp"].isoformat()
                return rows
    except Exception as e:
        print(f"⚠️  Failed to fetch evaluation results: {e}")
        return []


# ── Dashboard Stats ──

def get_dashboard_stats():
    """Compute dashboard summary statistics from logs."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_decisions,
                        COALESCE(AVG(reward), 0) as avg_reward,
                        COALESCE(AVG(latency), 0) as avg_latency,
                        COALESCE(AVG(cost), 0) as avg_cost,
                        COALESCE(AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END), 0) as success_rate
                    FROM api_logs
                    """
                )
                stats = cur.fetchone()

                # Provider distribution
                cur.execute(
                    """
                    SELECT provider, COUNT(*) as count
                    FROM api_logs
                    GROUP BY provider
                    """
                )
                provider_rows = cur.fetchall()
                provider_dist = {
                    row["provider"]: row["count"] for row in provider_rows
                }

                # Trend (compare last 50 vs previous 50)
                cur.execute(
                    """
                    WITH recent AS (
                        SELECT AVG(reward) as avg_r
                        FROM (SELECT reward FROM api_logs ORDER BY timestamp DESC LIMIT 50) sub
                    ),
                    previous AS (
                        SELECT AVG(reward) as avg_r
                        FROM (SELECT reward FROM api_logs ORDER BY timestamp DESC LIMIT 100 OFFSET 50) sub
                    )
                    SELECT
                        COALESCE(recent.avg_r, 0) as recent_avg,
                        COALESCE(previous.avg_r, 0) as previous_avg
                    FROM recent, previous
                    """
                )
                trend_data = cur.fetchone()
                if trend_data["recent_avg"] > trend_data["previous_avg"] + 0.05:
                    trend = "improving"
                elif trend_data["recent_avg"] < trend_data["previous_avg"] - 0.05:
                    trend = "declining"
                else:
                    trend = "stable"

                return {
                    "total_decisions": stats["total_decisions"],
                    "avg_reward": float(stats["avg_reward"]),
                    "avg_latency": float(stats["avg_latency"]),
                    "avg_cost": float(stats["avg_cost"]),
                    "success_rate": float(stats["success_rate"]),
                    "provider_distribution": provider_dist,
                    "recent_trend": trend,
                }
    except Exception as e:
        print(f"⚠️  Failed to get dashboard stats: {e}")
        return {
            "total_decisions": 0,
            "avg_reward": 0,
            "avg_latency": 0,
            "avg_cost": 0,
            "success_rate": 0,
            "provider_distribution": {},
            "recent_trend": "stable",
        }
