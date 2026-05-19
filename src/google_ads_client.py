import os
from datetime import date, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from config import config


_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google-ads.yaml")


def _get_client() -> GoogleAdsClient:
    return GoogleAdsClient.load_from_storage(_YAML_PATH)


def _date_range_clause(start: date, end: date) -> str:
    return f"segments.date BETWEEN '{start}' AND '{end}'"


def _run_query(query: str) -> list:
    client = _get_client()
    ga_service = client.get_service("GoogleAdsService")
    response = ga_service.search_stream(
        customer_id=config.GOOGLE_ADS_CUSTOMER_ID,
        query=query,
    )
    rows = []
    for batch in response:
        for row in batch.results:
            rows.append(row)
    return rows


# ── Queries ────────────────────────────────────────────────────────────────

_ACCOUNT_QUERY = """
    SELECT
        customer.descriptive_name,
        customer.currency_code,
        metrics.impressions,
        metrics.clicks,
        metrics.ctr,
        metrics.average_cpc,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value,
        metrics.cost_per_conversion,
        segments.date
    FROM customer
    WHERE {date_clause}
    ORDER BY segments.date DESC
"""

_CAMPAIGN_QUERY = """
    SELECT
        campaign.name,
        campaign.status,
        metrics.impressions,
        metrics.clicks,
        metrics.ctr,
        metrics.average_cpc,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value,
        metrics.cost_per_conversion,
        segments.date
    FROM campaign
    WHERE {date_clause}
      AND campaign.status != 'REMOVED'
    ORDER BY metrics.cost_micros DESC
    LIMIT 20
"""

_AD_GROUP_QUERY = """
    SELECT
        ad_group.name,
        campaign.name,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions,
        segments.date
    FROM ad_group
    WHERE {date_clause}
      AND ad_group.status != 'REMOVED'
    ORDER BY metrics.cost_micros DESC
    LIMIT 10
"""


# ── Aggregation helpers ─────────────────────────────────────────────────────

def _aggregate_rows(rows: list) -> dict:
    totals = {
        "impressions": 0,
        "clicks": 0,
        "cost": 0.0,
        "conversions": 0.0,
        "conversions_value": 0.0,
    }
    for row in rows:
        m = row.metrics
        totals["impressions"] += m.impressions
        totals["clicks"] += m.clicks
        totals["cost"] += m.cost_micros / 1_000_000
        totals["conversions"] += m.conversions
        totals["conversions_value"] += m.conversions_value

    totals["ctr"] = (totals["clicks"] / totals["impressions"] * 100) if totals["impressions"] else 0
    totals["avg_cpc"] = (totals["cost"] / totals["clicks"]) if totals["clicks"] else 0
    totals["cost_per_conversion"] = (totals["cost"] / totals["conversions"]) if totals["conversions"] else 0
    totals["roas"] = (totals["conversions_value"] / totals["cost"]) if totals["cost"] else 0
    return totals


def _campaigns_to_list(rows: list) -> list[dict]:
    campaigns: dict[str, dict] = {}
    for row in rows:
        name = row.campaign.name
        if name not in campaigns:
            campaigns[name] = {
                "name": name,
                "status": row.campaign.status.name,
                "impressions": 0,
                "clicks": 0,
                "cost": 0.0,
                "conversions": 0.0,
            }
        m = row.metrics
        campaigns[name]["impressions"] += m.impressions
        campaigns[name]["clicks"] += m.clicks
        campaigns[name]["cost"] += m.cost_micros / 1_000_000
        campaigns[name]["conversions"] += m.conversions

    result = list(campaigns.values())
    for c in result:
        c["ctr"] = (c["clicks"] / c["impressions"] * 100) if c["impressions"] else 0
        c["avg_cpc"] = (c["cost"] / c["clicks"]) if c["clicks"] else 0
    return sorted(result, key=lambda x: x["cost"], reverse=True)


# ── Public API ──────────────────────────────────────────────────────────────

def fetch_daily_data(target_date: date) -> dict:
    """
    Fetches account-level + campaign-level data for `target_date`
    and the previous day, returning both for comparison.
    """
    prev_day = target_date - timedelta(days=1)

    current_rows = _run_query(_ACCOUNT_QUERY.format(date_clause=_date_range_clause(target_date, target_date)))
    prev_rows = _run_query(_ACCOUNT_QUERY.format(date_clause=_date_range_clause(prev_day, prev_day)))
    campaign_rows = _run_query(_CAMPAIGN_QUERY.format(date_clause=_date_range_clause(target_date, target_date)))

    return {
        "date": target_date,
        "prev_date": prev_day,
        "current": _aggregate_rows(current_rows),
        "previous": _aggregate_rows(prev_rows),
        "campaigns": _campaigns_to_list(campaign_rows),
    }


def fetch_monthly_period_data(target_date: date) -> dict:
    """
    Fetches data from 1st of current month to `target_date`,
    compared with the same period last month.
    """
    current_start = target_date.replace(day=1)
    current_end = target_date

    last_month = target_date.month - 1 if target_date.month > 1 else 12
    last_month_year = target_date.year if target_date.month > 1 else target_date.year - 1
    comparison_start = target_date.replace(year=last_month_year, month=last_month, day=1)
    comparison_end = target_date.replace(year=last_month_year, month=last_month)

    current_rows = _run_query(_ACCOUNT_QUERY.format(
        date_clause=_date_range_clause(current_start, current_end)))
    comparison_rows = _run_query(_ACCOUNT_QUERY.format(
        date_clause=_date_range_clause(comparison_start, comparison_end)))
    campaign_rows = _run_query(_CAMPAIGN_QUERY.format(
        date_clause=_date_range_clause(current_start, current_end)))

    return {
        "current_period": {"start": current_start, "end": current_end},
        "comparison_period": {"start": comparison_start, "end": comparison_end},
        "current": _aggregate_rows(current_rows),
        "comparison": _aggregate_rows(comparison_rows),
        "campaigns": _campaigns_to_list(campaign_rows),
    }
