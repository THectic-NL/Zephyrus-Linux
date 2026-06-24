# ICC Color Profiles

Factory-calibrated and manufacturer-provided ICC profiles, organized per device.

## Directory Structure

```
icc-profiles/
├── Zephyrus G16 (2024) GA605WV/   # Profiles for the ASUS ROG Zephyrus G16 GA605WV
│   └── SxxB80xT.icm               # Samsung Thunderbolt display profile (external monitor)
├── LS27B800TGUXEN - S80TB/        # Profiles for the Samsung ViewFinity S8 Thunderbolt
│   └── SxxB80xT.icm               # Samsung color profile
├── GA605WV_*_CMDEF.icm            # Factory-calibrated profiles for the built-in OLED panel
├── ASUS_*.icm                     # Generic ASUS colorspace profiles
└── README.md
```

## System Install Path

On Linux, color profiles can be installed either system-wide or per-user:

| Location | Scope |
|---|---|
| `/usr/share/color/icc/colord/` | System-wide (all users, requires root) |
| `~/.local/share/icc/` | Current user only |

---

## Zephyrus G16 (2024) GA605WV — Built-in Display

Factory-calibrated ICC profiles for the Zephyrus G16 GA605WV built-in display.

The GA605WV was shipped with different panels depending on the unit. The standard model uses an IPS panel (ROG Nebula Display); some configurations ship with an OLED panel instead. Three panel variants are known:

| Panel ID | Manufacturer | Model | Type | Source |
|---|---|---|---|---|
| `104D158E` | Sharp | LQ160R1JW02 | IPS (ROG Nebula Display) | Verified via EDID on device |
| `834C41AE` | Samsung | ATNA60DL04-0 | OLED | [LaptopMedia](https://laptopmedia.com/screen/atna60dl04-0-sdc41ae/) · [Linux Hardware](https://linux-hardware.org/?id=eisa:samsung-sdc41ae) |
| `E5090C19` | Unknown | — | Unknown | Present in ASUS driver package; not yet publicly identified |

To check which panel your unit has:

```bash
cat /sys/class/drm/card*-eDP-*/edid | edid-decode 2>/dev/null | grep -i "manufacturer\|model\|product name"
```

### Source

Profiles were extracted from the ASUS Windows driver package by reverse engineering the ASUS CDN structure and driver ZIP contents:

```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip
```

The ICC metadata `desc` tags were modified so profiles appear with readable names in GNOME Color Management.

### Files

| Filename | GPU | Panel | Description |
|---|---|---|---|
| `GA605WV_1002_104D158E_CMDEF.icm` | AMD Radeon 890M (`1002`) | Sharp LQ160R1JW02 (`104D158E`) | **Recommended for most units** |
| `GA605WV_1002_834C41AE_CMDEF.icm` | AMD Radeon 890M (`1002`) | Samsung ATNA60DL04-0 (`834C41AE`) | For Samsung panel variant |
| `GA605WV_1002_E5090C19_CMDEF.icm` | AMD Radeon 890M (`1002`) | Unknown (`E5090C19`) | For unknown panel variant |
| `GA605WV_10DE_104D158E_CMDEF.icm` | NVIDIA RTX 4060 (`10DE`) | Sharp LQ160R1JW02 (`104D158E`) | For NVIDIA-primary mode |
| `GA605WV_10DE_834C41AE_CMDEF.icm` | NVIDIA RTX 4060 (`10DE`) | Samsung ATNA60DL04-0 (`834C41AE`) | For NVIDIA-primary + Samsung panel |
| `GA605WV_10DE_E5090C19_CMDEF.icm` | NVIDIA RTX 4060 (`10DE`) | Unknown (`E5090C19`) | For NVIDIA-primary + unknown panel |
| `ASUS_sRGB.icm` | Any | Any | sRGB colorspace (web, photo) |
| `ASUS_DisplayP3.icm` | Any | Any | Display P3 colorspace (Apple) |
| `ASUS_DCIP3.icm` | Any | Any | DCI-P3 colorspace (cinema) |

### Install

```bash
# System-wide install:
sudo cp GA605WV_1002_104D158E_CMDEF.icm /usr/share/color/icc/colord/

# Or per-user install:
mkdir -p ~/.local/share/icc
cp GA605WV_1002_104D158E_CMDEF.icm ~/.local/share/icc/
```

Then activate in **GNOME Settings** → **Color Management** → select your display → **Add Profile** → select the profile matching your GPU and panel combination.

---

## LS27B800TGUXEN - S80TB — Samsung ViewFinity S8 Thunderbolt

Color profile for the Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN) external monitor.

### Source

Extracted from the Samsung Windows driver package (`S80TB-INF-Driver-Win11x64`).

### Files

| Filename | Description |
|---|---|
| `SxxB80xT.icm` | Samsung factory color profile for the S80TB Thunderbolt display |

### Install

```bash
# System-wide (all users):
sudo cp SxxB80xT.icm /usr/share/color/icc/colord/

# Or per-user:
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

Then activate in **GNOME Settings** → **Color Management** → select the Samsung display → **Add Profile** → select `SxxB80xT`.
