# tools/find_ottobock_paths.py

Ranks a LinkedIn **Connections.csv** export by how useful each contact is as a
path into Ottobock (prosthetics / orthotics / SUITX exoskeletons).

## 1. Export your connections from LinkedIn

LinkedIn (web) → **Me** → **Settings & Privacy** → **Data privacy** →
**Get a copy of your data** → tick **Connections** → **Request archive**.
LinkedIn emails a download link within about 10 minutes. Unzip it; the file
you want is `Connections.csv`.

## 2. Run

```bash
python3 tools/find_ottobock_paths.py ~/Downloads/Connections.csv --csv ranked.csv --top 60
```

No dependencies beyond Python 3.

## 3. Read the output

Each match gets a tier (1 = strongest):

| Tier | Meaning |
|------|---------|
| 1 | Works at Ottobock, SUITX by Ottobock, or Ottobock.care |
| 2 | Prosthetics / orthotics / exoskeleton industry (Össur, Hanger, Fillauer, Ekso, …) |
| 3 | Medical device / med-tech / rehab (Medtronic, Stryker, "medical device", FDA, ISO 13485, …) |
| 4 | Lives or works in an Ottobock hub (Austin TX, Salt Lake City UT, Louisville KY, Emeryville/Berkeley CA, Duderstadt, Vienna) or is tied to UC Davis |
| 5 | Sensor / MCU / motor / battery suppliers that sell into bionics, or recruiters and university career staff |

Edit the `TIERS` list at the top of the script to add companies or keywords.
