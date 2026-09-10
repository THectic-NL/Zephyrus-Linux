---
title: "asusctl & ROG Control Center"
weight: 1
prev: docs/hardware
next: docs/hardware/color-profiles
---

The Zephyrus G16 has a lot of hardware features that don't work out of the box on Linux: fan curves, performance profiles, the Slash LED on the lid, GPU switching, battery charge limiting. This page documents how I got all of it working using asusctl and the ASUS Linux project tools. Everything below the installation step is identical on both distributions, since it's the same daemon reading the same hardware. Only getting it installed differs.

{{< callout type="warning" >}}
**supergfxctl is abandoned.** If you come across guides that mention `supergfxctl` or `supergfxd` for GPU switching on ASUS laptops: don't use them. The project is unmaintained and poses security risks. Everything it used to handle is now part of `asusctl` and ROG Control Center, which are actively maintained by the asus-linux team.
{{< /callout >}}

**Package Information (at the time of writing):**
- `asusctl` 6.4.0: CLI frontend for fan curves, profiles, battery limit, RGB, Slash LED, GPU switching. Also ships `asusd`, the background daemon that actually talks to the hardware, and its systemd service — there's no separate `asusd` package to install, `pacman -Q asusd` / `rpm -q asusd` will come back empty even though the daemon is very much there.
- `rog-control-center` 6.4.0: graphical frontend, communicates with asusd
- Source: [asusctl releases](https://github.com/OpenGamingCollective/asusctl/releases) · in the CachyOS/Arch repos, and in [Terra](https://terra.fyralabs.com/) for Fedora

{{< callout type="info" >}}
Verify what's actually installed with `asusctl info` (prints the asusctl version alongside detected hardware) or `pacman -Q asusctl rog-control-center` / `rpm -q asusctl rog-control-center`.
{{< /callout >}}

{{< callout type="info" >}}
The project moved in 2026. Development used to live in the `asus-linux` GitLab organisation (now archived, read-only); `asusctl`, `asusd` and `rog-control-center` are now maintained under the [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl) on GitHub. [asus-linux.org](https://asus-linux.org/) is still the project site. Older guides that point at `gitlab.com/asus-linux` or the `lukenukem` Fedora COPR are out of date.
{{< /callout >}}

ROG Control Center describes itself, via its own **About** tab, as "a powerful graphical interface for managing ASUS ROG, TUF, and ProArt laptops on Linux... the official GUI for the asusctl toolset." It currently requires kernel 6.19, ships under the MPL-2.0 license, and lists its own work-in-progress items (widget theming, a CPU/GPU temp/fan info bar, Screenpad and ROG Ally-specific settings) — worth checking there yourself before assuming a missing feature is a bug.

![ROG Control Center - About tab](/images/rog-control-about.avif)


## Installation

{{% steps %}}

### Install asusctl and ROG Control Center

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S asusctl rog-control-center
```

Both packages come straight from the repos and everything works out of the box. No kernel patching or deep system configuration required.

{{< /tab >}}
{{< tab name="Bazzite" >}}

`asusd` is a system daemon with a kernel-facing job, so this is one of the few cases where layering is the right answer rather than a last resort. It isn't in Fedora's own repositories; the ASUS Linux packages live in [Terra](https://terra.fyralabs.com/).

Add the Terra repository, then layer the packages:

```bash
curl -fsSL https://github.com/terrapkg/subatomic-repos/raw/main/terra.repo | pkexec tee /etc/yum.repos.d/terra.repo
rpm-ostree install terra-release
systemctl reboot
```

```bash
rpm-ostree install asusctl rog-control-center
systemctl reboot
```

Two reboots, because a layered package is applied to the next image rather than the running one.

{{< callout type="warning" >}}
Check before you layer. Bazzite images built for ASUS handhelds already ship `asusctl`, and layering a package that's in the image is a conflict rather than an upgrade:

```bash
rpm -q asusctl
ujust
```

If `asusctl` is already there, or `ujust` lists an ASUS recipe, use that instead.
{{< /callout >}}

The older `lukenukem/asus-linux` COPR that most guides point at is no longer maintained. Use Terra.

{{< /tab >}}
{{< /tabs >}}

This gives you:
- `asusd`: the backend daemon that manages all ASUS hardware features
- `asusctl`: CLI frontend that communicates with asusd
- `rog-control-center`: graphical frontend that communicates with asusd

### Enable services

```bash
sudo systemctl enable --now asusd.service
```

Reboot to ensure all services start correctly:
```bash
sudo reboot
```

### Verify hardware detection

After reboot, verify asusctl detected your hardware correctly:

```bash
asusctl info
```

Expected output should include:
```
Product family: ROG Zephyrus G16
Board name: GA605WV
```

### Install monitoring tools (optional)

Useful utilities for monitoring hardware alongside asusctl:

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S nvtop powertop s-tui lm_sensors i2c-tools
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

These are command-line tools, so Homebrew or a distrobox container is the right place for them rather than the image:

```bash
brew install nvtop powertop s-tui
```

`lm_sensors` and `i2c-tools` read hardware directly and want to be on the host. `lm_sensors` is generally already present; layer `i2c-tools` if you need it:

```bash
rpm-ostree install i2c-tools
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

| Package | Description |
|---------|-------------|
| `nvtop` | GPU process monitor (AMD + NVIDIA simultaneously) |
| `powertop` | Power consumption analysis per process/device |
| `s-tui` | TUI dashboard: CPU frequency, temperature, load, stress test |
| `lm_sensors` | Hardware temperature sensor readout |
| `i2c-tools` | Low-level hardware bus diagnostics |

{{% /steps %}}


## Configuration

{{% details title="Set battery charge limit (recommended: 80%)" closed="true" %}}

Limiting the charge to 80% significantly extends battery lifespan. The laptop runs normally on AC power regardless of this setting.

**Set via CLI:**
```bash
asusctl battery --charge-limit 80
```

**Set via GUI:**
Open ROG Control Center (`rog-control-center`) → System Control → Battery Charge Limit.

**Verify:**
```bash
asusctl battery
```

This setting persists across reboots and is managed by `asusd`.

{{% /details %}}

{{% details title="Configure Slash LED (the light bar on the lid)" closed="true" %}}

The Slash LED is the diagonal light bar on the lid of the G16. It supports multiple animations and can be configured to turn off on battery.

**Show available animations:**
```bash
asusctl slash --list
```

Available animations: `Static`, `Bounce`, `Slash`, `Loading`, `BitStream`, `Transmission`, `Flow`, `Flux`, `Phantom`, `Spectrum`, `Hazard`, `Interfacing`, `Ramp`, `GameOver`, `Start`, `Buzzer`

**Recommended setup (AC only, off on battery and during sleep):**
```bash
asusctl slash --enable -b false -s false
```

**What these flags do:**
- `--enable`: turn on the Slash LED
- `-b false`: disable on battery power
- `-s false`: disable during sleep

**Set animation:**
```bash
asusctl slash --mode Spectrum
```

**Set brightness (0–255):**
```bash
asusctl slash -l 128
```

![ROG Control Center - Slash Lighting](/images/rog-control-slash-lighting.avif)

{{% /details %}}

{{% details title="Performance profiles" closed="true" %}}

asusctl provides three performance profiles that control CPU/GPU power limits and fan behavior:

| Profile | Description |
|---------|-------------|
| `Silent` | Low power, quiet fans, throttled performance |
| `Balanced` | Default. Moderate power and noise |
| `Performance` | Maximum CPU/GPU power, aggressive fans |

**Set a profile:**
```bash
asusctl profile -P Balanced
asusctl profile -P Silent
asusctl profile -P Performance
```

**Cycle through profiles:**
```bash
asusctl profile --next
```

**Check current profile:**
```bash
asusctl profile
```

> **Note:** Profile switching requires `power-profiles-daemon` to be running. See the installation steps above.

{{% /details %}}

{{% details title="GPU mode switching (ROG Control Center / asusctl armoury)" closed="true" %}}

The GA605WV has a hybrid GPU setup with a physical MUX switch: the AMD Radeon 890M (iGPU) and the NVIDIA RTX 4060 (dGPU) can each drive the internal display, not just the iGPU as earlier revisions of this page assumed.

GPU switching is managed via ROG Control Center (GUI, **GPU Configuration** tab) or `asusctl armoury` (CLI), both of which interface directly with the `asus-armoury` kernel driver (available since kernel 6.19).

**Confirmed on this hardware, current ROG Control Center build:** the GPU Configuration tab exposes three modes:

| Mode | Description |
|------|-------------|
| Hybrid | Both GPUs active. NVIDIA handles GPU workloads, AMD drives the display. Best for gaming. |
| Integrated | Only AMD iGPU. Lower power consumption, no NVIDIA. Good for battery. |
| Ultimate | dGPU drives the display directly via the physical MUX. Highest NVIDIA performance, no iGPU overhead — but the AMD iGPU is unavailable while active. |

{{< callout type="warning" >}}
**Ultimate mode is new to this page.** Earlier versions of this guide only listed Hybrid/Integrated via `dgpu_disable`, written before the physical MUX and Ultimate mode were confirmed on this laptop. The CLI property for switching into Ultimate mode hasn't been verified yet — treat the `dgpu_disable` commands below as covering only Hybrid/Integrated until that's confirmed on-device.

**Mode switches can silently fail to apply.** A known upstream bug (see [Known Issues]({{< relref "/docs/known-issues" >}})) can abort the mode-switch write during shutdown with no error shown to you — the dropdown just shows the old mode again after reboot, from both the GUI and `asusctl armoury`. If a switch doesn't seem to take, that's the likely cause, not something wrong with your setup.
{{< /callout >}}

**Switch via GUI (ROG Control Center):**

Open ROG Control Center and go to **GPU Configuration** in the sidebar. Pick a mode from the **GPU mode** dropdown.

![ROG Control Center - GPU Configuration showing Integrated/Ultimate/Hybrid](/images/rog-control-gpu-configuration.avif)

> The dropdown always shows the current mode; changes only take effect after a reboot. You can't switch live yet, unlike Windows tools such as G-Helper.

**Switch via CLI (asusctl armoury) — Hybrid and Integrated only:**

**Check current dGPU state:**
```bash
asusctl armoury get dgpu_disable
```

**Switch to iGPU-only (disable dGPU):**
```bash
asusctl armoury set dgpu_disable 1
```

**Switch to Hybrid (enable dGPU):**
```bash
asusctl armoury set dgpu_disable 0
```

> **Note:** A reboot or logout/login may be required after switching modes.

> **Important:** Keep `nvidia-powerd.service` masked on this laptop regardless of GPU mode — see [Known Issues]({{< relref "/docs/known-issues" >}}) for why.

{{% /details %}}

{{% details title="App Settings (background & tray behavior)" closed="true" %}}

ROG Control Center has an **App Settings** tab controlling how the app itself runs, separate from hardware configuration:

- **Run in background after closing** — keep `asusd`/the tray icon alive when the window is closed
- **Start app in background (UI closed)** — launch minimized to tray
- **Enable system tray icon**
- **Enable dGPU notifications** — pops up a notification when the dGPU is suspended/resumed (this is the "dGPU status changed: suspended" toast you'll see after switching GPU modes or letting the dGPU idle down)

![ROG Control Center - App Settings](/images/rog-control-app-settings.avif)

The app marks this tab **work in progress**; notifications in particular are incomplete.

{{% /details %}}

{{% details title="Keyboard RGB (Aura)" closed="true" %}}

**Set keyboard backlight brightness (0–100):**
```bash
asusctl led-brighter
asusctl led-dimmer
```

**Open Aura configuration in ROG Control Center:**
```bash
rog-control-center
```

Navigate to the "Keyboard Aura" section for animation, color, and per-key configuration.

![ROG Control Center - Keyboard Aura](/images/rog-control-keyboard-aura.avif)

{{% /details %}}

{{% details title="Custom fan curves" closed="true" %}}

Fan curves can be configured per performance profile in ROG Control Center or via CLI.

**Open ROG Control Center:**
```bash
rog-control-center
```

Navigate to "Fan Curves" to set temperature/speed curves per profile (Silent, Balanced, Performance).

**CLI fan curve format:**
```bash
# Show current fan curve data for a profile
asusctl fan-curve -m Balanced

# Set a custom curve (8 temperature/speed pairs: temp:speed,temp:speed,...)
asusctl fan-curve -m Balanced -D 30:0,40:10,50:30,60:50,70:70,80:85,90:100,100:100
```

![ROG Control Center - Fan Curves](/images/rog-control-fan-curves.avif)

> **Note:** Fan curve customization requires the `asus-armoury` kernel driver. On kernel < 6.19, the driver is not available and curves set in the GUI may not persist as expected. See the [Known Issues]({{< relref "/docs/known-issues" >}}) page for details.

{{% /details %}}


## Monitoring

{{% details title="Hardware monitoring commands" closed="true" %}}

**GPU monitor (AMD + NVIDIA):**
```bash
nvtop
```

**CPU frequency, temperature, load dashboard:**
```bash
s-tui
```

**Power consumption per process/device:**
```bash
sudo powertop
```

**Hardware temperatures:**
```bash
sensors
```

**Check asusd service logs:**
```bash
sudo journalctl -b -u asusd
```

{{% /details %}}


{{< callout type="info" >}}
Known issues and troubleshooting for asusctl & ROG Control Center are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}


## CLI Quick Reference

| Command | Description |
|---------|-------------|
| `asusctl info` | Show detected hardware |
| `asusctl battery --charge-limit 80` | Set battery charge limit to 80% |
| `asusctl battery` | Show current charge limit |
| `asusctl profile` | Show current performance profile |
| `asusctl profile -P Balanced` | Set performance profile |
| `asusctl profile --next` | Cycle to next profile |
| `asusctl slash --list` | List available Slash LED animations |
| `asusctl slash --enable -b false -s false` | Enable Slash LED, off on battery and sleep |
| `asusctl slash --mode Spectrum` | Set Slash LED animation |
| `asusctl slash -l 128` | Set Slash LED brightness (0–255) |
| `asusctl armoury get dgpu_disable` | Show current dGPU state (0=enabled, 1=disabled) |
| `asusctl armoury set dgpu_disable 1` | Switch to iGPU-only (disable dGPU) |
| `asusctl armoury set dgpu_disable 0` | Switch to Hybrid mode (enable dGPU) |
| `rog-control-center` | Open ROG Control Center GUI |


## Kernel Updates

### Kernel 6.19: asus-armoury driver lands in mainline

The `asus-armoury` driver has been [merged into Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). This new `platform/x86` driver replaces parts of the older `asus-wmi` with a cleaner sysfs-based API, enabling panel mode switching, APU memory allocation, PPT tuning, and more directly from the kernel. The driver is entirely community-developed by the [asus-linux team](https://asus-linux.org/), with no involvement from ASUS themselves. This driver has been included in every CachyOS kernel from 6.19 onwards. The current kernel at the time of writing is 7.2.4-1-cachyos.

**Before**: basic asusctl controls without Armoury settings:

![ROG Control before asus-armoury in mainline](/images/rog-control-armoury.avif)

**After**: full Armoury settings exposed, including PPT/power limit tuning:

![ROG Control System Control with Armoury settings and power limit tuning](/images/rog-control-system-control.avif)

**Sources:** [Phoronix article](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussion](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)

### Kernel 7.0: ASUS laptop quirks + newer AMDGPU enablement

Kernel 7.0 shipped in April 2026 and CachyOS picked it up fast. For this ASUS ROG G16 it delivered what was promised: better AMDGPU coverage for newer RDNA 3.5-class IP blocks (GFX11.5.4) and further NVIDIA work. Gaming performance on the Radeon 890M improved noticeably, roughly in line with the ~20% uplift that was anticipated. Combined with the improvements from 6.19, this hardware finally runs the way it should on Linux. The current CachyOS kernel is 7.2.4-1-cachyos.

**Sources:** [Linus confirms Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks for ASUS ROG models](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)


## Additional Resources

- [asus-linux.org](https://asus-linux.org/): official project site
- [asusctl on GitHub](https://github.com/OpenGamingCollective/asusctl): source code and issue tracker
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/): CachyOS-specific documentation
- NVIDIA driver setup and known issues: [CachyOS]({{< relref "/docs/cachyos/nvidia" >}}) · [Bazzite]({{< relref "/docs/bazzite/nvidia" >}})
