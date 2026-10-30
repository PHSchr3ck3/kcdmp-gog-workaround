"""Probe which identity fields the launcher's build check compares (read-only for the game)."""
import copy
import json
import os
import subprocess
import sys

ROOT = r"D:\download\KcdMp-0.48.0-win-x64"
GAME = r"D:\Spiele\GoG\Kingdom Come Deliverance II"
bj = json.load(open(os.path.join(ROOT, "builds.json"), encoding="utf-8"))
ms = [b for b in bj["builds"] if b["store"] == "msstore"][0]
g = copy.deepcopy(ms)
g["id"] = "gog-1.5.6-c59754b9"
g["store"] = "gog"
g["steam_buildid"] = None
g["whgame"] = {
    "sha256": "c59754b925c669b26c46723eb6c19c3217aba2fac94a1ad2d8bcc229d9363870",
    "size": 89078272, "timestamp": 1782121515, "size_of_image": 95490048,
    "pdb_guid": "4B3F7D2D4D22434DA6CA550A88ED0D8C", "pdb_age": 2,
}
g["exe"] = {"sha256": "2e4c3189f32cc8d2a1a768eaf54754079d3ec90dac563b392dbd6cad9ea4e63b",
            "size": 1525760, "timestamp": None, "size_of_image": None}

variants = {
    "exact": {},
    "no_pdb": {"pdb_guid": "00000000000000000000000000000000", "pdb_age": 9},
    "no_size_of_image": {"size_of_image": 1},
    "no_timestamp": {"timestamp": 1},
    "no_sha": {"sha256": "00" * 32},
    "no_size": {"size": 1},
    "timestamp_only": None,
}

argfile = os.path.join(ROOT, "tools", "probe_builds.json")
for name, patch in variants.items():
    e = copy.deepcopy(g)
    if patch is None:  # strip everything but timestamp
        e["whgame"] = {"timestamp": g["whgame"]["timestamp"]}
        e["exe"] = {}
    else:
        e["whgame"].update(patch)
    data = {"schema": bj["schema"], "generated_by": "tools/probe_identity.py",
            "builds": [e]}
    json.dump(data, open(argfile, "w", encoding="utf-8"), indent=2)
    r = subprocess.run([os.path.join(ROOT, "KcdMp_launcher.exe"), "--check-game",
                        "--game", GAME, "--builds", argfile],
                       capture_output=True, text=True, timeout=60)
    out = (r.stdout + r.stderr).strip().replace("\n", " | ")
    print("%-18s exit=%d %s" % (name, r.returncode, out[:220]))
