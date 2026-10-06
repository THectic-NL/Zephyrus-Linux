---
title: "Display Color Profiles"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS calibrates the panel of every GA605WV in the factory and ships the profiles in its Windows driver package. Nothing applies them on Linux by itself, so the built-in screen stays on its defaults until you install them. The [setup window]({{< relref "/docs/setup-script" >}}) installs them for you and switches between the modes, the way G-Helper does on Windows.

## Switching modes

Open the setup window and go to **Display**. The **Color mode** switch works right away, there is no apply step, and the choice is saved, so it survives a restart. The **Undo** button in the notification puts the previous mode back.

| Mode | What you see | What color-managed apps are told |
|---|---|---|
| **Native** | The panel as it comes, with its whole wide gamut. sRGB content looks vivid and a bit oversaturated | The factory profile of your panel |
| **sRGB** | Colors the way sRGB content was made | The ASUS sRGB profile |
| **DCI-P3** | The same picture as Native | The ASUS DCI-P3 profile |
| **Display P3** | The same picture as Native | The ASUS Display P3 profile |

Only **sRGB** changes the picture, and it needs GNOME 50 or newer on Wayland. It uses GNOME's own `sdr-native` color mode: GNOME reads the real primaries of the panel from its EDID and maps sRGB content onto them. That is a conversion in software, the panel itself does not change. On an older GNOME the switch only changes the profile.

The two P3 modes only tell color-managed apps, such as image editors, what to expect from the screen. For the desktop itself they look like Native. A quick check: open a colorful image and switch between Native and sRGB. Native should be the more saturated one.

The Display page of the window also shows the model, the panel, the GPU the screen hangs off, and how much of sRGB and DCI-P3 the panel covers, as far as its EDID says.

### How it finds the right profiles

G-Helper takes the model code from the BIOS version (`GA605WV.309` is a GA605WV) and uses it to get the profile package for that model from ASUS. The setup window does the same lookup. It then picks the factory profile that matches your GPU and panel. The file name says which: the model, the GPU (`1002` is AMD, `10DE` is NVIDIA) and the panel ID from the EDID, for example `GA605WV_1002_104D158E_CMDEF`. The profiles are in this repository, so nothing is downloaded from ASUS, and each file is checked against a SHA-256 built into the script. The three generic ones (sRGB, DCI-P3, Display P3) are the same for every panel.

After you switch GPU mode (Hybrid, Integrated or Ultimate), the screen hangs off another GPU and gets a profile of its own. Apply **ASUS color profiles** in the setup window once more.

### What Linux cannot do

On Windows, G-Helper switches the gamut of the panel with ASUS's own software. It runs `AsusSplendid.exe` with a `GamutMode` command, and that talks to the firmware through the `ATKWMIACPIIO` driver ([the source](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). I found nothing like it on Linux: `asusctl` and the kernel's `asus-armoury` interface have `panel_overdrive` and nothing for gamut. The other ASUS Visual modes, Vivid for example, are firmware too, so they are not here either. Native is the vivid one.

A profile on its own does not change the picture. GNOME only reads the gamma table (`vcgt`) out of it, which is what Night Light changes, and none of the four ASUS profiles has one: the sRGB, DCI-P3 and Display P3 files are plain matrix profiles of about 640 bytes. I tried all four in Settings with nothing else switched. Nothing changed, while Night Light did. That is why the sRGB mode uses GNOME's color mode and the profile is only there for the apps.

The sRGB, DCI-P3 and Display P3 profiles describe the panel *after* ASUS's hardware switch. Without that switch they tell color-managed apps something that is not true for DCI-P3 and Display P3, so **Native** is the safest one to leave active.

## Install them by hand

The setup window does all of this. This is for doing it yourself. Nothing here is distribution-specific except where a profile is allowed to live: `/usr/share` is writable on CachyOS and read-only on Bazzite. The per-user location works identically on both, so if you only use one account, use that.

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

These color profiles were obtained by reverse engineering the ASUS Windows driver package. By analyzing the ASUS CDN structure and the contents of the driver ZIP files, all factory-calibrated profiles for this laptop were recovered. The files keep ASUS's own technical names, for example `ASUS_GA605WV_1002_104D158E_CMDEF`. The setup window installs them under readable ones.

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

The profiles in this repository are ASUS's files as they came out of the driver package. The setup window only rewrites the description tag while it installs them (the name GNOME shows) and leaves the color data untouched. [G-Helper](https://github.com/seerge/g-helper) does the Windows version of this: it downloads the zip for your model from ASUS's CDN into `C:\ProgramData\ASUS\GameVisual` and offers the profiles in it as Native, sRGB, DCIP3 and DisplayP3.

{{% /details %}}
