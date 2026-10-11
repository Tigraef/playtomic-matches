# playtomic-matches

Privates Archiv meiner Playtomic-Spielergebnisse.

Eine GitHub Action (`.github/workflows/fetch-matches.yml`) läuft täglich, holt
meine Matches über die **inoffizielle** Playtomic-API und führt sie mit
`data/matches.json` zusammen. Bereits gesicherte Matches bleiben erhalten, auch
wenn Playtomic sie nicht mehr ausliefert. Gespeichert wird die Rohantwort der
API, damit keine Felder verloren gehen.

## Einrichtung

Unter *Settings → Secrets and variables → Actions* zwei Secrets anlegen:

- `PLAYTOMIC_EMAIL`
- `PLAYTOMIC_PASSWORD`

Manuell starten: *Actions → Playtomic-Matches sichern → Run workflow*.

## Lokal ausführen

```sh
PLAYTOMIC_EMAIL=... PLAYTOMIC_PASSWORD=... python3 scripts/fetch_matches.py
```

Das Repo ist privat, weil die Daten Namen und IDs der Mitspieler enthalten.
