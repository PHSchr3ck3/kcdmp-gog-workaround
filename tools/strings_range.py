import re
import sys

path = r"D:\download\KcdMp-0.48.0-win-x64\KcdMp_client.dll"
data = open(path, "rb").read()

start = int(sys.argv[1], 0)
end = int(sys.argv[2], 0)
chunk = data[start:end]
# printable runs
runs = re.finditer(rb"[\x20-\x7e]{4,}", chunk)
for m in runs:
    s = m.group().decode()
    print("%08x  %s" % (start + m.start(), s))
