"""Find RIP-relative references to a file offset/RVA in a PE and disassemble around them.

Usage: python tools/xref.py 0xc0d488 [--context 40] [--file KcdMp_client.dll]
"""
import argparse
import sys

sys.path.insert(0, r"D:\download\KcdMp-0.48.0-win-x64\tools\pylibs")
import capstone
import pefile

BASE = 0x1d9100000


def load(path):
    pe = pefile.PE(path, fast_load=True)
    data = open(path, "rb").read()
    secs = []
    for s in pe.sections:
        secs.append((s.Name.rstrip(b"\0").decode(errors="replace"), s.VirtualAddress,
                     s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
    return pe, data, secs


def off2rva(secs, off):
    for name, va, vs, raw, rs in secs:
        if raw <= off < raw + rs:
            return va + (off - raw), name
    return None, None


def rva2off(secs, rva):
    for name, va, vs, raw, rs in secs:
        if va <= rva < va + max(vs, rs):
            return raw + (rva - va)
    return None


def find_xrefs(data, secs, target_rva):
    text = [s for s in secs if s[0] == ".text"][0]
    name, tva, tvs, traw, trs = text
    hits = []
    i = traw
    end = traw + trs
    while i < end - 8:
        b = data[i]
        # REX.W 8D /r  (lea r64, [rip+disp32]) with mod=00 rm=101
        if b in (0x48, 0x4C, 0x49, 0x4D) and data[i + 1] == 0x8D:
            modrm = data[i + 2]
            if (modrm & 0xC7) == 0x05:
                disp = int.from_bytes(data[i + 3:i + 7], "little", signed=True)
                rva = tva + (i - traw)
                tgt = (rva + 7 + disp) & 0xFFFFFFFF
                if tgt == target_rva:
                    hits.append((rva, 7))
                i += 7
                continue
        i += 1
    return hits


def disasm(data, secs, rva, count, before=0):
    off = rva2off(secs, rva)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    insns = list(md.disasm(data[off:off + 400], rva))
    out = []
    for ins in insns[:count]:
        out.append("  %08x  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="target file offset or RVA, hex")
    ap.add_argument("--file", default=r"D:\download\KcdMp-0.48.0-win-x64\KcdMp_client.dll")
    ap.add_argument("--context", type=int, default=30)
    ap.add_argument("--raw", action="store_true", help="target is a file offset")
    a = ap.parse_args()
    pe, data, secs = load(a.file)
    t = int(a.target, 0)
    target_rva, sec = (off2rva(secs, t) if a.raw else (t, None))
    if target_rva is None:
        print("target not in a section")
        return
    print("target rva %#x (%s)" % (target_rva, sec or ""))
    hits = find_xrefs(data, secs, target_rva)
    print("xrefs:", len(hits), [hex(h[0]) for h in hits])
    for rva, _ in hits:
        print("---- around %#x ----" % rva)
        print(disasm(data, secs, max(rva - a.context * 4, 0), a.context * 2))


if __name__ == "__main__":
    main()
