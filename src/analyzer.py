"""
Transforms raw Reportei API data into structured analysis:
PlatformAnalysis (per source) + ReportData (full report with executive summary).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

ANOMALY_THRESHOLD = 0.20   # 20%
HIGHLIGHT_THRESHOLD = 0.10  # 10%


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class MetricBox:
    label: str
    current: float
    previous: float
    pct_change: float
    unit: str = ""
    direction: str = "flat"   # "up" | "down" | "flat"
    is_anomaly: bool = False
    positive_direction: str = "up"  # which direction is "good" for this metric

    @property
    def is_positive(self) -> bool:
        return self.direction == self.positive_direction and self.direction != "flat"

    @property
    def is_negative(self) -> bool:
        return self.direction != self.positive_direction and self.direction != "flat"

    @property
    def fmt_current(self) -> str:  return _fmt(self.current, self.unit)
    @property
    def fmt_previous(self) -> str: return _fmt(self.previous, self.unit)
    @property
    def fmt_pct(self) -> str:
        sign = "+" if self.pct_change >= 0 else ""
        return f"{sign}{self.pct_change:.1f}%"


@dataclass
class PlatformAnalysis:
    name: str
    color: str            # hex color for the platform accent
    icon_svg: str         # inline SVG string
    metrics: list[MetricBox] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    anomalies: list[str]  = field(default_factory=list)
    positives: list[str]  = field(default_factory=list)
    negatives: list[str]  = field(default_factory=list)
    insights: list[str]   = field(default_factory=list)
    actions: list[str]    = field(default_factory=list)


@dataclass
class ReportData:
    title: str
    report_type: str      # "daily" | "monthly" | "weekly"
    period_label: str
    comparison_label: str
    generated_at: datetime
    summary_highlights: list[str] = field(default_factory=list)
    summary_positives: list[str]  = field(default_factory=list)
    summary_negatives: list[str]  = field(default_factory=list)
    platforms: list[PlatformAnalysis] = field(default_factory=list)


# ── Platform config ──────────────────────────────────────────────────────────

_PLATFORM_META = {
    "GA4 — Sessoes e Trafego": {
        "color": "#4285F4",
        "short": "Google Analytics 4",
        "icon": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M22.84 2.998C21.616 1.702 19.864 1 18 1c-1.864 0-3.616.702-4.84 1.998L12 4.201l-1.16-1.203C9.616 1.702 7.864 1 6 1 4.136 1 2.384 1.702 1.16 2.998 0 4.228 0 6.001 0 7c0 5.005 5.824 9.98 10.814 13.496L12 21.4l1.186-.904C18.176 16.98 24 12.005 24 7c0-.999 0-2.772-1.16-4.002z"/></svg>',
    },
    "Facebook Ads — NEX Curitiba": {
        "color": "#1877F2",
        "short": "Facebook Ads",
        "icon": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.397 20.997v-8.196h2.765l.411-3.209h-3.176V7.548c0-.926.258-1.56 1.587-1.56h1.684V3.127A22.336 22.336 0 0 0 14.201 3c-2.444 0-4.122 1.492-4.122 4.231v2.355H7.332v3.209h2.753v8.202h3.312z"/></svg>',
    },
    "Google Ads — NEX.WORK": {
        "color": "#34A853",
        "short": "Google Ads",
        "icon": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></svg>',
    },
    "Search Console — nex.work": {
        "color": "#EA4335",
        "short": "Search Console",
        "icon": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
    },
}

# ── Metric definitions (reference_key → label, unit, positive_direction) ────

_METRIC_CONFIG = {
    # GA4
    "google_analytics_4:all_sessions":  ("Sessoes",        "",   "up"),
    "google_analytics_4:total_users":   ("Usuarios",       "",   "up"),
    "google_analytics_4:new_users":     ("Novos Usuarios", "",   "up"),
    "google_analytics_4:all_pageviews": ("Pageviews",      "",   "up"),
    # Facebook Ads
    "fb_ads:spend":       ("Investimento",  "R$",  "neutral"),
    "fb_ads:impressions": ("Impressoes",    "",    "up"),
    "fb_ads:clicks":      ("Cliques",       "",    "up"),
    "fb_ads:reach":       ("Alcance",       "",    "up"),
    "fb_ads:ctr":         ("CTR",           "%",   "up"),
    "fb_ads:cpm":         ("CPM",           "R$",  "down"),
    "fb_ads:cpc":         ("CPC",           "R$",  "down"),
    # Google Ads
    "gads:impressions":        ("Impressoes",     "",   "up"),
    "gads:clicks":             ("Cliques",        "",   "up"),
    "gads:cost_micros":        ("Investimento",   "R$", "neutral"),
    "gads:conversions":        ("Conversoes",     "",   "up"),
    "gads:ctr":                ("CTR",            "%",  "up"),
    "gads:average_cpc":        ("CPC Medio",      "R$", "down"),
    "gads:roas":               ("ROAS",           "x",  "up"),
    "gads:cost_per_conversion":("Custo/Conv",     "R$", "down"),
    # Search Console
    "search_console:clicks":      ("Cliques Org.",    "", "up"),
    "search_console:impressions": ("Impressoes Org.", "", "up"),
    "search_console:ctr":         ("CTR Organico",    "%","up"),
}


# ── Core helpers ─────────────────────────────────────────────────────────────

def _pct(current: float, previous: float) -> float:
    if not previous:
        return 100.0 if current > 0 else 0.0
    return (current - previous) / abs(previous) * 100


def _direction(pct: float) -> str:
    if pct > 1:  return "up"
    if pct < -1: return "down"
    return "flat"


def _fmt(value: float, unit: str) -> str:
    if unit == "R$":
        return f"R$ {value:,.2f}"
    if unit == "%":
        v = value * 100 if value < 1 else value
        return f"{v:.2f}%"
    if unit == "x":
        return f"{value:.2f}x"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:,.0f}" if value == int(value) else f"{value:.2f}"


def _make_box(ref_key: str, current: float, previous: float) -> MetricBox:
    label, unit, pos_dir = _METRIC_CONFIG.get(ref_key, (ref_key.split(":")[-1], "", "up"))
    pct = _pct(current, previous)
    direction = _direction(pct)
    return MetricBox(
        label=label, current=current, previous=previous,
        pct_change=pct, unit=unit, direction=direction,
        is_anomaly=abs(pct) >= ANOMALY_THRESHOLD * 100,
        positive_direction=pos_dir,
    )


# ── Platform analyzers ────────────────────────────────────────────────────────

def _analyze_ga4(metrics: dict[str, dict], comparison_label: str) -> PlatformAnalysis:
    meta = _PLATFORM_META["GA4 — Sessoes e Trafego"]
    p = PlatformAnalysis(name="Google Analytics 4 — Trafego", color=meta["color"], icon_svg=meta["icon"])

    def cur(k):  return metrics.get(k, {}).get("current", 0) or 0
    def comp(k): return metrics.get(k, {}).get("comparison", 0) or 0

    sessions    = cur("google_analytics_4:all_sessions")
    sessions_p  = comp("google_analytics_4:all_sessions")
    users       = cur("google_analytics_4:total_users")
    users_p     = comp("google_analytics_4:total_users")
    new_users   = cur("google_analytics_4:new_users")
    new_users_p = comp("google_analytics_4:new_users")
    pageviews   = cur("google_analytics_4:all_pageviews")
    pageviews_p = comp("google_analytics_4:all_pageviews")

    for key in ["google_analytics_4:all_sessions","google_analytics_4:total_users",
                "google_analytics_4:new_users","google_analytics_4:all_pageviews"]:
        if cur(key) or comp(key):
            p.metrics.append(_make_box(key, cur(key), comp(key)))

    # Highlights
    if sessions > 0:
        p.highlights.append(f"{int(sessions):,} sessoes no periodo analisado")
    if new_users > 0:
        ratio = new_users / users * 100 if users else 0
        p.highlights.append(f"{ratio:.1f}% dos usuarios sao novos ({int(new_users):,} de {int(users):,})")

    # Anomalias + Positivos + Negativos
    for box in p.metrics:
        if box.is_anomaly:
            p.anomalies.append(
                f"{box.label}: {box.fmt_pct} vs {comparison_label} ({box.fmt_previous} → {box.fmt_current})"
            )
        if box.is_positive:
            p.positives.append(f"{box.label} cresceu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")
        elif box.is_negative:
            p.negatives.append(f"{box.label} caiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")

    # Insights
    s_pct = _pct(sessions, sessions_p)
    if s_pct > 20:
        p.insights.append(f"Crescimento expressivo de trafego (+{s_pct:.1f}%) — verificar qual canal esta gerando mais sessoes.")
    elif s_pct < -20:
        p.insights.append(f"Queda significativa de sessoes ({s_pct:.1f}%) — possivel impacto de campanhas pausadas ou sazonalidade.")

    pv_per_session = pageviews / sessions if sessions else 0
    if pv_per_session > 3:
        p.insights.append(f"Engajamento alto: media de {pv_per_session:.1f} paginas por sessao.")
    elif pv_per_session < 1.5 and sessions > 50:
        p.insights.append(f"Engajamento baixo: apenas {pv_per_session:.1f} paginas por sessao — revisar experiencia no site.")

    nu_pct = _pct(new_users, new_users_p)
    if nu_pct > 15:
        p.insights.append(f"Aquisicao em alta (+{nu_pct:.1f}% novos usuarios) — campanhas de topo de funil funcionando.")

    # Ações
    if s_pct < -15:
        p.actions.append("Verificar status das campanhas pagas e check de indexacao no Google Search Console.")
    if pv_per_session < 1.5 and sessions > 50:
        p.actions.append("Revisar CTA e estrutura de navegacao para aumentar paginas por sessao.")
    if nu_pct < -10:
        p.actions.append("Avaliar aumento de investimento em campanhas de aquisicao (topo de funil).")
    if not p.actions:
        p.actions.append("Manter estrategia atual e monitorar evolucao semanal do trafego.")

    return p


def _analyze_fb_ads(metrics: dict[str, dict], comparison_label: str) -> PlatformAnalysis:
    meta = _PLATFORM_META["Facebook Ads — NEX Curitiba"]
    p = PlatformAnalysis(name="Facebook Ads — NEX Curitiba", color=meta["color"], icon_svg=meta["icon"])

    def cur(k):  return metrics.get(k, {}).get("current", 0) or 0
    def comp(k): return metrics.get(k, {}).get("comparison", 0) or 0

    spend    = cur("fb_ads:spend");    spend_p  = comp("fb_ads:spend")
    impr     = cur("fb_ads:impressions"); impr_p = comp("fb_ads:impressions")
    clicks   = cur("fb_ads:clicks");   clicks_p = comp("fb_ads:clicks")
    reach    = cur("fb_ads:reach");    reach_p  = comp("fb_ads:reach")
    ctr_raw  = cur("fb_ads:ctr");      ctr_p    = comp("fb_ads:ctr")
    cpm      = cur("fb_ads:cpm");      cpm_p    = comp("fb_ads:cpm")
    cpc      = cur("fb_ads:cpc");      cpc_p    = comp("fb_ads:cpc")

    ctr = ctr_raw * 100 if ctr_raw < 1 else ctr_raw

    for key in ["fb_ads:spend","fb_ads:impressions","fb_ads:clicks","fb_ads:reach","fb_ads:ctr","fb_ads:cpm","fb_ads:cpc"]:
        v, vp = cur(key), comp(key)
        if v or vp:
            b = _make_box(key, v, vp)
            if key == "fb_ads:ctr":  # normalize CTR display
                b.current  = b.current  * 100 if b.current  < 1 else b.current
                b.previous = b.previous * 100 if b.previous < 1 else b.previous
            p.metrics.append(b)

    # Highlights
    if spend > 0:
        p.highlights.append(f"Investimento de R$ {spend:,.2f} no periodo")
    if reach > 0:
        p.highlights.append(f"Alcance de {int(reach):,} pessoas")
    if ctr > 0:
        p.highlights.append(f"CTR de {ctr:.2f}%")

    # Anomalias + Positivos + Negativos
    for box in p.metrics:
        if box.is_anomaly:
            p.anomalies.append(f"{box.label}: {box.fmt_pct} vs {comparison_label}")
        if box.label in ("CTR", "Cliques", "Alcance", "Impressoes") and box.is_positive:
            p.positives.append(f"{box.label} subiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")
        elif box.label in ("CTR", "Cliques", "Alcance", "Impressoes") and box.is_negative:
            p.negatives.append(f"{box.label} caiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")
        if box.label in ("CPM", "CPC") and box.is_positive:
            p.positives.append(f"{box.label} reduziu {box.fmt_pct} — maior eficiencia de custo")
        elif box.label in ("CPM", "CPC") and box.is_negative:
            p.negatives.append(f"{box.label} subiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")

    # Investimento vs entrega
    spend_pct = _pct(spend, spend_p)
    impr_pct  = _pct(impr,  impr_p)
    if spend_pct > 10 and impr_pct < spend_pct - 15:
        p.insights.append(f"Gasto subiu {spend_pct:.1f}% mas impressoes cresceram apenas {impr_pct:.1f}% — CPM aumentando.")
        p.negatives.append(f"Eficiencia de entrega caindo: mais gasto, menos alcance proporcional")
    elif spend_pct > 0 and impr_pct > spend_pct:
        p.insights.append(f"Boa eficiencia: gasto +{spend_pct:.1f}% gerou +{impr_pct:.1f}% de impressoes.")
        p.positives.append(f"CPM em queda — melhor custo por impressao")

    cpm_pct = _pct(cpm, cpm_p)
    if cpm_pct > 30:
        p.insights.append(f"CPM subiu {cpm_pct:.1f}% — mercado mais competitivo ou audience saturada.")
        p.actions.append("Testar novos publicos ou ampliar audience para reduzir CPM.")
    elif cpm_pct < -15:
        p.insights.append(f"CPM caiu {abs(cpm_pct):.1f}% — oportunidade de escalar investimento mantendo eficiencia.")
        p.actions.append("Considerar aumento de orcamento aproveitando CPM baixo.")

    ctr_pct = _pct(ctr, ctr_p * 100 if ctr_p < 1 else ctr_p)
    if ctr < 1.0:
        p.insights.append(f"CTR abaixo de 1% ({ctr:.2f}%) — criativos podem estar com fadiga.")
        p.actions.append("Renovar criativos e testar novos formatos (Reels, UGC) para melhorar CTR.")
    elif ctr_pct > 20:
        p.insights.append(f"CTR em alta (+{ctr_pct:.1f}%) — criativos com boa ressonancia.")

    if not p.actions:
        p.actions.append("Manter mix de criativos atual e acompanhar frequencia para evitar fadiga.")

    return p


def _analyze_gads(metrics: dict[str, dict], comparison_label: str) -> PlatformAnalysis:
    meta = _PLATFORM_META["Google Ads — NEX.WORK"]
    p = PlatformAnalysis(name="Google Ads — NEX.WORK", color=meta["color"], icon_svg=meta["icon"])

    def cur(k):  return metrics.get(k, {}).get("current", 0) or 0
    def comp(k): return metrics.get(k, {}).get("comparison", 0) or 0

    impressions = cur("gads:impressions"); impressions_p = comp("gads:impressions")
    clicks      = cur("gads:clicks");      clicks_p      = comp("gads:clicks")
    cost        = cur("gads:cost_micros"); cost_p        = comp("gads:cost_micros")
    conversions = cur("gads:conversions"); conversions_p = comp("gads:conversions")
    ctr_raw     = cur("gads:ctr");         ctr_p         = comp("gads:ctr")
    avg_cpc     = cur("gads:average_cpc"); avg_cpc_p     = comp("gads:average_cpc")
    roas        = cur("gads:roas")
    cpp         = cur("gads:cost_per_conversion"); cpp_p = comp("gads:cost_per_conversion")

    ctr = ctr_raw * 100 if ctr_raw < 1 else ctr_raw

    for key in ["gads:impressions","gads:clicks","gads:cost_micros","gads:conversions",
                "gads:ctr","gads:average_cpc","gads:roas","gads:cost_per_conversion"]:
        v, vp = cur(key), comp(key)
        if v or vp:
            b = _make_box(key, v, vp)
            if key == "gads:ctr":
                b.current  = b.current  * 100 if b.current  < 1 else b.current
                b.previous = b.previous * 100 if b.previous < 1 else b.previous
            p.metrics.append(b)

    # Highlights
    if cost > 0:
        p.highlights.append(f"Investimento de R$ {cost:,.2f} no periodo")
    if conversions > 0:
        p.highlights.append(f"{conversions:.0f} conversoes registradas")
    if cpp > 0:
        p.highlights.append(f"Custo por conversao: R$ {cpp:,.2f}")

    # Anomalias
    for box in p.metrics:
        if box.is_anomaly and box.label != "Investimento":
            p.anomalies.append(f"{box.label}: {box.fmt_pct} vs {comparison_label} ({box.fmt_previous} → {box.fmt_current})")

    # Positivos / Negativos
    cost_pct = _pct(cost, cost_p)
    conv_pct = _pct(conversions, conversions_p)
    cpc_pct  = _pct(avg_cpc, avg_cpc_p)

    if conv_pct > 0 and cost_pct <= conv_pct:
        p.positives.append(f"Conversoes +{conv_pct:.1f}% com gasto +{cost_pct:.1f}% — eficiencia melhorando")
    elif conv_pct > 0:
        p.positives.append(f"Conversoes cresceram {conv_pct:.1f}%")

    if cpc_pct < -5:
        p.positives.append(f"CPC medio caiu {abs(cpc_pct):.1f}% — cliques mais baratos")
    elif cpc_pct > 15:
        p.negatives.append(f"CPC medio subiu {cpc_pct:.1f}% — cliques mais caros")

    if conv_pct < -10 and cost_pct > 0:
        p.negatives.append(f"Conversoes caindo ({conv_pct:.1f}%) com gasto subindo (+{cost_pct:.1f}%) — ROI deteriorando")
    if ctr < 3.0 and impressions > 500:
        p.negatives.append(f"CTR abaixo de 3% ({ctr:.2f}%) — anuncios com baixa relevancia ou competicao alta")

    # Insights
    if roas > 3:
        p.insights.append(f"ROAS de {roas:.2f}x — campanha gerando retorno muito positivo.")
    elif roas > 1:
        p.insights.append(f"ROAS de {roas:.2f}x — acima de 1, campanha rentavel.")
    elif roas > 0 and roas < 1:
        p.insights.append(f"ROAS de {roas:.2f}x — abaixo de 1, campanha custando mais do que retorna.")
        p.negatives.append(f"ROAS {roas:.2f}x — campanha no prejuizo em termos de receita direta")

    impr_pct = _pct(impressions, impressions_p)
    ctr_pct  = _pct(ctr, ctr_p * 100 if ctr_p < 1 else ctr_p)
    if impr_pct > 20 and ctr_pct < -10:
        p.insights.append(f"Impressoes +{impr_pct:.1f}% mas CTR caiu {abs(ctr_pct):.1f}% — cobertura maior porem menos relevante.")
        p.actions.append("Revisar match types e negativar termos irrelevantes para melhorar CTR.")
    elif impr_pct > 20 and ctr_pct >= 0:
        p.insights.append(f"Escala com qualidade: impressoes +{impr_pct:.1f}% sem perda de CTR.")

    # Ações
    if roas < 1 and roas > 0:
        p.actions.append("Auditar campanhas com ROAS < 1 e pausar grupos de anuncios ineficientes.")
    if cpc_pct > 20:
        p.actions.append("Revisar estrategia de lances — considerar tCPA ou tROAS para controle de custo.")
    if conv_pct < -15:
        p.actions.append("Checar tracking de conversoes e revisar landing pages para melhorar taxa de conversao.")
    if not p.actions:
        p.actions.append("Manter configuracoes atuais e ampliar orcamento nas campanhas com melhor ROAS.")

    return p


def _analyze_search_console(metrics: dict[str, dict], comparison_label: str) -> PlatformAnalysis:
    meta = _PLATFORM_META["Search Console — nex.work"]
    p = PlatformAnalysis(name="Search Console — nex.work (SEO)", color=meta["color"], icon_svg=meta["icon"])

    def cur(k):  return metrics.get(k, {}).get("current", 0) or 0
    def comp(k): return metrics.get(k, {}).get("comparison", 0) or 0

    clicks   = cur("search_console:clicks");      clicks_p  = comp("search_console:clicks")
    impr     = cur("search_console:impressions"); impr_p   = comp("search_console:impressions")
    ctr_raw  = cur("search_console:ctr");          ctr_p    = comp("search_console:ctr")
    ctr  = ctr_raw  * 100 if ctr_raw  < 1 else ctr_raw

    for key in ["search_console:clicks","search_console:impressions","search_console:ctr"]:
        v, vp = cur(key), comp(key)
        if v or vp:
            b = _make_box(key, v, vp)
            if key == "search_console:ctr":
                b.current  = b.current  * 100 if b.current  < 1 else b.current
                b.previous = b.previous * 100 if b.previous < 1 else b.previous
            p.metrics.append(b)

    # Highlights
    if clicks > 0:
        p.highlights.append(f"{int(clicks):,} cliques organicos no periodo")
    if impr > 0:
        p.highlights.append(f"{int(impr):,} impressoes na busca organica")
    if ctr > 0:
        p.highlights.append(f"CTR organico de {ctr:.2f}%")

    # Anomalias + Positivos + Negativos
    for box in p.metrics:
        if box.is_anomaly:
            p.anomalies.append(f"{box.label}: {box.fmt_pct} vs {comparison_label}")
        if box.is_positive:
            p.positives.append(f"{box.label} subiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")
        elif box.is_negative:
            p.negatives.append(f"{box.label} caiu {box.fmt_pct} ({box.fmt_previous} → {box.fmt_current})")

    # Insights
    clicks_pct = _pct(clicks, clicks_p)
    impr_pct   = _pct(impr, impr_p)
    ctr_pct    = _pct(ctr, ctr_p * 100 if ctr_p < 1 else ctr_p)

    if clicks_pct > 15:
        p.insights.append(f"Crescimento organico solido (+{clicks_pct:.1f}% cliques) — estrategia de SEO com resultado.")
    elif clicks_pct < -15:
        p.insights.append(f"Queda organica ({clicks_pct:.1f}%) — possivel perda de posicoes ou sazonalidade.")

    if impr_pct > 20 and ctr_pct < -10:
        p.insights.append(f"Mais impressoes (+{impr_pct:.1f}%) mas CTR caindo — ranqueando para novos termos mas com baixo CTR.")
        p.actions.append("Otimizar title tags e meta descriptions das paginas com mais impressoes e baixo CTR.")
    elif impr_pct > 15 and ctr_pct >= 0:
        p.insights.append(f"Expansao de cobertura organica sem perda de qualidade — bom sinal de crescimento SEO.")

    if ctr < 2.0 and impr > 1000:
        p.actions.append("CTR organico abaixo de 2% — revisar snippets e adicionar schema markup para rich results.")
    elif ctr > 5.0:
        p.insights.append(f"CTR excepcional ({ctr:.1f}%) — titulo e descricao das paginas muito relevantes.")
        p.positives.append(f"CTR organico de {ctr:.1f}% — acima da media do mercado (2-3%)")

    if not p.actions:
        p.actions.append("Continuar producao de conteudo e monitorar posicoes das principais palavras-chave.")

    return p


# ── Platform dispatcher ──────────────────────────────────────────────────────

_PLATFORM_ANALYZERS = {
    "GA4 — Sessoes e Trafego":       _analyze_ga4,
    "Facebook Ads — NEX Curitiba":   _analyze_fb_ads,
    "Google Ads — NEX.WORK":         _analyze_gads,
    "Search Console — nex.work":     _analyze_search_console,
}


# ── Public API ───────────────────────────────────────────────────────────────

def analyze_reportei_daily(data: dict, target_date: Any) -> ReportData:
    """data = output of ReporteiClient.fetch_daily_data()"""
    date_str = target_date.strftime("%d/%m/%Y") if hasattr(target_date, "strftime") else str(target_date)

    report = ReportData(
        title="Analise Diaria de Performance",
        report_type="daily",
        period_label=date_str,
        comparison_label="dia anterior e mesmo dia do mes passado",
        generated_at=datetime.now(),
    )

    for source_name, int_data in data.items():
        analyzer_fn = _PLATFORM_ANALYZERS.get(source_name)
        if not analyzer_fn:
            continue
        metrics = int_data.get("vs_prev_day", {})
        platform = analyzer_fn(metrics, "dia anterior")
        report.platforms.append(platform)

    _build_executive_summary(report)
    return report


def analyze_reportei_monthly(data: dict) -> ReportData:
    """data = output of ReporteiClient.fetch_monthly_period_data()"""
    period_label = ""
    comparison_label = ""
    for int_data in data.values():
        cp, pp = int_data.get("current_period", {}), int_data.get("comparison_period", {})
        if cp:
            fmt = lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
            period_label = f"{fmt(cp.get('start'))} a {fmt(cp.get('end'))}"
            comparison_label = f"{fmt(pp.get('start'))} a {fmt(pp.get('end'))}"
            break

    report = ReportData(
        title="Relatorio Mensal de Performance",
        report_type="monthly",
        period_label=period_label,
        comparison_label=comparison_label,
        generated_at=datetime.now(),
    )

    for source_name, int_data in data.items():
        analyzer_fn = _PLATFORM_ANALYZERS.get(source_name)
        if not analyzer_fn:
            continue
        platform = analyzer_fn(int_data.get("data", {}), "periodo anterior")
        report.platforms.append(platform)

    _build_executive_summary(report)
    return report


def analyze_google_ads_daily(data: dict) -> ReportData:
    """data = output of ReporteiClient.fetch_gads_daily()"""
    target_date = data.get("date")
    prev_date   = data.get("prev_date")

    date_str  = target_date.strftime("%d/%m/%Y") if target_date else ""
    prev_str  = prev_date.strftime("%d/%m/%Y") if prev_date else "dia anterior"

    report = ReportData(
        title="Analise Diaria — Google Ads",
        report_type="daily",
        period_label=date_str,
        comparison_label=prev_str,
        generated_at=datetime.now(),
    )

    raw = data.get("_raw", {})
    platform = _analyze_gads(raw, prev_str)
    report.platforms.append(platform)
    _build_executive_summary(report)
    return report


def analyze_google_ads_monthly(data: dict) -> ReportData:
    cp = data.get("current_period", {})
    pp = data.get("comparison_period", {})
    fmt = lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)

    report = ReportData(
        title="Relatorio Mensal — Google Ads",
        report_type="monthly",
        period_label=f"{fmt(cp.get('start'))} a {fmt(cp.get('end'))}",
        comparison_label=f"{fmt(pp.get('start'))} a {fmt(pp.get('end'))}",
        generated_at=datetime.now(),
    )

    cur  = data.get("current", {})
    comp = data.get("comparison", {})
    metrics = {
        "gads:impressions":        {"current": cur.get("impressions",0),        "comparison": comp.get("impressions",0)},
        "gads:clicks":             {"current": cur.get("clicks",0),             "comparison": comp.get("clicks",0)},
        "gads:cost_micros":        {"current": cur.get("cost",0),               "comparison": comp.get("cost",0)},
        "gads:conversions":        {"current": cur.get("conversions",0),        "comparison": comp.get("conversions",0)},
        "gads:ctr":                {"current": cur.get("ctr",0),                "comparison": comp.get("ctr",0)},
        "gads:average_cpc":        {"current": cur.get("avg_cpc",0),            "comparison": comp.get("avg_cpc",0)},
        "gads:roas":               {"current": cur.get("roas",0),               "comparison": comp.get("roas",0)},
        "gads:cost_per_conversion":{"current": cur.get("cost_per_conversion",0),"comparison": comp.get("cost_per_conversion",0)},
    }
    platform = _analyze_gads(metrics, "periodo anterior")
    report.platforms.append(platform)
    _build_executive_summary(report)
    return report


def analyze_weekly(data: dict) -> ReportData:
    """data = output of ReporteiClient.fetch_weekly_data()"""
    period_label = ""
    comparison_label = ""
    for int_data in data.values():
        cp, pp = int_data.get("current_period", {}), int_data.get("comparison_period", {})
        if cp:
            fmt = lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
            period_label = f"{fmt(cp.get('start'))} a {fmt(cp.get('end'))}"
            comparison_label = f"{fmt(pp.get('start'))} a {fmt(pp.get('end'))}"
            break

    report = ReportData(
        title="Relatorio Semanal de Performance",
        report_type="weekly",
        period_label=period_label,
        comparison_label=comparison_label,
        generated_at=datetime.now(),
    )

    for source_name, int_data in data.items():
        analyzer_fn = _PLATFORM_ANALYZERS.get(source_name)
        if not analyzer_fn:
            continue
        platform = analyzer_fn(int_data.get("data", {}), "mesma semana mes anterior")
        report.platforms.append(platform)

    _build_executive_summary(report)
    return report


# ── Executive Summary builder ────────────────────────────────────────────────

def _build_executive_summary(report: ReportData):
    all_positives = []
    all_negatives = []
    all_highlights = []

    for p in report.platforms:
        short_name = p.name.split(" — ")[0] if " — " in p.name else p.name
        for h in p.highlights[:2]:
            all_highlights.append(f"[{short_name}] {h}")
        for pos in p.positives[:2]:
            all_positives.append(f"[{short_name}] {pos}")
        for neg in p.negatives[:2]:
            all_negatives.append(f"[{short_name}] {neg}")

    report.summary_highlights = all_highlights[:5]
    report.summary_positives  = all_positives[:4]
    report.summary_negatives  = all_negatives[:4]
