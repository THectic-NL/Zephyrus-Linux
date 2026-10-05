---
title: "Display Color Profiles"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS factory-calibrates the panel in every GA605WV and ships the profiles through its Windows driver package. Nothing applies them on Linux, so the built-in display is left on its defaults until you install the profiles by hand.

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
| `~/.local/share/icc/` | Current user only. **Use this** |
| `/usr/local/share/color/icc/` | System-wide. `/usr/local` is a symlink to `/var/usrlocal` on an atomic system, so it survives image updates and is writable |

Layering a profile into the image with `rpm-ostree` would work but is the wrong tool: these are data files for your account, not part of the system.

{{< /tab >}}
{{< /tabs >}}

## The profiles

{{< callout type="info" >}}
**One command instead of the steps below.** The [setup script]({{< relref "/docs/setup-script" >}}) installs the four profiles G-Helper lists on Windows, **Native** (the factory-calibrated profile of your panel), **sRGB**, **DCI-P3** and **Display P3**, under readable names in colord's own profile folder, and adds them to the Built-in Screen, so you can pick one in Settings → Color Management. Switch from the terminal with `python3 zephyrus-setup.py color set srgb`.

**This does not change how your screen looks.** On Linux a profile tells color-managed apps (browsers, image editors, video players) what the panel does. It does not switch the panel's own gamut mode the way ASUS's Windows software does. [G-Helper's source](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs) switches the gamut by running ASUS's `AsusSplendid.exe` with a `GamutMode` command, which talks to the firmware through the `ATKWMIACPIIO` driver; the `.icm` files only sit next to that. I found no sign that `asusctl` or the kernel's `asus-armoury` interface exposes such a switch: on this laptop its attributes include `panel_overdrive` but nothing for gamut. GNOME's own contribution is limited too. It applies a profile's `vcgt` gamma table (that is what Night Light changes), and none of these four profiles has one: the sRGB, DCI-P3 and Display P3 files are plain matrix profiles of about 640 bytes. Tested here by switching between all four while watching the screen: nothing changes, while Night Light does.

One more consequence: the sRGB, DCI-P3 and Display P3 profiles describe the panel *after* ASUS's hardware switch. Without that switch they tell color-managed apps the wrong thing, so **Native** is the one to leave active.
{{< /callout >}}

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

These color profiles were obtained by reverse engineering the ASUS Windows driver package. By analyzing the ASUS CDN structure and the contents of the driver ZIP files, all factory-calibrated profiles for this laptop were recovered. The files keep ASUS's own technical names, for example `ASUS_GA605WV_1002_104D158E_CMDEF`. The setup script installs them under readable ones.

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
4. Select the profile matching your display and GPU combination (e.g. **ASUS GA605WV 1002 104D158E CMDEF** for AMD iGPU + Sharp LQ160R1JW02)
5. Click **Add**

**Note:** Copied by hand, the profiles show up under their technical names, like "ASUS GA605WV 1002 104D158E CMDEF". If a profile you just copied is missing, close Settings and reopen it, or log out and back in to refresh the color cache.

The filename encodes your GPU (`1002` = AMD, `10DE` = NVIDIA) and panel ID. Match them to your unit using the panel table above. All profiles are in the [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) directory.

**Background:**

The profiles were found through analysis of ASUS Windows driver packages. The ASUS CDN URL structure:
```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

For the GA605WV, this is: `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`

**Technical Details:**

The profiles in this repository are ASUS's files as they came out of the driver package. The setup script only rewrites the description tag while it installs them (the name GNOME shows) and leaves the color data untouched. [G-Helper](https://github.com/seerge/g-helper) does the Windows version of this: it downloads the zip for your model from ASUS's CDN into `C:\ProgramData\ASUS\GameVisual` and offers the profiles in it as Native, sRGB, DCIP3 and DisplayP3.

{{% /details %}}
