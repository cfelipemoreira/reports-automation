import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Reportei
    REPORTEI_API_TOKEN = os.getenv("REPORTEI_API_TOKEN", "")
    REPORTEI_DASHBOARD_NAME = os.getenv("REPORTEI_DASHBOARD_NAME", "[WEEKLY] TT")
    REPORTEI_BASE_URL = "https://app.reportei.com/api/v2"

    # Google Ads
    GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "977-263-6001").replace("-", "")

    # E-mail
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    EMAIL_DAILY_TO = os.getenv("EMAIL_DAILY_TO", "felipe@nex.work")
    EMAIL_WEEKLY_TO = os.getenv("EMAIL_WEEKLY_TO", "felipe@nexcoworking.com.br")

    # Git
    GIT_REPO_PATH = os.getenv("GIT_REPO_PATH", os.path.dirname(__file__))
    GIT_REMOTE = os.getenv("GIT_REMOTE", "origin")
    GIT_BRANCH = os.getenv("GIT_BRANCH", "main")

    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")

    # Paths
    REPORTS_DIR = os.path.join(os.path.dirname(__file__), "data", "reports")


config = Config()
