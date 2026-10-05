#!/usr/bin/env python3
"""Sync the repository's public README and icon to its Modrinth project."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API = "https://api.modrinth.com/v2"
ROOT = Path(__file__).resolve().parents[2]


def request(url: str, token: str, body: bytes, content_type: str) -> None:
    """Send one authenticated metadata update without printing credentials."""
    req = Request(
        url,
        data=body,
        method="PATCH",
        headers={
            "Authorization": token,
            "Content-Type": content_type,
            "User-Agent": "SlimefunNewHorizons/Mantle-Unofficial (GitHub Actions)",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            if response.status not in (200, 204):
                raise RuntimeError(f"Modrinth returned unexpected HTTP status {response.status}.")
    except HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Modrinth metadata update failed (HTTP {exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Modrinth: {exc.reason}") from exc


def main() -> int:
    """Publish the checked-in README body and SVG project icon."""
    token = os.environ.get("MODRINTH_TOKEN", "").strip()
    project_id = os.environ.get("MODRINTH_PROJECT_ID", "").strip()
    if not token or not project_id:
        print("Set the MODRINTH_TOKEN secret and MODRINTH_PROJECT_ID repository variable.", file=sys.stderr)
        return 2

    project = quote(project_id, safe="")
    try:
        body = json.dumps(
            {
                "description": "Unofficial Mantle shared-library port for Minecraft 1.21.1 on NeoForge.",
                "body": (ROOT / "README.md").read_text(encoding="utf-8"),
            },
            ensure_ascii=False,
        ).encode("utf-8")
        icon = (ROOT / "docs/assets/icon.svg").read_bytes()
        if len(icon) > 256 * 1024:
            raise RuntimeError("Project icon exceeds Modrinth's 256 KiB limit.")

        request(f"{API}/project/{project}", token, body, "application/json")
        request(f"{API}/project/{project}/icon?ext=svg", token, icon, "image/svg+xml")
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"Modrinth metadata sync failed: {exc}", file=sys.stderr)
        return 1

    print("Modrinth project description and icon synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
