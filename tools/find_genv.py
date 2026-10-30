"""Find WHGame.gEnv: the CSystem constructor stores the vtable and the global env pointer.

Scans .text for `lea reg,[CSystem vtable]`, disassembles the surrounding function and
looks for a store into a rip-relative global (the candidate gEnv).
"""
import struct
import sys

sys.path.insert(0, r"D:\download\KcdMp-0.48.0-win-x64\tools\pylibs")
import capstone
import pefile

P = r"D:\Spiele\GoG\Kingdom Come Deliverance II\Bin\Win64MasterMasterGogPGO\WHGame.dll"
VT = 0x3daf478          # CSystem vtable RVA (derived)
IB = 0x180000000

pe = pefile.PE(P, fast_load=True)
data = open(P, "rb").read()
secs = {s.Name.rstrip(b"\0").decode(): (s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections}
tva, tvs, traw, trs = secs[".text"]
tlo, thi = tva, tva + tvs


def r2o(r):
    for n, (va, vs, raw, rs) in secs.items():
        if va <= r < va + max(vs, rs):
            return raw + (r - va)


def o2r(o):
    for n, (va, vs, raw, rs) in secs.items():
        if raw <= o < raw + rs:
            return va + (o - raw)


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True

hits = []
i = traw
end = traw + trs - 7
while i < end:
    if data[i] in (0x48, 0x4C, 0x49, 0x4D) and data[i + 1] == 0x8D and (data[i + 2] & 0xC7) == 0x05:
        disp = struct.unpack_from("<i", data, i + 3)[0]
        rva = tva + (i - traw)
        if (rva + 7 + disp) & 0xFFFFFFFF == VT:
            hits.append(rva)
        i += 7
        continue
    i += 1
print("lea-to-CSystem-vtable sites:", len(hits), [hex(h) for h in hits[:10]])

for rva in hits[:8]:
    off = r2o(rva)
    print("\n==== site %#x ====" % rva)
    insns = list(md.disasm(data[off - 48:off + 220], rva - 48))
    for ins in insns:
        mark = "  <<<" if ins.address == rva else ""
        print("  %08x  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
