#!/usr/bin/env python3
"""
Rank a LinkedIn Connections.csv export by usefulness as a warm path into
Ottobock for Noah: neurobiology major, pulled toward engineering.
Location preference: Emeryville / Bay Area first, Salt Lake City second.

Getting the input
-----------------
LinkedIn -> Me -> Settings & Privacy -> Data privacy -> "Get a copy of your data"
-> Connections -> download the zip -> Connections.csv.
(This script also accepts the .zip directly.)

Usage
-----
    python3 tools/find_ottobock_paths.py ~/Downloads/Basic_LinkedInDataExport.zip
    python3 tools/find_ottobock_paths.py Connections.csv --csv ranked.csv --top 60

Scoring
-------
Points accumulate across four independent axes, so a Bay Area neuroscientist
at a med-device company outranks a distant Ottobock-adjacent name.

  RELEVANCE  how close the employer is to Ottobock's business
  NEURO      neural / biomechanics signal -- Noah's bridge from neurobio to eng
  LOCATION   Emeryville & Bay Area (his 1st choice) > Salt Lake City (2nd)
  ACCESS     recruiter, hiring manager, professor -- people who open doors

Caveat: LinkedIn's export has no location column. Location is inferred from
company and title text plus a list of known-HQ employers, so it is best-effort
and will miss people whose city is not implied by where they work.
"""
import argparse
import csv
import io
import os
import re
import sys
import zipfile

# ---------------------------------------------------------------- relevance --
RELEVANCE = [
    (100, "Ottobock itself", [
        r"\botto ?bock\b", r"\bsuitx\b", r"\bsuit ?x\b", r"\bottobock\.care\b",
    ]),
    (70, "Prosthetics / orthotics / exoskeleton", [
        r"\b[oö]ssur\b", r"\bhanger clinic\b", r"\bfillauer\b", r"\bblatchford\b",
        r"\bproteor\b", r"\bwillowwood\b", r"\bcollege park industries\b",
        r"\bopen bionics\b", r"\bpsyonic\b", r"\bcoapt\b", r"\bvincent systems\b",
        r"\bekso ?bionics\b", r"\brewalk\b", r"\bsarcos\b", r"\bgerman bionic\b",
        r"\bwandercraft\b", r"\bcyberdyne\b", r"\bdephy\b", r"\bhumotech\b",
        r"\bprosthe", r"\borthotic", r"\bexoskelet", r"\bamputee\b", r"\bbionic",
        r"\bo&p\b", r"\blimb loss\b",
    ]),
    (45, "Medical device / rehab", [
        r"\bmedtronic\b", r"\bstryker\b", r"\bzimmer biomet\b", r"\bsmith ?\+? ?nephew\b",
        r"\bdepuy\b", r"\bj&j medtech\b", r"\bboston scientific\b", r"\babbott\b",
        r"\bedwards lifesciences\b", r"\bintuitive surgical\b", r"\bdexcom\b",
        r"\binsulet\b", r"\bresmed\b", r"\bbecton\b", r"\bbaxter\b", r"\bhologic\b",
        r"\bvaric", r"\bge healthcare\b", r"\bsiemens healthineers\b",
        r"\bphilips healthcare\b", r"\bmedical device", r"\bmedtech\b",
        r"\bbiomedical engineer", r"\bbiomed\b", r"\brehabilitation\b", r"\brehab\b",
        r"\biso 13485\b", r"\bregulatory affairs\b", r"\bclinical engineer",
        r"\bphysical therap", r"\bkinesiolog",
    ]),
    (25, "Robotics / wearables / mechatronics", [
        r"\brobotic", r"\bmechatronic", r"\bwearable", r"\bactuator",
        r"\bmotion control\b", r"\bcontrol systems?\b", r"\bhuman factors\b",
        r"\bhaptic", r"\bteleoperat", r"\bmaxon\b", r"\bfaulhaber\b",
        r"\bharmonic drive\b", r"\bportescap\b", r"\bmoog\b",
    ]),
    (12, "Embedded / sensing supplier", [
        r"\btexas instruments\b", r"\banalog devices\b", r"\bnxp\b", r"\bstmicro",
        r"\bmicrochip\b", r"\brenesas\b", r"\binfineon\b", r"\bnordic semi",
        r"\bsilicon labs\b", r"\bbosch sensortec\b", r"\binvensense\b",
        r"\bembedded\b", r"\bfirmware\b", r"\bimu\b", r"\bsensor fusion\b",
        r"\bbattery\b", r"\bsignal processing\b", r"\bdsp\b",
    ]),
]

# ------------------------------------------------------------------- neuro --
# Noah's neurobiology background is an asset exactly here. Ottobock's
# microprocessor knees and myoelectric arms are applied neuro-engineering.
NEURO = [
    (35, "Neural interface / neurotech", [
        r"\bblackrock neurotech\b", r"\bneuralink\b", r"\bparadromics\b",
        r"\bsynchron\b", r"\bprecision neuroscience\b", r"\bmotif neuro",
        r"\bcortical\b", r"\bneural interface\b", r"\bbrain ?-? ?computer\b",
        r"\bbci\b", r"\bneuroprosthe", r"\bneuromodulation\b", r"\bneurostim",
        r"\bdeep brain stim", r"\bemg\b", r"\bmyoelectric\b", r"\belectromyograph",
        r"\bosseointegrat", r"\btargeted muscle reinnervation\b", r"\btmr\b",
    ]),
    (22, "Neuroscience / biomechanics", [
        r"\bneuroscien", r"\bneurobiolog", r"\bneurolog", r"\bneuro ?eng",
        r"\bmotor control\b", r"\bbiomechanic", r"\bgait\b", r"\bmovement science\b",
        r"\bhuman movement\b", r"\bmuscle physiolog", r"\bsensorimotor\b",
        r"\bneural engineering\b", r"\bcomputational neuro",
    ]),
]

# ---------------------------------------------------------------- location --
# No location column in the export, so these fire on company/title text and on
# employers whose HQ metro is known.
LOCATION = [
    (30, "Bay Area (Emeryville - 1st choice)", [
        r"\bemeryville\b", r"\bberkeley\b", r"\boakland\b", r"\brichmond,? ca\b",
        r"\balameda\b", r"\bbay area\b", r"\bsan francisco\b", r"\bsf bay\b",
        r"\buc ?berkeley\b", r"\buniversity of california,? berkeley\b",
        r"\blawrence berkeley\b", r"\blbnl\b", r"\bucsf\b",
        r"\bzymergen\b", r"\bamyris\b", r"\bdynamic ?devices\b", r"\bnovartis.*emeryville\b",
    ]),
    (20, "Salt Lake City / Utah (2nd choice)", [
        r"\bsalt lake\b", r"\bslc\b", r"\butah\b", r"\bprovo\b", r"\blehi\b",
        r"\bogden\b", r"\bpark city\b", r"\bblackrock neurotech\b",
        r"\buniversity of utah\b", r"\bbiofire\b", r"\bmerit medical\b",
        r"\bvarian.*utah\b", r"\bedwards.*draper\b",
    ]),
    (8, "Austin (Ottobock NA HQ)", [
        r"\baustin\b", r"\bround rock\b", r"\bcedar park\b", r"\but austin\b",
    ]),
    (6, "Ottobock Europe / other hub", [
        r"\bduderstadt\b", r"\bg[öo]ttingen\b", r"\bvienna\b", r"\bwien\b",
        r"\blouisville\b",
    ]),
    (10, "UC Davis (Noah's school)", [
        r"\buc ?davis\b", r"\buniversity of california,? davis\b", r"\bdavis,? ca\b",
        r"\buc davis health\b",
    ]),
]

# ------------------------------------------------------------------ access --
ACCESS = [
    (20, "Recruiting / talent", [
        r"\brecruit", r"\btalent acquisition\b", r"\bsourcer\b", r"\bstaffing\b",
        r"\bhead of people\b", r"\bhuman resources\b", r"\bhris\b",
    ]),
    (15, "Hiring decision-maker", [
        r"\bhiring manager\b", r"\bvp\b", r"\bvice president\b", r"\bdirector\b",
        r"\bhead of\b", r"\bchief\b", r"\bcto\b", r"\bceo\b", r"\bfounder\b",
        r"\bgeneral manager\b", r"\bgm,\b", r"\bprincipal\b",
    ]),
    (15, "Academic / mentor", [
        r"\bprofessor\b", r"\blecturer\b", r"\bdean\b", r"\bpostdoc",
        r"\bprincipal investigator\b", r"\blab director\b", r"\bresearch scientist\b",
        r"\bcareer (services|center|advisor)\b", r"\binternship coordinator\b",
    ]),
]

AXES = [("RELEVANCE", RELEVANCE), ("NEURO", NEURO), ("LOCATION", LOCATION), ("ACCESS", ACCESS)]
COMPILED = [(axis, [(pts, label, [re.compile(p, re.I) for p in pats])
                    for pts, label, pats in rules]) for axis, rules in AXES]


def load_rows(path):
    """Accept Connections.csv, or the LinkedIn export .zip containing it."""
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith("connections.csv")]
            if not names:
                raise SystemExit(
                    f"No Connections.csv inside {path}.\nFound: {', '.join(z.namelist()[:25])}"
                )
            text = z.read(names[0]).decode("utf-8-sig", errors="replace")
    else:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    lines = text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.lower().lstrip('"').startswith("first name")), 0)
    return list(csv.DictReader(io.StringIO("".join(lines[start:]))))


def score(row):
    blob = " | ".join([row.get("Company", "") or "", row.get("Position", "") or ""])
    total, reasons, axis_scores = 0, [], {}
    for axis, rules in COMPILED:
        best_pts, best_label, best_hit = 0, None, None
        for pts, label, pats in rules:
            for p in pats:
                m = p.search(blob)
                if m and pts > best_pts:
                    best_pts, best_label, best_hit = pts, label, m.group(0)
                    break
        axis_scores[axis] = best_pts
        if best_pts:
            total += best_pts
            reasons.append(f"{axis} +{best_pts} {best_label} ('{best_hit}')")
    return total, axis_scores, reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("connections", help="Connections.csv or the LinkedIn export .zip")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--csv", help="write the full ranked list here")
    ap.add_argument("--min-score", type=int, default=10)
    args = ap.parse_args()

    if not os.path.exists(args.connections):
        raise SystemExit(f"No such file: {args.connections}")

    rows = load_rows(args.connections)
    ranked = []
    for r in rows:
        total, axes, reasons = score(r)
        if total >= args.min_score:
            ranked.append((total, axes, r, reasons))
    ranked.sort(key=lambda t: -t[0])

    print(f"{len(rows)} connections scanned, {len(ranked)} scored >= {args.min_score}.\n")
    for total, axes, r, reasons in ranked[: args.top]:
        name = f"{r.get('First Name','')} {r.get('Last Name','')}".strip()
        print(f"[{total:3d}] {name} — {r.get('Position','')} @ {r.get('Company','')}")
        if r.get("URL"):
            print(f"      {r['URL']}")
        for reason in reasons:
            print(f"      {reason}")
        print()

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["score", "relevance", "neuro", "location", "access", "first_name",
                        "last_name", "company", "position", "url", "connected_on", "why"])
            for total, axes, r, reasons in ranked:
                w.writerow([total, axes["RELEVANCE"], axes["NEURO"], axes["LOCATION"],
                            axes["ACCESS"], r.get("First Name", ""), r.get("Last Name", ""),
                            r.get("Company", ""), r.get("Position", ""), r.get("URL", ""),
                            r.get("Connected On", ""), "; ".join(reasons)])
        print(f"Full ranked list -> {args.csv}")

    if not ranked:
        print("No matches. Confirm this is LinkedIn's Connections.csv "
              "(columns: First Name, Last Name, URL, Email Address, Company, Position, Connected On).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
