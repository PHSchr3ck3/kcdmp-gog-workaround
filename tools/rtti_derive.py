"""Derive GOG WHGame.dll anchor addresses from RTTI and the PE export table.

For every rtti entry in a reference build (default: msstore) the class' decorated
name is looked up in the GOG binary (any namespace), its RTTICompleteObjectLocator
is located and the vtable that references it is read.  Vtable slots are resolved
for the slot / pattern_slot / string_slot entries of the same class; when the
reference vtable belongs to an interface (ISystem, IEntity, ...), the interface's
own RTTI vtable is used.  Every function address is checked against the .pdata
table (function starts) and against the .text section.

Writes a JSON report with per-anchor value, evidence and confidence.
"""
import argparse
import json
import struct

import pefile

TEXT_SEC = ".text"


def load(path):
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"],
                                           pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
    data = open(path, "rb").read()
    ib = pe.OPTIONAL_HEADER.ImageBase
    secs = {}
    order = []
    for s in pe.sections:
        n = s.Name.rstrip(b"\0").decode(errors="replace")
        secs[n] = (s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
        order.append(n)
    return pe, data, ib, secs, order


def rva2off(secs, rva):
    for n, (va, vs, raw, rs) in secs.items():
        if va <= rva < va + max(vs, rs):
            return raw + (rva - va)
    return None


def off2rva(secs, off):
    for n, (va, vs, raw, rs) in secs.items():
        if raw <= off < raw + rs:
            return va + (off - raw)
    return None


def qword(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def dword(data, off):
    return struct.unpack_from("<I", data, off)[0]


def find_all(data, needle):
    out = []
    i = data.find(needle)
    while i >= 0:
        out.append(i)
        i = data.find(needle, i + 1)
    return out


def index_type_names(data):
    idx = {}
    for pre in (b".?AV", b".?AU"):
        start = 0
        while True:
            i = data.find(pre, start)
            if i < 0:
                break
            start = i + 1
            end = data.find(b"\0", i, i + 220)
            if end < 0:
                continue
            name = data[i:end]
            if not name.endswith(b"@@"):
                continue
            token = name[4:].split(b"@")[0]
            if not token or not all(32 <= c < 127 for c in token):
                continue
            idx.setdefault(token, []).append((i, name))
    return idx


def vtables_for_token(token_bytes, tindex, data, secs, ib, tlo, thi, funcs):
    """All vtables whose RTTI TypeDescriptor name has this class token."""
    cols = []
    for name_off, name in tindex.get(token_bytes, []):
        for td in (name_off - 16, name_off - 24):
            td_rva = off2rva(secs, td) if td >= 0 else None
            if td_rva is None:
                continue
            if dword(data, td + 8) != 0 or dword(data, td + 12) != 0:
                continue
            for p in find_all(data, struct.pack("<I", td_rva)):
                if p < 12:
                    continue
                col_off = p - 12
                if dword(data, col_off) != 1:
                    continue
                col_rva = off2rva(secs, col_off)
                if col_rva is None:
                    continue
                if dword(data, col_off + 20) not in (col_rva, col_off):
                    continue
                cols.append(col_rva)
    cols = sorted(set(cols))
    out = []
    for col_rva in cols:
        for p in find_all(data, struct.pack("<Q", ib + col_rva)):
            vstart = p + 8
            vrva = off2rva(secs, vstart)
            n = 0
            valid = 0
            while n < 4000:
                r = qword(data, vstart + n * 8) - ib
                if not (tlo <= r < thi):
                    break
                n += 1
                if r in funcs:
                    valid += 1
            out.append({"vtable_rva": vrva, "slots": n, "valid": valid, "col": hex(col_rva)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dll", default=r"D:\Spiele\GoG\Kingdom Come Deliverance II\Bin\Win64MasterMasterGogPGO\WHGame.dll")
    ap.add_argument("--builds", default=r"D:\download\KcdMp-0.48.0-win-x64\builds.json")
    ap.add_argument("--store", default="msstore")
    ap.add_argument("--out", default=r"D:\download\KcdMp-0.48.0-win-x64\tools\gog_anchors.json")
    a = ap.parse_args()

    bj = json.load(open(a.builds, encoding="utf-8"))
    ref = [x for x in bj["builds"] if x["store"] == a.store][0]
    res = ref["resolved"]

    pe, data, ib, secs, order = load(a.game_dll)
    print("imagebase %#x  size %d" % (ib, len(data)))

    funcs = set()
    if hasattr(pe, "DIRECTORY_ENTRY_EXCEPTION"):
        for e in pe.DIRECTORY_ENTRY_EXCEPTION:
            funcs.add(e.struct.BeginAddress)
    print("pdata functions:", len(funcs))

    text = secs[TEXT_SEC]
    tlo, thi = text[0], text[0] + text[1]

    exports = {}
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        for sym in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if sym.name:
                exports[sym.name.decode(errors="replace")] = sym.address

    print("indexing type names ...")
    tindex = index_type_names(data)
    print("class tokens:", len(tindex))

    diag = {}
    chosen = {}
    for key, val in res.items():
        if val["method"] != "rtti":
            continue
        cls = key.split(".")[1]
        expected = val["slots"]
        vt = vtables_for_token(cls.encode(), tindex, data, secs, ib, tlo, thi, funcs)
        ranked = sorted(vt, key=lambda v: (abs(v["slots"] - expected), -v["valid"]))
        best = ranked[0] if ranked else None
        if best:
            best["delta"] = best["slots"] - expected
            best["exact"] = len([v for v in vt if v["slots"] == expected])
            best["confidence"] = "high" if best["delta"] == 0 else ("medium" if abs(best["delta"]) <= 2 else "low")
            chosen[key] = best
        diag[key] = {"expected": expected, "candidates": vt, "best": best}

    high = sum(1 for k in chosen if chosen[k]["confidence"] == "high")
    print("vtables chosen: %d / %d (exact slot count: %d)" % (len(chosen), 74, high))
    for k in sorted(diag):
        d = diag[k]
        if not d["best"] or d["best"]["confidence"] != "high":
            print("  %-52s exp %3d  best %s" % (k, d["expected"],
                  "none" if not d["best"] else "%#x slots %d (delta %+d)" % (d["best"]["vtable_rva"], d["best"]["slots"], d["best"]["delta"])))

    exp_report = {}
    for key, val in res.items():
        if val["method"] != "export":
            continue
        short = key.split(".", 1)[1]          # C_Game.CreateInstance
        cls, meth = short.split(".") if "." in short else (None, short)
        match = None
        if cls is None:
            match = exports.get(short)
        if match is None:
            for name, rva in exports.items():
                if name == short or ("?%s@%s@" % (meth, cls)) in name:
                    match = rva
                    break
        exp_report[key] = {"rva": hex(match) if match else None, "status": "ok" if match else "not found"}

    # slot resolution: primary class vtable, else the interface named by the key prefix
    slot_report = {}
    for key, val in res.items():
        m = val["method"]
        if m not in ("slot", "pattern_slot", "string_slot"):
            continue
        vref = val.get("vtable")
        rk = next((k for k, v in res.items() if v["method"] == "rtti" and v.get("vtable") == vref), None)
        source = None
        if rk is not None and rk in chosen:
            source = chosen[rk]
        if source is None:
            iface = key.split(".")[1]
            cand = vtables_for_token(iface.encode(), tindex, data, secs, ib, tlo, thi, funcs)
            need = val["slot"] + 1
            usable = [c for c in cand if c["slots"] >= need]
            usable.sort(key=lambda v: (-v["valid"], v["slots"]))
            if len(usable) == 1:
                source = usable[0]
            elif usable:
                # several candidates; accept only if the slot target lands in .text for all
                rvas = []
                for c in usable:
                    off = rva2off(secs, c["vtable_rva"] + val["slot"] * 8)
                    rvas.append((c, qword(data, off) - ib))
                good = [(c, r) for c, r in rvas if tlo <= r < thi]
                if len(good) == 1:
                    source = good[0][0]
        if source is None:
            slot_report[key] = {"method": m, "status": "vtable-unresolved"}
            continue
        slot = val["slot"]
        addr_rva = source["vtable_rva"] + slot * 8
        off = rva2off(secs, addr_rva)
        ptr = qword(data, off) - ib
        if addr_rva >= source["vtable_rva"] + source["slots"] * 8:
            status = "slot-outside-vtable"
        elif ptr in funcs:
            status = "ok"
        elif tlo <= ptr < thi:
            status = "in-text-no-pdata-start"
        else:
            status = "outside-text"
        slot_report[key] = {"method": m, "vtable": hex(source["vtable_rva"]),
                            "vtable_slots": source["slots"], "slot": slot,
                            "rva": hex(ptr), "status": status}

    from collections import Counter
    c = Counter(v["status"] for v in slot_report.values())
    print("slot anchors:", dict(c))
    print("export anchors:", {k: v["status"] for k, v in exp_report.items()})

    json.dump({"rtti": diag, "chosen": chosen, "slots": slot_report, "exports": exp_report},
              open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
