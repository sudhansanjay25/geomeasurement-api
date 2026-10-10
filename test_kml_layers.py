import pyogrio
from pathlib import Path

kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Folder>
      <name>F1</name>
      <Placemark><Point><coordinates>0,0</coordinates></Point></Placemark>
    </Folder>
    <Folder>
      <name>F2</name>
      <Placemark><LineString><coordinates>0,0 1,1</coordinates></LineString></Placemark>
    </Folder>
  </Document>
</kml>
"""
Path("test_layers.kml").write_text(kml)
layers = pyogrio.list_layers("test_layers.kml")
print(layers)
