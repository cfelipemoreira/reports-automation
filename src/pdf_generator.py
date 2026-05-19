"""
Generates PDF reports from AnalysisResult objects using ReportLab.
"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.analyzer import AnalysisResult, MetricChange
from config import config

# ── Brand palette ────────────────────────────────────────────────────────────
C_PRIMARY = colors.HexColor("#1A73E8")   # Google-blue accent
C_SUCCESS = colors.HexColor("#34A853")
C_DANGER  = colors.HexColor("#EA4335")
C_WARNING = colors.HexColor("#FBBC04")
C_DARK    = colors.HexColor("#202124")
C_GRAY    = colors.HexColor("#5F6368")
C_LIGHT   = colors.HexColor("#F8F9FA")
C_WHITE   = colors.white
C_BORDER  = colors.HexColor("#DADCE0")


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom["title"] = ParagraphStyle(
        "title", parent=base["Normal"],
        fontSize=22, textColor=C_DARK, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    custom["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontSize=11, textColor=C_GRAY, spaceAfter=12,
        fontName="Helvetica",
    )
    custom["section"] = ParagraphStyle(
        "section", parent=base["Normal"],
        fontSize=13, textColor=C_PRIMARY, spaceBefore=16, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    custom["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=10, textColor=C_DARK, spaceAfter=4,
        fontName="Helvetica",
    )
    custom["insight"] = ParagraphStyle(
        "insight", parent=base["Normal"],
        fontSize=10, textColor=C_DARK, spaceAfter=3,
        leftIndent=12, fontName="Helvetica",
    )
    custom["anomaly"] = ParagraphStyle(
        "anomaly", parent=base["Normal"],
        fontSize=10, textColor=C_DANGER, spaceAfter=3,
        leftIndent=12, fontName="Helvetica-Bold",
    )
    custom["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"],
        fontSize=8, textColor=C_GRAY, alignment=TA_CENTER,
        fontName="Helvetica",
    )
    return custom


def _metric_color(direction: str) -> colors.Color:
    if direction == "up":
        return C_SUCCESS
    if direction == "down":
        return C_DANGER
    return C_GRAY


def _build_metrics_table(metrics: list[MetricChange], S: dict) -> Table:
    header = [
        Paragraph("<b>Metrica</b>", S["body"]),
        Paragraph("<b>Atual</b>", S["body"]),
        Paragraph("<b>Anterior</b>", S["body"]),
        Paragraph("<b>Variacao</b>", S["body"]),
    ]
    rows = [header]
    for m in metrics:
        arrow = "▲" if m.direction == "up" else ("▼" if m.direction == "down" else "—")
        pct_text = f"{arrow} {m.formatted_pct}"
        pct_para = Paragraph(
            f'<font color="{"#34A853" if m.direction == "up" else "#EA4335" if m.direction == "down" else "#5F6368"}">'
            f'<b>{pct_text}</b></font>',
            S["body"],
        )
        rows.append([
            Paragraph(m.name, S["body"]),
            Paragraph(m.formatted_current, S["body"]),
            Paragraph(m.formatted_previous, S["body"]),
            pct_para,
        ])

    col_widths = [8 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _build_campaigns_table(campaigns: list[dict], S: dict) -> Table:
    header = [
        Paragraph("<b>Campanha</b>", S["body"]),
        Paragraph("<b>Impressoes</b>", S["body"]),
        Paragraph("<b>Cliques</b>", S["body"]),
        Paragraph("<b>CTR</b>", S["body"]),
        Paragraph("<b>Gasto</b>", S["body"]),
        Paragraph("<b>Conversoes</b>", S["body"]),
    ]
    rows = [header]
    for c in campaigns:
        rows.append([
            Paragraph(c["name"][:40], S["body"]),
            Paragraph(f"{c['impressions']:,}", S["body"]),
            Paragraph(f"{c['clicks']:,}", S["body"]),
            Paragraph(f"{c['ctr']:.2f}%", S["body"]),
            Paragraph(f"R$ {c['cost']:.2f}", S["body"]),
            Paragraph(f"{c['conversions']:.0f}", S["body"]),
        ])

    col_widths = [5.5 * cm, 2.8 * cm, 2.2 * cm, 2.2 * cm, 2.8 * cm, 2.8 * cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def generate_pdf(analysis: AnalysisResult, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    S = _styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # ── Header ──────────────────────────────────────────────
    story.append(Paragraph(analysis.title, S["title"]))
    story.append(Paragraph(
        f"Periodo: <b>{analysis.period_label}</b> &nbsp;|&nbsp; "
        f"Comparacao: <b>{analysis.comparison_label}</b>",
        S["subtitle"],
    ))
    story.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        S["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=12))

    # ── Metrics table ────────────────────────────────────────
    if analysis.metrics:
        story.append(Paragraph("Metricas Principais", S["section"]))
        story.append(_build_metrics_table(analysis.metrics, S))
        story.append(Spacer(1, 0.4 * cm))

    # ── Anomalies ────────────────────────────────────────────
    if analysis.anomalies:
        story.append(Paragraph("Anomalias Detectadas", S["section"]))
        for anomaly in analysis.anomalies:
            story.append(Paragraph(f"• {anomaly}", S["anomaly"]))
        story.append(Spacer(1, 0.3 * cm))

    # ── Insights ─────────────────────────────────────────────
    if analysis.insights:
        story.append(Paragraph("Insights e Recomendacoes", S["section"]))
        for insight in analysis.insights:
            story.append(Paragraph(f"• {insight}", S["insight"]))
        story.append(Spacer(1, 0.3 * cm))

    # ── Top Campaigns ─────────────────────────────────────────
    if analysis.top_campaigns:
        story.append(KeepTogether([
            Paragraph("Campanhas em Destaque", S["section"]),
            _build_campaigns_table(analysis.top_campaigns, S),
        ]))
        story.append(Spacer(1, 0.4 * cm))

    # ── Footer ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=12))
    story.append(Paragraph(
        "Relatorio gerado automaticamente | NEX Coworking — felipe@nexcoworking.com.br",
        S["footer"],
    ))

    doc.build(story)
    return output_path


def pdf_path(report_type: str, date_str: str) -> str:
    filename = f"{report_type}_{date_str}.pdf"
    return os.path.join(config.REPORTS_DIR, filename)
