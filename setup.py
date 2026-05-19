#!/usr/bin/env python3
"""
Interactive setup wizard — run once to configure credentials and test connections.
Usage: python setup.py
"""
import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _print(msg, color=None):
    codes = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m", "blue": "\033[94m", "reset": "\033[0m"}
    c = codes.get(color, "")
    r = codes["reset"]
    print(f"{c}{msg}{r}")


def step(n, title):
    _print(f"\n{'='*60}", "blue")
    _print(f"  Passo {n}: {title}", "blue")
    _print(f"{'='*60}", "blue")


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default


def write_env(values: dict):
    env_path = os.path.join(BASE_DIR, ".env")
    example_path = os.path.join(BASE_DIR, ".env.example")
    shutil.copy(example_path, env_path)

    with open(env_path, "r") as f:
        content = f.read()

    for key, value in values.items():
        import re
        content = re.sub(
            rf"^({re.escape(key)}=).*$",
            rf"\g<1>{value}",
            content,
            flags=re.MULTILINE,
        )

    with open(env_path, "w") as f:
        f.write(content)
    _print(f".env criado/atualizado.", "green")


def write_google_ads_yaml(developer_token, client_id, client_secret, refresh_token, customer_id):
    yaml_path = os.path.join(BASE_DIR, "google-ads.yaml")
    login_id = customer_id.replace("-", "")
    content = f"""developer_token: {developer_token}
client_id: {client_id}
client_secret: {client_secret}
refresh_token: {refresh_token}
login_customer_id: "{login_id}"
use_proto_plus: True
"""
    with open(yaml_path, "w") as f:
        f.write(content)
    _print("google-ads.yaml criado.", "green")


def install_deps():
    _print("Instalando dependencias Python...", "yellow")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r",
                           os.path.join(BASE_DIR, "requirements.txt")])
    _print("Dependencias instaladas.", "green")


def test_reportei(token):
    _print("Testando conexao com Reportei...", "yellow")
    import requests
    try:
        resp = requests.get(
            "https://app.reportei.com/api/v2/companies/settings",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            _print("Reportei: conexao OK!", "green")
            return True
        else:
            _print(f"Reportei: erro {resp.status_code} — verifique o token.", "red")
            return False
    except Exception as e:
        _print(f"Reportei: falha na conexao — {e}", "red")
        return False


def test_gmail(user, password):
    _print("Testando conexao Gmail SMTP...", "yellow")
    import smtplib, ssl
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(user, password)
        _print("Gmail SMTP: conexao OK!", "green")
        return True
    except Exception as e:
        _print(f"Gmail SMTP: falha — {e}", "red")
        _print("Dica: gere um App Password em https://myaccount.google.com/apppasswords", "yellow")
        return False


def main():
    _print("\n  REPORTS AUTOMATION — Setup Wizard", "blue")
    _print("  NEX Coworking / felipe@nexcoworking.com.br\n", "blue")

    # Step 1: Install deps
    step(1, "Instalar dependencias")
    if ask("Instalar agora?", "s").lower() in ("s", "sim", "y", "yes"):
        install_deps()

    # Step 2: Reportei
    step(2, "Reportei API Token")
    _print("Acesse: app.reportei.com > Configuracoes > API Reportei > Gerar Token")
    reportei_token = ask("Cole seu token aqui")

    # Step 3: Google Ads
    step(3, "Google Ads API (OAuth2)")
    _print("Voce precisara de:")
    _print("  1. Developer Token (console.developers.google.com/googleads)")
    _print("  2. OAuth2 Client ID + Secret (Google Cloud Console > Credenciais)")
    _print("  3. Refresh Token (gerado via: python -c 'from google_auth_oauthlib...')")
    _print("\nSiga o guia completo no README.md para obter esses valores.\n")
    dev_token = ask("Developer Token")
    client_id = ask("OAuth2 Client ID")
    client_secret = ask("OAuth2 Client Secret")
    refresh_token = ask("Refresh Token")
    customer_id = ask("Customer ID (ex: 977-263-6001)", "977-263-6001")

    # Step 4: Gmail
    step(4, "Gmail SMTP — App Password")
    _print("Para gerar um App Password:")
    _print("  1. Ative a verificacao em 2 etapas: https://myaccount.google.com/security")
    _print("  2. Acesse: https://myaccount.google.com/apppasswords")
    _print("  3. Selecione 'Mail' e gere a senha de 16 caracteres")
    gmail_user = ask("E-mail Gmail", "felipe@nexcoworking.com.br")
    gmail_pass = ask("App Password (sem espacos)")

    # Step 5: Email recipients
    step(5, "Destinatarios dos relatorios")
    daily_to = ask("E-mail para relatorios DIARIOS", "felipe@nex.work")
    weekly_to = ask("E-mail para relatorios MENSAIS (segunda-feira)", "felipe@nexcoworking.com.br")

    # Write config files
    step(6, "Salvando configuracoes")
    write_env({
        "REPORTEI_API_TOKEN": reportei_token,
        "GMAIL_USER": gmail_user,
        "GMAIL_APP_PASSWORD": gmail_pass,
        "EMAIL_DAILY_TO": daily_to,
        "EMAIL_WEEKLY_TO": weekly_to,
        "GOOGLE_ADS_CUSTOMER_ID": customer_id,
    })
    write_google_ads_yaml(dev_token, client_id, client_secret, refresh_token, customer_id)

    # Test connections
    step(7, "Testando conexoes")
    test_reportei(reportei_token)
    test_gmail(gmail_user, gmail_pass)

    # Done
    step(8, "Pronto!")
    _print("\nSetup concluido. Para iniciar o sistema:", "green")
    _print("  python main.py                        # inicia o scheduler (roda em background)", "yellow")
    _print("  python main.py --now all               # executa todos os relatorios agora", "yellow")
    _print("  python main.py --now reportei-daily    # testa apenas o Reportei diario", "yellow")
    _print("  python main.py --now gads-daily        # testa apenas o Google Ads diario\n", "yellow")


if __name__ == "__main__":
    main()
