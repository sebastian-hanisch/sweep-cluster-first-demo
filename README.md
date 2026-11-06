# Sweep und Cluster-first – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-sweep-cluster-first-demo.streamlit.app/)** -->

Sechstes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt; Stück 2 ([riesentouren-erzeugen-demo](https://github.com/sebastian-hanisch/riesentouren-erzeugen-demo)) baut solche Reihenfolgen, Stück 3 ([split-gegen-fuellen-demo](https://github.com/sebastian-hanisch/split-gegen-fuellen-demo)) vergleicht den Split mit „Füllen bis voll“, Stück 4 ([savings-gegen-split-demo](https://github.com/sebastian-hanisch/savings-gegen-split-demo)) und Stück 5 ([savings-varianten-demo](https://github.com/sebastian-hanisch/savings-varianten-demo)) legen Routen zusammen. Dieses Stück geht den anderen Weg: **erst Gruppen bilden, dann je Gruppe die Reihenfolge** (cluster-first, route-second), am Beispiel des **Sweeps**.

## Kernfrage

Wo scheitert „erst Gruppen, dann Reihenfolge“? Die Demo zeigt den Sweep Schritt für Schritt (Winkelfolge um das Depot, Startkunde und Richtung, „Füllen bis voll“ als Schnitt, Rundreise je Cluster), alle Starts auf einer Instanz, die Zerlegung der Verluste (Gruppenbildung, Schnitt, Reihenfolge im Cluster), den Vergleich mit Savings und Einfügen nach Split mit **derselben Rundreise je Route** und Bänder über feste Instanzen bis 100 Kunden mit Aufteilung nach Depotlage, Kartenart, Kapazität und Routenlänge.

## Modell

Wie in den Stücken 1 bis 5: ein Depot, n Kunden mit ganzzahliger Nachfrage, gleiche Fahrzeuge der Kapazität Q (ohne Flottengrenze), euklidische Entfernungen; die Kapazität folgt aus der **Auslastung** (aufgerundet Gesamtnachfrage geteilt durch Zielroutenzahl mal Auslastung, mindestens die größte Nachfrage). **Sweep:** die Kunden nach dem Polarwinkel um das Depot ordnen (0 bis 2π gegen den Uhrzeigersinn ab Osten; Gleichstand: kleinerer Abstand, dann kleinere Nummer; Kunde auf dem Depot: Winkel 0), den Kreis bei einem Startkunden öffnen und in einer der beiden Richtungen lesen, durch „Füllen bis voll“ (Stück 3) in Cluster schneiden. **Zweiter Schritt:** die Winkelfolge je Cluster oder die kürzeste Rundreise (exakt bis 12 Kunden je Cluster, darüber 2-opt und Or-opt ab der Winkelfolge). **Fester Start:** der Kunde mit dem kleinsten Winkel, gegen den Uhrzeigersinn; **bester Start:** das Minimum über alle 2n Starts. **Schnittoptimum:** die beste Zerlegung der zyklischen Winkelfolge in zusammenhängende Cluster mit Rundreise je Cluster (ein kürzester Weg im Hilfsgraphen von Stück 1; nach dem Namen ein Sektor-Petal). **„+ Rundreise“:** jede Route eines Plans von Savings oder Einfügen nach Split neu als kürzeste Rundreise. Formeln und der Zählsatz stehen im 📐-Expander der App.

## Methodik

- **Kern** (`swp_algorithm.py`): aus Stück 5 kopiert und umbenannt (Split, Hilfsgraph, exakter Löser mit Held–Karp, kürzeste Rundreise); Erzeuger Einfügen nach Split in `swp_construct.py`; Savings in `swp_savings.py` (aus Stück 5, unverändert).
- **Sweep** (`swp_sweep.py`): neu: Winkelfolge, Drehung und Richtung, „Füllen bis voll“, kürzeste Rundreise je Cluster (exakt als Teilmengen-DP, vektorisiert; Heuristik darüber), Sweep über alle Starts, Winkelfolge + Split, Schnittoptimum, Prüfung „Sweep-Zerlegung“, Zählformeln.
- **Fünf Experimente:** Sweep Schritt für Schritt (Karte mit Schnittstrahlen); der Start entscheidet; wo verliert die Gruppenbildung; Sweep gegen Savings gegen Einfügen nach Split (mit gleicher Rundreise); Bänder über feste Instanzen.
- **Bänder** (`swp_bands.json`, erzeugt von `generate_precomputed.py`): die Instanzen, Referenzen und Kosten von Einfügen nach Split und Savings aus Stück 5 (`svv_bands.json`), nur Zellen mit Referenz: n = 10 und n = 12 (Auslastung 60, 75, 90, 98 %) mit je 80 Instanzen und exaktem Optimum, n = 25, 50, 100 (Auslastung 90 %) mit je 32 Instanzen und der Referenz PyVRP, dazu kurze Routen (n = 50, 8 Zielrouten, Auslastung 90 und 98 %); vier Zellen (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke). Bei n = 100 steht der beste Start nur über jede fünfte Startposition, das Schnittoptimum bis n = 25, Einfügen nach Split + Rundreise bis n = 50.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Seeds (Abstand zum Optimum beziehungsweise zur PyVRP-Referenz in Prozent: Median / Mittel / Maximum; „gepaart“ heißt Sweep billiger / gleich / teurer auf denselben Instanzen; vier Zellen zusammen), nachgerechnet in `tests/test_claims.py`, `tests/test_bands.py`, `tests/test_algorithm.py` und `tests/test_oracle_sweep.py`. Die Zahlen wurden in der Planung mit eigenen Skripten unabhängig vorgerechnet und stimmen überein. Ab 25 Kunden ist die Referenz PyVRP (keine bewiesene Untergrenze).

**Sweep gegen Savings und Einfügen nach Split, alle mit derselben Rundreise je Route**

| Zelle (n, Auslastung, Zielrouten) | Sweep, fester Start + Rundreise | Sweep, bester Start + Rundreise | Savings λ = 1 + Rundreise | Bestes von 9 λ + Rundreise | Einfügen nach Split + Rundreise | Sweep (bester Start) gegen Savings + Rundreise: billiger / gleich / teurer |
|---|---|---|---|---|---|---|
| n = 10, 90 %, 3 | 6,1 / 10,8 / 49,2 | **1,3 / 4,3 / 21,9** | 0,0 / 1,6 / 15,0 | 0,0 / 0,9 / 11,1 | 0,0 / 0,9 / 10,0 | 20 / 17 / 43 |
| n = 12, 60 %, 3 | 3,6 / 6,2 / 54,9 | **0,0 / 1,4 / 14,2** | 0,0 / 1,4 / 12,0 | 0,0 / 0,8 / 6,7 | 0,0 / 1,1 / 13,5 | 26 / 30 / 24 |
| n = 12, 75 %, 3 | 11,7 / 12,6 / 31,9 | **3,7 / 4,7 / 17,0** | 0,0 / 2,0 / 15,6 | 0,0 / 1,1 / 12,1 | 0,0 / 1,5 / 10,7 | 16 / 7 / 57 |
| n = 12, 90 %, 3 | 7,9 / 12,5 / 55,7 | **2,3 / 4,2 / 25,9** | 0,3 / 1,5 / 9,9 | 0,0 / 0,8 / 7,9 | 0,0 / 1,5 / 15,3 | 25 / 8 / 47 |
| n = 12, 98 %, 3 | 18,4 / 18,8 / 63,5 | **7,2 / 8,7 / 28,6** | 1,9 / 4,7 / 26,5 | 0,2 / 1,9 / 15,9 | 0,8 / 2,5 / 15,7 | 20 / 7 / 53 |
| n = 25, 90 %, 3 | 6,9 / 7,4 / 25,1 | **1,3 / 3,1 / 22,2** | 1,3 / 2,3 / 10,6 | 0,5 / 1,2 / 6,6 | 2,6 / 3,6 / 18,4 | 13 / 6 / 13 |
| n = 50, 90 %, 3 | 6,6 / 9,5 / 34,4 | **2,9 / 4,1 / 21,6** | 5,4 / 5,5 / 15,5 | 2,1 / 3,0 / 12,8 | 5,7 / 5,7 / 13,2 | 23 / 0 / 9 |
| n = 100, 90 %, 3 | 7,0 / 8,3 / 24,3 | **4,5 / 4,7 / 14,6** | 7,1 / 6,8 / 14,6 | 4,0 / 4,2 / 11,2 | – | 23 / 0 / 9 |
| n = 50, 90 %, 8 | 14,8 / 14,8 / 27,5 | **9,9 / 10,6 / 26,1** | 2,9 / 3,2 / 7,2 | 2,2 / 2,4 / 5,7 | 4,6 / 5,4 / 13,8 | 2 / 0 / 30 |
| n = 50, 98 %, 8 | 18,5 / 18,5 / 30,9 | **14,1 / 14,1 / 28,9** | 3,3 / 3,9 / 11,7 | 1,9 / 2,5 / 6,8 | 5,4 / 6,2 / 13,3 | 1 / 0 / 31 |

| Frage | Befund |
|---|---|
| **Winkelfolge als Route taugt nicht** | Sweep, fester Start, Reihenfolge der Winkel in jedem Cluster: Median **11,3 / 16,4 / 41,1 / 83,8 / 145,5 %** bei n = 10 / 12 (90 %) / 25 / 50 / 100 (3 Zielrouten). Mit kürzester Rundreise je Cluster 6,1 / 7,9 / 6,9 / 6,6 / 7,0 %. Mit dem besten Start: Winkelfolge 4,4 / 9,0 / 28,2 / 68,3 / 132,3 %, Rundreise 1,3 / 2,3 / 1,3 / 2,9 / 4,5 % |
| **Winkelfolge als Riesentour mit Split** | Bester Start, optimaler Split (Stück 1): 4,4 / 9,0 / 28,2 / 65,8 / 129,4 % bei n = 10 / 12 / 25 / 50 / 100, gegen Einfügen nach Split 0,0 / 0,6 / 3,3 / 8,3 / 11,7 %; gepaart gegen Einfügen nach Split 9 / 3 / 68, 14 / 2 / 64, 2 / 0 / 30, 0 / 0 / 32, 0 / 0 / 32. Benachbarte Kunden im Winkel liegen im Abstand zum Depot weit auseinander: Die Winkelfolge ist eine schwache Riesentour |
| **Der Start zählt** | Fester Start gegen bester von 2n Starts, jeweils mit Rundreise: n = 10 / 12 / 25 / 50 / 100: 6,1 / 7,9 / 6,9 / 6,6 / 7,0 % gegen 1,3 / 2,3 / 1,3 / 2,9 / 4,5 % (n = 100: jeder fünfte Start); kurze Routen 14,8 gegen 9,9 % (90 %). Der Preis sind 2n Rundreisen statt einer |
| **Fairer Vergleich schrumpft den scheinbaren Vorsprung** | Ohne die Rundreise je Route für Savings gewinnt der Sweep (bester Start) bei n = 25 in 20 von 32, bei n = 50 in 24 von 32 Instanzen gegen Savings mit λ = 1; mit derselben Rundreise je Route ist es bei n = 25 gleichauf (13 / 6 / 13) und bei n = 50 gegen das Beste von 9 λ weg: 16 / 0 / 16. Ein Teil des Sweep-Vorsprungs ist die Rundreise, nicht die Gruppenbildung |
| **Bei wenigen dicken Keilen ebenbürtig** | n = 50, 3 Routen: Sweep bester Start 2,9 % gegen Savings mit Rundreise 5,4 % (23 / 0 / 9), gegen das Beste von 9 λ mit Rundreise 2,1 % (16 / 0 / 16 gleichauf); n = 100: 4,5 gegen 7,1 % (23 / 0 / 9), gegen das Beste von 9 λ 4,0 % (17 / 0 / 15, Median des Unterschieds −0,4 %). Bei n ≤ 12 liegt Savings mit Rundreise vorn (n = 12, 90 %: 25 / 8 / 47, Median des Unterschieds +1,7 %), bei n = 25 gleichauf |
| **Kurze Routen** (n = 50, 8 Zielrouten) | Sweep bester Start 9,9 % (90 %) und 14,1 % (98 %) gegen Savings mit Rundreise 2,9 und 3,3 %; Sweep billiger in 2 und 1 von 32 Instanzen. Acht dünne Keile zerschneiden die Gruppen, die ein Plan braucht |
| **Enge Kapazität: die Fahrzeuggrenze** | Der Sweep mit festem Start braucht mehr Routen als die Mindestroutenzahl m in 1 / 0 / 20 / **67** von 80 Instanzen (n = 12 bei 60 / 75 / 90 / 98 %), 22 von 80 bei n = 10, 0 von 32 bei n = 25, 50 und 100, 1 und **30** von 32 bei den kurzen Routen (90 und 98 %); über alle Starts im Mittel 2 / 0 / 22 / 78 % der Starts (n = 12). Mit der Flottengrenze m wäre der Sweep dort nicht zulässig. Das Optimum fährt bei 98 % in 14 von 80 Instanzen mehr als m Routen. Der Abstand wächst mit: Sweep bester Start + Rundreise bei n = 12 und 60 / 75 / 90 / 98 %: 0,0 / 3,7 / 2,3 / **7,2 %** gegen Savings + Rundreise 0,0 / 0,0 / 0,3 / 1,9 % |
| **Depot in der Ecke** | Sweep bester Start + Rundreise, Depot Mitte gegen Ecke (Median): n = 10: 0,0 / 3,7; n = 12 (90 %): 0,1 / 4,4; n = 12 (98 %): 5,2 / 10,4; n = 25: 0,3 / 2,6; n = 50 (3 Routen): 1,4 / 3,7; n = 100: 3,7 / 4,8; kurze Routen: 7,8 / 12,6 (90 %) und 9,8 / 17,0 (98 %). In jeder gemessenen Zelle ist die Ecke für den Sweep schlechter; bei Savings + Rundreise ist der Unterschied nicht gerichtet (n = 25: 1,3 / 1,2, kurze Routen 3,8 / 2,4) |
| **Zerlegung der Verluste** (Median, n ≤ 25) | *Cluster-Verlust* (Schnittoptimum gegen die Referenz): n = 12 bei Auslastung 60 / 75 / 90 / 98 %: **0,0 / 2,3 / 2,3 / 6,1 %**, n = 10 1,3 %, n = 25 1,3 %. *Schnitt-Verlust* des festen Starts gegen das Schnittoptimum: 1,0 / 6,3 / 3,4 / 6,8 % (n = 12). *Routing-Verlust* der Winkelfolge gegen die Rundreise je Cluster bei festem Start: 10,6 / 5,4 / 6,0 / 3,8 % (n = 12) und 26,9 % (n = 25) |
| **Das Optimum ist oft kein Sweep** | Das exakte Optimum besteht aus Routen, die zusammenhängende Stücke der zyklischen Winkelfolge sind, in 39 / 26 / 25 / 16 von 80 Instanzen (n = 12 bei 60 / 75 / 90 / 98 %) und in 28 von 80 bei n = 10; der Sweep kann es sonst nie erreichen |
| **Wie wenige Gruppierungen sieht der Sweep?** | Zerlegungen eines Kreises aus n Kunden in k zusammenhängende Gruppen: C(n, k) (k ≥ 2); alle Zerlegungen in k Gruppen: die Stirling-Zahl zweiter Art. Für n = 12, k = 3: 220 gegen 86 526 (an kleinen n gegen die Aufzählung geprüft) |
| **Handinstanz** (n = 6, Depot in der Ecke (0, 0), Kapazität 11, Optimum 77,79) | Das Optimum (2 6 1 4) und (3 5) ist keine Sweep-Zerlegung: Kunde 5 liegt bei (2, 1) nahe am Depot im Winkelbereich der Kunden 4 und 1, gehört aber zum fernen Kunden 3. Winkelfolge 4, 5, 1, 2, 6, 3; Füllen bis voll (Last 11): {4, 5, 1, 2} und {6, 3}; mit Rundreise je Cluster **93,73** (+20,5 %); bester Start **91,54** (+17,7 %); Winkelfolge + Split 104,26 mit drei Routen; Savings und Einfügen nach Split treffen 77,79 |
| **Voreinstellung** (n = 8, zufällig verteilt, Depot in der Mitte, Auslastung 90 %, Seed 0) | Optimum 444,40; Einfügen nach Split trifft es, ist aber keine Sweep-Zerlegung; Sweep fester Start 517,11 (+16,4 %, 4 Routen statt 3), bester Start und Schnittoptimum 492,17 (+10,8 %); Savings 459,10 (+3,3 %) |

## Ehrliche Grenzen

- Die Aussagen gelten für die gemessenen Größen (10, 12, 25, 50, 100 Kunden), drei Zielrouten (und 8 bei n = 50) und die drei Kartenarten; sie sind keine Aussagen über echte Daten oder andere Zielroutenzahlen.
- Ab 25 Kunden ist die Referenz PyVRP (5 Sekunden, ein Seed), eine gute Lösung und keine bewiesene Untergrenze; nur Zellen mit Referenz sind in den Bändern.
- Die Rundreise je Cluster ist exakt bis 12 Kunden, darüber eine Heuristik (2-opt und Or-opt); bei n = 50 und 100 sind die Cluster größer. Alle Verfahren bekommen dieselbe Regel, aber nicht die bestmögliche.
- Bei n = 100 steht der beste Start nur über jede fünfte Startposition (200 Starts würden über zwei Stunden rechnen), das Schnittoptimum nur bis n = 25, Einfügen nach Split + Rundreise nur bis n = 50.
- „Gleichauf“ heißt hier: die Mediane des gepaarten Unterschieds liegen weniger als einen Prozentpunkt auseinander; bei vielen gleich teuren Paaren ist der Median 0,0 %.
- Der Sweep ist ohne Flottengrenze gerechnet; „braucht mehr als die Mindestroutenzahl“ ist die Zahl der Instanzen, in denen er mit einer Flottengrenze in Höhe der Mindestroutenzahl nicht zulässig wäre.
- Das Schnittoptimum ist nach dem Namen ein Sektor-Petal (Ryan, Hjorring und Glover, 1993; nur als Name gesehen); Fisher und Jaikumar (1981) sind nicht gebaut. Keine Zahl aus der Literatur wird übernommen.
- Die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet ebenfalls einen Sweep; ihre Zahlen werden nicht übernommen.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge (die Flottengrenze fehlt), euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.
- „Sweep“ meint die Fassung mit Winkelfolge um das Depot, „Füllen bis voll“ als Schnitt und einem Startkunden (beide Richtungen); das Depot bestimmt den Winkel, ein Kunde auf dem Depot hat per Setzung den Winkel 0. Das Verfahren ist nach Sekundärquellen übernommen (Gillett und Miller, 1974), nicht an der Originalarbeit geprüft.
- „Rundreise je Cluster“ meint die kürzeste Rundreise durch das Depot und alle Kunden des Clusters: exakt bis 12 Kunden, darüber eine Heuristik (2-opt und Or-opt ab der Winkelfolge, nie unter der kürzesten Rundreise). Savings und Einfügen nach Split bekommen für den Vergleich dieselbe Regel („+ Rundreise“).

**Grenzen**
- Live rechnet die App bis zu 12 Kunden mit exaktem Optimum. Die Bänder gelten für 10 und 12 Kunden (exaktes Optimum, je 80 feste Instanzen) und für 25, 50 und 100 Kunden (je 32 feste Instanzen, Referenz PyVRP, nicht bewiesen optimal) bei drei Zielrouten sowie für 50 Kunden mit 8 Zielrouten; nur Zellen mit Referenz.
- Bei 100 Kunden steht der beste Start nur über jede fünfte Startposition (beide Richtungen); das Schnittoptimum steht bis 25 Kunden, Einfügen nach Split + Rundreise bis 50 Kunden.
- Die Referenz PyVRP (5 Sekunden, ein Seed) ist eine gute Lösung, keine Untergrenze: Abstände zur Referenz sind keine Abstände zum Optimum.
- Der Sweep ist ohne Flottengrenze gerechnet; „braucht mehr als die Mindestroutenzahl“ zählt, wie oft er bei einer Flottengrenze in Höhe der Mindestroutenzahl nicht zulässig wäre.
- Das Schnittoptimum ist nach dem Namen ein Sektor-Petal (Ryan, Hjorring und Glover, 1993); die Gleichsetzung ist nicht geprüft. Fisher–Jaikumar ist nicht gebaut.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über feste Instanzen, keine Trends und keine Aussagen über andere Kartenarten oder Zielroutenzahlen; zu n steht keine Trendaussage in der App.
- Die Rundreise je Cluster ist ab 13 Kunden eine Heuristik; der Vergleich mit Savings und Einfügen nach Split nutzt dieselbe Regel, nicht eine bessere.
- Der Winkel bestimmt die Folge; bei Kunden auf einer Geraden durch das Depot entscheidet der Abstand, dann die Nummer, und bei Rundungsfehlern können Gleichstände anders ausfallen.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Preset „Der Start entscheidet“:** Die Planung zeigte Seed 0 mit Depot in der Ecke (+57,5 % beim festen Start); das ist genau die Voreinstellung mit geändertem Depot und hätte die Hervorhebung im Schnellstart verwischt. Das Preset nutzt Seed 6 (fester Start +20,0 %, 4 statt 3 Routen, der beste Start trifft das Optimum).
- **Phase-0-Zahlen reproduziert:** Alle Zahlen der Planung (Sweep, Schnittoptimum, Savings und Einfügen nach Split mit Rundreise) kommen aus dem neuen Kern identisch heraus; die Planungsskripte benutzten einen Zwischenspeicher mit der Speicheradresse der Instanz als Schlüssel, der bei wiederverwendeten Adressen falsche Werte hätte liefern können; der neue Kern speichert nach der Instanz selbst, und die Stichprobe der Nachrechnung fand keine Abweichung.
- **Verdikt-Schwelle für den Sweep gegen Savings:** Das Verdikt benutzt dieselbe „gleichauf“-Regel wie Stück 4 und 5 (Mediane unter einem Prozentpunkt); bei n = 25 sind Sweep und Savings mit Rundreise gleichauf, obwohl die gepaarten Zählungen 13 / 6 / 13 sind.
- **Savings-Plan nach der Rundreise:** In dieser Demo heißt „Savings + Rundreise“ jede Route des Savings-Plans (λ = 1) neu als kürzeste Rundreise; „Bestes von 9 λ + Rundreise“ nimmt je Instanz den besten der neun neu optimierten Pläne. Das ist eine Setzung dieser Demo.
- **Winkel bei Gleichstand:** Kunden mit gleichem Winkel stehen nach dem Abstand, dann der Nummer; die Tests für das Orakel nutzen deshalb nur Familien mit stetigen Koordinaten.

## Verifikation

- **Kern:** Winkel aus atan2, Winkelfolge, Drehung und Füllen, alle 12 Startvarianten der Handinstanz mit Cluster und Kosten, eine Cluster-Rundreise aus Wurzeln, bester Start, Winkelfolge + Split, Schnittoptimum, „ist keine Sweep-Zerlegung“ mit den Winkelbereichen der Routen, Zählformeln (`tests/test_algorithm.py`).
- **Orakel:** Winkelfolge mit math.atan2 und eigener Sortierung; Füllen gegen eine eigene Schleife; Rundreise je Cluster gegen die Aufzählung aller Reihenfolgen (bis 7 Kunden) und die Heuristik nie unter der exakten Länge; Schnittoptimum gegen die Aufzählung aller Zerlegungen der zyklischen Folge in zusammenhängende Stücke; Zählformeln gegen die Aufzählung; „Sweep-Zerlegung“ gegen eine direkte Prüfung; Dominanz (Minimum über alle Reihenfolgen von Split gleich Optimum) (`tests/test_oracle_sweep.py`).
- **Eigenschaften:** Zulässigkeit jedes Starts, Rundreise nie schlechter als die Winkelfolge, bester Start nie schlechter als jeder Start, Schnittoptimum nie schlechter als jeder Sweep und selbst eine Sweep-Zerlegung, Verschieben, Skalieren, Drehen, Spiegeln und Umnummerieren, ein Cluster bei unbegrenzter Kapazität, Rundreise-Verbesserung nie schlechter, Reihenfolge der Strategien (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Kunden, Kunde auf dem Depot, alle Kunden auf einem Strahl, Nachfrage gleich Kapazität, Kapazität für alle, Depot in der Ecke (ein Quadrant), Cluster über der Grenze der exakten Rundreise, jede zehnte Startposition bei 100 Kunden, Reglergrenzen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau, Stimmigkeit und gegen eine frische Rechnung je Zelle (`tests/test_bands.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Start-, Richtungs- und Reihenfolgeregler, Planauswahl, Bänder inklusive kurzer Routen, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

238 Tests. Laufzeit lokal etwa zwei Minuten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `swp_bands.json` aus den Instanzen und Referenzen von Stück 5 (Teile lassen sich parallel rechnen) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `swp_algorithm.py` | Kern: Split, Hilfsgraph, exakter Löser, Held–Karp, kürzeste Rundreise |
| `swp_bands.json` | vorberechnete Bänder (Größen, Auslastungen, kurze Routen; je vier Zellen) |
| `swp_constants.py` | Regler-Grenzen, Verfahren, Bänder, Farben, Presets, Annahmentext |
| `swp_construct.py` | Einfügen nach Split und fernstes Einfügen |
| `swp_evaluation.py` | Analyse, Bänder, Kennzahlen, Verdikt-Logik |
| `swp_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `swp_pdf_export.py` | PDF-Export des Ergebnisses |
| `swp_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `swp_savings.py` | Savings (aus Stück 5, für den Vergleich) |
| `swp_scenario.py` | Instanzen (aus Stück 1, mit Auslastung als Parameter) |
| `swp_sweep.py` | Sweep, Rundreise je Cluster, Schnittoptimum, Prüfung und Zählformeln |
| `swp_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanzen, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Fisher–Jaikumar** (Zuordnung der Kunden zu Fahrzeugen statt nach dem Winkel): nur als Name genannt.
- **Petal-Verfahren mit beliebigen Blütenblättern** (Mengenzerlegung): hier nur das Schnittoptimum mit Sektoren.
- **Flottengrenze:** der Sweep wird ohne Grenze gerechnet; die Zahl der Instanzen mit mehr als der Mindestroutenzahl ist das Maß.
- **Verbesserung zwischen den Routen** (Austausch, Verschieben von Kunden): die Verfahren bleiben Konstruktion; Nachbarschaften stehen in den Demos zu VRP-Nachbarschaften und in der Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/).
- **Zeitfenster** (Stück 8): der Winkel ist dann nur ein Teil der Ordnung.
- **Asymmetrische Entfernungen und verschiedene Fahrzeugtypen:** nur symmetrische Entfernungen und gleiche Fahrzeuge.
- **Instanzen über 12 Kunden live:** größere Instanzen stehen nur in den vorberechneten Bändern.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
