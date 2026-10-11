# playtomic-matches

Privates Archiv meiner Playtomic-Spielergebnisse in `data/matches.json`.

`scripts/fetch_matches.py` holt meine Matches über die **inoffizielle**
Playtomic-API und führt sie mit dem Archiv zusammen. Bereits gesicherte Matches
bleiben erhalten, auch wenn Playtomic sie nicht mehr ausliefert. Gespeichert
wird die Rohantwort der API, damit keine Felder verloren gehen.

Das Skript muss **zu Hause** laufen: Playtomic blockt Anfragen aus
Rechenzentren (z. B. GitHub Actions) mit 403.

## Einrichtung (einmalig)

Voraussetzungen: [Python 3](https://www.python.org/downloads/) und
[Git](https://git-scm.com/downloads), keine weiteren Pakete.

```sh
git clone https://github.com/Tigraef/playtomic-matches.git
cd playtomic-matches
cp .env.example .env      # Windows: copy .env.example .env
```

Dann in `.env` Playtomic-E-Mail und -Passwort eintragen. Die Datei wird nie
committet.

## Ausführen

```sh
python3 scripts/fetch_matches.py --push   # Windows: py scripts\fetch_matches.py --push
```

Ohne `--push` wird nur `data/matches.json` lokal aktualisiert.

## Automatisch ausführen

**Mac/Linux** (täglich um 20 Uhr), per `crontab -e`:

```
0 20 * * * cd /pfad/zu/playtomic-matches && python3 scripts/fetch_matches.py --push >> fetch.log 2>&1
```

**Windows**: Aufgabenplanung → *Einfache Aufgabe erstellen* → täglich →
*Programm starten*:
- Programm: `py`
- Argumente: `scripts\fetch_matches.py --push`
- Starten in: `C:\pfad\zu\playtomic-matches`

Das Repo ist privat, weil die Daten Namen und IDs der Mitspieler enthalten.
