Werkzeuge zur Herleitung (nur Lesen, kein Schreiben in Spiel- oder Moddateien)
=============================================================================

recon.py           Hashes, PE-Kopfdaten, Form der Build-Tabelle, Lage der Strings.
embedded_json.py   Sucht die eingebettete Tabelle in KcdMp_client.dll und misst
                   Offset und Länge (Ergebnis: 0xd2d401, 237.680 Byte).
probe_identity.py  Laesst KcdMp_launcher.exe --check-game mit veraenderten
                   Identitaetsfeldern laufen und zeigt, welche Felder zaehlen.
rtti_derive.py     Leitet aus WHGame.dll alle RTTI-Vtables, deren Slots und die
                   PE-Exporte ab; schreibt tools/gog_anchors.json.
find_genv.py       Findet WHGame.gEnv ueber den CSystem-Konstruktor (braucht
                   capstone, siehe unten).
xref.py            Findet RIP-relative Verweise auf einen String (Beweisfuehrung).
strings_range.py   Druckt lesbare Strings aus einem Dateibereich.

Beispiel:
  python tools\recon.py
  python tools\rtti_derive.py
  python tools\find_genv.py

Abhaengigkeiten
---------------
pefile ist installiert. find_genv.py und xref.py brauchen zusaetzlich capstone:
  python -m pip install capstone
Falls pip haengt, laesst sich das passende Wheel direkt laden:
  python -c "import json,urllib.request,zipfile,io,os; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/capstone/json')); f=[x for x in d['urls'] if x['filename'].endswith('py3-none-win_amd64.whl')][0]; os.makedirs('tools/pylibs',exist_ok=True); zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(f['url']).read())).extractall('tools/pylibs')"
Dann in den Skripten sys.path um tools\pylibs ergaenzen (find_genv.py macht das bereits).

Hinweis: Die 247 pattern-Anker lassen sich mit diesen Werkzeugen NICHT herleiten.
Die Byte-Muster stehen nicht im Client; ohne zweiten WHGame.dll-Build gibt es keine
belegbare Zuordnung.
