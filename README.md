# reports-automation

Sistema de relatórios automáticos integrado ao **Reportei** e **Google Ads** para NEX Coworking.

---

## O que faz

| Quando | O quê | Destino |
|--------|-------|---------|
| Todo dia às 12h | Análise diária Reportei (hoje vs ontem + mesmo dia mês passado) | felipe@nex.work |
| Toda segunda às 12h | Relatório mensal Reportei (1/mês até hoje vs período anterior) | felipe@nexcoworking.com.br |
| Todo dia às 12h | Análise diária Google Ads (hoje vs ontem) | felipe@nex.work |
| Toda segunda às 12h | Relatório mensal Google Ads (1/mês até hoje vs período anterior) | felipe@nexcoworking.com.br |

Cada relatório é enviado como **e-mail HTML** com um **PDF em anexo** contendo métricas, anomalias detectadas e insights.

Após cada envio, o sistema faz **commit + push automático** para o GitHub.

---

## Instalação rápida

```bash
cd reports-automation
python setup.py
```

O wizard interativo pede todas as credenciais e testa as conexões.

---

## Configuração manual

### 1. Dependências

```bash
pip install -r requirements.txt
```

### 2. Arquivo `.env`

```bash
cp .env.example .env
# edite .env com suas credenciais
```

### 3. Reportei API Token

1. Acesse `app.reportei.com` → Configurações → **API Reportei**
2. Gere um token e cole em `REPORTEI_API_TOKEN` no `.env`

### 4. Google Ads API

#### 4.1 Developer Token
1. Acesse [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Solicite acesso (pode levar 24h para aprovação)
3. Cole em `google-ads.yaml` > `developer_token`

#### 4.2 OAuth2 Credentials
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou use um existente
3. Ative a **Google Ads API**
4. Em **Credenciais** → Criar credencial → **ID do cliente OAuth 2.0**
5. Tipo: **Aplicativo para computador**
6. Baixe o JSON e anote `client_id` e `client_secret`

#### 4.3 Refresh Token
```bash
pip install google-auth-oauthlib
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/adwords']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
print('Refresh Token:', creds.refresh_token)
"
```

#### 4.4 `google-ads.yaml`
```bash
cp google-ads.yaml.example google-ads.yaml
# preencha com developer_token, client_id, client_secret, refresh_token
```

### 5. Gmail App Password

1. Ative verificação em 2 etapas: https://myaccount.google.com/security
2. Gere App Password: https://myaccount.google.com/apppasswords
3. Selecione "Mail" → copie a senha de 16 caracteres
4. Cole em `GMAIL_APP_PASSWORD` no `.env`

---

## Uso

```bash
# Iniciar scheduler (processo contínuo, rode em background ou via launchd/systemd)
python main.py

# Executar manualmente para testar
python main.py --now all               # todos os relatórios
python main.py --now reportei-daily    # Reportei diário
python main.py --now reportei-monthly  # Reportei mensal
python main.py --now gads-daily        # Google Ads diário
python main.py --now gads-monthly      # Google Ads mensal
```

### Rodar em background (macOS)

```bash
nohup python main.py > logs/scheduler.log 2>&1 &
echo $! > scheduler.pid
```

Para parar:
```bash
kill $(cat scheduler.pid)
```

---

## Estrutura do projeto

```
reports-automation/
├── main.py                # Scheduler + orquestrador
├── config.py              # Configurações centralizadas
├── setup.py               # Wizard de instalação
├── requirements.txt
├── .env                   # Credenciais (não comitado)
├── .env.example
├── google-ads.yaml        # Credenciais Google Ads (não comitado)
├── google-ads.yaml.example
├── src/
│   ├── reportei_client.py # Integração Reportei API v2
│   ├── google_ads_client.py # Integração Google Ads API
│   ├── analyzer.py        # Cálculos, anomalias, insights
│   ├── pdf_generator.py   # Geração de PDFs com ReportLab
│   ├── email_sender.py    # Envio via Gmail SMTP
│   └── git_manager.py     # Auto-commit e push
└── data/
    └── reports/           # PDFs gerados (não comitados)
```

---

## Auto-commit no GitHub

Após cada relatório enviado, o sistema faz automaticamente:

```bash
git add .
git commit -m "auto: gads-daily — 2026-05-19"
git push origin main
```

Certifique-se de que o repositório tem um remote `origin` configurado e que suas chaves SSH ou credenciais HTTPS estão ativas.

---

## Anomalias e Insights

O sistema detecta automaticamente:

- Variações ≥ 20% em qualquer métrica (sinalizadas como **ANOMALIA**)
- ROAS abaixo de 1 (campanha no prejuízo)
- CTR caindo sem melhora em conversões
- Taxa de rejeição acima de 70%
- Crescimento de gasto desproporcionalmente maior que conversões
