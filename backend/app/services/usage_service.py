import csv
import io
from datetime import datetime, timezone
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from app.models.token_usage import TokenUsage
from app.models.model_registry import ModelRegistry
from app.models.api_key import ApiKey
from app.models.user import User
from app.utils.time_helpers import get_time_range


def get_usage_summary(db: Session, user_id: int | None = None) -> dict:
    """Get aggregate usage summary for the last 24 hours."""
    start_time, _ = get_time_range("24h")

    query = db.query(
        func.count(TokenUsage.id).label("total_requests"),
        func.coalesce(func.sum(TokenUsage.prompt_tokens), 0).label("total_prompt_tokens"),
        func.coalesce(func.sum(TokenUsage.completion_tokens), 0).label("total_completion_tokens"),
        func.coalesce(func.sum(TokenUsage.total_tokens), 0).label("total_tokens"),
    ).filter(TokenUsage.request_timestamp >= start_time)

    if user_id:
        query = query.filter(TokenUsage.user_id == user_id)

    result = query.first()

    active_models = (
        db.query(func.count(ModelRegistry.id))
        .filter(ModelRegistry.is_active == True)
        .scalar()
    )
    active_keys = (
        db.query(func.count(ApiKey.id))
        .filter(ApiKey.is_active == True)
        .scalar()
    )

    return {
        "total_requests": result.total_requests or 0,
        "total_prompt_tokens": result.total_prompt_tokens or 0,
        "total_completion_tokens": result.total_completion_tokens or 0,
        "total_tokens": result.total_tokens or 0,
        "active_models": active_models or 0,
        "active_api_keys": active_keys or 0,
    }


def get_chart_data(
    db: Session,
    range_key: str,
    model_id: int | None = None,
    user_id: int | None = None,
    group_by: str = "total",
) -> dict:
    """Get time-series data for line charts."""
    start_time, bucket_seconds = get_time_range(range_key)
    start_ts = int(start_time.timestamp())
    now_ts = int(datetime.now(timezone.utc).timestamp())

    # Generate all bucket timestamps
    all_buckets = []
    ts = (start_ts // bucket_seconds) * bucket_seconds
    while ts <= now_ts:
        all_buckets.append(ts)
        ts += bucket_seconds

    # Build query
    bucket_expr = text(
        f"(CAST(strftime('%s', request_timestamp) AS INTEGER) / {bucket_seconds}) * {bucket_seconds}"
    )

    if group_by == "model":
        group_col = TokenUsage.model_id
    elif group_by == "user":
        group_col = TokenUsage.user_id
    else:
        group_col = None

    query = db.query(
        bucket_expr.label("bucket_ts"),
        func.sum(TokenUsage.total_tokens).label("tokens"),
    )

    if group_col is not None:
        query = query.add_columns(group_col.label("group_id"))

    query = query.filter(TokenUsage.request_timestamp >= start_time)

    if model_id:
        query = query.filter(TokenUsage.model_id == model_id)
    if user_id:
        query = query.filter(TokenUsage.user_id == user_id)

    query = query.group_by("bucket_ts")
    if group_col is not None:
        query = query.group_by(group_col)

    query = query.order_by("bucket_ts")
    rows = query.all()

    # Build response
    if group_by == "total" or group_col is None:
        data_map = {b: 0 for b in all_buckets}
        for row in rows:
            bucket = int(row.bucket_ts)
            if bucket in data_map:
                data_map[bucket] = int(row.tokens)
        return {
            "timestamps": all_buckets,
            "series": [{"name": "總計", "data": [data_map[b] for b in all_buckets]}],
        }
    else:
        # Get group names
        if group_by == "model":
            name_map = {
                m.id: m.display_name
                for m in db.query(ModelRegistry).all()
            }
        else:
            name_map = {
                u.id: u.username
                for u in db.query(User).all()
            }

        group_data: dict[int, dict[int, int]] = {}
        for row in rows:
            gid = int(row.group_id)
            bucket = int(row.bucket_ts)
            if gid not in group_data:
                group_data[gid] = {b: 0 for b in all_buckets}
            if bucket in group_data[gid]:
                group_data[gid][bucket] = int(row.tokens)

        series = []
        for gid, data_map in group_data.items():
            series.append({
                "name": name_map.get(gid, str(gid)),
                "data": [data_map[b] for b in all_buckets],
            })

        return {"timestamps": all_buckets, "series": series}


def get_top_models(db: Session, limit: int = 10) -> list[dict]:
    start_time, _ = get_time_range("30d")
    results = (
        db.query(
            TokenUsage.model_id,
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.count(TokenUsage.id).label("total_requests"),
        )
        .filter(TokenUsage.request_timestamp >= start_time)
        .group_by(TokenUsage.model_id)
        .order_by(func.sum(TokenUsage.total_tokens).desc())
        .limit(limit)
        .all()
    )

    model_map = {m.id: m for m in db.query(ModelRegistry).all()}
    return [
        {
            "model_id": r.model_id,
            "model_name": model_map.get(r.model_id, ModelRegistry()).display_name or "未知",
            "model_type": model_map.get(r.model_id, ModelRegistry()).model_type or "未知",
            "total_tokens": int(r.total_tokens),
            "total_requests": r.total_requests,
        }
        for r in results
    ]


def get_top_users(db: Session, limit: int = 10) -> list[dict]:
    start_time, _ = get_time_range("30d")
    results = (
        db.query(
            TokenUsage.user_id,
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.count(TokenUsage.id).label("total_requests"),
        )
        .filter(TokenUsage.request_timestamp >= start_time)
        .group_by(TokenUsage.user_id)
        .order_by(func.sum(TokenUsage.total_tokens).desc())
        .limit(limit)
        .all()
    )

    user_map = {u.id: u.username for u in db.query(User).all()}
    return [
        {
            "user_id": r.user_id,
            "username": user_map.get(r.user_id, "未知"),
            "total_tokens": int(r.total_tokens),
            "total_requests": r.total_requests,
        }
        for r in results
    ]


def export_usage_csv(
    db: Session,
    range_key: str,
    model_id: int | None = None,
    user_id: int | None = None,
) -> str:
    """Export usage data as CSV string."""
    start_time, _ = get_time_range(range_key)

    query = db.query(
        TokenUsage.request_timestamp,
        User.username,
        ModelRegistry.display_name.label("model_name"),
        ModelRegistry.model_type,
        TokenUsage.prompt_tokens,
        TokenUsage.completion_tokens,
        TokenUsage.total_tokens,
        TokenUsage.request_duration_ms,
    ).join(
        User, TokenUsage.user_id == User.id
    ).join(
        ModelRegistry, TokenUsage.model_id == ModelRegistry.id
    ).filter(
        TokenUsage.request_timestamp >= start_time
    )

    if model_id:
        query = query.filter(TokenUsage.model_id == model_id)
    if user_id:
        query = query.filter(TokenUsage.user_id == user_id)

    query = query.order_by(TokenUsage.request_timestamp.desc())
    rows = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "時間", "使用者", "模型", "類型",
        "輸入 Tokens", "輸出 Tokens", "總計 Tokens", "延遲 (ms)"
    ])
    for row in rows:
        writer.writerow([
            row.request_timestamp.isoformat() if row.request_timestamp else "",
            row.username,
            row.model_name,
            row.model_type,
            row.prompt_tokens,
            row.completion_tokens,
            row.total_tokens,
            row.request_duration_ms or "",
        ])

    return output.getvalue()
