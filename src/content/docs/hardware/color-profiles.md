---
title: "Display Color Profiles"
weight: 6
prev: docs/hardware/asusctl-rog-control
next: docs/security/autologin
---

ASUS factory-calibrates the panel in every GA605WV and ships the profiles through its Windows driver package. Nothing applies them on Linux, so both the built-in display and an external Samsung ViewFinity are left on their defaults until you install the profiles by hand.

Nothing on this page is distribution-specific except where a profile is allowed to live: `/usr/share` is writable on CachyOS and read-only on Bazzite. The per-user location works identically on both, so if you only use one account, use that and skip the question entirely.

{{< tabs >}}
{{< tab name="CachyOS" >}}

| Location | Scope |
|---|---|
| `/usr/share/color/icc/colord/` | System-wide (all users, requires root) |
| `~/.local/share/icc/` | Current user only |

{{< /tab >}}
{{< tab name="Bazzite" >}}

`/usr` belongs to the image and is read-only, so the system-wide path from the CachyOS tab does not exist here. Use the per-user location:

| Location | Scope |
|---|---|
| `~/.local/share/icc/` | Current user only — **use this** |
| `/usr/local/share/color/icc/` | System-wide. `/usr/local` is a symlink to `/var/usrlocal` on an atomic system, so it survives image updates and is writable |

Layering a profile into the image with `rpm-ostree` would work but is the wrong tool: these are data files for your account, not part of the system.

{{< /tab >}}
{{< /tabs >}}

## The profiles

{{% details title="Install ASUS GameVisual color profiles for GA605WV built-in display" closed="true" %}}

The GA605WV ships with a 16" 2560x1600 240Hz ROG Nebula Display. ASUS factory-calibrates each panel and provides color profiles via their ASUS System Control Interface. On Windows, these are automatically applied by Armoury Crate/GameVisual. On Linux, we must install them manually.

The GA605WV was shipped with different panels depending on the unit. The standard model uses an IPS panel (ROG Nebula Display); some configurations ship with an OLED panel instead:

| Panel ID | Manufacturer | Model | Type |
|---|---|---|---|
| `104D158E` | Sharp | LQ160R1JW02 | IPS (ROG Nebula Display) |
| `834C41AE` | Samsung | ATNA60DL04-0 ([LaptopMedia](https://laptopmedia.com/screen/atna60dl04-0-sdc41ae/) · [Linux Hardware](https://linux-hardware.org/?id=eisa:samsung-sdc41ae)) | OLED |
| `E5090C19` | Unknown | (present in ASUS driver package, not yet publicly identified) | Unknown |

To check which panel your unit has:

```bash
cat /sys/class/drm/card*-eDP-*/edid | edid-decode 2>/dev/null | grep -i "manufacturer\|model\|product name"
```

These color profiles were obtained by reverse engineering the ASUS Windows driver package. By analyzing the ASUS CDN structure and the contents of the driver ZIP files, all factory-calibrated profiles for this laptop were recovered. The ICC metadata was then modified so the profiles appear with readable names directly in GNOME Color Management.

**Install the color profiles:**

The ICC color profiles are located in the [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) directory of this repository. Clone the repository or manually download the profiles, then copy them into one of the locations listed at the top of this page. Per-user works the same on both distributions:

```bash
mkdir -p ~/.local/share/icc
cp GA605WV_1002_104D158E_CMDEF.icm ~/.local/share/icc/
```

**Activate your profile in GNOME:**

1. Open **Settings** → **Color Management**
2. Select your display (e.g. **Built-In Screen**)
3. Click **Add Profile**
4. Select the profile matching your display and GPU combination (e.g. **Native** for AMD iGPU + Sharp LQ160R1JW02)
5. Click **Add**

**Note:** If GNOME Settings shows old technical names (e.g., "ASUS GA605WV 1002 104D158E CMDEF" instead of "Native"), close Settings and reopen, or log out/in to refresh the color cache.

The filename encodes your GPU (`1002` = AMD, `10DE` = NVIDIA) and panel ID. Match them to your unit using the panel table above. All profiles are in the [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) directory.

**Background:**

The profiles were found through analysis of ASUS Windows driver packages. The ASUS CDN URL structure:
```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

For the GA605WV, this is: `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`

**Technical Details:**

The profiles in this repository are pre-processed with custom ICC metadata 'desc' tags so they appear with readable names directly in GNOME Color Management. For users interested in how such modifications work, you can implement similar ICC 'desc' tag manipulation yourself using Python's PIL/ImageCms.

{{% /details %}}

{{% details title="Install Samsung color profile for LS27B800TGUXEN (S80TB) Thunderbolt display" closed="true" %}}

The Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN) ships with a factory color profile (`SxxB80xT.icm`) included in the Windows INF driver package. On Linux, this profile must be installed manually.

The profile is located in the [`/icc-profiles/LS27B800TGUXEN - S80TB/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles/LS27B800TGUXEN%20-%20S80TB) directory of this repository.

**Install the color profile:**

Same locations as above:

```bash
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

**Activate in GNOME:**

1. Open **Settings** → **Color Management**
2. Select the **Samsung display** (e.g. "LS27B800TGUXEN")
3. Click **Add Profile**
4. Select `SxxB80xT`
5. Click **Add**

{{% /details %}}
