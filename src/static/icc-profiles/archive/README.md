# Archive

Colour profiles for hardware I no longer use. They stay here for anyone who still has the hardware, but
nothing in this folder is maintained or tested any more.

## LS27B800TGUXEN - S80TB, Samsung ViewFinity S8 Thunderbolt

Color profile for the Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN) external monitor.

### Source

Extracted from the Samsung Windows driver package (`S80TB-INF-Driver-Win11x64`).

### Files

| Filename | Description |
|---|---|
| `LS27B800TGUXEN - S80TB/SxxB80xT.icm` | Samsung factory color profile for the S80TB Thunderbolt display |

### Install

```bash
# System-wide (all users):
sudo cp SxxB80xT.icm /usr/share/color/icc/colord/

# Or per-user:
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

Then activate in **GNOME Settings** → **Color Management** → select the Samsung display → **Add Profile** → select `SxxB80xT`.
