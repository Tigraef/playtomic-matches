#!/usr/bin/env python3
"""Holt die eigenen Playtomic-Matches und führt sie mit data/matches.json zusammen.

Nutzt die inoffizielle Playtomic-API. Zugangsdaten kommen aus den
Umgebungsvariablen PLAYTOMIC_EMAIL und PLAYTOMIC_PASSWORD oder aus einer
.env-Datei im Repo-Wurzelverzeichnis. Mit --push werden Änderungen direkt
committet und gepusht.
Bereits gesicherte Matches werden nie gelöscht, nur aktualisiert.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Der alte Host api.playtomic.io ist abgeschaltet.
API = "https://api.app.playtomic.io"
ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "matches.json"
ENV_FILE = ROOT / ".env"
PAGE_SIZE = 50
MAX_PAGES = 200
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    # CloudFront blockt unbekannte User-Agents, daher wie die Web-App auftreten
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Origin": "https://app.playtomic.io",
    "Referer": "https://app.playtomic.io/",
    "X-Requested-With": "com.playtomic.web",
}


def request(method, path, token=None, params=None, body=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        snippet = e.read().decode(errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code} bei {method} {path}: {snippet}") from None


def login(email, password):
    res = request("POST", "/v3/auth/login", body={
        "email": email,
        "password": password,
        "requested_user_roles": ["ROLE_CUSTOMER"],  # sonst INVALID_TOKEN_SCOPE
    })
    token = res.get("access_token")
    user_id = res.get("user_id")
    if not token or not user_id:
        sys.exit(f"Login-Antwort unerwartet, Felder: {sorted(res)}")
    return token, str(user_id)


def fetch_matches(token, user_id, filter_param):
    matches = []
    for page in range(MAX_PAGES):
        res = request("GET", "/v1/matches", token, {
            filter_param: user_id,
            "sort": "start_date,DESC",
            "page": page,
            "size": PAGE_SIZE,
        })
        # Antwort kann eine Liste oder ein Spring-Page-Objekt sein
        items = res.get("content", []) if isinstance(res, dict) else res
        matches.extend(items)
        if len(items) < PAGE_SIZE:
            break
    return matches


def match_id(m):
    return str(m.get("match_id") or m.get("id"))


def load_env_file():
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.strip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)


def commit_and_push():
    git("add", str(ARCHIVE.relative_to(ROOT)))
    if not git("status", "--porcelain", "--", str(ARCHIVE.relative_to(ROOT))).stdout.strip():
        print("Keine Änderungen, nichts zu pushen.")
        return
    git("commit", "-m", "Matches aktualisiert")
    git("push")
    print("Änderungen committet und gepusht.")


def main():
    load_env_file()
    email = os.environ.get("PLAYTOMIC_EMAIL")
    password = os.environ.get("PLAYTOMIC_PASSWORD")
    if not email or not password:
        sys.exit(f"PLAYTOMIC_EMAIL und PLAYTOMIC_PASSWORD fehlen (in {ENV_FILE} eintragen).")

    try:
        token, user_id = login(email, password)
    except RuntimeError as e:
        sys.exit(f"Login fehlgeschlagen: {e}")

    # Unklar, welcher Filter alle eigenen Matches liefert, daher beide abfragen
    fetched, errors = [], []
    for param in ("player_user_id", "user_id"):
        try:
            found = fetch_matches(token, user_id, param)
        except RuntimeError as e:
            errors.append(f"{param}: {e}")
            continue
        print(f"Filter {param}: {len(found)} Matches.")
        fetched.extend(found)
    if errors and not fetched:
        sys.exit("Abruf fehlgeschlagen:\n" + "\n".join(errors))
    for err in errors:
        print(f"Warnung: {err}")
    print(f"{len({match_id(m) for m in fetched})} verschiedene Matches von Playtomic geladen.")
    if fetched:
        print(f"Felder eines Matches: {sorted(fetched[0])}")

    archive = json.loads(ARCHIVE.read_text(encoding="utf-8")) if ARCHIVE.exists() else []
    by_id = {match_id(m): m for m in archive}
    before = len(by_id)
    for m in fetched:
        by_id[match_id(m)] = m  # neuere Version (z. B. mit Ergebnis) ersetzt alte

    merged = sorted(by_id.values(), key=lambda m: m.get("start_date") or "", reverse=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Archiv: {before} -> {len(merged)} Matches.")

    if "--push" in sys.argv[1:]:
        try:
            commit_and_push()
        except subprocess.CalledProcessError as e:
            sys.exit(f"git {' '.join(e.cmd[1:])} fehlgeschlagen: {e.stderr.strip()}")


if __name__ == "__main__":
    main()
