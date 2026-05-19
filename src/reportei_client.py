import requests
from datetime import date, timedelta
from config import config


class ReporteiClient:
    def __init__(self):
        self.base_url = config.REPORTEI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {config.REPORTEI_API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get(self, path, params=None):
        resp = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path, payload):
        resp = requests.post(f"{self.base_url}{path}", headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Discovery ──────────────────────────────────────────────────────────

    def get_dashboard_id(self, name: str) -> str | None:
        page = 1
        while True:
            data = self._get("/dashboards", params={"page": page, "per_page": 100})
            items = data.get("data", [])
            for d in items:
                if d.get("name", "") == name:
                    return d["id"]
            if page >= data.get("last_page", 1):
                break
            page += 1
        return None

    def get_dashboard(self, dashboard_id: str) -> dict:
        return self._get(f"/dashboards/{dashboard_id}")

    def list_integrations(self) -> list[dict]:
        data = self._get("/integrations", params={"per_page": 100})
        return data.get("data", [])

    def get_projects(self) -> list[dict]:
        data = self._get("/projects", params={"per_page": 100})
        return data.get("data", [])

    # ── Metrics ────────────────────────────────────────────────────────────

    def get_metrics(
        self,
        integration_id: str,
        start: date,
        end: date,
        metrics: list[dict],
        comparison_start: date | None = None,
        comparison_end: date | None = None,
    ) -> dict:
        payload = {
            "integration_id": integration_id,
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "metrics": metrics,
        }
        if comparison_start and comparison_end:
            payload["comparison_start"] = comparison_start.strftime("%Y-%m-%d")
            payload["comparison_end"] = comparison_end.strftime("%Y-%m-%d")
        return self._post("/metrics/get-data", payload)

    # ── High-level helpers ─────────────────────────────────────────────────

    def fetch_daily_data(self, dashboard_id: str, target_date: date) -> dict:
        """
        Fetches metrics for `target_date`, comparing with the previous day
        and the same day last month.
        """
        dashboard = self.get_dashboard(dashboard_id)
        integrations = dashboard.get("integrations", [])

        prev_day = target_date - timedelta(days=1)
        same_day_last_month = target_date.replace(
            month=target_date.month - 1 if target_date.month > 1 else 12,
            year=target_date.year if target_date.month > 1 else target_date.year - 1,
        )

        results = {}
        for integration in integrations:
            int_id = integration.get("id") or integration.get("integration_id")
            if not int_id:
                continue
            metrics_def = _build_metrics_definition(integration)

            current = self.get_metrics(int_id, target_date, target_date, metrics_def)
            vs_prev = self.get_metrics(int_id, prev_day, prev_day, metrics_def)
            vs_last_month = self.get_metrics(
                int_id, target_date, target_date, metrics_def,
                comparison_start=same_day_last_month,
                comparison_end=same_day_last_month,
            )

            results[int_id] = {
                "integration": integration,
                "current": current,
                "vs_previous_day": vs_prev,
                "vs_same_day_last_month": vs_last_month,
            }
        return results

    def fetch_monthly_period_data(self, dashboard_id: str, target_date: date) -> dict:
        """
        Fetches metrics from the 1st of the current month to `target_date`,
        compared with the same period last month.
        """
        dashboard = self.get_dashboard(dashboard_id)
        integrations = dashboard.get("integrations", [])

        current_start = target_date.replace(day=1)
        current_end = target_date

        last_month_year = target_date.year if target_date.month > 1 else target_date.year - 1
        last_month = target_date.month - 1 if target_date.month > 1 else 12
        comparison_start = target_date.replace(year=last_month_year, month=last_month, day=1)
        comparison_end = target_date.replace(year=last_month_year, month=last_month)

        results = {}
        for integration in integrations:
            int_id = integration.get("id") or integration.get("integration_id")
            if not int_id:
                continue
            metrics_def = _build_metrics_definition(integration)

            current = self.get_metrics(int_id, current_start, current_end, metrics_def)
            comparison = self.get_metrics(
                int_id, current_start, current_end, metrics_def,
                comparison_start=comparison_start,
                comparison_end=comparison_end,
            )

            results[int_id] = {
                "integration": integration,
                "current_period": {"start": current_start, "end": current_end},
                "comparison_period": {"start": comparison_start, "end": comparison_end},
                "current": current,
                "comparison": comparison,
            }
        return results


def _build_metrics_definition(integration: dict) -> list[dict]:
    """
    Builds a generic metrics definition based on the integration type.
    The Reportei API requires at minimum a reference_key and component.
    """
    source = (integration.get("source") or integration.get("type") or "").lower()

    if "google_analytics" in source or "ga4" in source:
        return [
            {"reference_key": "sessions", "component": "summary", "metrics": ["sessions"]},
            {"reference_key": "users", "component": "summary", "metrics": ["users"]},
            {"reference_key": "pageviews", "component": "summary", "metrics": ["screenPageViews"]},
            {"reference_key": "bounce_rate", "component": "summary", "metrics": ["bounceRate"]},
        ]
    elif "google_ads" in source or "adwords" in source:
        return [
            {"reference_key": "impressions", "component": "summary", "metrics": ["impressions"]},
            {"reference_key": "clicks", "component": "summary", "metrics": ["clicks"]},
            {"reference_key": "cost", "component": "summary", "metrics": ["cost"]},
            {"reference_key": "ctr", "component": "summary", "metrics": ["ctr"]},
            {"reference_key": "conversions", "component": "summary", "metrics": ["conversions"]},
        ]
    elif "facebook" in source or "meta" in source or "instagram" in source:
        return [
            {"reference_key": "reach", "component": "summary", "metrics": ["reach"]},
            {"reference_key": "impressions", "component": "summary", "metrics": ["impressions"]},
            {"reference_key": "clicks", "component": "summary", "metrics": ["clicks"]},
            {"reference_key": "spend", "component": "summary", "metrics": ["spend"]},
        ]
    else:
        # Generic fallback — fetch whatever the integration exposes
        return [
            {"reference_key": "impressions", "component": "summary", "metrics": ["impressions"]},
            {"reference_key": "clicks", "component": "summary", "metrics": ["clicks"]},
        ]
