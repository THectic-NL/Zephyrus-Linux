---
title: "Display Color Profiles"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS calibrates the panel of every GA605WV in the factory and ships the profiles in its Windows driver package. I found no other way to get them on Linux, so I took them out of that package by reverse engineering it, and put them in this repository.

**There is not much you can do with them yet.** By default your screen on Linux and GNOME already runs in its native, vivid colors, and GNOME does not apply a color profile to the screen itself, so adding one changes nothing you can see. I share them because they are hard to get any other way, and because they may become something nice to have: they are what a GNOME that applies a profile to the display would need (see below). Color-managed apps can already read a profile from colord.

## Where they come from

ASUS ships the factory profiles inside a per-model driver package for Windows. [G-Helper](https://github.com/seerge/g-helper) works with that package on Windows: it takes the model code from the BIOS version (`GA605WV.309` is a GA605WV), downloads the zip for that model from ASUS's CDN into `C:\ProgramData\ASUS\GameVisual`, and offers the profiles in it as Native, sRGB, DCIP3 and DisplayP3.

I recovered the Linux copies by reverse engineering the structure of that CDN and the contents of the driver zip. The URL looks like this:

```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

For the GA605WV it is `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`. The files in this repository are ASUS's own, as they came out of the package, with ASUS's technical names. The name says which one is yours: the model, the GPU (`1002` is AMD, `10DE` is NVIDIA) and the panel ID from the EDID, for example `GA605WV_1002_104D158E_CMDEF`. All of them are in the [`icc-profiles`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) folder, with a README that lists them.

## Why switching profiles in Settings does nothing

In **Settings → Color** you can add a profile to the built-in screen and pick one. That stores the choice in colord, and color-managed apps can use it, but GNOME does not apply the profile to the screen. The panel was made for calibrated profiles from a colorimeter. Those contain a gamma table (`vcgt`) that GNOME loads into the screen, and apps read the rest. The compositor reads nothing else out of a profile, and none of the ASUS profiles has a `vcgt`: the generic sRGB, DCI-P3 and Display P3 files are plain matrix profiles of under 700 bytes. So switching between them changes nothing you can see.

This is not specific to ASUS or to this laptop. The same thing is reported upstream for a wide gamut monitor with a profile and no `vcgt`: [mutter issue 4597](https://gitlab.gnome.org/GNOME/mutter/-/issues/4597). GNOME 52 is meant to change it. The display configuration then carries an ICC profile and the compositor applies it ([mutter merge request 5177](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/5177), still open at the time of writing). Until that ships, the screen shows the panel's native colors, and that is the vivid look you already have.

## What the setup window does

The [setup window]({{< relref "/docs/setup-script" >}}) has one item for this, **ASUS factory color profile**, in the Display section. It puts the factory profile of your panel in colord and makes it the active profile there, for color-managed apps. That is all: the picture on your screen does not change. **Select recommended** leaves it out.

It picks the profile that matches your GPU and panel, using the file name described above. The profiles are in this repository, so nothing is downloaded from ASUS, and each file is checked against a SHA-256 built into the script. After you switch GPU mode (Hybrid, Integrated or Ultimate), the screen hangs off another GPU and gets a profile of its own. Apply the item once more then.

An earlier version of the window also had a **Native** and **sRGB** switch. It is gone: switching changed nothing you could see, and Native is what the screen does by default anyway.

## What Windows can do that Linux cannot

Everything under **Flicker-free Dimming / Visual Mode** in G-Helper is one thing on Windows: `AsusSplendid.exe`, started with a different command for each control. The gamut list, the visual modes, the color temperature and the dimming slider all go through it ([the source](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). It comes with ASUS's own software, so G-Helper's source does not show what it does to the panel. The `.icm` files only decide which modes G-Helper lists, and they describe the panel after that switch. I found nothing like it on Linux: `asusctl` and the kernel's `asus-armoury` interface have `panel_overdrive` and nothing for the display.

| G-Helper | On GNOME |
|---|---|
| Gamut: Native | What the screen already does |
| Gamut: sRGB, DCIP3 and DisplayP3 | Nothing yet. The profiles exist, nothing applies them |
| Visual mode (Vivid, Cinema, FPS and the rest) | Nothing. Native is the vivid one |
| Color temperature | Night Light, in **Settings → Displays**. It warms the screen, on a schedule you set |
| Flicker-free dimming | Nothing that I found |

What is still missing is the compositor applying the factory profile itself. With that, the screen would be accurate from the measured values of your panel instead of the ones in its EDID. That is the GNOME 52 work above, and the reason these files are worth keeping around.

## Install them by hand

The setup window does the colord part for you. This is for doing it yourself. Nothing here is distribution-specific except where a profile is allowed to live: `/usr/share` is writable on CachyOS and read-only on Bazzite. The per-user location works identically on both, so if you only use one account, use that.

{{< callout type="warning" >}}
Only add the file that matches your GPU and panel. The generic `ASUS_sRGB`, `ASUS_DCIP3` and `ASUS_DisplayP3` files describe the modes ASUS's Windows tool switches to. Set active on Linux, they tell color-managed apps something that is not true about your screen.
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

**Install the color profiles:**

The ICC color profiles are located in the [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) directory of this repository. Clone the repository or manually download the profiles, then copy them into one of the locations listed above. Per-user works the same on both distributions:

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

**Technical Details:**

The profiles in this repository are ASUS's files as they came out of the driver package. The setup window only rewrites the description tag while it installs the profile (the name GNOME shows) and leaves the color data untouched.

{{% /details %}}
