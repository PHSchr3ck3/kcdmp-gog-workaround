# KCD:MP 0.48.1 auf der GOG-Version von KCD2 1.5.x

Workaround für die Build-Sperre von **KCD:MP 0.48.1** mit **Kingdom Come: Deliverance II
von GOG** (1.5.x). Der Eintrag `gog-1.5.6-c59754b9` wird in `builds.json` neben
`KcdMp_client.dll` ergänzt – **es wird keine Binärdatei verändert**.

> **Teilweiser Fix, kein offizieller GOG-Support.** Das Build-Gate lässt durch, die Engine
> startet, Hooks werden installiert und der Client verbindet sich. Von 548 Ankern sind aber
> nur **277 hergeleitet** – es fehlen **271**: **247 Pattern-Anker** (aus KCD:MPs `sigscan`,
> ohne die Byte-Muster nicht rekonstruierbar), 23 Slot-Anker und 1 RTTI-Anker. Der Client
> meldet jeden fehlenden Anker im Log und schaltet die passende Funktion ab – auch einige
> Absturz-Fänger. Details unter [Grenzen](#grenzen).

Die KCD:MP-FAQ sagt selbst: *„The GOG version needs its own build of KCD:MP, and it may come
later."* Für einen vollständigen Fix muss das KCD:MP-Team den Eintrag mit
`tools/sigscan/sigscan.py` erzeugen; die fertige Anfrage liegt in
[`docs/request-to-kcdmp.txt`](docs/request-to-kcdmp.txt).

## Schnellstart

```
git clone https://github.com/PHSchr3ck3/kcdmp-gog-fix
cd kcdmp-gog-fix
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
```

Danach `KcdMp_launcher.exe` **als Administrator** starten und im Launcher einen Server
wählen. Im Log `%LOCALAPPDATA%\KcdMp\client.log` muss stehen:

```
build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
hooks: 21 installed in one freeze
```

Schritt für Schritt mit Fehlerbehebung: **[ANLEITUNG.de.md](ANLEITUNG.de.md)**

## Dokumentation

| Datei | Inhalt |
|---|---|
| [ANLEITUNG.de.md](ANLEITUNG.de.md) | Installation, Start, Prüfen, Deinstallation, Fehlerbehebung |
| [README.de.md](README.de.md) | Ausführlicher Status, was belegt ist, Grenzen |
| [docs/TECHNICAL.de.md](docs/TECHNICAL.de.md) | Herleitung der 277 Anker, Zahlen, offene Punkte |
| [docs/request-to-kcdmp.txt](docs/request-to-kcdmp.txt) | Anfrage an das KCD:MP-Team |
| [tools/](tools/) | Herleitungsskripte und `gog_anchors.json` |
| [README.en.md](README.en.md) | English version |

## Getestet mit

| Datei | SHA-256 |
|---|---|
| KCD:MP 0.48.1 `KcdMp_client.dll` (15.625.152 Byte) | `AD44B2A0…C6653B` |
| KCD2 GOG `WHGame.dll` (89.078.272 Byte, Timestamp 1782121515, SizeOfImage 95490048, PDB `4B3F7D2D…0D8C`/2) | `C59754B9…D9363870` |
| KCD2 GOG `KingdomCome.exe` | `2E4C3189…9EA4E63B` |

`install.ps1` bricht bei jeder anderen Client-DLL ab. Vollständige Hashes in
[CHECKSUMS.txt](CHECKSUMS.txt).

## Grenzen

- **247 Pattern-Anker fehlen** (Pickpocket, HorsePullDown, Lip-Sync, Operator-Queue,
  Kampf-Trigger, Teile der Kamera …).
- **23 Slot- und 1 RTTI-Anker fehlen** (`IEntity`, `ISkeletonAnim`, `IAnimationSet`,
  `IGeomManager`, Teile von `I3DEngine`/`IPhysicalWorld`, `CStatistics`).
- **Absturz-Fänger sind aus** (`inventory/living/transition/combat/hand/ui guard`, drei
  `mp rules`-Anker). In den Testläufen kein Absturz, das Risiko steht aber im Log.
- **Keine Steam-ID** (GOG hat kein `steam_api64.dll`); Server mit Steam-Pflicht lehnen ab.
  Es wird keine Identität gefälscht.
- Ein KCD:MP-Update kann `builds.json` ersetzen → `install.ps1` erneut ausführen.
- Nicht getestet: längere Sitzungen, Kampf, Inventar, Levelwechsel, mehrere Spieler.

## Kein offizieller Support

Fan-Arbeit, nicht mit Warhorse Studios, Deep Silver oder dem KCD:MP-Team verbunden.
Nutzung auf eigene Gefahr.
