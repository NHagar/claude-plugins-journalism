"""
Sportförderung in Deutschland – Haushalte und Etats
Bundesministerien, Landesministerien und Kommunen
Erstellt auf Basis öffentlich verfügbarer Haushaltsdaten (Stand: 2024/2025)

Quellen:
- Bundeshaushalt BMI Einzelplan 06, Kapitel 0602 (bundeshaushalt.de)
- Bundestag Pressemitteilungen (bundestag.de)
- DOSB-Berichte (dosb.de)
- Landesregierungen und Landessportbünde
- Sportministerkonferenz-Beschlüsse
- Stadtportale / kommunale Haushalte
"""

import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

# ─── Datenbasis ────────────────────────────────────────────────────────────────
# Spalten: Ebene | Bundesland | Träger / Ministerium | Einzelplan / Kapitel |
#          Titel / Haushaltsstelle | Maßnahme / Beschreibung |
#          Förderbereich | Betrag_Mio_EUR | Haushaltsjahr | Quelle / Anmerkung

DATA = [
    # ── BUND ──────────────────────────────────────────────────────────────────
    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602, TGr. 02", "Gesamtsportetat BMI",
     "Gesamter Sportetat des BMI (Titelgruppe 02) – Spitzen- und Breitensport",
     "Spitzensport + Breitensport", 282.55, 2024,
     "Bundestag Pressemitteilung; BMI Jahresbericht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602, TGr. 02", "Zentrale Maßnahmen Sport",
     "Zentrale Maßnahmen auf dem Gebiet des Sports (inkl. Olympiakader, WM-Vorbereitung, Verbände)",
     "Spitzensport", 177.88, 2024,
     "BMI Förderübersicht; bmi.bund.de"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Olympiakader / Perspektivkader / WM-Vorbereitung",
     "Förderung olympischer Kader und Vorbereitung auf internationale Wettkämpfe",
     "Spitzensport", 50.32, 2025,
     "Bundestag hib 2025 (Planansatz 2025)"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Leistungssportpersonal (Trainer, Management)",
     "Mischfinanzierte Trainer und Managementpersonal der Bundesverbände",
     "Spitzensport", 58.46, 2025,
     "BMI Förderentscheidung Sept. 2024; Zeitraum 2025–2028 je ~39 Mio. €"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Olympiastützpunkte und Trainingszentren",
     "Betrieb und Investitionen Olympiastützpunkte (OSP) sowie Bundesleistungszentren",
     "Spitzensport", 58.10, 2025,
     "Bundestag hib 2025 (Planansatz 2025)"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602, Tit. 684", "Nicht-olympische Verbände",
     "Zuwendungen an Verbände nicht-olympischer Sportarten (Breitenwirkung, Inklusion)",
     "Spitzensport", 13.50, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602, Tit. 683", "Sportgroßveranstaltungen",
     "Beteiligung des Bundes an der Ausrichtung von Sportgroßveranstaltungen in Deutschland",
     "Spitzensport", 7.31, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "IAT und FES – Projektförderung",
     "Institut für Angewandte Trainingswissenschaften (IAT) und Institut für Forschung und Entwicklung von Sportgeräten (FES)",
     "Spitzensport", 7.09, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "NADA – Dopingbekämpfung",
     "Zuschuss an die Nationale Anti Doping Agentur (NADA)",
     "Spitzensport", 10.38, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "WADA – Zuschuss",
     "Beitrag Deutschlands an die World Anti-Doping Agency (WADA)",
     "Spitzensport", 1.26, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Zentrum Safe Sport",
     "Unabhängige Anlaufstelle für Betroffene von Missbrauch im Sport",
     "Spitzensport", 1.25, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Spitzensport-Agentur (Aufbau)",
     "Anschubfinanzierung für die neue Nationale Spitzensport-Agentur",
     "Spitzensport", 0.20, 2024,
     "BMI Förderübersicht 2024"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Sportstätten-Infrastruktur (Bauunterhaltung)",
     "Unterrichtung, Ausstattung und Bauunterhaltung von Sportstätten für den Höchstleistungssport",
     "Spitzensport", 18.82, 2024,
     "BMI; Vorjahr: 24,6 Mio. €"),

    ("Bund", "Gesamt (Bund)", "Bundesministerium des Innern (BMI)",
     "EP 06, Kap. 0602", "Leistungssportpersonal – Jahresplanung",
     "Jährliche Förderentscheidung für Leistungssportpersonal (Herbstplanung)",
     "Spitzensport", 41.00, 2024,
     "BMI Förderentscheidung Dez. 2024"),

    ("Bund", "Gesamt (Bund)", "BMFSFJ – Bundesministerium für Familie",
     "EP 17, Kinder- und Jugendplan (KJP)", "Kinder- und Jugendplan – Sport / Breitensport",
     "Förderung von Jugend- und Breitensport durch Sportverbände und -organisationen im Rahmen des KJP",
     "Breitensport", 194.50, 2024,
     "Bundestag; Vorjahr 2023: 239,1 Mio. €"),

    ("Bund", "Gesamt (Bund)", "BMWSB – Bundesbauministerium",
     "EP 25, Investitionspakt Sportstätten", "Investitionspakt kommunale Sportstätten",
     "Bundesanteil am Investitionspakt zur Förderung von Sportstätten (kommunal)",
     "Breitensport", 60.50, 2024,
     "BMWSB Pressemitteilung; bisp-sportinfrastruktur.de"),

    ("Bund", "Gesamt (Bund)", "BMWSB – Bundesbauministerium",
     "EP 25, Sondervermögen KTF", "Sanierung kommunaler Einrichtungen (Sport, Jugend, Kultur)",
     "Bundesprogramm zur Sanierung kommunaler Sport-, Jugend- und Kultureinrichtungen aus dem KTF",
     "Breitensport", 364.60, 2024,
     "Bundestag Drucksache 20/14971"),

    # ── LÄNDER ────────────────────────────────────────────────────────────────
    # BAYERN
    ("Land", "Bayern", "Bayerisches Staatsministerium des Innern, für Sport und Integration (StMI)",
     "EP 03 (StMI)", "Gesamtvolumen Sportförderung Bayern",
     "Breiten- und Nachwuchsleistungssportförderung inkl. Vereinspauschale, Verbandsförderung, Sondermaßnahmen",
     "Spitzensport + Breitensport", 110.60, 2024,
     "StMI Bayern; blsv.de – Sportförderung auf Rekordniveau 2024"),

    ("Land", "Bayern", "Bayerisches Staatsministerium des Innern, für Sport und Integration (StMI)",
     "EP 03 (StMI)", "Seepferdchen-Gutscheinprogramm",
     "Schwimmkurse für Kinder – staatlich gefördertes Gutscheinprogramm",
     "Breitensport", 10.80, 2024,
     "StMI Bayern Pressemitteilung 2024"),

    ("Land", "Bayern", "Bayerisches Staatsministerium des Innern, für Sport und Integration (StMI)",
     "EP 03 (StMI)", "Sonderfördermaßnahmen Sport",
     "Besondere Sportfördermaßnahmen (Integration, Inklusion, Projekte)",
     "Breitensport", 4.10, 2024,
     "StMI Bayern Pressemitteilung 2024"),

    # NORDRHEIN-WESTFALEN
    ("Land", "Nordrhein-Westfalen",
     "Staatskanzlei NRW, Abt. Sport und Ehrenamt / MHKBG NRW",
     "NRW-Sportmilliarde", "NRW-Sportmilliarde – Kommunale Sportstätten & Schwimmbäder",
     "Investitionsprogramm für Neubau und Sanierung kommunaler Sportstätten (600 Mio.) + Sportpauschale (375 Mio.)",
     "Breitensport", 975.00, 2024,
     "Staatskanzlei NRW; lsb.nrw – Sportmilliarde (Laufzeit mehrere Jahre)"),

    ("Land", "Nordrhein-Westfalen",
     "Staatskanzlei NRW / Landessportbund NRW (LSB)",
     "LSB NRW – Sportförderung", "Laufende Sportförderung über den LSB NRW",
     "Jährliche institutionelle Sportförderung (Verbände, Vereine, Jugend) über den LSB NRW",
     "Breitensport", 66.00, 2024,
     "lsb.nrw – Rund eine Milliarde Euro für den Sport in NRW"),

    ("Land", "Nordrhein-Westfalen",
     "Ministerium für Heimat, Kommunales, Bau und Digitalisierung NRW (MHKBD)",
     "Investitionspakt Sportstätten NRW", "Investitionspakt Sportstätten – 66 Projekte",
     "50 Mio. € Bundesmittel + Landesmittel für 66 Sportstättenprojekte in Städten und Gemeinden",
     "Breitensport", 50.00, 2024,
     "MHKBD.NRW Pressemitteilung 2024"),

    ("Land", "Nordrhein-Westfalen",
     "Staatskanzlei NRW",
     "EU-Programm REACT-EU (NRW)", "Digitalisierungsoffensive Breitensport NRW",
     "EU-Mittel für digitale Infrastruktur gemeinnütziger Sportorganisationen in NRW",
     "Breitensport", 30.00, 2024,
     "land.nrw – Digitalisierungsoffensive Sportorganisationen"),

    # BERLIN
    ("Land", "Berlin",
     "Senatsverwaltung für Inneres und Sport Berlin",
     "Berliner Haushalt (Sportförderung)", "Sportförderung Berlin – Gesamtvolumen Doppelhaushalt",
     "Förderung von Sport-/Breitensport aus Berliner Haushalt und Lottomitteln (Doppelhaushalt)",
     "Breitensport", 33.00, 2024,
     "Tagesspiegel; Senat reformiert Sportförderung Berlin"),

    # SACHSEN
    ("Land", "Sachsen",
     "Sächsisches Staatsministerium des Innern (SMI)",
     "Sächsischer Haushalt – Sportförderung", "Sportförderung Sachsen 2022",
     "Breiten-, Nachwuchs- und Leistungssportförderung inkl. Verbände und Vereine",
     "Spitzensport + Breitensport", 26.30, 2022,
     "kreissportbund.net; Sachsen erhöht Sportförderung (Doppelhaushalt 2021/2022)"),

    ("Land", "Sachsen",
     "Sächsisches Staatsministerium des Innern (SMI)",
     "Sächsischer Haushalt – Sportförderung", "Sportförderung Sachsen 2021",
     "Breiten-, Nachwuchs- und Leistungssportförderung inkl. Verbände und Vereine",
     "Spitzensport + Breitensport", 25.70, 2021,
     "kreissportbund.net; Sachsen erhöht Sportförderung (Doppelhaushalt 2021/2022)"),

    # BRANDENBURG
    ("Land", "Brandenburg",
     "Ministerium für Bildung, Jugend und Sport Brandenburg (MBJS)",
     "Brandenburger Haushalt – Sportförderung", "Sportförderung Brandenburg 2022/2023",
     "Breiten- und Leistungssportförderung (Vereine, Projekte, Nachwuchs) – Doppelhaushalt",
     "Spitzensport + Breitensport", 59.30, 2022,
     "Landesregierung Brandenburg Pressemitteilung (59,3 Mio. für 2022+2023 gesamt)"),

    # BADEN-WÜRTTEMBERG
    ("Land", "Baden-Württemberg",
     "Ministerium für Kultus, Jugend und Sport Baden-Württemberg (KM BW)",
     "BW-Haushalt – Sportstättenförderung", "Sportstättenbau – 117 kommunale Projekte",
     "Zuschüsse für Neubau und Sanierung von Sporthallen und Freisportanlagen",
     "Breitensport", 18.30, 2024,
     "km.baden-wuerttemberg.de; Regierungspräsidium Stuttgart PM 2024"),

    # SACHSEN-ANHALT
    ("Land", "Sachsen-Anhalt",
     "Ministerium für Inneres und Sport Sachsen-Anhalt",
     "LSB Sachsen-Anhalt – Sportstättenförderung", "Vereinssportstättenbau Sachsen-Anhalt",
     "Förderung von Neubau und Sanierung von Vereinssportstätten (98 Bauvorhaben)",
     "Breitensport", 5.60, 2024,
     "lsb-sachsen-anhalt.de – Vereinssportstätten 2024 mit 5,6 Mio. € gefördert"),

    # SAARLAND
    ("Land", "Saarland",
     "Ministerium des Innern, für Sport, Infrastruktur und Kommunales Saarland",
     "Saarländischer Haushalt – Sportförderung", "Spitzensportförderung Saarland",
     "Zuwendungsbudget für den Spitzensport (erhöht um 250.000 €)",
     "Spitzensport", 0.33, 2024,
     "Homburg1.de; Olympische und Paralympische Spiele 2024 – Zuwendungen 1,1 Mio. € gesamt"),

    ("Land", "Saarland",
     "Ministerium des Innern, für Sport, Infrastruktur und Kommunales Saarland",
     "Saarländischer Haushalt – Sportveranstaltungen", "Sportveranstaltungen Saarland",
     "Förderbudget für besondere sportliche Veranstaltungen mit überregionalem Stellenwert",
     "Spitzensport + Breitensport", 0.71, 2024,
     "Homburg1.de Pressemitteilung 2024"),

    # HESSEN
    ("Land", "Hessen",
     "Hessisches Ministerium des Innern, für Sicherheit und Heimatschutz (HMdIS)",
     "Hessischer Haushalt – Sportförderung", "Sportprojektförderung Hessen Q1–Q3 2024",
     "Förderung von 1.001 Sportprojekten im Jahr 2024 (Stand nach Q3: 233 Projekte mit 10,6 Mio. €)",
     "Breitensport", 10.60, 2024,
     "familie.hessen.de; innen.hessen.de – 233 Sportprojekte mit 10,6 Mio. € gefördert (Q3 2024)"),

    # NIEDERSACHSEN
    ("Land", "Niedersachsen",
     "Niedersächsisches Ministerium für Inneres und Sport (MI Niedersachsen)",
     "Nds. Haushalt – Sportstättensanierung", "Sportstättensanierungsprogramm Niedersachsen",
     "Sanierung kommunaler und vereinseigener Sportstätten (80 Mio. kommunal + 20 Mio. Vereine)",
     "Breitensport", 100.00, 2019,
     "mi.niedersachsen.de – 100 Mio. Euro-Programm (Laufzeit 2019–2022)"),

    # SCHLESWIG-HOLSTEIN
    ("Land", "Schleswig-Holstein",
     "Ministerium für Inneres, Kommunales, Wohnen und Sport Schleswig-Holstein",
     "SH-Haushalt – Sportstättenförderung", "Sportstättensanierung Schleswig-Holstein",
     "Jährliche Förderung der Sportstättensanierung aus Landesmitteln (Schwerpunkt Schwimmsport)",
     "Breitensport", 2.00, 2024,
     "SPD Schleswig-Holstein Sportpolitik; Landeshaushalt SH 2024 (geschätzt Vorjahresbasis)"),

    ("Land", "Schleswig-Holstein",
     "Ministerium für Inneres, Kommunales, Wohnen und Sport Schleswig-Holstein",
     "SH-Haushalt – Sportförderung (Glücksspielmittel)", "Sportförderung aus Glücksspielmitteln SH",
     "Sportförderung über Lottomittel an den LSB Schleswig-Holstein",
     "Breitensport", 8.00, 2024,
     "SPD SH Sportpolitik; Wert von 2015: 8 Mio. €, Schätzwert 2024"),

    # ── KOMMUNEN ──────────────────────────────────────────────────────────────
    ("Kommune", "Bayern", "Landeshauptstadt München",
     "Stadthaushalt München – Sport", "Sportamt München – Betrieb öffentlicher Sportanlagen",
     "Betrieb und Unterhalt städtischer Sportstätten, Freibäder, Hallen durch Sportamt",
     "Breitensport", 85.00, 2024,
     "Münchner Stadthaushalt 2024 (Schätzwert auf Basis Mehrjahresplanung Sportamt)"),

    ("Kommune", "Bayern", "Landeshauptstadt München",
     "Stadthaushalt München – Sport", "Sportförderung Vereine und Verbände München",
     "Direkte Vereinsförderung, Jugend- und Breitensportförderung der Stadt München",
     "Breitensport", 15.00, 2024,
     "Stadthaushalt München 2024 (Schätzwert; offizielle Veröffentlichung Referat für Bildung und Sport)"),

    ("Kommune", "Nordrhein-Westfalen", "Stadt Köln",
     "Kölner Stadthaushalt – Sport", "Sportförderung Köln (Betrieb und Zuschüsse)",
     "Betrieb kommunaler Sportanlagen und Vereinsförderung durch die Stadt Köln",
     "Breitensport", 50.00, 2024,
     "Kölner Stadthaushalt 2024 (Schätzwert – Amt für Stadtentwicklung und Statistik)"),

    ("Kommune", "Nordrhein-Westfalen", "Stadt Dortmund",
     "Dortmunder Stadthaushalt – Sport", "Sportförderung Dortmund",
     "Kommunale Sportförderung inkl. Sportstättenunterhalt und Vereinsförderung",
     "Breitensport", 30.00, 2024,
     "Stadthaushalt Dortmund 2024 (Schätzwert)"),

    ("Kommune", "Hamburg", "Freie und Hansestadt Hamburg",
     "Hamburger Haushalt – Sport", "Bezirks- und Landesförderung Sport Hamburg",
     "Sportförderung über Behörde für Inneres und Sport sowie Bezirksämter Hamburg",
     "Breitensport", 45.00, 2024,
     "Behörde für Inneres und Sport Hamburg; Schätzwert auf Basis Sportbericht Hamburg"),

    ("Kommune", "Berlin", "Land Berlin (Bezirke)",
     "Berliner Bezirkshaushalte – Sport", "Bezirkliche Sportförderung Berlin",
     "Sportförderung und Sportstättenbetrieb durch die 12 Berliner Bezirke (additiv)",
     "Breitensport", 120.00, 2024,
     "Senatsverwaltung für Sport Berlin; Gesamtschätzung alle 12 Bezirke 2024"),

    ("Kommune", "Nordrhein-Westfalen", "Bundesstadt Bonn",
     "Bonner Stadthaushalt – Sport", "Sportförderung Bonn",
     "Kommunale Sportförderung (Sportstätten, Vereine, Jugend) in der Bundesstadt Bonn",
     "Breitensport", 12.00, 2024,
     "Stadt Bonn Haushaltsplan 2024 (Schätzwert)"),
]

# Spaltentitel
COLS_POSITIONEN = [
    "Ebene", "Bundesland", "Träger / Ministerium",
    "Einzelplan / Kapitel / Haushaltsstelle",
    "Titel / Maßnahme",
    "Beschreibung",
    "Förderbereich", "Betrag (Mio. €)", "Haushaltsjahr",
    "Quelle / Anmerkung"
]

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def header_fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)

def thin_border() -> Border:
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def apply_header_row(ws, row_num: int, values: list, fill_hex: str,
                     font_color: str = "FFFFFF"):
    fill = header_fill(fill_hex)
    font = Font(bold=True, color=font_color, size=10)
    border = thin_border()
    for col_num, val in enumerate(values, start=1):
        cell = ws.cell(row=row_num, column=col_num, value=val)
        cell.fill = fill
        cell.font = font
        cell.border = border
        cell.alignment = Alignment(wrap_text=True, vertical="center",
                                   horizontal="center")

def write_data_row(ws, row_num: int, values: list,
                   fill_hex: str | None = None):
    fill = header_fill(fill_hex) if fill_hex else None
    border = thin_border()
    for col_num, val in enumerate(values, start=1):
        cell = ws.cell(row=row_num, column=col_num, value=val)
        if fill:
            cell.fill = fill
        cell.border = border
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        # Währungsformat für Beträge
        if col_num == 8:  # Betrag-Spalte
            cell.number_format = '#,##0.00" Mio. €"'
            cell.alignment = Alignment(horizontal="right", vertical="top")

def autofit_columns(ws, max_width: int = 60):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                lines = str(cell.value).split("\n")
                for line in lines:
                    max_len = max(max_len, len(line))
        ws.column_dimensions[col_letter].width = min(max_len + 4, max_width)

# ─── Datei 1: Nach Haushaltspositionen ────────────────────────────────────────

def create_file_by_positionen():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sportförderung nach Positionen"

    # Titel-Zeile
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value = (
        "Sportförderung in Deutschland – Bundesministerien, Landesministerien und Kommunen "
        "(nach Haushaltspositionen, Stand 2024/2025)"
    )
    title_cell.font = Font(bold=True, size=13, color="1F3864")
    title_cell.alignment = Alignment(horizontal="center", vertical="center",
                                     wrap_text=True)
    ws.row_dimensions[1].height = 40

    # Hinweis-Zeile
    ws.merge_cells("A2:J2")
    hint_cell = ws["A2"]
    hint_cell.value = (
        "Hinweis: Beträge in Millionen Euro (Mio. €). Schätzwerte für kommunale Ebene "
        "sind als solche in der Quellspalte markiert. Primärquellen: BMI, Bundestag, "
        "Landesregierungen, Landessportbünde, DOSB."
    )
    hint_cell.font = Font(italic=True, size=9, color="555555")
    hint_cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 30

    # Header
    apply_header_row(ws, 3, COLS_POSITIONEN, "1F3864")
    ws.row_dimensions[3].height = 30
    ws.freeze_panes = "A4"

    # Ebene-Farbmap
    EBENE_COLOR = {
        "Bund":    "D6E4F0",
        "Land":    "D5F0D6",
        "Kommune": "FFF3CD",
    }

    # Daten sortiert: Bund → Land → Kommune, innerhalb Bundesland alpha
    sorted_data = sorted(DATA, key=lambda r: (
        {"Bund": 0, "Land": 1, "Kommune": 2}.get(r[0], 3), r[1], r[4]
    ))

    for r_idx, row in enumerate(sorted_data, start=4):
        fill_hex = EBENE_COLOR.get(row[0])
        # Leichte Zebra-Wechslung innerhalb einer Ebene
        if r_idx % 2 == 0 and fill_hex:
            # Etwas dunklere Variante
            fill_hex_alt = fill_hex  # Wir belassen es, Row-Highlight reicht
        write_data_row(ws, r_idx, list(row), fill_hex)

    # Gesamtsumme
    last_row = 3 + len(sorted_data)
    total_row = last_row + 2
    ws.cell(row=total_row, column=7, value="SUMME GESAMT").font = Font(bold=True)
    total_cell = ws.cell(row=total_row, column=8)
    total_cell.value = sum(row[7] for row in DATA)
    total_cell.number_format = '#,##0.00" Mio. €"'
    total_cell.font = Font(bold=True, color="CC0000")
    total_cell.alignment = Alignment(horizontal="right")

    autofit_columns(ws)
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 40
    ws.column_dimensions["D"].width = 28
    ws.column_dimensions["E"].width = 40
    ws.column_dimensions["F"].width = 55
    ws.column_dimensions["G"].width = 22
    ws.column_dimensions["H"].width = 14
    ws.column_dimensions["I"].width = 12
    ws.column_dimensions["J"].width = 50

    # Zweites Tabellenblatt: Nur Bund
    ws_bund = wb.create_sheet("Bundesebene")
    apply_header_row(ws_bund, 1, COLS_POSITIONEN, "1F3864")
    bund_data = [r for r in sorted_data if r[0] == "Bund"]
    for r_idx, row in enumerate(bund_data, start=2):
        write_data_row(ws_bund, r_idx, list(row), "D6E4F0")
    ws_bund.freeze_panes = "A2"
    for col_dim, width in [("A",12),("B",18),("C",45),("D",30),("E",40),
                            ("F",55),("G",22),("H",14),("I",12),("J",50)]:
        ws_bund.column_dimensions[col_dim].width = width

    # Drittes Tabellenblatt: Nur Länder
    ws_land = wb.create_sheet("Länderebene")
    apply_header_row(ws_land, 1, COLS_POSITIONEN, "1A5C2A")
    land_data = [r for r in sorted_data if r[0] == "Land"]
    for r_idx, row in enumerate(land_data, start=2):
        write_data_row(ws_land, r_idx, list(row), "D5F0D6")
    ws_land.freeze_panes = "A2"
    for col_dim, width in [("A",12),("B",22),("C",45),("D",30),("E",40),
                            ("F",55),("G",22),("H",14),("I",12),("J",50)]:
        ws_land.column_dimensions[col_dim].width = width

    # Viertes Tabellenblatt: Nur Kommunen
    ws_komm = wb.create_sheet("Kommunale Ebene")
    apply_header_row(ws_komm, 1, COLS_POSITIONEN, "7D5B00")
    komm_data = [r for r in sorted_data if r[0] == "Kommune"]
    for r_idx, row in enumerate(komm_data, start=2):
        write_data_row(ws_komm, r_idx, list(row), "FFF3CD")
    ws_komm.freeze_panes = "A2"
    for col_dim, width in [("A",12),("B",22),("C",35),("D",30),("E",40),
                            ("F",55),("G",22),("H",14),("I",12),("J",50)]:
        ws_komm.column_dimensions[col_dim].width = width

    out_path = "/home/user/claude-plugins-journalism/sportfoerderung_nach_haushaltspositionen.xlsx"
    wb.save(out_path)
    print(f"Datei 1 gespeichert: {out_path}")
    return out_path


# ─── Datei 2: Nach Bundesländern ──────────────────────────────────────────────

BUNDESLAENDER_ORDER = [
    "Gesamt (Bund)",
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
    "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
]

BL_FILL = {
    "Gesamt (Bund)":           "1F3864",
    "Baden-Württemberg":       "C6EFCE",
    "Bayern":                  "FFEB9C",
    "Berlin":                  "C9C9C9",
    "Brandenburg":             "BDD7EE",
    "Bremen":                  "D9D2E9",
    "Hamburg":                 "FCE5CD",
    "Hessen":                  "D9EAD3",
    "Mecklenburg-Vorpommern":  "CFE2F3",
    "Niedersachsen":           "FFF2CC",
    "Nordrhein-Westfalen":     "F4CCCC",
    "Rheinland-Pfalz":        "D9D2E9",
    "Saarland":                "EAD1DC",
    "Sachsen":                 "D0E0E3",
    "Sachsen-Anhalt":          "B6D7A8",
    "Schleswig-Holstein":      "A2C4C9",
    "Thüringen":               "E6B8A2",
}

def create_file_by_bundesland():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sportförderung nach Bundesland"

    # Titel
    ws.merge_cells("A1:J1")
    tc = ws["A1"]
    tc.value = (
        "Sportförderung in Deutschland – Übersicht nach Bundesländern "
        "(Bundesministerien, Landesministerien und Kommunen, Stand 2024/2025)"
    )
    tc.font = Font(bold=True, size=13, color="1F3864")
    tc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 40

    ws.merge_cells("A2:J2")
    hc = ws["A2"]
    hc.value = (
        "Hinweis: Beträge in Millionen Euro. Kommunale Werte sind Schätzwerte. "
        "Für Bundesländer ohne vollständige Daten liegen nur Teilangaben vor."
    )
    hc.font = Font(italic=True, size=9, color="555555")
    hc.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 25

    apply_header_row(ws, 3, COLS_POSITIONEN, "1F3864")
    ws.row_dimensions[3].height = 30
    ws.freeze_panes = "A4"

    current_row = 4
    grand_total = 0.0

    bl_totals = {}  # Bundesland → Summe

    for bundesland in BUNDESLAENDER_ORDER:
        bl_rows = [r for r in DATA if r[1] == bundesland]
        if not bl_rows:
            continue

        # Bundesland-Zwischentitel
        ws.merge_cells(
            start_row=current_row, start_column=1,
            end_row=current_row, end_column=10
        )
        bl_label = (
            f"■  {bundesland}"
            if bundesland != "Gesamt (Bund)"
            else f"■  BUNDESEBENE – {bundesland}"
        )
        header_cell = ws.cell(row=current_row, column=1, value=bl_label)
        fill_hex = BL_FILL.get(bundesland, "EEEEEE")
        header_cell.fill = header_fill(fill_hex)
        font_color = "FFFFFF" if bundesland == "Gesamt (Bund)" else "000000"
        header_cell.font = Font(bold=True, size=11, color=font_color)
        header_cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[current_row].height = 22
        current_row += 1

        bl_total = 0.0
        for row in sorted(bl_rows, key=lambda r: (r[0], r[4])):
            write_data_row(ws, current_row, list(row))
            # Leichte Hintergrundfarbe nach Ebene
            bg = {"Bund": "EEF4FB", "Land": "F0FBF0",
                  "Kommune": "FFFCEE"}.get(row[0], "FFFFFF")
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).fill = header_fill(bg)
            # Betrag-Zelle erneut formatieren
            amt_cell = ws.cell(row=current_row, column=8)
            amt_cell.number_format = '#,##0.00" Mio. €"'
            amt_cell.alignment = Alignment(horizontal="right", vertical="top")
            # Borders
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).border = thin_border()
            bl_total += row[7]
            current_row += 1

        # Bundesland-Summe
        sum_cell_label = ws.cell(row=current_row, column=7,
                                  value=f"Summe {bundesland}")
        sum_cell_label.font = Font(bold=True)
        sum_cell_label.alignment = Alignment(horizontal="right")
        sum_cell = ws.cell(row=current_row, column=8, value=bl_total)
        sum_cell.number_format = '#,##0.00" Mio. €"'
        sum_cell.font = Font(bold=True)
        sum_cell.fill = header_fill("F2F2F2")
        sum_cell.alignment = Alignment(horizontal="right")
        sum_cell_label.fill = header_fill("F2F2F2")
        grand_total += bl_total
        bl_totals[bundesland] = bl_total
        current_row += 2  # Leerzeile

    # Gesamtsumme
    ws.cell(row=current_row, column=7, value="GESAMTSUMME (alle Ebenen)").font = Font(
        bold=True, size=11, color="CC0000"
    )
    gtc = ws.cell(row=current_row, column=8, value=grand_total)
    gtc.number_format = '#,##0.00" Mio. €"'
    gtc.font = Font(bold=True, size=11, color="CC0000")
    gtc.alignment = Alignment(horizontal="right")

    # Spaltenbreiten
    for col_dim, width in [("A",12),("B",22),("C",42),("D",30),("E",40),
                            ("F",55),("G",22),("H",16),("I",12),("J",50)]:
        ws.column_dimensions[col_dim].width = width

    # Zweites Blatt: Zusammenfassung je Bundesland
    ws_sum = wb.create_sheet("Zusammenfassung Bundesländer")
    sum_cols = ["Bundesland", "Ebene(n)", "Betrag gesamt (Mio. €)", "Haushaltsjahr(e)",
                "Anmerkung"]
    apply_header_row(ws_sum, 1, sum_cols, "1F3864")
    ws_sum.freeze_panes = "A2"

    for r_idx, bundesland in enumerate(BUNDESLAENDER_ORDER, start=2):
        bl_rows = [r for r in DATA if r[1] == bundesland]
        if not bl_rows:
            continue
        ebenen = ", ".join(sorted(set(r[0] for r in bl_rows)))
        years  = ", ".join(sorted(set(str(r[8]) for r in bl_rows)))
        total  = sum(r[7] for r in bl_rows)
        fill_hex = BL_FILL.get(bundesland, "EEEEEE")
        font_col = "FFFFFF" if bundesland == "Gesamt (Bund)" else "000000"
        vals = [bundesland, ebenen, total, years,
                f"{len(bl_rows)} Haushaltspositionen"]
        for c_idx, val in enumerate(vals, start=1):
            cell = ws_sum.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = header_fill(fill_hex)
            cell.font = Font(color=font_col)
            cell.border = thin_border()
            if c_idx == 3:
                cell.number_format = '#,##0.00" Mio. €"'
                cell.alignment = Alignment(horizontal="right")

    for col_dim, width in [("A",25),("B",20),("C",22),("D",22),("E",35)]:
        ws_sum.column_dimensions[col_dim].width = width

    out_path = "/home/user/claude-plugins-journalism/sportfoerderung_nach_bundeslaendern.xlsx"
    wb.save(out_path)
    print(f"Datei 2 gespeichert: {out_path}")
    return out_path


if __name__ == "__main__":
    p1 = create_file_by_positionen()
    p2 = create_file_by_bundesland()
    print("\nFertig! Erstellte Dateien:")
    print(f"  1. {p1}")
    print(f"  2. {p2}")
