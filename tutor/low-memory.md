# Low memory

Symptoms: the notebook kernel dies without a Python error, a process prints `Killed`, the machine freezes while loading data, `MemoryError`.

## Find the cause first

1. `free -h`: how much RAM does Linux see? Under WSL it is half of the machine by default.
2. `uv run course profile`: which data profile is active?
3. What was loaded? Ask the learner to show the loading line. The usual cause is reading the raw file without `columns=`, which pulls in the two hourly columns: about 7.5 GB at peak for the whole file, against 221 MB for the scalar columns with small types.

## Fixes, cheapest first

| Fix | When |
|---|---|
| Restart the kernel, close other notebooks | several notebooks hold copies of the data |
| Select columns and filter cities while reading | the raw file is read whole. This is rule D1 and the first lesson of module 07 |
| Delete large intermediates (`del frame`), avoid keeping `raw`, `clean` and `merged` alive together | memory grows cell by cell |
| `uv run course profile small` | RAM seen by Linux is below 6 GB |
| Raise the WSL limit: `%UserProfile%\.wslconfig`, `[wsl2]`, `memory=12GB`, then `wsl --shutdown` | the machine has more RAM than Linux sees |

## Profiles

| Profile | Series | Rows | Works with |
|---|---|---|---|
| `small` | 493 | 44 thousand | any machine |
| `standard` | 2,648 | 238 thousand | 6 GB and more |
| `full` | 50,000 | 4.5 million | 12 GB and more, modules 14, 18 and the capstone |

Checks run on a fixed small sample, so every task can be passed on any profile. On `small`, the modules that ask for the full data run on `standard` instead; say so in the capstone report.

Treat the first out-of-memory crash as a teaching moment, not a nuisance: have the learner estimate the size of what they tried to load (rows × bytes per row) before you name the fix.
