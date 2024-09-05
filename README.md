# com6Utils
External support routines for com6
Readme für scarp_avaframe

Info:
Der Code wurde noch nicht an die vorgegebenen Programmierrichtlinien angepasst (habe ich ehrlich gesagt nach dem Urlaub etwas vergessen) -> wird bei der Implementierung in das Projekt nachgeholt

Die Laufzeit beträgt bei mir ca 1 Minute. Das hängt aber sicher stark von den verwendeten Dateien und Inputs ab

Anleitung:

-Am besten ZIP in eigenem Ordner entpacken, dann müssen keine File-Paths festgelegt werden

-Ansonsten Pfade festlegen:

	"elevation": Pfad zum DGM
 
	"perimeter": Pfad zum asci File, welches die maximale Fläche der Release Area festlegt (kann in QGIS erzeugt werden)
		
-Ganz unten im Skript (Zeile 150) unter "method" entweder plane oder ellipsoid wählen

-Inputs eingeben:

	-Diese müssen durch Beistriche getrennt werden. Auch mehrere Ebenen sind derzeit nur durch Beistrich getrennt (in Zukunft per Liste)
 
	-Plane:
		x, y & z  Koordinate des Punktes um den die Ebene gedreht wird (In Qgis ablesen, aktuell EPSG 32633 Koordinaten, und Höhe in m für z)
		Dip angle: Drehung der Ebene
		Slope Angle: Neigung der Ebene
	
	-Ellipsoid:
		x,y Koordinate des Punktes um den das Rotationsellipsoid erzeugt wird (In Qgis ablesen, aktuell EPSG 32633 Koordinaten)
		max_depth: Maximale Tiefe des Scarps (quasi max. Höhe/Tiefe in m der Release Area)
		semi_major_axis, semi_minor_axis: Radien der Ellipse (in m)
-Nach Ausführen des Skripts Output Files in QGIS laden
