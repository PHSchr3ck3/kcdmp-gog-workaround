"""Read-only reconnaissance for KCD:MP 0.48.1 on a GOG build.

Prints facts only (hashes, offsets, table shapes) - nothing is modified.
"""
import hashlib
import json
import os
import sys

import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLL = os.path.join(ROOT, "KcdMp_client.dll")
LAUNCHER = os.path.join(ROOT, "KcdMp_launcher.exe")
GAME = r"D:\Spiele\GoG\Kingdom Come Deliverance II"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize_build(entry):
    res = entry.get("resolved", {})
    methods = {}
    for k, v in res.items():
        m = v.get("method", "?") if isinstance(v, dict) else "?"
        methods[m] = methods.get(m, 0) + 1
    return {
        "keys": sorted(entry.keys()),
        "resolved_count": len(res),
        "methods": dict(sorted(methods.items())),
    }


def main():
    print("== client dll ==")
    data = open(DLL, "rb").read()
    print("size   ", len(data))
    print("sha256 ", sha256(DLL))
    pe = pefile.PE(DLL, fast_load=True)
    print("machine", hex(pe.FILE_HEADER.Machine), "timestamp", pe.FILE_HEADER.TimeDateStamp,
          "imagebase", hex(pe.OPTIONAL_HEADER.ImageBase), "sizeofimage", hex(pe.OPTIONAL_HEADER.SizeOfImage))
    for s in pe.sections:
        print("  sec %-8s va=%08x vs=%08x raw=%08x rs=%08x" % (
            s.Name.rstrip(b"\0").decode(errors="replace"), s.VirtualAddress, s.Misc_VirtualSize,
            s.PointerToRawData, s.SizeOfRawData))
    print()
    print("== launcher ==")
    ld = open(LAUNCHER, "rb").read()
    print("size   ", len(ld))
    print("sha256 ", sha256(LAUNCHER))
    lpe = pefile.PE(LAUNCHER, fast_load=True)
    print("machine", hex(lpe.FILE_HEADER.Machine), "timestamp", lpe.FILE_HEADER.TimeDateStamp)
    print()
    print("== builds.json ==")
    bj = json.load(open(os.path.join(ROOT, "builds.json"), encoding="utf-8"))
    print("top keys", list(bj.keys()))
    print("json size", os.path.getsize(os.path.join(ROOT, "builds.json")))
    for k in bj:
        v = bj[k]
        if isinstance(v, dict) and "resolved" in v:
            print("build", k, json.dumps(summarize_build(v), indent=None)[:400])
            print("   meta", {kk: vv for kk, vv in v.items() if kk != "resolved"})
        else:
            print("key", k, type(v).__name__, str(v)[:200])
    print()
    print("== strings in client dll ==")
    for needle in [b"unknown game build", b"supported game builds", b"build gate",
                   b"builds.json", b"KcdMp_client", b"gog-1.5.6", b"self-test"]:
        idx = []
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            idx.append(i)
            start = i + 1
        print("%-24s %s" % (needle.decode(), [hex(x) for x in idx[:10]]), "count", len(idx))
    print()
    print("== game ==")
    for rel in [r"Bin\Win64MasterMasterGogPGO\WHGame.dll", r"Bin\Win64MasterMasterGogPGO\KingdomCome.exe",
                r"Bin\Win64MasterMasterSteamPGO\WHGame.dll"]:
        p = os.path.join(GAME, rel)
        if os.path.exists(p):
            print(rel, os.path.getsize(p), sha256(p))
        else:
            print(rel, "MISSING")


if __name__ == "__main__":
    main()
