"""
Sends emails with PDF attachments via Gmail SMTP.
"""
import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import date

from config import config


_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def _build_html_body(subject: str, period: str, comparison: str, report_type: str) -> str:
    is_weekly = "Mensal" in report_type or "Semanal" in report_type
    color = "#1A73E8"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 24px auto; background: #fff; border-radius: 8px;
                  border: 1px solid #dadce0; overflow: hidden; }}
    .header {{ background: {color}; padding: 28px 32px; }}
    .header h1 {{ color: #fff; margin: 0; font-size: 20px; }}
    .header p {{ color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 13px; }}
    .body {{ padding: 28px 32px; }}
    .body p {{ color: #202124; font-size: 14px; line-height: 1.6; margin: 0 0 14px; }}
    .pill {{ display: inline-block; background: #e8f0fe; color: {color};
             padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
    .footer {{ background: #f8f9fa; padding: 16px 32px; text-align: center;
               color: #80868b; font-size: 11px; border-top: 1px solid #dadce0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{subject}</h1>
      <p>Relatorio automatico gerado as 12h (horario de Brasilia)</p>
    </div>
    <div class="body">
      <p>Ola,</p>
      <p>
        {"Segue o relatorio " + ("mensal" if is_weekly else "diario") + " em anexo."}<br>
        O PDF contem a analise completa com metricas, anomalias e insights.
      </p>
      <p>
        <span class="pill">Periodo analisado: {period}</span>&nbsp;
        <span class="pill">Comparacao: {comparison}</span>
      </p>
      <p style="color:#5F6368; font-size:12px;">
        Este relatorio e enviado automaticamente todos os dias as 12h
        {"e toda segunda-feira com analise mensal." if is_weekly else "."}
      </p>
    </div>
    <div class="footer">
      NEX Coworking &bull; felipe@nexcoworking.com.br &bull; Relatorio automatico
    </div>
  </div>
</body>
</html>
"""


def send_report(
    to: str,
    subject: str,
    pdf_path: str,
    period: str,
    comparison: str,
    report_type: str,
):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF nao encontrado: {pdf_path}")

    msg = MIMEMultipart("alternative")
    msg["From"] = config.GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject

    html_body = _build_html_body(subject, period, comparison, report_type)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with open(pdf_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(pdf_path),
        )
        msg_full = MIMEMultipart("mixed")
        msg_full["From"] = config.GMAIL_USER
        msg_full["To"] = to
        msg_full["Subject"] = subject
        msg_full.attach(msg)
        msg_full.attach(attachment)

    context = ssl.create_default_context()
    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        server.sendmail(config.GMAIL_USER, to, msg_full.as_string())

    print(f"[email] Enviado para {to}: {subject}")


# ── Convenience wrappers ────────────────────────────────────────────────────

def send_reportei_daily(pdf_path: str, analysis_date: date):
    send_report(
        to=config.EMAIL_DAILY_TO,
        subject=f"[Reportei] Analise Diaria — {analysis_date.strftime('%d/%m/%Y')}",
        pdf_path=pdf_path,
        period=analysis_date.strftime("%d/%m/%Y"),
        comparison="Dia anterior + mesmo dia mes passado",
        report_type="Reportei Diario",
    )


def send_reportei_monthly(pdf_path: str, period_start: date, period_end: date):
    send_report(
        to=config.EMAIL_WEEKLY_TO,
        subject=(
            f"[Reportei] Relatorio Mensal — "
            f"{period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m/%Y')}"
        ),
        pdf_path=pdf_path,
        period=f"{period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m/%Y')}",
        comparison=f"{period_start.replace(month=period_start.month-1 if period_start.month>1 else 12).strftime('%d/%m')} - mesmo periodo mes anterior",
        report_type="Reportei Mensal",
    )


def send_google_ads_daily(pdf_path: str, analysis_date: date):
    send_report(
        to=config.EMAIL_DAILY_TO,
        subject=f"[Google Ads] Analise Diaria — {analysis_date.strftime('%d/%m/%Y')}",
        pdf_path=pdf_path,
        period=analysis_date.strftime("%d/%m/%Y"),
        comparison="Dia anterior",
        report_type="Google Ads Diario",
    )


def send_google_ads_monthly(pdf_path: str, period_start: date, period_end: date):
    send_report(
        to=config.EMAIL_WEEKLY_TO,
        subject=(
            f"[Google Ads] Relatorio Mensal — "
            f"{period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m/%Y')}"
        ),
        pdf_path=pdf_path,
        period=f"{period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m/%Y')}",
        comparison="Mesmo periodo mes anterior",
        report_type="Google Ads Mensal",
    )
