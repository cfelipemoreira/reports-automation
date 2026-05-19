"""
Turns raw API data into structured analysis: % changes, insights, anomalies.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


ANOMALY_THRESHOLD = 0.20  # 20% change triggers an anomaly flag


@dataclass
class MetricChange:
    name: str
    current: float
    previous: float
    pct_change: float
    is_anomaly: bool
    direction: str  # "up" | "down" | "flat"
    unit: str = ""

    @property
    def formatted_current(self) -> str:
        return _fmt(self.current, self.unit)

    @property
    def formatted_previous(self) -> str:
        return _fmt(self.previous, self.unit)

    @property
    def formatted_pct(self) -> str:
        sign = "+" if self.pct_change >= 0 else ""
        return f"{sign}{self.pct_change:.1f}%"


@dataclass
class AnalysisResult:
    title: str
    period_label: str
    comparison_label: str
    metrics: list[MetricChange] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    top_campaigns: list[dict] = field(default_factory=list)


# ── Core helpers ────────────────────────────────────────────────────────────

def _pct(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return (current - previous) / abs(previous) * 100


def _direction(pct: float) -> str:
    if pct > 1:
        return "up"
    if pct < -1:
        return "down"
    return "flat"


def _fmt(value: float, unit: str) -> str:
    if unit == "R$":
        return f"R$ {value:,.2f}"
    if unit == "%":
        return f"{value:.2f}%"
    if unit == "x":
        return f"{value:.2f}x"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:,.0f}" if value == int(value) else f"{value:.2f}"


def _make_metric(name: str, current: float, previous: float, unit: str = "") -> MetricChange:
    pct = _pct(current, previous)
    return MetricChange(
        name=name,
        current=current,
        previous=previous,
        pct_change=pct,
        is_anomaly=abs(pct) >= ANOMALY_THRESHOLD * 100,
        direction=_direction(pct),
        unit=unit,
    )


# ── Google Ads analysis ─────────────────────────────────────────────────────

def analyze_google_ads_daily(data: dict) -> AnalysisResult:
    cur = data["current"]
    prev = data["previous"]
    target_date = data["date"]
    prev_date = data["prev_date"]

    metrics = [
        _make_metric("Impressoes", cur["impressions"], prev["impressions"]),
        _make_metric("Cliques", cur["clicks"], prev["clicks"]),
        _make_metric("CTR", cur["ctr"], prev["ctr"], "%"),
        _make_metric("CPC Medio", cur["avg_cpc"], prev["avg_cpc"], "R$"),
        _make_metric("Gasto Total", cur["cost"], prev["cost"], "R$"),
        _make_metric("Conversoes", cur["conversions"], prev["conversions"]),
        _make_metric("Custo/Conversao", cur["cost_per_conversion"], prev["cost_per_conversion"], "R$"),
        _make_metric("ROAS", cur["roas"], prev["roas"], "x"),
    ]

    result = AnalysisResult(
        title="Google Ads — Analise Diaria",
        period_label=target_date.strftime("%d/%m/%Y"),
        comparison_label=prev_date.strftime("%d/%m/%Y"),
        metrics=metrics,
        top_campaigns=data.get("campaigns", [])[:5],
    )

    _generate_google_ads_insights(result, cur, prev)
    return result


def analyze_google_ads_monthly(data: dict) -> AnalysisResult:
    cur = data["current"]
    comp = data["comparison"]
    cp = data["current_period"]
    pp = data["comparison_period"]

    metrics = [
        _make_metric("Impressoes", cur["impressions"], comp["impressions"]),
        _make_metric("Cliques", cur["clicks"], comp["clicks"]),
        _make_metric("CTR", cur["ctr"], comp["ctr"], "%"),
        _make_metric("CPC Medio", cur["avg_cpc"], comp["avg_cpc"], "R$"),
        _make_metric("Gasto Total", cur["cost"], comp["cost"], "R$"),
        _make_metric("Conversoes", cur["conversions"], comp["conversions"]),
        _make_metric("Custo/Conversao", cur["cost_per_conversion"], comp["cost_per_conversion"], "R$"),
        _make_metric("ROAS", cur["roas"], comp["roas"], "x"),
    ]

    result = AnalysisResult(
        title="Google Ads — Relatorio Mensal",
        period_label=f"{cp['start'].strftime('%d/%m')} - {cp['end'].strftime('%d/%m/%Y')}",
        comparison_label=f"{pp['start'].strftime('%d/%m')} - {pp['end'].strftime('%d/%m/%Y')}",
        metrics=metrics,
        top_campaigns=data.get("campaigns", [])[:10],
    )

    _generate_google_ads_insights(result, cur, comp)
    return result


def _generate_google_ads_insights(result: AnalysisResult, cur: dict, prev: dict):
    for m in result.metrics:
        if m.is_anomaly:
            direction_word = "aumentou" if m.direction == "up" else "caiu"
            result.anomalies.append(
                f"ANOMALIA: {m.name} {direction_word} {m.formatted_pct} "
                f"({m.formatted_previous} -> {m.formatted_current})"
            )

    # Positive signals
    if cur["roas"] > 3:
        result.insights.append(f"ROAS excelente: {cur['roas']:.2f}x — campanha gerando bom retorno.")
    elif cur["roas"] > 1:
        result.insights.append(f"ROAS positivo: {cur['roas']:.2f}x — receita acima do gasto.")
    elif cur["roas"] > 0:
        result.insights.append(f"ATENCAO: ROAS baixo ({cur['roas']:.2f}x) — revise a estrategia de conversao.")

    ctr_change = _pct(cur["ctr"], prev["ctr"])
    if ctr_change > 10:
        result.insights.append(f"CTR subiu {ctr_change:.1f}% — criativos mais relevantes ou segmentacao melhorada.")
    elif ctr_change < -10:
        result.insights.append(f"CTR caiu {abs(ctr_change):.1f}% — considere renovar criativos ou revisar segmentacao.")

    cost_change = _pct(cur["cost"], prev["cost"])
    conv_change = _pct(cur["conversions"], prev["conversions"])
    if cost_change > 5 and conv_change < cost_change - 10:
        result.insights.append(
            f"Gasto cresceu {cost_change:.1f}% mas conversoes cresceram apenas {conv_change:.1f}% — "
            "eficiencia caindo."
        )
    elif conv_change > cost_change + 10:
        result.insights.append(
            f"Conversoes cresceram {conv_change:.1f}% com gasto subindo {cost_change:.1f}% — "
            "eficiencia melhorou."
        )


# ── Reportei analysis ───────────────────────────────────────────────────────

def analyze_reportei_daily(data: dict, target_date: Any) -> AnalysisResult:
    result = AnalysisResult(
        title="Reportei — Analise Diaria",
        period_label=target_date.strftime("%d/%m/%Y") if hasattr(target_date, "strftime") else str(target_date),
        comparison_label="Dia anterior e mesmo dia mes passado",
    )

    for int_id, int_data in data.items():
        integration = int_data.get("integration", {})
        source_name = integration.get("name") or integration.get("source") or f"Integracao {int_id}"
        current = _extract_reportei_metrics(int_data.get("current", {}))
        vs_prev = _extract_reportei_metrics(int_data.get("vs_previous_day", {}))
        vs_lm = _extract_reportei_metrics(int_data.get("vs_same_day_last_month", {}))

        for key, label, unit in _REPORTEI_METRIC_MAP:
            if key in current and key in vs_prev:
                m = _make_metric(f"{source_name} — {label}", current[key], vs_prev[key], unit)
                result.metrics.append(m)
                if m.is_anomaly:
                    direction_word = "subiu" if m.direction == "up" else "caiu"
                    result.anomalies.append(
                        f"ANOMALIA [{source_name}]: {label} {direction_word} {m.formatted_pct} vs dia anterior"
                    )
                if key in vs_lm:
                    lm_pct = _pct(current[key], vs_lm[key])
                    if abs(lm_pct) >= ANOMALY_THRESHOLD * 100:
                        direction_word = "acima" if lm_pct > 0 else "abaixo"
                        result.insights.append(
                            f"{source_name} — {label} esta {abs(lm_pct):.1f}% {direction_word} "
                            f"do mesmo dia no mes passado."
                        )

    return result


def analyze_reportei_monthly(data: dict) -> AnalysisResult:
    result = AnalysisResult(
        title="Reportei — Relatorio Mensal",
        period_label="",
        comparison_label="",
    )

    for int_id, int_data in data.items():
        integration = int_data.get("integration", {})
        source_name = integration.get("name") or integration.get("source") or f"Integracao {int_id}"

        cp = int_data.get("current_period", {})
        pp = int_data.get("comparison_period", {})

        if cp and not result.period_label:
            result.period_label = (
                f"{cp.get('start', '').strftime('%d/%m') if hasattr(cp.get('start',''), 'strftime') else ''}"
                f" - {cp.get('end', '').strftime('%d/%m/%Y') if hasattr(cp.get('end',''), 'strftime') else ''}"
            )
            result.comparison_label = (
                f"{pp.get('start', '').strftime('%d/%m') if hasattr(pp.get('start',''), 'strftime') else ''}"
                f" - {pp.get('end', '').strftime('%d/%m/%Y') if hasattr(pp.get('end',''), 'strftime') else ''}"
            )

        current = _extract_reportei_metrics(int_data.get("current", {}))
        comparison = _extract_reportei_metrics(int_data.get("comparison", {}))

        for key, label, unit in _REPORTEI_METRIC_MAP:
            if key in current and key in comparison:
                m = _make_metric(f"{source_name} — {label}", current[key], comparison[key], unit)
                result.metrics.append(m)
                if m.is_anomaly:
                    direction_word = "cresceu" if m.direction == "up" else "caiu"
                    result.anomalies.append(
                        f"{source_name}: {label} {direction_word} {m.formatted_pct} vs periodo anterior"
                    )

        _generate_reportei_insights(result, source_name, current, comparison)

    return result


_REPORTEI_METRIC_MAP = [
    ("sessions", "Sessoes", ""),
    ("users", "Usuarios", ""),
    ("screenPageViews", "Pageviews", ""),
    ("bounceRate", "Taxa de Rejeicao", "%"),
    ("impressions", "Impressoes", ""),
    ("clicks", "Cliques", ""),
    ("cost", "Gasto", "R$"),
    ("ctr", "CTR", "%"),
    ("conversions", "Conversoes", ""),
    ("reach", "Alcance", ""),
    ("spend", "Investimento", "R$"),
]


def _extract_reportei_metrics(api_response: dict) -> dict:
    """Flattens Reportei's metric response into a simple key->float dict."""
    result = {}
    if not api_response:
        return result
    data = api_response.get("data") or api_response
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                key = item.get("reference_key") or item.get("key") or item.get("id")
                value = item.get("value") or item.get("total") or 0
                if key:
                    try:
                        result[key] = float(value)
                    except (TypeError, ValueError):
                        pass
    elif isinstance(data, dict):
        for k, v in data.items():
            try:
                result[k] = float(v)
            except (TypeError, ValueError):
                pass
    return result


def _generate_reportei_insights(result: AnalysisResult, source: str, cur: dict, prev: dict):
    sessions_change = _pct(cur.get("sessions", 0), prev.get("sessions", 0))
    if abs(sessions_change) > 15:
        direction = "crescimento" if sessions_change > 0 else "queda"
        result.insights.append(
            f"{source}: {direction} de {abs(sessions_change):.1f}% em sessoes vs periodo anterior."
        )

    bounce_cur = cur.get("bounceRate", 0)
    bounce_prev = prev.get("bounceRate", 0)
    if bounce_cur > 70:
        result.insights.append(
            f"{source}: Taxa de rejeicao alta ({bounce_cur:.1f}%) — otimize landing pages."
        )
    elif bounce_cur < bounce_prev - 5:
        result.insights.append(
            f"{source}: Taxa de rejeicao melhorou ({bounce_prev:.1f}% -> {bounce_cur:.1f}%)."
        )
