#!/usr/bin/env python3
"""Holt die eigenen Playtomic-Matches und führt sie mit data/matches.json zusammen.

Nutzt die inoffizielle Playtomic-API. Zugangsdaten kommen aus den
Umgebungsvariablen PLAYTOMIC_EMAIL und PLAYTOMIC_PASSWORD.
Bereits gesicherte Matches werden nie gelöscht, nur aktualisiert.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Der alte Host api.playtomic.io ist abgeschaltet.
API = "https://api.app.playtomic.io"
ARCHIVE = Path(__file__).resolve().parent.parent / "data" / "matches.json"
PAGE_SIZE = 50
MAX_PAGES = 200
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "playtomic-matches-archive/1.0",
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
    res = request("POST", "/v3/auth/login", body={"email": email, "password": password})
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


def main():
    email = os.environ.get("PLAYTOMIC_EMAIL")
    password = os.environ.get("PLAYTOMIC_PASSWORD")
    if not email or not password:
        sys.exit("PLAYTOMIC_EMAIL und PLAYTOMIC_PASSWORD müssen gesetzt sein.")

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

    archive = json.loads(ARCHIVE.read_text()) if ARCHIVE.exists() else []
    by_id = {match_id(m): m for m in archive}
    before = len(by_id)
    for m in fetched:
        by_id[match_id(m)] = m  # neuere Version (z. B. mit Ergebnis) ersetzt alte

    merged = sorted(by_id.values(), key=lambda m: m.get("start_date") or "", reverse=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(f"Archiv: {before} -> {len(merged)} Matches.")


if __name__ == "__main__":
    main()
