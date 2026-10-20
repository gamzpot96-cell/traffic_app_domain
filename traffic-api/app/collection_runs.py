"""F19 daily collection processor. Not scheduled or exposed to public HTTP.

No implicit execution on import, startup, page view or application deploy.
Enabling a production Cron/secret endpoint requires separate user approval.
"""
from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import uuid4

from app.database import get_database_connection
from app.operation_policies import scheduled_slot_utc
from app.traffic_analysis import SEOUL_ROUTES, analyze_one_route


def reserve_collection_day(day: date):
    """Atomically claim one 09:00 KST collection slot. Never overwrite a run."""
    scheduled_for = scheduled_slot_utc(day)
    run_id = uuid4()
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.traffic_collection_runs
                    (id, scheduled_for, count_total, outcome)
                VALUES (%s, %s, %s, 'running')
                ON CONFLICT (scheduled_for) DO NOTHING
                RETURNING id
                """,
                (run_id, scheduled_for, len(SEOUL_ROUTES))
            )
            inserted = cursor.fetchone()
    return str(inserted[0]) if inserted else None


def store_collection_observation(run_id, origin, destination, result, retrieved_at):
    """Save only validated aggregated Kakao values; do not store response bodies."""
    distance = result.get("distance_m")
    congested = result.get("congested_distance_m")
    total_roads = result.get("total_road_count")
    congested_roads = result.get("congested_count")
    duration = result.get("duration_seconds")
    if not isinstance(distance, int) or distance <= 0:
        raise ValueError("Invalid distance")
    if not isinstance(congested, int) or not 0 <= congested <= distance:
        raise ValueError("Invalid congested distance")
    if not isinstance(total_roads, int) or total_roads < 0:
        raise ValueError("Invalid road count")
    if not isinstance(congested_roads, int) or not 0 <= congested_roads <= total_roads:
        raise ValueError("Invalid congested road count")
    if duration is not None and (not isinstance(duration, int) or duration < 0):
        raise ValueError("Invalid duration")
    ratio = Decimal(congested) * Decimal(100) / Decimal(distance)
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.traffic_observations
                    (run_id, origin, destination, retrieved_at, distance_m,
                     duration_seconds, total_road_count, congested_count,
                     congested_distance_m, congestion_ratio, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'kakao')
                ON CONFLICT (run_id, origin, destination) DO NOTHING
                """,
                (run_id, origin, destination, retrieved_at, distance,
                 duration, total_roads, congested_roads, congested, ratio)
            )


def finish_collection_run(run_id, succeeded, failed):
    outcome = "success" if failed == 0 else "partial" if succeeded else "failed"
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.traffic_collection_runs
                SET finished_at = now(), outcome = %s,
                    count_succeeded = %s, count_failed = %s,
                    safe_error_code = %s
                WHERE id = %s AND outcome = 'running'
                """,
                (outcome, succeeded, failed,
                 "unexpected_error" if failed else None, run_id)
            )
    return outcome


async def collect_daily_routes(day: date):
    """Explicit-only worker; calling this makes real Kakao API and DB writes."""
    from asyncio import to_thread

    run_id = await to_thread(reserve_collection_day, day)
    if run_id is None:
        return {"status": "duplicate", "scheduled_for": scheduled_slot_utc(day).isoformat()}

    succeeded = 0
    failed = 0
    for origin, destination in SEOUL_ROUTES:
        try:
            result = await analyze_one_route(origin, destination)
            await to_thread(
                store_collection_observation,
                run_id, origin, destination, result, datetime.now(timezone.utc)
            )
            succeeded += 1
        except Exception:
            # Do not preserve place input or exception body as durable error.
            failed += 1

    outcome = await to_thread(finish_collection_run, run_id, succeeded, failed)
    return {"status": outcome, "run_id": run_id,
            "count_succeeded": succeeded, "count_failed": failed}


def get_collection_run_history(limit=20):
    if not 1 <= limit <= 100:
        raise ValueError("Invalid limit")
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT scheduled_for, started_at, finished_at, outcome,
                       count_total, count_succeeded, count_failed
                FROM public.traffic_collection_runs
                ORDER BY scheduled_for DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
    return [
        {
            "scheduled_for": row[0].isoformat(),
            "started_at": row[1].isoformat(),
            "finished_at": row[2].isoformat() if row[2] else None,
            "outcome": row[3],
            "count_total": row[4],
            "count_succeeded": row[5],
            "count_failed": row[6]
        }
        for row in rows
    ]
