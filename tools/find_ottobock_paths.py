#!/usr/bin/env python3
"""
Score a LinkedIn Connections.csv export for paths to Ottobock (for Noah).

How to get the input file
-------------------------
LinkedIn -> Me -> Settings & Privacy -> Data privacy -> "Get a copy of your data"
-> pick "Connections" (fast, ~10 min) -> download the zip -> unzip Connections.csv.

Usage
-----
    python3 tools/find_ottobock_paths.py path/to/Connections.csv
    python3 tools/find_ottobock_paths.py Connections.csv --csv out.csv --top 60

Output: ranked list of connections, with the tier they matched and why.
Tiers (highest first):
  1  Works at Ottobock / SUITX / Ottobock.care today
  2  Prosthetics, orthotics or exoskeleton industry (Össur, Hanger, etc.)
  3  Medical device / med-tech / rehab robotics
  4  Located in an Ottobock hub (Austin TX, Salt Lake City UT, Louisville KY,
     Emeryville / Berkeley CA, Duderstadt / Vienna) or UC Davis affiliation
  5  Sensor / MCU / embedded / battery / motion-control suppliers likely to
     sell into Ottobock's bionics, or recruiters / university career staff
"""
import argparse
import csv
import re
import sys

TIERS = [
    (1, "Ottobock / SUITX", [
        r"\botto ?bock\b", r"\bsuitx\b", r"\bottobock\.care\b", r"\bottobock care\b",
    ]),
    (2, "Prosthetics / orthotics / exoskeleton industry", [
        r"\bössur\b", r"\bossur\b", r"\bhanger\b", r"\bfillauer\b", r"\bblatchford\b",
        r"\bproteor\b", r"\bwillowwood\b", r"\bcollege park\b", r"\bfreedom innovations\b",
        r"\bopen bionics\b", r"\bpsyonic\b", r"\bcoapt\b", r"\bbionx\b", r"\bekso\b",
        r"\brewalk\b", r"\bsarcos\b", r"\bgerman bionic\b", r"\bprosthe", r"\borthotic",
        r"\borthopedic technolog", r"\bo&p\b", r"\bexoskelet", r"\bcpo\b", r"\bamputee",
        r"\bbionic",
    ]),
    (3, "Medical device / rehab robotics", [
        r"\bmedtronic\b", r"\bstryker\b", r"\bzimmer biomet\b", r"\bsmith ?\+? ?nephew\b",
        r"\bdepuy\b", r"\bj&j medtech\b", r"\babbott\b", r"\bboston scientific\b",
        r"\bedwards lifesciences\b", r"\bintuitive\b", r"\bdexcom\b", r"\binsulet\b",
        r"\bresmed\b", r"\bphilips healthcare\b", r"\bge healthcare\b", r"\bsiemens healthineers\b",
        r"\bmedical device", r"\bmed ?tech\b", r"\bmedtech\b", r"\bbiomedical\b",
        r"\brehab", r"\bwearable", r"\bhealth ?care\b", r"\bfda\b", r"\biso 13485\b",
        r"\bclass ii\b", r"\bregulatory affairs\b", r"\bquality engineer",
    ]),
    (4, "Ottobock hub location or UC Davis", [
        r"\baustin\b", r"\bsalt lake\b", r"\butah\b", r"\blouisville\b", r"\bemeryville\b",
        r"\bberkeley\b", r"\bduderstadt\b", r"\bvienna\b", r"\bwien\b", r"\bg[öo]ttingen\b",
        r"\buc ?davis\b", r"\buniversity of california,? davis\b", r"\bdavis,? ca\b",
    ]),
    (5, "Component supplier / recruiter / university careers", [
        r"\btexas instruments\b", r"\bti\b", r"\banalog devices\b", r"\badi\b", r"\bnxp\b",
        r"\bstmicro", r"\bmicrochip\b", r"\brenesas\b", r"\binfineon\b", r"\bnordic semi",
        r"\bsilicon labs\b", r"\bbosch sensortec\b", r"\btdk invensense\b", r"\bmaxon\b",
        r"\bfaulhaber\b", r"\bharmonic drive\b", r"\bportescap\b", r"\bmoog\b",
        r"\bmotion control\b", r"\bactuator", r"\bimu\b", r"\bsensor fusion\b",
        r"\bbattery\b", r"\bbms\b", r"\bfirmware\b", r"\bembedded\b", r"\bmechatronic",
        r"\bcontrols? engineer", r"\brobotic", r"\brecruit", r"\btalent acquisition\b",
        r"\bcareer (services|center)\b", r"\bhandshake\b", r"\bhuman resources\b", r"\bhr\b",
    ]),
]

COMPILED = [(tier, label, [re.compile(p, re.I) for p in pats]) for tier, label, pats in TIERS]


def open_connections(path):
    """LinkedIn prefixes Connections.csv with a 'Notes:' preamble; skip to the header row."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = fh.readlines()
    start = 0
    for i, line in enumerate(lines):
        if line.lower().startswith("first name"):
            start = i
            break
    return list(csv.DictReader(lines[start:]))


def score(row):
    company = row.get("Company", "") or ""
    position = row.get("Position", "") or ""
    blob = " | ".join([company, position])
    hits = []
    best = None
    for tier, label, pats in COMPILED:
        for p in pats:
            m = p.search(blob)
            if m:
                hits.append(f"T{tier} {label}: '{m.group(0)}'")
                if best is None or tier < best:
                    best = tier
                break  # one hit per tier is enough
    return best, hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("connections_csv")
    ap.add_argument("--top", type=int, default=50, help="how many rows to print (default 50)")
    ap.add_argument("--csv", help="also write the full ranked list to this CSV")
    ap.add_argument("--max-tier", type=int, default=5, help="ignore matches weaker than this tier")
    args = ap.parse_args()

    rows = open_connections(args.connections_csv)
    ranked = []
    for r in rows:
        best, hits = score(r)
        if best is not None and best <= args.max_tier:
            ranked.append((best, r, hits))
    ranked.sort(key=lambda t: (t[0], (t[1].get("Company") or "").lower(), (t[1].get("Last Name") or "").lower()))

    print(f"{len(rows)} connections scanned, {len(ranked)} matched.\n")
    for best, r, hits in ranked[: args.top]:
        name = f"{r.get('First Name','')} {r.get('Last Name','')}".strip()
        print(f"[T{best}] {name} — {r.get('Position','')} @ {r.get('Company','')}")
        if r.get("URL"):
            print(f"      {r['URL']}")
        for h in hits:
            print(f"      {h}")
        print()

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["tier", "first_name", "last_name", "company", "position", "url", "connected_on", "why"])
            for best, r, hits in ranked:
                w.writerow([best, r.get("First Name", ""), r.get("Last Name", ""), r.get("Company", ""),
                            r.get("Position", ""), r.get("URL", ""), r.get("Connected On", ""), "; ".join(hits)])
        print(f"Full ranked list written to {args.csv}")

    if not ranked:
        print("No matches. Check that the file is LinkedIn's Connections.csv (columns: First Name, Last Name, URL, Email Address, Company, Position, Connected On).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
