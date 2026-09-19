# find_ottobock_paths.py

Ranks a LinkedIn **Connections.csv** export by how useful each contact is as a
warm path into **Ottobock** for Noah — neurobiology major, pulled toward
engineering, who'd prefer **Emeryville** (SUITX by Ottobock) and then
**Salt Lake City** (Ottobock's North American engineering and manufacturing).

## 1. Export connections from LinkedIn

Me → Settings & Privacy → Data privacy → **Get a copy of your data** →
tick **Connections** → Request archive. LinkedIn emails a link in ~10 minutes.

## 2. Run

```bash
# the .zip works directly -- no need to unzip
python3 tools/find_ottobock_paths.py ~/Downloads/Basic_LinkedInDataExport.zip \
    --csv ranked.csv --top 60
```

Python 3, no dependencies.

## 3. How scoring works

Points accumulate across four independent axes, so a Bay Area neuroscientist at
a medical-device company outranks a distant Ottobock-adjacent name.

| Axis | Max | What earns points |
|------|-----|-------------------|
| **RELEVANCE** | 100 | Ottobock or SUITX (100) › prosthetics/orthotics/exoskeleton (70) › medical device & rehab (45) › robotics & wearables (25) › embedded/sensor suppliers (12) |
| **NEURO** | 35 | Neural interfaces, myoelectric/EMG, neuroprosthetics (35) › neuroscience, biomechanics, motor control (22) |
| **LOCATION** | 30 | Bay Area / Emeryville / Berkeley (30) › Salt Lake City & Utah (20) › UC Davis (10) › Austin (8) › Duderstadt, Vienna, Louisville (6) |
| **ACCESS** | 20 | Recruiters and talent (20) › hiring decision-makers, VP/Director/founder (15) › professors, PIs, career staff (15) |

**The NEURO axis is the point.** Ottobock's microprocessor knees and myoelectric
arms are applied neuro-engineering, so Noah's major is an asset rather than a
detour. Contacts scoring on both NEURO and RELEVANCE are the best introductions.

### Caveat on location

LinkedIn's export has **no location column**. Location is inferred from company
and title text plus a list of known-HQ employers, so it is best-effort and will
miss people whose city isn't implied by where they work.

## 4. Tuning

Edit the `RELEVANCE`, `NEURO`, `LOCATION`, and `ACCESS` tables at the top of the
script to add employers or adjust weights.
