"""Publish the PRIVATE dashboard to Cloudflare Pages, behind Cloudflare Access (login required).

Safety: nothing is uploaded unless `LIFELOG_ACCESS_CONFIRMED=1` is set in .env — set it only after
the Access app protects BOTH `<project>.pages.dev` and `*.<project>.pages.dev` (previews).
Teardown: `npx wrangler pages project delete <project>` + delete the Access application.
"""

import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger("lifelog.publish")

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
LOCAL_JSON = WEB / "public" / "data" / "lifelog.local.json"


class PublishError(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"))


def project_name() -> str:
    return os.environ.get("LIFELOG_PAGES_PROJECT", "lifelog-private")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=WEB, capture_output=True, text=True, env=os.environ.copy())
    if result.returncode != 0:
        raise PublishError(f"{' '.join(cmd[:4])}… failed:\n{result.stderr[-1500:]}")
    return result.stdout


def publish() -> str:
    """Build the web app with the private JSON and deploy it. Returns the deployment URL line."""
    if not configured():
        raise PublishError("CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID not set in .env")
    if os.environ.get("LIFELOG_ACCESS_CONFIRMED") != "1":
        raise PublishError(
            "Refusing to upload private data: set LIFELOG_ACCESS_CONFIRMED=1 only after Cloudflare "
            "Access protects the site (see docs/private-dashboard.md)."
        )
    if not LOCAL_JSON.exists():
        raise PublishError("No private data yet (web/public/data/lifelog.local.json).")
    _run(["npm", "run", "build"])
    out = _run(
        ["npx", "wrangler", "pages", "deploy", "dist", "--project-name", project_name(),
         "--branch", "main", "--commit-dirty=true"]
    )  # fmt: skip
    url = next((line for line in out.splitlines() if "pages.dev" in line), "")
    log.info("published private dashboard %s", url.strip())
    return url.strip()


def create_project() -> str:
    return _run(
        [
            "npx",
            "wrangler",
            "pages",
            "project",
            "create",
            project_name(),
            "--production-branch",
            "main",
        ]
    )
