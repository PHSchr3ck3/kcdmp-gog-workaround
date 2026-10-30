# Technische Herleitung – KCD:MP 0.48.1 auf KCD2-GOG 1.5.x

Alle Adressen sind RVAs in `WHGame.dll` (ImageBase `0x180000000`,
`Bin\Win64MasterMasterGogPGO\WHGame.dll`, SHA-256 `c59754b9…3870`, 89.078.272 Byte).
Der Client liegt als `KcdMp_client.dll` (15.625.152 Byte, SHA-256 `ad44b2a0…653b`,
ImageBase `0x1d9100000`). Es wurde keine Binärdatei verändert.

## 1. Wo die Build-Tabelle liegt

- Eingebettete Kopie: Dateioffset **0xd2d401**, Länge **237.680 Byte**, endet exakt an
  der Stelle `0xd67449`; davor stehen Nullen, kein Längenfeld, kein Hash. Die Kopie ist
  genau einmal vorhanden. Sie ist **nicht byte-identisch** mit `builds.json`
  (eingebettet SHA-256 `5ca7bdf2…8553`, Datei `2d809e78…6207`), aber gleich lang und
  mit denselben drei Builds.
- `builds.json` neben der DLL: 237.680 Byte, `schema: 2`,
  `generated_by: tools/sigscan/sigscan.py`, Builds `epic-1.5.6-b341eefe`,
  `msstore-1.5.6-74126a4c`, `steam-1.5.6-bdf8f9e4`, je 548 Einträge unter `resolved`.
- Der Client bevorzugt die Datei: Log `build gate: the entry comes from builds.json
  next to KcdMp_client.dll`; die eingebettete Kopie dient nur dem Selbsttest
  (`the table of supported game builds inside the DLL holds 3 build(s)`).

## 2. Wie der Build erkannt wird

Der Launcher wurde mit `--check-game` und einer synthetischen Tabelle (`--builds`)
gegen die GOG-Installation gemessen. Ergebnis-Matrix:

| Feld im Eintrag | weggelassen/geändert | `--check-game` |
|---|---|---|
| `timestamp` + `size_of_image` korrekt | – | `supported`, Exit 0 |
| `pdb_guid`/`pdb_age` falsch | `0000…`/9 | `supported`, Exit 0 |
| `sha256` falsch | `00…00` | `supported`, Exit 0 |
| `size` falsch | 1 | `supported`, Exit 0 |
| `size_of_image` falsch | 1 | `newer`, Exit 3 |
| `timestamp` falsch | 1 | `newer`, Exit 3 |
| nur `timestamp` | – | `newer`, Exit 3 |

Also: **Timestamp und SizeOfImage sind die Schlüsselfelder**, PDB und SHA-256 werden
vom Launcher nicht verglichen. Der Client prüft dieselbe Identität; sein Log nennt
Timestamp und PDB-GUID. Die genaue Client-Bedingung wurde nicht vollständig
disassembliert – belegt ist, dass ein Eintrag mit den GOG-Werten akzeptiert wird
(siehe Abschnitt 6).

## 3. Anker: was herleitbar ist und was nicht

Pro Build: 548 Einträge, Methoden `pattern 247`, `slot 148`, `rtti 74`,
`pattern_slot 51`, `string_slot 20`, `runtime 4`, `export 2`, `ctor_data 1`,
`absent 1` (Zählung für Epic; MS Store/Steam weichen bei slot/string_slot um ±2 ab).

Hergeleitet für GOG (277):

| Methode | Anzahl | Herleitung |
|---|---|---|
| `rtti` | 73 / 74 | Dekorierter RTTI-Name (`.?AVCSystem@@`, `.?AVC_Player@entitymodule@wh@@` …) → TypeDescriptor → RTTICompleteObjectLocator → Vtable; Slot-Anzahl exakt wie im Referenz-Build. |
| `slot`, `pattern_slot`, `string_slot` | 197 / 220 | `vtable[slot]` aus der gefundenen Vtable; bei Interface-Vtables (ISystem, IHardwareMouse, I3DEngine …) die Vtable des Interfaces. |
| `export` | 2 / 2 | PE-Exporttabelle: `CreateGameStartup`, `?CreateInstance@C_Game@game@wh@@…`. |
| `runtime` | 4 / 4 | Konstanten (2, 4, 8, 88), keine Adressen. |
| `ctor_data` | 1 / 1 | `gEnv` über den CSystem-Konstruktor (Abschnitt 5). |

Nicht hergeleitet (271):

- **247 `pattern`-Anker.** Die Byte-Muster stehen nicht im Client und auf dem Rechner
  existiert kein zweiter WHGame.dll-Build (Steam/Epic/MS Store) als Vergleich. Ohne
  Muster oder Referenzbinärdatei ist keine belegbare Zuordnung möglich; geraten wurde
  nichts.
- **23 Slot-Anker**, deren Interface-Vtable nicht eindeutig auffindbar war
  (`IEntity`, `ISkeletonAnim`, `IAnimationSet`, `IGeomManager`, Teile von
  `I3DEngine`/`IPhysicalWorld`, `C_Human` …). Acht davon lieferte der Client selbst im
  Log („slot 156 of I3DEngine is WHGame.DLL+0xa6eb50 …"); diese acht wurden
  nachgetragen.
- **1 `rtti`-Anker**: `CStatistics` hat in der GOG-DLL keinen auffindbaren
  RTTI-Namen.

Die Zuordnung ist als `tools/gog_anchors.json` abgelegt; `tools/rtti_derive.py`
erzeugt sie neu.

## 4. Validierung der Vtables

- 73 von 74 Klassen: genau eine Vtable mit **exakt** der Slot-Anzahl des
  Referenz-Builds.
- Gegenprobe pro Slot: Zieladresse liegt in `.text`; ein Teil ist zusätzlich als
  Funktionsanfang in `.pdata` registriert (291.224 Funktionen). Viele Getter sind
  Leaf-Funktionen ohne `.pdata`-Eintrag, daher ist `.pdata` nur eine Zusatzprüfung.
- Der Client prüft zur Laufzeit selbst und schreibt `verified` bzw. `… is X but the
  anchor says Y`. Beispiele aus dem Lauf:
  `WHGame.ISystem.GetGlobalEnvironment: verified, slot 3 -> WHGame.DLL+0x19a3140`,
  `WHGame.IHardwareMouse.Event: verified, slot 3 -> WHGame.DLL+0x5924ac`.

## 5. `gEnv`

`ISystem::GetGlobalEnvironment` (Slot 3 der CSystem-Vtable, `0x19a3140`) ist
`mov rax, [rcx+0x20]; ret`. Der CSystem-Konstruktor (bei `0xa484fa`) legt in
`[this+0x20]` die Adresse `WHGame+0x4917800` ab. Dieser Bereich wird aus `.text`
**12.778-mal** im Fenster ±0x200 referenziert (Referenz-Build: 12.647), und der
Client bestätigt zur Laufzeit:

```
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
```

Damit ist `WHGame.gEnv = 0x4917800` belegt (Befehl: `python tools\find_genv.py`).

## 6. Hardware-Maus (Cursor im Server-Login)

Der erste Lauf meldete `player cursor: the hardware mouse's anchors are not resolved`.
`IHardwareMouse` hat keinen eigenen RTTI-Namen; die Implementierung ist
`CHardwareMouse` (`.?AVCHardwareMouse@@`) mit drei Vtables. Die 34-Slot-Vtable bei
**0x3a79868** ist die Interface-Vtable (24 der 34 Slots sind `.pdata`-Funktionsanfänge).
Damit ließen sich die Slots 3 (`Event`, `0x5924ac`), 11 (`0x90fd8c`), 12 (`0x90fe54`)
und 25 (`ConfineCursor`, `0x9100e0`) belegen; der Client bestätigt alle vier als
`verified` und zeigt den Zeiger (`player cursor: the game's pointer shown (count 1)`).

## 7. Verifikationslauf (30.10.2026)

```
build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
gEnv: 43 typed fields; system=… script=… console=… log=… timer=… entities=… framework=0x0 game=WHGame.DLL+0x56386e0
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
engine boot done at frame 1 (lua ready, console ready)
hooks: 21 installed in one freeze, 58 ms (the engine boot)
phase 0 probe: gEnv ok | lua ok | console ok (frame 120, pings 2)
spawn: we are net 53 at 758.0 3350.5 142.3 …
```

Server: `play-de.kcdroleplay.com:7799`; das Login-Fenster stammt vom Server-Skript
`account.lua` („KCDRoleplay.com – Anmelden / Konto erstellen").

## 8. Offene Punkte

1. **247 Pattern-Anker** – nur mit den Original-Mustern oder einem Referenz-Build
   belegbar. Das ist der Grund, warum das kein vollwertiger GOG-Support ist.
2. **Start nur als Administrator** – ohne Erhöhung brach das Spiel mit
   `ERROR: CryInput.dll could not be loaded!` ab; die Datei ist im GOG-Paket nicht
   enthalten und lag auch sonst nirgends auf dem Laufwerk. Ursache nicht ermittelt,
   unabhängig von diesem Fix.
3. **Keine Steam-ID** – GOG liefert keine `steam_api64.dll`; Server mit Steam-Pflicht
   lehnen ab. Identitäten werden nicht gefälscht.
4. **Updater** – kann `builds.json` bei einer neuen KCD:MP-Version ersetzen;
   `install.ps1` danach erneut ausführen.
5. **Schutz-Hooks aus** – `inventory guard`, `living guard`, `transition guard`,
   `combat guard`, `hand guard`, `ui guard` und drei `mp rules`-Anker fehlen; die
   zugehörigen Absturz-Fänger sind damit nicht installiert (siehe Log, 01:00:21).
   Kein Absturz in den Testläufen, aber das Risiko ist belegt und benannt.
6. **Nicht getestet** – Kampf, Inventar, Levelwechsel, mehrere Spieler, längere Sitzung.

## 9. Werkzeuge und Befehle

```
python tools\recon.py                      # Hashes, PE-Daten, Tabellenform
python tools\probe_identity.py             # welche Felder --check-game vergleicht
python tools\rtti_derive.py                # Vtables, Slots, Exporte -> tools\gog_anchors.json
python tools\find_genv.py                  # gEnv über den CSystem-Konstruktor
python tools\embedded_json.py              # Lage der eingebetteten Tabelle
powershell -File .\install.ps1 -GameDir "<Spielordner>"
powershell -File .\uninstall.ps1
```

Abhängigkeiten: `pefile` (vorhanden), `capstone` (nur für `find_genv.py`; als Wheel
unter `tools\pylibs` nachladbar, siehe `tools\README.txt`).
