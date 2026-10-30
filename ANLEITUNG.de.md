# Anleitung – KCD:MP 0.48.1 mit KCD2 von GOG

Schritt für Schritt. Alle Befehle sind zum Kopieren; Pfade bitte anpassen, wenn dein
Mod- oder Spielordner anders heißt.

## Voraussetzungen

- Windows 10/11, PowerShell (in Windows enthalten).
- **Kingdom Come: Deliverance II von GOG**, Version 1.5.x (getestet:
  `release_1_5_1308617_68`, WHGame.dll `c59754b9…3870`).
- **KCD:MP 0.48.1** entpackt, z. B. in `D:\download\KcdMp-0.48.0-win-x64`; darin liegen
  `KcdMp_launcher.exe`, `KcdMp_client.dll`, `builds.json`.
- Der Launcher hat das Spiel schon einmal gefunden (Einstellungen → Spielordner), sonst
  beim ersten Start den Ordner mit `Bin` auswählen:
  `D:\Spiele\GoG\Kingdom Come Deliverance II`.

## 1. Repository holen

Mit Git:

```
git clone https://github.com/PHSchr3ck3/kcdmp-gog-fix
cd kcdmp-gog-fix
```

Ohne Git: auf der Repo-Seite **Code → Download ZIP**, entpacken, in den entpackten Ordner
wechseln.

## 2. Fix installieren

Im Repo-Ordner:

```
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
```

Was das Skript macht:

1. prüft Größe (15.625.152 Byte) und SHA-256 der `KcdMp_client.dll` – bei einer anderen
   Version bricht es ab,
2. sichert `builds.json` nach `builds.json.kcdmp-gog.bak`,
3. schreibt den Eintrag `gog-1.5.6-c59754b9` mit 277 Ankern hinein,
4. prüft die Datei nach dem Schreiben.

Erwartete Ausgabe:

```
Backup: builds.json.kcdmp-gog.bak
Installed gog-1.5.6-c59754b9 with 277 anchors into builds.json.
```

Mit `-GameDir "D:\Spiele\GoG\Kingdom Come Deliverance II"` kommt zusätzlich:

```
verdict: supported (gog-1.5.6-c59754b9)
launcher --check-game exit code: 0 (0 = supported)
```

## 3. Launcher als Administrator starten

Rechtsklick auf `KcdMp_launcher.exe` → **Als Administrator ausführen**, UAC bestätigen.

Warum: In der getesteten Umgebung startete das Spiel ohne Erhöhung nicht und brach mit
`ERROR: CryInput.dll could not be loaded!` ab. Mit Erhöhung lief es. Die Ursache dafür
wurde nicht ermittelt; sie hängt nicht mit diesem Fix zusammen.

## 4. Server wählen und joinen

Im Launcher **Servers** → Server anklicken → **Join** (oder unten rechts der goldene
Button). Der Client startet das Spiel und verbindet sich.

Wenn du keinen RP-Server willst: nach Modus filtern (`freeroam`, `duel_arena`,
`TDM / Duels`). Ein Fenster „Konto erstellen / Anmelden" kommt **vom jeweiligen Server**
(z. B. `account.lua` von KCDRoleplay), nicht von KCD:MP – dort brauchst du ein Konto bei
diesem Server.

## 5. Prüfen, ob der Fix greift

Log öffnen: `%LOCALAPPDATA%\KcdMp\client.log` (im Explorer
`%LOCALAPPDATA%\KcdMp` eingeben).

Diese Zeilen müssen vorkommen:

```
build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
hooks: 21 installed in one freeze
```

Steht dort weiter `unknown game build`, wurde die falsche `builds.json` gelesen – dann
Schritt 2 im richtigen `-ClientDir` wiederholen.

## 6. Deinstallieren

```
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
```

Stellt `builds.json` byte-identisch aus der Sicherung wieder her (oder entfernt ohne
Sicherung alle `gog`-Einträge). Die `KcdMp_client.dll` wird nie verändert.

## Fehlerbehebung

| Symptom | Ursache / Lösung |
|---|---|
| `ERROR: CryInput.dll could not be loaded!` | Launcher nicht erhöht → als Administrator starten. Tritt auch beim direkten Start der `KingdomCome.exe` auf. |
| Klick auf „Join" bewirkt nichts | Meist derselbe CryInput-Abbruch: im Task-Manager erscheint `KingdomCome.exe` und verschwindet nach 1–3 s. Launcher erhöht starten. |
| `build gate: unknown game build` | `builds.json` ohne GOG-Eintrag (z. B. nach KCD:MP-Update) → `install.ps1` erneut ausführen. |
| Maus im Spiel/Login reagiert nicht | `LALT` drücken (Cursor-Taste aus `launcher.json`). |
| Server lehnt ab, „SteamID fehlt" | GOG liefert keine Steam-ID. Server mit Steam-Pflicht können GOG-Spieler nicht aufnehmen; es wird bewusst keine ID gefälscht. |
| Spiel stürzt bei Kämpfen/Inventar ab | Erwartbar: mehrere Schutz-Hooks fehlen (siehe unten). Log aufbewahren. |
| Launcher findet das Spiel nicht | Einstellungen → Spielordner: `D:\Spiele\GoG\Kingdom Come Deliverance II` (der Ordner mit `Bin`). |

## Was dieser Fix nicht leistet

- 247 von 548 Ankern fehlen (Pattern-Anker, nicht rekonstruierbar). Dadurch sind u. a.
  Pickpocket, HorsePullDown, Lip-Sync, Operator-Queue, Kampf-Trigger und Teile der Kamera
  aus.
- 23 Slot- und 1 RTTI-Anker fehlen.
- Die Absturz-Fänger (`inventory guard`, `living guard`, `transition guard`,
  `combat guard`, `hand guard`, `ui guard`, `mp rules`) sind deshalb nicht installiert.
  In den Testläufen ist nichts passiert, das Risiko bleibt aber.
- Offizieller GOG-Support existiert nicht. Für einen vollständigen Fix siehe
  [`docs/request-to-kcdmp.txt`](docs/request-to-kcdmp.txt).

Technische Herleitung und Zahlen: [`docs/TECHNICAL.de.md`](docs/TECHNICAL.de.md).
