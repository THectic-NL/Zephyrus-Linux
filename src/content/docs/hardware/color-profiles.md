---
title: "Display Color Profiles"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS calibrates the panel of every GA605WV in the factory and ships the profiles in its Windows driver package. They are in this repository. The [setup window]({{< relref "/docs/setup-script" >}}) installs the factory profile of your panel and switches the screen between **Native** and **sRGB**, the two G-Helper modes that mean something on Linux.

## Why switching profiles in Settings does nothing

In **Settings → Color** you can add a profile to the built-in screen and pick one. That stores the choice in colord, and color-managed apps can use it, but GNOME does not apply the profile to the screen. The panel was made for calibrated profiles from a colorimeter. Those contain a gamma table (`vcgt`) that GNOME loads into the screen, and apps read the rest. The compositor reads nothing else out of a profile, and none of the ASUS profiles has a `vcgt`: the generic sRGB, DCI-P3 and Display P3 files are plain matrix profiles of under 700 bytes. So switching between them changes nothing you can see.

This is not specific to ASUS or to this laptop. The same thing is reported upstream for a wide gamut monitor with a profile and no `vcgt`: [mutter issue 4597](https://gitlab.gnome.org/GNOME/mutter/-/issues/4597). GNOME 52 is meant to change it. The display configuration then carries an ICC profile and the compositor applies it ([mutter merge request 5177](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/5177), still open at the time of writing). Until that ships, the only thing GNOME can do for the whole screen is the color mode below.

## Switching modes

Open the setup window and go to **Display**. The **Color mode** switch works right away, there is no apply step, and the choice is saved, so it survives a restart. The **Undo** button in the notification puts the previous mode back.

| Mode | What you see | What color-managed apps are told |
|---|---|---|
| **Native** | Vivid. The panel as it comes, with its whole wide gamut, so sRGB content is stretched to it | The factory profile of your panel |
| **sRGB** | Colors the way sRGB content was made | The ASUS sRGB profile |

**sRGB** needs GNOME 50 or newer on Wayland. It uses GNOME's own `sdr-native` color mode: GNOME reads the primaries, the white point and the gamma of the panel from its EDID and maps sRGB content onto them. That is a conversion in software, the panel itself does not change. It also lets apps that support Wayland color management use the whole gamut of the panel. GNOME offers the mode only when the EDID has all three, and Settings has no switch for it. The cost is that fullscreen apps usually can no longer skip the compositor (direct scanout), so a fullscreen game may get a little more latency. Switch back to Native for those if it matters.

To see that it works, the window shows five saturated colors under **Compare the colors**. In sRGB the reds and greens should look calmer than in Native.

If nothing changes, look at **This screen** on the same page. **GNOME color mode** shows what GNOME uses now and **GNOME offers** lists what it can do for this screen. `sdr-native` has to be in that list. `gdctl show --properties` shows the same under `supported-color-modes`. **Copy details** puts everything the window knows in the clipboard, which is what a bug report needs.

### Why no DCI-P3 or Display P3

The factory profile of the IPS panel says it covers about 94% of DCI-P3 by itself (the OLED covers all of it), so Native already is the wide gamut mode. G-Helper lists DCI-P3 and Display P3 on Windows because ASUS's own tool can switch to them. G-Helper shows a mode only when the matching profile file exists, and then asks `AsusSplendid.exe` to do the switch. The profiles describe the panel after that switch.

On Linux nothing does the switch. A P3 mode would show the same picture as Native while telling color-managed apps that the screen is DCI-P3, with a gamma of 2.6 where the panel has about 2.15. Their colors would come out wrong. So the window does not offer those two modes, and it installs only the profile of your panel and the sRGB one.

### How it finds the right profiles

G-Helper takes the model code from the BIOS version (`GA605WV.309` is a GA605WV) and uses it to get the profile package for that model from ASUS. The setup window does the same lookup. It then picks the factory profile that matches your GPU and panel. The file name says which: the model, the GPU (`1002` is AMD, `10DE` is NVIDIA) and the panel ID from the EDID, for example `GA605WV_1002_104D158E_CMDEF`. The profiles are in this repository, so nothing is downloaded from ASUS, and each file is checked against a SHA-256 built into the script.

After you switch GPU mode (Hybrid, Integrated or Ultimate), the screen hangs off another GPU and gets a profile of its own. Apply **ASUS color profiles** in the setup window once more.

### What Linux cannot do

Everything under **Flicker-free Dimming / Visual Mode** in G-Helper is one thing on Windows: `AsusSplendid.exe`, started with a different command for each control. The gamut list, the visual modes, the color temperature and the dimming slider all go through it ([the source](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). It comes with ASUS's own software, so G-Helper's source does not show what it does to the panel. I found nothing like it on Linux: `asusctl` and the kernel's `asus-armoury` interface have `panel_overdrive` and nothing for the display.

| G-Helper | On GNOME |
|---|---|
| Gamut: Native | **Native** in the setup window |
| Gamut: sRGB, if your G-Helper lists it | **sRGB** in the setup window |
| Gamut: DCIP3 and DisplayP3 | Not here, see above |
| Visual mode (Vivid, Cinema, FPS and the rest) | Nothing. Native is the vivid one |
| Color temperature | Night Light, in **Settings → Displays**. It warms the screen, on a schedule you set |
| Flicker-free dimming | Nothing that I found |

What is still missing is the compositor applying the factory profile itself. With that, the screen would be accurate from the measured values of your panel instead of the ones in its EDID. That is the GNOME 52 work above.

## Install them by hand

The setup window does all of this. This is for doing it yourself. Nothing here is distribution-specific except where a profile is allowed to live: `/usr/share` is writable on CachyOS and read-only on Bazzite. The per-user location works identically on both, so if you only use one account, use that.

{{< callout type="warning" >}}
Only add the file that matches your GPU and panel. The generic `ASUS_sRGB`, `ASUS_DCIP3` and `ASUS_DisplayP3` files describe the modes ASUS's Windows tool switches to. Set active on Linux, they tell color-managed apps something that is not true about your screen. `ASUS_sRGB` only fits while the screen is in the sRGB mode of the setup window.
{{< /callout >}}

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
