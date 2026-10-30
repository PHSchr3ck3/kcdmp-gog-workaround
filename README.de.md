# KCD:MP 0.48.1 mit der GOG-Version von KCD2 1.5.x

**English:** [README.md](README.md) · **Anleitung:** [ANLEITUNG.de.md](ANLEITUNG.de.md)

**Stand:** 30.10.2026, getestet mit KCD:MP 0.48.1 (Originaldateien unverändert),
Kingdom Come: Deliverance II GOG `release_1_5_1308617_68`, WHGame.dll
`c59754b9…d9363870` (89.078.272 Byte, Timestamp 1782121515, SizeOfImage 95490048,
PDB `4B3F7D2D4D22434DA6CA550A88ED0D8C`/2).

## Was hier entsteht

KCD:MP 0.48.1 kennt drei Spiel-Builds (Epic, Microsoft Store, Steam). Diese Fassung
ergänzt den GOG-Build als **vierten Eintrag in `builds.json`**. Weder
`KcdMp_client.dll` noch eine Spieldatei wird verändert: der Client liest die Tabelle
beim Start aus `builds.json` neben der DLL (Log: `build gate: the entry comes from
builds.json next to KcdMp_client.dll`).

Der Eintrag `gog-1.5.6-c59754b9` enthält **277 von 548 Ankern**. Es fehlen **271**:
**247 Pattern-Anker**, 23 Slot-Anker und 1 RTTI-Anker. Die 247 Anker, die
das Originalwerkzeug `tools/sigscan/sigscan.py` über Byte-Muster gefunden hat, sind
nicht herleitbar: die Muster stehen nicht im Client, und auf dem Rechner liegt kein
zweiter WHGame.dll-Build als Vergleich. Diese 247 Anker fehlen daher; der Client
meldet sie einzeln als „not resolved" und schaltet die jeweilige Funktion ab.

**Das ist deshalb kein vollwertiger GOG-Support.** Der Build-Check ist umgangen,
Engine-Zugriff, Hooks und die Verbindung zum Server funktionieren; einzelne
Funktionen (Kampf-Sync, Kamera, Items, Operator-Queue u. a.) bleiben aus.

Die KCD:MP-Website sagt dazu selbst: *„The GOG version needs its own build of KCD:MP,
and it may come later."* (kcd-mp.com, FAQ, abgerufen 30.10.2026).

## Installation

1. KCD:MP 0.48.1 muss unverändert im Ordner liegen (`KcdMp_client.dll` 15.625.152 Byte,
   SHA-256 `AD44B2A0…3B`). `install.ps1` prüft beides und bricht sonst ab.
2. PowerShell in diesem Repository, mit dem Mod-Ordner als Ziel:
   ```
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64" -GameDir "D:\Spiele\GoG\Kingdom Come Deliverance II"
   ```
   Liegt `install.ps1` direkt im Mod-Ordner, reicht `-File .\install.ps1`.
   Das legt `builds.json.kcdmp-gog.bak` an und schreibt den GOG-Eintrag.
3. `KcdMp_launcher.exe` **als Administrator** starten. In der getesteten Umgebung
   startete das Spiel ohne Erhöhung nicht (Abbruch mit „ERROR: CryInput.dll could not
   be loaded!"), mit Erhöhung lief es. Die Ursache dafür wurde nicht ermittelt; sie
   hängt nicht mit diesem Fix zusammen.
4. Im Log `%LOCALAPPDATA%\KcdMp\client.log` muss stehen:
   ```
   build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
   ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
   hooks: 21 installed in one freeze
   ```

## Deinstallation

```
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```
Stellt `builds.json` aus der Sicherung wieder her (Hash-geprüft identisch zum Original)
oder entfernt ohne Sicherung alle `store: "gog"`-Einträge. `KcdMp_client.dll` wird von
beiden Skripten nie angefasst.

## Was belegt ist (Auszug aus den Läufen)

| Prüfung | Ergebnis |
|---|---|
| `KcdMp_launcher.exe --check-game` | `verdict: supported (gog-1.5.6-c59754b9)`, Exit 0 |
| Build-Gate im Client | `build gog-1.5.6-c59754b9 (supported), 277 anchors` |
| gEnv-Anker | `WHGame.DLL+0x4917800`, vom Client als „matches the gEnv anchor" bestätigt |
| Hardware-Maus-Anker | Slots 3/11/12/25 vom Client als „verified" bestätigt, Zeiger sichtbar |
| Hooks | `hooks: 21 installed in one freeze, 58 ms (the engine boot)` |
| Verbindung | Server begrüßt, Spawn (`spawn: we are net 53 …`), Server-Login-Fenster erscheint |
| Installation/Deinstallation | `install.ps1` → 277 Anker; `uninstall.ps1` → builds.json wieder byte-identisch (SHA-256 `2D809E78…6207`) |

## Einschränkungen

- **247 Pattern-Anker fehlen** (von 548). Betroffen sind u. a. `Pickpocket.*`,
  `HorsePullDown.*`, `COperatorQueue.Create`, Lip-Sync, Kampf-Trigger und Teile der
  Kamera. Der Client läuft weiter, diese Funktionen sind aber aus.
- **23 Slot-Anker fehlen** (u. a. `IEntity`, `ISkeletonAnim`, `IAnimationSet`,
  `IGeomManager`, einzelne Slots von `I3DEngine`/`IPhysicalWorld`). Acht Anker wurden
  aus den Laufzeitmeldungen des Clients nachgetragen (die echten Slot-Adressen standen
  im Log); damit laufen u. a. die Render-Node-Entfernung (1158 Entfernungen im Testlauf)
  und die Hardware-Maus. Die übrigen bleiben offen.
- **Keine Steam-ID:** GOG liefert kein `steam_api64.dll`, das Log sagt
  `identity: the game has no Steam client loaded (steam_api64.dll): no Steam ID`.
  Server, die eine Steam-ID verlangen, lehnen GOG-Spieler ab. Es wird bewusst keine
  Identität gefälscht.
- **Server-Login:** Das Fenster „KCDRoleplay.com – Anmelden / Konto erstellen" kommt
  vom Server-Skript (`account.lua`), nicht von KCD:MP. Dafür braucht man ein Konto
  bei diesem Server; das ist unabhängig von diesem Fix.
- **Updater:** Die KCD:MP-Aktualisierung kann `builds.json` ersetzen. Nach einem
  Update `install.ps1` erneut ausführen. Das Original-`KcdMp_client.dll` bleibt
  unverändert, der Updater sieht also keinen manipulierten Client.
- **Schutz-Hooks fehlen:** Weil die Anker fehlen, sind auch die Absturz-Fänger aus, die
  der Client sonst installiert. Im Log stehen sie namentlich:
  `inventory guard: no anchor`, `living guard: no anchors`, `transition guard: no
  anchors`, `combat guard: no anchors`, `hand guard: no anchors`, `ui guard: no
  anchors`, `mp rules: no anchor for the whistle's horse fetch`, `… the pair check`,
  `… the animations' show / hide`. In genau diesen Situationen (viele Angreifer auf
  einen Kämpfer, Inventar mit Pferdetaschen, UI-Listener auf dem Render-Thread,
  Pfeife/Stealth-Prüfung, entfernte Entities am Animationsende) kann das Spiel
  abstürzen. Kein Absturz in den Testläufen, aber das Risiko ist bekannt und steht so
  im Log.
- **Nicht getestet:** längeres Spielen, Kampf, Inventar, Übergänge zwischen Leveln,
  mehrere Spieler auf einem Server.

## Wenn es nicht funktioniert

`%LOCALAPPDATA%\KcdMp\client.log` und `client.prev.log` aufbewahren. Relevant sind die
Zeilen `build gate:`, `anchors`, `not resolved`, `gEnv`, `hooks:`. Für einen echten
GOG-Support braucht das KCD:MP-Team einen mit `tools/sigscan/sigscan.py` erzeugten
Eintrag für genau diese WHGame.dll; die Vorlage dafür liegt in
`docs/request-to-kcdmp.txt`.

## Dateien

- `install.ps1`, `uninstall.ps1` – Ein-/Ausbau des Eintrags, Sicherung, Hash-Prüfung
- `gog-1.5.6-c59754b9.json` – der Eintrag (277 Anker)
- `ANLEITUNG.de.md` – Schritt-für-Schritt-Anleitung mit Fehlerbehebung
- `README.md` (englisch, Startseite) und `README.de.md` (deutsch, ausführlich)
- `docs/TECHNICAL.de.md` – Herleitung, Zahlen, Befehle, offene Punkte
- `docs/request-to-kcdmp.txt` – fertige Anfrage an das KCD:MP-Team
- `tools/rtti_derive.py` – leitet RTTI-Vtables, Slots, Exporte, gEnv aus WHGame.dll ab
- `tools/find_genv.py` – findet `gEnv` über den CSystem-Konstruktor
- `tools/probe_identity.py` – misst, welche Identitätsfelder der Launcher vergleicht
- `CHECKSUMS.txt` – SHA-256 der Quelldateien und dieses Pakets
- `LICENSE` (MIT) und `NOTICE` – Lizenz des eigenen Codes; `NOTICE` hält fest, dass keine
  Dateien von KCD:MP, Warhorse oder Deep Silver enthalten sind

## Rückmeldung

Bitte mit Angabe von KCD:MP-Version, GOG-Build (Timestamp/PDB aus dem Log), Server
und den letzten 50 Zeilen aus `client.log` melden. Ohne diese Angaben ist eine
Zuordnung nicht möglich.
