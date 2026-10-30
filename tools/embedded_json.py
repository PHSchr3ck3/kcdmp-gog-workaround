import json

P = r"D:\download\KcdMp-0.48.0-win-x64\KcdMp_client.dll"
data = open(P, "rb").read()
off = 0xd2d404
# walk back to '{'
start = off
while data[start - 1:start] != b"{":
    start -= 1
    if off - start > 64:
        break
print("json start", hex(start), "bytes before:", data[start - 32:start].hex(" "))
# find matching end by brace counting aware of strings
i = start
depth = 0
in_str = False
esc = False
while i < len(data):
    c = data[i:i + 1]
    if in_str:
        if esc:
            esc = False
        elif c == b"\\":
            esc = True
        elif c == b'"':
            in_str = False
    else:
        if c == b'"':
            in_str = True
        elif c == b"{":
            depth += 1
        elif c == b"}":
            depth -= 1
            if depth == 0:
                break
    i += 1
print("json end", hex(i + 1), "length", i + 1 - start)
txt = data[start:i + 1]
print("after 32:", data[i + 1:i + 33].hex(" "))
try:
    obj = json.loads(txt)
    print("parsed ok; builds:", [b["id"] for b in obj["builds"]], "schema", obj["schema"])
    print("generated_by", obj["generated_by"])
except Exception as e:
    print("PARSE FAIL", e)

filetxt = open(r"D:\download\KcdMp-0.48.0-win-x64\builds.json", "rb").read()
print("file identical to embedded:", filetxt == txt, "file len", len(filetxt), "text len", len(txt))
print("file sha equal content:", __import__("hashlib").sha256(filetxt).hexdigest())
print("embedded sha:", __import__("hashlib").sha256(txt).hexdigest())

# length prefixes / hashes before start
for n in (2, 4, 8):
    print("u%d before:" % (n * 8), int.from_bytes(data[start - n:start], "little"))
