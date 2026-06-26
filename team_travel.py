"""
team_travel.py
Calculates group-stage travel distances (km) per team for:
  - proposed : Andrew's alternative 35-venue format
  - actual   : official FIFA 2026 venues (sourced from MLS Soccer / Wikipedia)

Scheduling pattern (3+3 split, one game per venue per matchday):
  MD1: T0vT1@V1,  T2vT3@V2
  MD2: T0vT2@V2,  T1vT3@V1
  MD3: T0vT3@V1,  T1vT2@V2

Venue sequence per team (0=V1 primary, 1=V2 secondary):
  T0 anchor (Pot 1) : V1 -> V2 -> V1   (2 x pair dist)
  T1        (Pot 2) : V1 -> V1 -> V2   (1 x pair dist)
  T2        (Pot 3) : V2 -> V2 -> V2   (0 — all 3 in same city; V2 still hosts Pot 1 in MD2)
  T3        (Pot 4) : V2 -> V1 -> V1   (1 x pair dist)

Outputs: team_travel.csv
Run from the folder containing stadiums_proposed.csv.
"""

import csv
import math
from pathlib import Path


# ── 1. HAVERSINE ──────────────────────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# ── 2. LOAD STADIUMS ──────────────────────────────────────────────────────────

def load_stadiums(path="stadiums_proposed.csv"):
    stadiums = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = int(row["stadium_id"])
            stadiums[sid] = {
                "name":    row["stadium_name"],
                "city":    row["city"],
                "country": row["country"],
                "lat":     float(row["lat"]),
                "lon":     float(row["lon"]),
            }
    return stadiums


# ── 3. GROUPS & TEAMS ─────────────────────────────────────────────────────────
# Order within each group: [Pot1 anchor, Pot2, Pot3, Pot4]

GROUPS = {
    "A": ["Mexico",      "South Africa",          "South Korea",    "Czechia"],
    "B": ["Canada",      "Bosnia and Herzegovina", "Qatar",          "Switzerland"],
    "C": ["Brazil",      "Morocco",               "Haiti",          "Scotland"],
    "D": ["USA",         "Paraguay",              "Australia",      "Türkiye"],
    "E": ["Germany",     "Curaçao",               "Ivory Coast",    "Ecuador"],
    "F": ["Netherlands", "Japan",                 "Sweden",         "Tunisia"],
    "G": ["Belgium",     "Egypt",                 "Iran",           "New Zealand"],
    "H": ["Spain",       "Cape Verde",            "Saudi Arabia",   "Uruguay"],
    "I": ["France",      "Senegal",               "Iraq",           "Norway"],
    "J": ["Argentina",   "Algeria",               "Austria",        "Jordan"],
    "K": ["Portugal",    "DR Congo",              "Uzbekistan",     "Colombia"],
    "L": ["England",     "Croatia",               "Ghana",          "Panama"],
}


# ── 4. PROPOSED VENUE PAIRS ───────────────────────────────────────────────────
# (V1_stadium_id, V2_stadium_id)  — see stadiums_proposed.csv for IDs

PROPOSED_VENUES = {
    "A": (13, 38),   # Akron + Corregidora           (Guadalajara + Querétaro)
    "B": ( 3,  4),   # BMO Field + Stade Olympique   (Toronto + Montreal)
    "C": (25, 26),   # Memorial + Arrowhead          (Lincoln + Kansas City)
    "D": (27, 28),   # Gillette + Lincoln Financial  (Boston + Philadelphia)
    "E": (15, 16),   # Michigan + Ohio               (Ann Arbor + Columbus)
    "F": (21, 22),   # Neyland + Clemson             (Knoxville + Clemson)
    "G": (20, 19),   # NRG + Tiger Stadium           (Houston + Baton Rouge)
    "H": ( 8,  9),   # Cuauhtémoc + Morelos          (Puebla + Morelia)
    "I": (17, 18),   # Jordan-Hare + Bryant-Denny    (Auburn + Tuscaloosa)
    "J": ( 1,  2),   # Mosaic + Princess Auto        (Regina + Winnipeg)
    "K": (23, 24),   # Autzen + Lumen                (Eugene + Seattle)
    "L": (29, 30),   # Lambeau + Camp Randall        (Green Bay + Madison)
}

PROPOSED_PATTERN = [
    [0, 1, 0],   # T0 anchor
    [0, 0, 1],   # T1
    [1, 1, 1],   # T2 (Pot 3 — stays at V2 all 3 games)
    [1, 0, 0],   # T3
]


# ── 5. ACTUAL VENUE ASSIGNMENTS ───────────────────────────────────────────────
# Source: MLS Soccer venue-by-venue schedule + Wikipedia 2026 group stage
# Format: "Team": (MD1_id, MD2_id, MD3_id)
# Key IDs: 3=BMO 7=BC Place 10=BBVA 13=Akron 14=Azteca 20=NRG 24=Lumen
#          26=Arrowhead 27=Gillette 28=Lincoln Financial 31=AT&T 32=SoFi
#          33=MBZ Atlanta 35=MetLife 36=Hard Rock Miami 37=Levi's SF

ACTUAL_VENUES = {
    # GROUP A
    "Mexico":        (14, 13, 14),
    "South Africa":  (14, 33, 10),
    "South Korea":   (13, 13, 10),
    "Czechia":       (13, 33, 14),
    # GROUP B
    "Canada":                    ( 3,  7,  7),
    "Bosnia and Herzegovina":    ( 3, 32, 24),
    "Qatar":                     (37,  7, 24),
    "Switzerland":               (37, 32,  7),
    # GROUP C
    "Brazil":    (35, 28, 36),
    "Morocco":   (35, 27, 33),
    "Haiti":     (27, 28, 33),
    "Scotland":  (27, 27, 36),
    # GROUP D
    "USA":        (32, 24, 32),
    "Paraguay":   (32, 37, 37),
    "Australia":  ( 7, 24, 37),
    "Türkiye":    ( 7, 37, 32),
    # GROUP E
    "Germany":      (20,  3, 35),
    "Curaçao":      (20, 26, 28),
    "Ivory Coast":  (28,  3, 28),
    "Ecuador":      (28, 26, 35),
    # GROUP F
    "Netherlands":  (31, 20, 26),
    "Japan":        (31, 10, 31),
    "Sweden":       (10, 20, 31),
    "Tunisia":      (10, 10, 26),
    # GROUP G
    "Belgium":      (24, 32,  7),
    "Egypt":        (24,  7, 24),
    "Iran":         (32, 32, 24),
    "New Zealand":  (32,  7,  7),
    # GROUP H
    "Spain":         (33, 33, 13),
    "Cape Verde":    (33, 36, 20),
    "Saudi Arabia":  (36, 33, 20),
    "Uruguay":       (36, 36, 13),
    # GROUP I
    "France":   (35, 28, 27),
    "Senegal":  (35, 35,  3),
    "Iraq":     (27, 28,  3),
    "Norway":   (27, 35, 27),
    # GROUP J
    "Argentina":  (26, 31, 31),
    "Algeria":    (26, 37, 26),
    "Austria":    (37, 31, 26),
    "Jordan":     (37, 37, 31),
    # GROUP K
    "Portugal":    (20, 20, 36),
    "DR Congo":    (20, 13, 33),
    "Uzbekistan":  (14, 20, 33),
    "Colombia":    (14, 13, 36),
    # GROUP L
    "England":  (31, 27, 35),
    "Croatia":  (31,  3, 28),
    "Ghana":    ( 3, 27, 28),
    "Panama":   ( 3,  3, 35),
}


# ── 6. BUILD ROWS ─────────────────────────────────────────────────────────────

def _travel_row(travel_id, team, group_id, scenario, g1, g2, g3, stadiums, pair_dist=""):
    s1, s2, s3 = stadiums[g1], stadiums[g2], stadiums[g3]
    leg1 = haversine_km(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
    leg2 = haversine_km(s2["lat"], s2["lon"], s3["lat"], s3["lon"])
    return {
        "travel_id":         travel_id,
        "team_name":         team,
        "group_id":          group_id,
        "scenario":          scenario,
        "game_1_stadium_id": g1,
        "game_2_stadium_id": g2,
        "game_3_stadium_id": g3,
        "game_1_stadium":    s1["name"],
        "game_2_stadium":    s2["name"],
        "game_3_stadium":    s3["name"],
        "game_1_to_2_km":    round(leg1, 1),
        "game_2_to_3_km":    round(leg2, 1),
        "total_km":          round(leg1 + leg2, 1),
        "pair_dist_km":      pair_dist,
    }


def build_proposed(stadiums):
    rows, tid = [], 1
    for group, teams in GROUPS.items():
        v1_id, v2_id = PROPOSED_VENUES[group]
        pair_dist = round(haversine_km(
            stadiums[v1_id]["lat"], stadiums[v1_id]["lon"],
            stadiums[v2_id]["lat"], stadiums[v2_id]["lon"]
        ), 1)
        venue_ids = [v1_id, v2_id]
        for t_idx, team in enumerate(teams):
            pat = PROPOSED_PATTERN[t_idx]
            g1, g2, g3 = venue_ids[pat[0]], venue_ids[pat[1]], venue_ids[pat[2]]
            rows.append(_travel_row(tid, team, group, "proposed", g1, g2, g3, stadiums, pair_dist))
            tid += 1
    return rows


def build_actual(stadiums):
    rows, tid = [], 1001
    team_to_group = {t: g for g, members in GROUPS.items() for t in members}
    for team, (g1, g2, g3) in ACTUAL_VENUES.items():
        group_id = team_to_group.get(team, "")
        rows.append(_travel_row(tid, team, group_id, "actual", g1, g2, g3, stadiums))
        tid += 1
    return rows


# ── 7. WRITE & SUMMARISE ──────────────────────────────────────────────────────

FIELDNAMES = [
    "travel_id", "team_name", "group_id", "scenario",
    "game_1_stadium_id", "game_2_stadium_id", "game_3_stadium_id",
    "game_1_stadium", "game_2_stadium", "game_3_stadium",
    "game_1_to_2_km", "game_2_to_3_km", "total_km", "pair_dist_km",
]


def main():
    stadiums = load_stadiums(Path(__file__).parent / "stadiums_proposed.csv")
    all_rows = build_proposed(stadiums) + build_actual(stadiums)

    out_path = Path(__file__).parent / "team_travel.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    for scenario in ("proposed", "actual"):
        subset = [r for r in all_rows if r["scenario"] == scenario]
        totals = [r["total_km"] for r in subset]
        mx = max(subset, key=lambda r: r["total_km"])
        mn = min(subset, key=lambda r: r["total_km"])
        print(f"\n{scenario.upper()} ({len(subset)} teams)")
        print(f"  Max: {mx['total_km']:>7.0f} km — {mx['team_name']}")
        print(f"  Min: {mn['total_km']:>7.0f} km — {mn['team_name']}")
        print(f"  Avg: {sum(totals)/len(totals):>7.0f} km")

    print(f"\nOutput: {out_path}")


if __name__ == "__main__":
    main()
