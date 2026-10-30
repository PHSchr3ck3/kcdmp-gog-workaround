# Technical derivation – KCD:MP 0.48.1 on KCD2 GOG 1.5.x

All addresses are RVAs in `WHGame.dll` (ImageBase `0x180000000`,
`Bin\Win64MasterMasterGogPGO\WHGame.dll`, SHA-256 `c59754b9…3870`, 89,078,272 bytes).
The client is `KcdMp_client.dll` (15,625,152 bytes, SHA-256 `ad44b2a0…653b`, ImageBase
`0x1d9100000`). No binary was modified.

## 1. Where the build table lives

- Embedded copy: file offset **0xd2d401**, length **237,680 bytes**, ending exactly at
  `0xd67449`; zeros before it, no length field, no hash. The copy exists once. It is
  **not byte-identical** to `builds.json` (embedded SHA-256 `5ca7bdf2…8553`, file
  `2d809e78…6207`), but the same length and the same three builds.
- `builds.json` next to the DLL: 237,680 bytes, `schema: 2`,
  `generated_by: tools/sigscan/sigscan.py`, builds `epic-1.5.6-b341eefe`,
  `msstore-1.5.6-74126a4c`, `steam-1.5.6-bdf8f9e4`, each with 548 entries under
  `resolved`.
- The client prefers the file: log `build gate: the entry comes from builds.json next
  to KcdMp_client.dll`; the embedded copy only serves the self-test
  (`the table of supported game builds inside the DLL holds 3 build(s)`).

## 2. How the build is recognised

The launcher was measured against the GOG installation with `--check-game` and a
synthetic table (`--builds`). Result matrix:

| Field in the entry | omitted/changed | `--check-game` |
|---|---|---|
| `timestamp` + `size_of_image` correct | – | `supported`, exit 0 |
| `pdb_guid`/`pdb_age` wrong | `0000…`/9 | `supported`, exit 0 |
| `sha256` wrong | `00…00` | `supported`, exit 0 |
| `size` wrong | 1 | `supported`, exit 0 |
| `size_of_image` wrong | 1 | `newer`, exit 3 |
| `timestamp` wrong | 1 | `newer`, exit 3 |
| only `timestamp` | – | `newer`, exit 3 |

So **timestamp and SizeOfImage are the key fields**; the launcher does not compare PDB
or SHA-256. The client checks the same identity; its log names timestamp and PDB GUID.
The exact client condition was not fully disassembled – what is proven is that an entry
with the GOG values is accepted (see section 6).

## 3. Anchors: what can be derived and what cannot

Per build: 548 entries, methods `pattern 247`, `slot 148`, `rtti 74`, `pattern_slot 51`,
`string_slot 20`, `runtime 4`, `export 2`, `ctor_data 1`, `absent 1` (counts for Epic;
MS Store/Steam differ by ±2 in slot/string_slot).

Derived for GOG (277):

| Method | Count | Derivation |
|---|---|---|
| `rtti` | 73 / 74 | Decorated RTTI name (`.?AVCSystem@@`, `.?AVC_Player@entitymodule@wh@@` …) → TypeDescriptor → RTTICompleteObjectLocator → vtable; slot count exactly as in the reference build. |
| `slot`, `pattern_slot`, `string_slot` | 197 / 220 | `vtable[slot]` from the located vtable; for interface vtables (ISystem, IHardwareMouse, I3DEngine …) the interface's vtable. |
| `export` | 2 / 2 | PE export table: `CreateGameStartup`, `?CreateInstance@C_Game@game@wh@@…`. |
| `runtime` | 4 / 4 | Constants (2, 4, 8, 88), no addresses. |
| `ctor_data` | 1 / 1 | `gEnv` via the CSystem constructor (section 5). |

Not derived (271):

- **247 `pattern` anchors.** The byte patterns are not stored in the client, and no
  second WHGame.dll build (Steam/Epic/MS Store) exists on this machine for comparison.
  Without patterns or a reference binary there is no provable mapping; nothing was
  guessed.
- **23 slot anchors** whose interface vtable could not be located unambiguously
  (`IEntity`, `ISkeletonAnim`, `IAnimationSet`, `IGeomManager`, parts of
  `I3DEngine`/`IPhysicalWorld`, `C_Human` …). Eight of them were reported by the client
  itself in the log ("slot 156 of I3DEngine is WHGame.DLL+0xa6eb50 …"); those eight were
  added.
- **1 `rtti` anchor**: `CStatistics` has no findable RTTI name in the GOG DLL.

The mapping is stored in `tools/gog_anchors.json`; `tools/rtti_derive.py` regenerates it.

## 4. Vtable validation

- 73 of 74 classes: exactly one vtable with **exactly** the reference build's slot count.
- Per-slot cross-check: the target lies in `.text`; some are also registered as function
  starts in `.pdata` (291,224 functions). Many getters are leaf functions without a
  `.pdata` entry, so `.pdata` is only an additional check.
- The client validates at runtime and logs `verified` or `… is X but the anchor says Y`.
  Examples from the run:
  `WHGame.ISystem.GetGlobalEnvironment: verified, slot 3 -> WHGame.DLL+0x19a3140`,
  `WHGame.IHardwareMouse.Event: verified, slot 3 -> WHGame.DLL+0x5924ac`.

## 5. `gEnv`

`ISystem::GetGlobalEnvironment` (slot 3 of the CSystem vtable, `0x19a3140`) is
`mov rax, [rcx+0x20]; ret`. The CSystem constructor (at `0xa484fa`) stores
`WHGame+0x4917800` into `[this+0x20]`. That area is referenced from `.text`
**12,778 times** within ±0x200 (reference build: 12,647), and the client confirms at
runtime:

```
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
```

So `WHGame.gEnv = 0x4917800` is proven (command: `python tools\find_genv.py`).

## 6. Hardware mouse (cursor in the server login)

The first run logged `player cursor: the hardware mouse's anchors are not resolved`.
`IHardwareMouse` has no RTTI name of its own; the implementation is `CHardwareMouse`
(`.?AVCHardwareMouse@@`) with three vtables. The 34-slot vtable at **0x3a79868** is the
interface vtable (24 of its 34 slots are `.pdata` function starts). It yielded slots 3
(`Event`, `0x5924ac`), 11 (`0x90fd8c`), 12 (`0x90fe54`) and 25 (`ConfineCursor`,
`0x9100e0`); the client confirms all four as `verified` and shows the pointer
(`player cursor: the game's pointer shown (count 1)`).

## 7. Verification run (2026-10-30)

```
build gate: build gog-1.5.6-c59754b9 (supported), 277 anchors
gEnv: 43 typed fields; system=… script=… console=… log=… timer=… entities=… framework=0x0 game=WHGame.DLL+0x56386e0
ISystem::GetGlobalEnvironment() = WHGame.DLL+0x4917800 (matches the gEnv anchor)
engine boot done at frame 1 (lua ready, console ready)
hooks: 21 installed in one freeze, 58 ms (the engine boot)
phase 0 probe: gEnv ok | lua ok | console ok (frame 120, pings 2)
spawn: we are net 53 at 758.0 3350.5 142.3 …
```

Server: `play-de.kcdroleplay.com:7799`; the login window comes from the server's script
`account.lua` ("KCDRoleplay.com – Anmelden / Konto erstellen").

## 8. Open points

1. **247 pattern anchors** – only provable with the original patterns or a reference
   build. This is why it is not full GOG support.
2. **Launcher must run as administrator** – without elevation the game aborted with
   `ERROR: CryInput.dll could not be loaded!`; the file is not part of the GOG package
   and was not present anywhere else on the drive. Cause not determined, unrelated to
   this fix.
3. **No Steam ID** – GOG ships no `steam_api64.dll`; servers requiring Steam refuse.
   Identities are not faked.
4. **Updater** – can replace `builds.json` on a new KCD:MP release; re-run `install.ps1`
   afterwards.
5. **Crash guards off** – `inventory guard`, `living guard`, `transition guard`,
   `combat guard`, `hand guard`, `ui guard` and three `mp rules` anchors are missing, so
   their crash catchers are not installed (see log, 01:00:21). No crash in the test runs,
   but the risk is proven and named.
6. **Not tested** – combat, inventory, level transitions, multiple players, longer
   sessions.

## 9. Tools and commands

```
python tools\recon.py                      # hashes, PE data, table shape
python tools\probe_identity.py             # which fields --check-game compares
python tools\rtti_derive.py                # vtables, slots, exports -> tools\gog_anchors.json
python tools\find_genv.py                  # gEnv via the CSystem constructor
python tools\embedded_json.py              # location of the embedded table
powershell -File .\install.ps1 -GameDir "<game folder>"
powershell -File .\uninstall.ps1
```

Dependencies: `pefile` (installed), `capstone` (only for `find_genv.py`; available as a
wheel under `tools\pylibs`, see `tools\README.txt`).
