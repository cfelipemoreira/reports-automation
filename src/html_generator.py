"""
Generates a self-contained, beautifully styled HTML report
from a ReportData object produced by src/analyzer.py.

Public API:
    html_path(report_type, date_str) -> str   # e.g. data/reports/reportei_daily_2026-05-21.html
    generate_html(report, path) -> str         # writes file, returns path
"""
from __future__ import annotations
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analyzer import ReportData, PlatformAnalysis, MetricBox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "data", "reports")


def html_path(report_type: str, date_str: str) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return os.path.join(REPORTS_DIR, f"{report_type}_{date_str}.html")


def generate_html(report: "ReportData", path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = _render_report(report)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ── Render helpers ────────────────────────────────────────────────────────────

def _badge_class(pct: float, positive_direction: str) -> str:
    if abs(pct) <= 1:
        return "badge-flat"
    is_up = pct > 0
    if positive_direction == "up":
        return "badge-positive" if is_up else "badge-negative"
    elif positive_direction == "down":
        return "badge-positive" if not is_up else "badge-negative"
    return "badge-neutral"  # "neutral" e.g. spend


def _arrow(direction: str) -> str:
    return {"up": "&#9650;", "down": "&#9660;", "flat": "&#8212;"}.get(direction, "&#8212;")


def _render_metric_box(box: "MetricBox") -> str:
    badge_cls = _badge_class(box.pct_change, box.positive_direction)
    arrow = _arrow(box.direction)
    anomaly_mark = '<span class="anomaly-dot" title="Anomalia detectada">!</span>' if box.is_anomaly else ""
    return f"""
      <div class="metric-box{' metric-box--anomaly' if box.is_anomaly else ''}">
        {anomaly_mark}
        <div class="metric-label">{box.label}</div>
        <div class="metric-current">{box.fmt_current}</div>
        <div class="metric-footer">
          <span class="metric-prev">ant: {box.fmt_previous}</span>
          <span class="badge {badge_cls}">{arrow} {box.fmt_pct}</span>
        </div>
      </div>"""


def _render_list_section(title: str, items: list[str], css_class: str, icon: str) -> str:
    if not items:
        return ""
    lis = "\n".join(f'          <li>{item}</li>' for item in items)
    return f"""
      <div class="section-block {css_class}">
        <div class="section-block-header">
          <span class="section-icon">{icon}</span>
          <span class="section-title">{title}</span>
        </div>
        <ul>
{lis}
        </ul>
      </div>"""


def _render_platform(p: "PlatformAnalysis") -> str:
    metrics_html = "\n".join(_render_metric_box(b) for b in p.metrics)
    metrics_grid = f'<div class="metrics-grid">{metrics_html}\n      </div>' if p.metrics else ""

    sections = (
        _render_list_section("Pontos de Destaque", p.highlights, "block-highlight", "&#9670;") +
        _render_list_section("Anomalias", p.anomalies, "block-anomaly", "&#9888;") +
        _render_list_section("Pontos Positivos", p.positives, "block-positive", "&#9650;") +
        _render_list_section("Pontos Negativos", p.negatives, "block-negative", "&#9660;") +
        _render_list_section("Insights", p.insights, "block-insight", "&#9670;") +
        _render_list_section("Acoes Propostas", p.actions, "block-action", "&#9654;")
    )

    return f"""
    <div class="platform-card" style="--platform-color: {p.color};">
      <div class="platform-header">
        <span class="platform-icon">{p.icon_svg}</span>
        <span class="platform-name">{p.name}</span>
      </div>
      <div class="platform-body">
        {metrics_grid}
        {sections}
      </div>
    </div>"""


def _render_executive_summary(report: "ReportData") -> str:
    highlights = "\n".join(
        f'          <li>{h}</li>' for h in report.summary_highlights
    ) if report.summary_highlights else "<li>Nenhum destaque registrado.</li>"

    positives = "\n".join(
        f'          <li>{p}</li>' for p in report.summary_positives
    ) if report.summary_positives else ""

    negatives = "\n".join(
        f'          <li>{n}</li>' for n in report.summary_negatives
    ) if report.summary_negatives else ""

    pos_block = f"""
          <div class="summary-col summary-positive">
            <div class="summary-col-title">&#9650; Principais Altas</div>
            <ul>{positives}</ul>
          </div>""" if positives else ""

    neg_block = f"""
          <div class="summary-col summary-negative">
            <div class="summary-col-title">&#9660; Principais Baixas</div>
            <ul>{negatives}</ul>
          </div>""" if negatives else ""

    return f"""
    <div class="exec-summary">
      <div class="exec-summary-header">Resumo Executivo</div>
      <div class="exec-highlights">
        <div class="exec-highlights-title">Destaques do Periodo</div>
        <ul>
{highlights}
        </ul>
      </div>
      <div class="summary-cols">
        {pos_block}
        {neg_block}
      </div>
    </div>"""


def _render_report(report: "ReportData") -> str:
    generated = report.generated_at.strftime("%d/%m/%Y %H:%M")
    platforms_html = "\n".join(_render_platform(p) for p in report.platforms)
    exec_summary_html = _render_executive_summary(report)

    report_type_label = {
        "daily": "Relatorio Diario",
        "monthly": "Relatorio Mensal",
        "weekly": "Relatorio Semanal",
    }.get(report.report_type, "Relatorio")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{report.title}</title>
  <style>
    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: #1a1a2e;
      background: #f0f2f5;
    }}

    /* ── Page wrapper ── */
    .page {{
      max-width: 900px;
      margin: 0 auto;
      padding: 32px 16px 64px;
    }}

    /* ── Report header ── */
    .report-header {{
      background: #1a1a2e;
      border-radius: 12px 12px 0 0;
      padding: 32px 36px;
      color: #fff;
      margin-bottom: 0;
    }}
    .report-header .report-type-label {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.55);
      margin-bottom: 8px;
    }}
    .report-header h1 {{
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 12px;
      line-height: 1.2;
    }}
    .report-meta {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}
    .meta-pill {{
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 12px;
      color: rgba(255,255,255,0.85);
    }}
    .meta-pill strong {{ color: #fff; }}
    .report-generated {{
      margin-top: 14px;
      font-size: 11px;
      color: rgba(255,255,255,0.4);
    }}

    /* ── Executive Summary ── */
    .exec-summary {{
      background: #fff;
      border-left: 5px solid #1a1a2e;
      border-radius: 0 0 0 0;
      padding: 28px 32px;
      margin-bottom: 2px;
    }}
    .exec-summary-header {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #1a1a2e;
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid #e8e8f0;
    }}
    .exec-highlights-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #5f6368;
      margin-bottom: 10px;
    }}
    .exec-highlights ul, .summary-col ul {{
      list-style: none;
      padding: 0;
    }}
    .exec-highlights li {{
      padding: 6px 0 6px 16px;
      position: relative;
      color: #3c3c4e;
      font-size: 13px;
      border-bottom: 1px solid #f0f0f5;
    }}
    .exec-highlights li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #1a1a2e;
    }}
    .exec-highlights li:last-child {{ border-bottom: none; }}

    .summary-cols {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 20px;
    }}
    @media (max-width: 600px) {{
      .summary-cols {{ grid-template-columns: 1fr; }}
    }}
    .summary-col {{
      border-radius: 8px;
      padding: 16px;
    }}
    .summary-positive {{ background: #f0faf4; border: 1px solid #c3e6cb; }}
    .summary-negative {{ background: #fff5f5; border: 1px solid #f5c6cb; }}
    .summary-col-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .summary-positive .summary-col-title {{ color: #1a7a3c; }}
    .summary-negative .summary-col-title {{ color: #c0392b; }}
    .summary-col li {{
      padding: 5px 0 5px 14px;
      position: relative;
      font-size: 12px;
      border-bottom: 1px solid rgba(0,0,0,0.06);
    }}
    .summary-col li:last-child {{ border-bottom: none; }}
    .summary-positive li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: #28a745;
    }}
    .summary-negative li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: #dc3545;
    }}

    /* ── Platform cards ── */
    .platform-card {{
      background: #fff;
      border-radius: 0;
      border-left: 5px solid var(--platform-color, #4285F4);
      margin-bottom: 2px;
      overflow: hidden;
    }}
    .platform-card:last-child {{
      border-radius: 0 0 12px 12px;
      margin-bottom: 0;
    }}
    .exec-summary:first-of-type + .platform-card,
    .platform-card:first-of-type {{
      margin-top: 0;
    }}

    .platform-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 20px 32px;
      background: #fafafa;
      border-bottom: 1px solid #e8e8f0;
    }}
    .platform-icon {{
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--platform-color);
      flex-shrink: 0;
    }}
    .platform-icon svg {{
      width: 22px;
      height: 22px;
      fill: var(--platform-color);
    }}
    .platform-name {{
      font-size: 15px;
      font-weight: 700;
      color: #1a1a2e;
    }}

    .platform-body {{
      padding: 24px 32px;
    }}

    /* ── Metric boxes ── */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .metric-box {{
      background: #f8f9fc;
      border: 1px solid #e8e8f0;
      border-radius: 8px;
      padding: 14px 16px;
      position: relative;
    }}
    .metric-box--anomaly {{
      border-color: #f0ad4e;
      background: #fffbf0;
    }}
    .anomaly-dot {{
      position: absolute;
      top: 8px;
      right: 8px;
      width: 18px;
      height: 18px;
      background: #f0ad4e;
      color: #fff;
      border-radius: 50%;
      font-size: 11px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
    }}
    .metric-label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: #6b6b80;
      margin-bottom: 8px;
    }}
    .metric-current {{
      font-size: 22px;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 8px;
      line-height: 1;
    }}
    .metric-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
    }}
    .metric-prev {{
      font-size: 11px;
      color: #9b9bae;
    }}

    /* ── Badges ── */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 2px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .badge-positive {{ background: #e6f4ea; color: #1a7a3c; }}
    .badge-negative {{ background: #fce8e6; color: #c0392b; }}
    .badge-flat      {{ background: #f1f3f4; color: #6b6b80; }}
    .badge-neutral   {{ background: #e8f0fe; color: #1967d2; }}

    /* ── Section blocks ── */
    .section-block {{
      margin-bottom: 16px;
      border-radius: 8px;
      padding: 14px 18px;
    }}
    .section-block:last-child {{ margin-bottom: 0; }}
    .section-block-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .section-icon {{
      font-size: 12px;
      line-height: 1;
    }}
    .section-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}
    .section-block ul {{
      list-style: none;
      padding: 0;
    }}
    .section-block li {{
      padding: 5px 0 5px 14px;
      position: relative;
      font-size: 13px;
      border-bottom: 1px solid rgba(0,0,0,0.05);
    }}
    .section-block li:last-child {{ border-bottom: none; }}
    .section-block li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 5px;
      height: 5px;
      border-radius: 50%;
    }}

    /* Block themes */
    .block-highlight {{
      background: #f5f5ff;
      border: 1px solid #ddd8ff;
    }}
    .block-highlight .section-title {{ color: #5040c0; }}
    .block-highlight .section-icon {{ color: #5040c0; }}
    .block-highlight li::before {{ background: #7b68ee; }}

    .block-anomaly {{
      background: #fffbf0;
      border: 1px solid #fde68a;
    }}
    .block-anomaly .section-title {{ color: #b45309; }}
    .block-anomaly .section-icon {{ color: #d97706; }}
    .block-anomaly li::before {{ background: #f59e0b; }}
    .block-anomaly li {{ color: #78350f; }}

    .block-positive {{
      background: #f0faf4;
      border: 1px solid #c3e6cb;
    }}
    .block-positive .section-title {{ color: #1a7a3c; }}
    .block-positive .section-icon {{ color: #28a745; }}
    .block-positive li::before {{ background: #28a745; }}
    .block-positive li {{ color: #155724; }}

    .block-negative {{
      background: #fff5f5;
      border: 1px solid #f5c6cb;
    }}
    .block-negative .section-title {{ color: #c0392b; }}
    .block-negative .section-icon {{ color: #dc3545; }}
    .block-negative li::before {{ background: #dc3545; }}
    .block-negative li {{ color: #721c24; }}

    .block-insight {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
    }}
    .block-insight .section-title {{ color: #1967d2; }}
    .block-insight .section-icon {{ color: #3b82f6; }}
    .block-insight li::before {{ background: #3b82f6; }}
    .block-insight li {{ color: #1e40af; }}

    .block-action {{
      background: #f5f3ff;
      border: 1px solid #ddd6fe;
    }}
    .block-action .section-title {{ color: #6d28d9; }}
    .block-action .section-icon {{ color: #7c3aed; }}
    .block-action li::before {{ background: #8b5cf6; }}
    .block-action li {{ color: #4c1d95; }}

    /* ── Footer ── */
    .report-footer {{
      margin-top: 32px;
      text-align: center;
      color: #9b9bae;
      font-size: 11px;
      padding: 0 16px;
    }}
    .report-footer strong {{ color: #6b6b80; }}
  </style>
</head>
<body>
  <div class="page">

    <!-- Header -->
    <div class="report-header">
      <div class="report-type-label">{report_type_label}</div>
      <h1>{report.title}</h1>
      <div class="report-meta">
        <span class="meta-pill"><strong>Periodo:</strong> {report.period_label}</span>
        <span class="meta-pill"><strong>Comparacao:</strong> {report.comparison_label}</span>
      </div>
      <div class="report-generated">Gerado em {generated}</div>
    </div>

    <!-- Executive Summary -->
    {exec_summary_html}

    <!-- Platform sections -->
    {platforms_html}

    <!-- Footer -->
    <div class="report-footer">
      <strong>NEX Coworking</strong> &bull; Relatorio automatico gerado pelo sistema de monitoramento &bull; {generated}
    </div>

  </div>
</body>
</html>"""
