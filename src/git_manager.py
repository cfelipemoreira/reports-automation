"""
Auto-commits and pushes generated reports to GitHub after each run.
"""
import os
import traceback
from datetime import datetime
import git

from config import config


def _repo() -> git.Repo:
    return git.Repo(config.GIT_REPO_PATH)


def commit_and_push(message: str | None = None):
    """
    Stages all changes (new PDFs + any config changes), commits, and pushes.
    Skips if the working tree is clean.
    """
    try:
        repo = _repo()

        # Stage everything that's not in .gitignore
        repo.git.add(".")

        if not repo.is_dirty(index=True, untracked_files=True):
            print("[git] Nenhuma alteracao para commitar.")
            return

        if message is None:
            message = f"auto: relatorios gerados em {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        repo.index.commit(message)
        origin = repo.remote(config.GIT_REMOTE)
        origin.push(refspec=f"HEAD:{config.GIT_BRANCH}")
        print(f"[git] Commit e push realizados: {message}")

    except git.exc.GitCommandError as e:
        print(f"[git] Erro ao fazer push: {e}")
    except Exception:
        print(f"[git] Erro inesperado:\n{traceback.format_exc()}")


def commit_report(report_type: str, analysis_date: str):
    commit_and_push(
        message=f"auto: {report_type} — {analysis_date}"
    )
