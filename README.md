# kcdmp-gog-fix

**Deutsch:** [README.de.md](README.de.md) · [Schritt-für-Schritt-Anleitung](ANLEITUNG.de.md)

Build-gate workaround for **KCD:MP 0.48.1** on the **GOG** release of *Kingdom Come:
Deliverance II* 1.5.x.

KCD:MP 0.48.1 ships build tables for Epic, Microsoft Store and Steam. This repository adds
a fourth entry, `gog-1.5.6-c59754b9`, to `builds.json` next to `KcdMp_client.dll`. **No
binary is modified** — the client reads the table from that file at startup.

> **This is a partial fix, not official GOG support.** The build gate passes, the engine
> boots, hooks install and the client connects to a server. Of 548 anchors, **277 are
> derived** and **271 are missing**: **247 `pattern` anchors** (found by KCD:MP's `sigscan`
> from byte patterns that are not shipped), 23 slot anchors and 1 RTTI anchor. The client
> logs each missing anchor and turns the matching feature off — including some crash guards.
> See *Limitations* below.

The KCD:MP FAQ says: *"The GOG version needs its own build of KCD:MP, and it may come later."*
For a complete fix the KCD:MP team has to generate the entry with `tools/sigscan/sigscan.py`;
the request with all measured data is in [`docs/request-to-kcdmp.txt`](docs/request-to-kcdmp.txt).

## Install

```
git clone https://github.com/PHSchr3ck3/kcdmp-gog-fix
cd kcdmp-gog-fix
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
```

The script checks size and SHA-256 of `KcdMp_client.dll`, backs `builds.json` up to
`builds.json.kcdmp-gog.bak`, replaces any `store: "gog"` entry with the one from
`gog-1.5.6-c59754b9.json` (277 anchors), and optionally runs
`KcdMp_launcher.exe --check-game` when `-GameDir` is given.

Start `KcdMp_launcher.exe` **as administrator**. In the tested environment the game only got
past its input module when elevated; otherwise it aborted with
`ERROR: CryInput.dll could not be loaded!` (cause not determined, unrelated to this fix).

Expected log lines in `%LOCALAPPDATA%\KcdMp\client.log`:

```
build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
hooks: 21 installed in one freeze
```

## Uninstall

```
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
```

Restores `builds.json` byte-identically from the backup (verified: SHA-256
`2D809E781310A4DFF0DBB50E092B331AB4CF4F6D72D90003753E17ECBFD36207`), or strips `gog` entries when
no backup exists. The client DLL is never touched.

## Limitations

- **247 `pattern` anchors are missing.** They were found by byte signatures that are not
  shipped. Affected: pickpocket, horse pull-down, lip sync, operator queue, combat triggers,
  parts of the camera, and more.
- **23 `slot` and 1 `rtti` anchors are missing** (`IEntity`, `ISkeletonAnim`, `IAnimationSet`,
  `IGeomManager`, parts of `I3DEngine`/`IPhysicalWorld`, `CStatistics`). Eight interface slots
  were recovered from the client's own runtime messages.
- **Crash guards are off** (`inventory guard`, `living guard`, `transition guard`,
  `combat guard`, `hand guard`, `ui guard`, three `mp rules` anchors). Crowded combat,
  horse-bag inventory, UI listeners on the render thread, whistle/stealth checks and removed
  entities at an animation's end can crash the game. No crash occurred in the test runs.
- **No Steam ID:** GOG has no `steam_api64.dll`; servers that require a Steam ID refuse GOG
  players. No identity is faked.
- A KCD:MP update can replace `builds.json`; re-run `install.ps1` afterwards.
- Not tested: longer sessions, combat, inventory, level transitions, multiple players.

## Tested against

| File | SHA-256 |
|---|---|
| KCD:MP 0.48.1 `KcdMp_client.dll` (15,625,152 bytes) | `AD44B2A081470563C9CE9885BACC008EB4AC0F12B239221DD47C8A383AC6653B` |
| KCD2 GOG `WHGame.dll` (89,078,272 bytes, timestamp 1782121515, SizeOfImage 95490048, PDB `4B3F7D2D4D22434DA6CA550A88ED0D8C`/2) | `C59754B925C669B26C46723EB6C19C3217ABA2FAC94A1AD2D8BCC229D9363870` |
| KCD2 GOG `KingdomCome.exe` | `2E4C3189F32CC8D2A1A768EAF54754079D3EC90DAC563B392DBD6CAD9EA4E63B` |

`install.ps1` refuses to run on any other client DLL. Full hashes in
[CHECKSUMS.txt](CHECKSUMS.txt).

## How the entry was derived

See [`docs/TECHNICAL.md`](docs/TECHNICAL.md) (English; German:
[`docs/TECHNICAL.de.md`](docs/TECHNICAL.de.md)). Summary:

- RTTI type names → `RTTICompleteObjectLocator` → vtable; 73 of 74 classes matched with the
  exact slot count of the reference build.
- Interface vtables for `slot` / `pattern_slot` / `string_slot` entries; each target checked
  against `.text` and the `.pdata` function table.
- PE exports for `CreateGameStartup` and `CGame::CreateInstance`.
- `gEnv` from the `CSystem` constructor: `WHGame+0x4917800`, confirmed at runtime by the client
  (`matches the gEnv anchor`, 12,778 references in ±0x200 in the GOG binary vs 12,647 in the
  reference).

The derivation scripts live in [`tools/`](tools/), the full report in
[`tools/gog_anchors.json`](tools/gog_anchors.json).

## Repository contents

- `install.ps1`, `uninstall.ps1`
- `gog-1.5.6-c59754b9.json` — the builds entry (277 anchors)
- English: this file · German: [`README.de.md`](README.de.md) and
  [`ANLEITUNG.de.md`](ANLEITUNG.de.md)
- [`docs/TECHNICAL.md`](docs/TECHNICAL.md) (English) / [`docs/TECHNICAL.de.md`](docs/TECHNICAL.de.md) (German),
  [`docs/request-to-kcdmp.txt`](docs/request-to-kcdmp.txt)
  (English; German: [`docs/request-to-kcdmp.de.txt`](docs/request-to-kcdmp.de.txt))
- `tools/` — read-only derivation scripts and their report
- `CHECKSUMS.txt`, `LICENSE`, `NOTICE`

No game files, no KCD:MP binaries, no server code. Nothing here bypasses server access
control, anti-cheat or identity checks; it only teaches the client its own game build.

## License

The code in this repository is **MIT** licensed (see [LICENSE](LICENSE)). [NOTICE](NOTICE)
records that no files or code from KCD:MP, Warhorse Studios or Deep Silver are included:
the addresses were derived independently from a legally owned GOG copy, and no binaries are
redistributed.

## Disclaimer

Fan-made workaround, not affiliated with Warhorse Studios, Deep Silver or the KCD:MP team.
Use at your own risk. The game and the mod remain the property of their owners.
