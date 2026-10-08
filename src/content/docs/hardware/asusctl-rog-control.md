---
title: "asusctl & ROG Control Center"
weight: 1
prev: docs/hardware
next: docs/hardware/color-profiles
---

The Zephyrus G16 has a lot of hardware features that don't work out of the box on Linux: fan curves, performance profiles, the Slash LED on the lid, GPU switching, battery charge limiting. This page documents how I got all of it working using asusctl and the ASUS Linux project tools. Everything below the installation step is identical on both distributions, since it's the same daemon reading the same hardware. Only getting it installed differs.

**Package information (at the time of writing):**
- `asusctl` 6.5.0: CLI frontend for fan curves, profiles, battery limit, RGB, Slash LED, GPU switching. Also ships `asusd`, the background daemon that actually talks to the hardware, and its systemd service. There's no separate `asusd` package to install: `pacman -Q asusd` / `rpm -q asusd` will come back empty even though the daemon is very much there.
- `rog-control-center` 6.5.0: graphical frontend, communicates with asusd
- Source: [asusctl releases](https://github.com/OpenGamingCollective/asusctl/releases) · in the CachyOS/Arch repos, and in [Terra](https://terra.fyralabs.com/) for Fedora
- Check what is installed with `asusctl info` (prints the asusctl version alongside the detected hardware) or `pacman -Q asusctl rog-control-center` / `rpm -q asusctl rog-control-center`

{{< callout type="warning" >}}
**Older guides are out of date.** `supergfxctl` and `supergfxd` are abandoned: the [Arch Wiki](https://wiki.archlinux.org/title/Supergfxctl) calls them deprecated and unmaintained, and asusctl's [changelog](https://github.com/OpenGamingCollective/asusctl/blob/main/CHANGELOG.md) lists "Remove supergfxctl completely" in 6.3.9. GPU mode switching is now part of `asusctl` (`asusctl armoury`) and ROG Control Center. The project moved in 2026 as well, from the archived `asus-linux` GitLab organisation to the [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl) on GitHub ([asus-linux.org](https://asus-linux.org/) is still the project site), so guides that point at `gitlab.com/asus-linux` or the `lukenukem` Fedora COPR are out of date too.
{{< /callout >}}

ROG Control Center describes itself, via its own **About** tab, as "a powerful graphical interface for managing ASUS ROG, TUF, and ProArt laptops on Linux... the official GUI for the asusctl toolset." It currently requires kernel 6.19, ships under the MPL-2.0 license, and lists its own work-in-progress items (widget theming, a CPU/GPU temp/fan info bar, Screenpad and ROG Ally-specific settings). Worth checking there yourself before assuming a missing feature is a bug.

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

When you generate your download on [bazzite.gg](https://bazzite.gg/), use the hardware picker and select **ASUS Laptop** under "What hardware are you using?" instead of a generic desktop option. It tailors the recommended image and setup steps to this hardware.

Don't layer `asusctl`/`rog-control-center` into the image yourself with `rpm-ostree install`. `asusd` is a system daemon with a kernel-facing job, which is normally a case for layering, but Bazzite ships its own maintained install path for it:

```bash
ujust asus
```

Installs `asusctl-linux` and `rog-control-center-linux` as Homebrew casks and enables the required services right away. No image layering, no reboot. The same install/uninstall toggle also shows up as "asusctl & ROG Control Center" in the first-boot setup wizard (yafti), if you'd rather turn it on there.

{{< callout type="warning" >}}
Already layered `asusctl`/`rog-control-center` from an older guide, including an earlier version of this page? `ujust asus` detects the layered packages, offers to remove them for you, then installs the Homebrew version in their place.
{{< /callout >}}

Older guides (including an earlier version of this page) point at the Terra repo or the unmaintained `lukenukem/asus-linux` COPR for these packages. Neither is needed for this anymore.

{{< /tab >}}
{{< /tabs >}}

This gives you:
- `asusd`: the backend daemon that manages all ASUS hardware features
- `asusctl`: CLI frontend that communicates with asusd
- `rog-control-center`: graphical frontend that communicates with asusd

### Confirm asusd is running

Don't enable `asusd.service` yourself. It ships as a `static` unit with no `[Install]` section, so `systemctl enable` has nothing to do. On this hardware family (the udev rule matches ROG, Zephyrus, TUF, Strix and a few others), `99-asusd.rules` starts it automatically once the `asus-nb-wmi` kernel driver loads, and on Bazzite `ujust asus` already enabled what it needs. [Upstream documents this directly](https://opengamingcollective.github.io/asusctl/distributions/arch.html): "the service doesn't need to be enabled and is not supposed to be."

Confirm it's actually running:
```bash
systemctl status asusd.service
```

Reboot if you just installed it, so the driver, udev rule, and daemon all initialize cleanly together:
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
asusctl battery limit 80
```

**Set via GUI:**
Open ROG Control Center (`rog-control-center`) → System Control → Battery Info → Charge limit.

**Verify:**
```bash
asusctl battery info
```

This setting persists across reboots and is managed by `asusd`.

{{% /details %}}

{{% details title="Configure Slash LED (the light bar on the lid)" closed="true" %}}

The Slash LED is the diagonal light bar on the lid of the G16. It supports multiple animations and can be configured to turn off on battery.

**Show available animations:**
```bash
asusctl slash list
```

Available animations: `Static`, `Bounce`, `Slash`, `Loading`, `BitStream`, `Transmission`, `Flow`, `Flux`, `Phantom`, `Spectrum`, `Hazard`, `Interfacing`, `Ramp`, `GameOver`, `Start`, `Buzzer`

**Recommended setup (AC only, off on battery and during sleep):**
```bash
asusctl slash set --enable -b false -s false
```

**What these flags do:**
- `--enable`: turn on the Slash LED
- `-b false`: disable on battery power
- `-s false`: disable during sleep

**Set animation:**
```bash
asusctl slash set --mode Spectrum
```

**Set brightness (0–255):**
```bash
asusctl slash set -l 128
```

![ROG Control Center - Slash Lighting](/images/rog-control-slash-lighting.avif)

{{% /details %}}

{{% details title="Performance profiles" closed="true" %}}

asusctl provides three performance profiles that control CPU/GPU power limits and fan behavior:

| Profile | Description |
|---------|-------------|
| `Quiet` (a.k.a. `LowPower`) | Low power, quiet fans, throttled performance. asusctl exposes whichever of the two names the kernel's `platform_profile` handler registers for this hardware, and auto-substitutes the other one if you ask for the unavailable name. |
| `Balanced` | Default. Moderate power and noise |
| `Performance` | Maximum CPU/GPU power, aggressive fans |

**Set a profile:**
```bash
asusctl profile set Balanced
asusctl profile set Quiet
asusctl profile set Performance
```

**Cycle through profiles:**
```bash
asusctl profile next
```

**Check current profile:**
```bash
asusctl profile get
```

{{< callout type="warning" >}}
**Don't run `power-profiles-daemon` or `tuned` alongside asusd.** asusd manages performance profiles and CPU EPP directly through the `platform_profile` ACPI interface, and a competing daemon writing to the same interface causes race conditions. [Upstream recommends](https://opengamingcollective.github.io/asusctl/distributions/arch.html) picking one:

```bash
sudo systemctl mask --now power-profiles-daemon.service
# or, if you use tuned instead:
sudo systemctl mask --now tuned.service tuned-ppd.service
```

`mask`, not `disable`: [upstream notes](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) that KDE Plasma's PowerDevil can respawn `power-profiles-daemon` via D-Bus activation even after a plain `disable`, the same class of problem as the `nvidia-powerd` conflict in [Known Issues]({{< relref "/docs/known-issues" >}}). If you'd rather keep the external daemon and let it own profile switching instead, turn off asusd's own management by setting `platform_profile_linked_epp`, `change_platform_profile_on_battery`, and `change_platform_profile_on_ac` to `false` in `/etc/asusd/asusd.ron`.
{{< /callout >}}

{{< callout type="info" >}}
**Why guides disagree about power-profiles-daemon.** The [asus-linux.org Arch guide](https://asus-linux.org/guides/arch-guide/) says "Asusctl is designed to work primarily with power-profiles-daemon" and tells you to enable it. The Open Gaming Collective, which maintains asusctl now, says the opposite: its [Arch](https://opengamingcollective.github.io/asusctl/distributions/arch.html) and [Bazzite](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) guides and its [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md) all warn that running both can cause race conditions, and offer the two ways out above. Two things point the same way. [Issue #205](https://github.com/OpenGamingCollective/asusctl/issues/205) reports PPD silently resetting asusd's EPP value to the amd_pstate default (asusd 6.3.10, a Strix G16), and since [PR #217](https://github.com/OpenGamingCollective/asusctl/pull/217) (merged August 3, 2026) asusctl and ROG Control Center print a warning when PPD runs next to asusd. The Arch package of asusctl 6.5.0 doesn't depend on PPD either: `pacman -Qi asusctl` lists only `glibc`, `libgcc`, `libusb` and `systemd-libs`. The [changelog](https://github.com/OpenGamingCollective/asusctl/blob/main/CHANGELOG.md) says profiles depended on PPD in 4.0.0, and that asusd uses the kernel's `platform_profile` interface only from 6.1.

One catch in that warning: it promises that asusd then handles the "KDE/GNOME sliders natively". The part of the pull request that would have done that, a replacement for PPD's D-Bus interface, was split off and dropped before the merge. So with PPD masked, GNOME's Power Mode switch has nothing behind it. On this laptop `net.hadess.PowerProfiles` is still listed as activatable on the system bus, but its unit is masked. Switch profiles with `asusctl profile next` or ROG Control Center instead. The mask-instead-of-disable advice was asked for in [issue #264](https://github.com/OpenGamingCollective/asusctl/issues/264).
{{< /callout >}}

{{% /details %}}

{{% details title="GPU mode switching (ROG Control Center / asusctl armoury)" closed="true" %}}

The GA605WV has a hybrid GPU setup with a physical MUX switch: the AMD Radeon 890M (iGPU) and the NVIDIA RTX 4060 (dGPU) can each drive the internal display, not just the iGPU as earlier revisions of this page assumed.

GPU switching is managed via ROG Control Center (GUI, **GPU Configuration** tab) or `asusctl armoury` (CLI), both of which interface directly with the `asus-armoury` kernel driver (available since kernel 6.19).

**Confirmed on this hardware, current ROG Control Center build:** the GPU Configuration tab exposes three modes:

| Mode | Description |
|------|-------------|
| Hybrid | Both GPUs active. NVIDIA handles GPU workloads, AMD drives the display. Best for gaming. |
| Integrated | Only AMD iGPU. Lower power consumption, no NVIDIA. Good for battery. |
| Ultimate | dGPU drives the display directly via the physical MUX. Highest NVIDIA performance, no iGPU overhead, though the AMD iGPU is unavailable while active. |

{{< callout type="warning" >}}
**The three modes map to two firmware attributes**, `dgpu_disable` and `gpu_mux_mode`, both under `/sys/class/firmware-attributes/asus-armoury/attributes/<name>/current_value`. Confirmed against asusd's own source (the `asus-shutdown` test suite) and cross-checked against this hardware's actual sysfs values:

| Mode | `dgpu_disable` | `gpu_mux_mode` |
|------|------|------|
| Ultimate | 0 | 0 |
| Hybrid | 0 | 1 |
| Integrated | 1 | 1 |

Hybrid ↔ Integrated only ever changes `dgpu_disable`; Ultimate is the only mode that also flips `gpu_mux_mode`.

**Mode switches can silently fail to apply.** A known upstream bug (see [Known Issues]({{< relref "/docs/known-issues" >}})) can abort the mode-switch write during shutdown with no error shown to you. The dropdown just shows the old mode again after reboot, whether you switched from the GUI or `asusctl armoury`. If a switch doesn't seem to take, that's the likely cause. Writing only the attribute that actually needs to change directly to its sysfs path above (bypassing asusd entirely) sidesteps the bug, at the cost of asusd/the GUI not knowing about the change until it catches up.
{{< /callout >}}

**Switch via GUI (ROG Control Center):**

Open ROG Control Center and go to **GPU Configuration** in the sidebar. Pick a mode from the **GPU mode** dropdown.

![ROG Control Center - GPU Configuration showing Integrated/Ultimate/Hybrid](/images/rog-control-gpu-configuration.avif)

> The dropdown itself always says changes need a reboot. In direct sysfs testing (see [Known Issues]({{< relref "/docs/known-issues" >}})), re-enabling the dGPU (→ Hybrid) actually applied live, no reboot needed; disabling it (→ Integrated) did not. Whether the same asymmetry holds through this normal GUI/asusd path is unconfirmed, since that path has its own known bug (below) that can prevent the switch from applying at all.

**Switch via CLI (asusctl armoury), Hybrid and Integrated only:**

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

{{% /details %}}

{{% details title="App Settings (background & tray behavior)" closed="true" %}}

ROG Control Center has an **App Settings** tab controlling how the app itself runs, separate from hardware configuration:

- **Run in background after closing**: keep `asusd`/the tray icon alive when the window is closed
- **Start app in background (UI closed)**: launch minimized to tray
- **Enable system tray icon**
- **Enable dGPU notifications**: pops up a notification when the dGPU is suspended/resumed (this is the "dGPU status changed: suspended" toast you'll see after switching GPU modes or letting the dGPU idle down)

![ROG Control Center - App Settings](/images/rog-control-app-settings.avif)

The app marks this tab **work in progress**; notifications in particular are incomplete.

{{% /details %}}

{{% details title="Keyboard RGB (Aura)" closed="true" %}}

**Set keyboard backlight brightness** (valid levels: `off`, `low`, `med`, `high`):
```bash
asusctl leds get     # show current level
asusctl leds set high
asusctl leds next     # one step brighter
asusctl leds prev     # one step dimmer
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

Navigate to "Fan Curves" to set temperature/speed curves per profile (Quiet/LowPower, Balanced, Performance).

**CLI fan curve format:**
```bash
# Show current fan curve data for a profile
asusctl fan-curve --mod-profile Balanced

# Set a custom curve (8 temperature:speed% pairs). The % suffix matters:
# omit it and asusctl treats the values as raw 0-255 fan-PWM steps, not percentages.
asusctl fan-curve --mod-profile Balanced --data 30c:0%,40c:10%,50c:30%,60c:50%,70c:70%,80c:85%,90c:100%,100c:100%
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
| `asusctl battery limit 80` | Set battery charge limit to 80% |
| `asusctl battery info` | Show current charge limit |
| `asusctl profile get` | Show current performance profile |
| `asusctl profile set Balanced` | Set performance profile |
| `asusctl profile next` | Cycle to next profile |
| `asusctl slash list` | List available Slash LED animations |
| `asusctl slash set --enable -b false -s false` | Enable Slash LED, off on battery and sleep |
| `asusctl slash set --mode Spectrum` | Set Slash LED animation |
| `asusctl slash set -l 128` | Set Slash LED brightness (0–255) |
| `asusctl leds set high` | Set keyboard backlight brightness |
| `asusctl armoury get dgpu_disable` | Show current dGPU state (0=enabled, 1=disabled) |
| `asusctl armoury set dgpu_disable 1` | Switch to iGPU-only (disable dGPU) |
| `asusctl armoury set dgpu_disable 0` | Switch to Hybrid mode (enable dGPU) |
| `rog-control-center` | Open ROG Control Center GUI |


## Kernel Updates

### Kernel 6.19: asus-armoury driver lands in mainline

The `asus-armoury` driver has been [merged into Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). This new `platform/x86` driver replaces parts of the older `asus-wmi` with a cleaner sysfs-based API, enabling panel mode switching, APU memory allocation, PPT tuning, and more directly from the kernel. The driver is entirely community-developed by the [asus-linux team](https://asus-linux.org/), with no involvement from ASUS themselves. This driver has been included in every CachyOS kernel from 6.19 onwards.

**Before**: basic asusctl controls without Armoury settings:

![ROG Control before asus-armoury in mainline](/images/rog-control-armoury.avif)

**After**: full Armoury settings exposed, including PPT/power limit tuning:

![ROG Control System Control with Armoury settings and power limit tuning](/images/rog-control-system-control.avif)

**Sources:** [Phoronix article](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussion](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)

### Kernel 7.0: ASUS laptop quirks + newer AMDGPU enablement

Kernel 7.0 shipped in April 2026 and CachyOS picked it up fast. For this ASUS ROG G16 it delivered what was promised: better AMDGPU coverage for newer RDNA 3.5-class IP blocks (GFX11.5.4) and further NVIDIA work. Gaming performance on the Radeon 890M improved noticeably, roughly in line with the ~20% uplift that was anticipated. Combined with the improvements from 6.19, this hardware finally runs the way it should on Linux.

**Sources:** [Linus confirms Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks for ASUS ROG models](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)

### Linux 7.3: scheduler rework and storage/memory wins

Linux 7.3, the October 2026 release, brings a scheduler rework that measured up to 25% better average FPS on older and low-power hardware, with improved cluster-aware scheduling across core types. That's directly relevant here, not just an Intel P/E-core story: the Ryzen AI 9 HX 370 in this laptop is itself a mixed Zen5/Zen5c-core design. Alongside the scheduler work: Direct I/O now runs through an iomap bounce buffer instead of falling back to buffered I/O (roughly half of theoretical throughput up to close to 95%), Btrfs skips slow paths on Direct I/O and `fsync()`, a KSM reverse-mapping lock fix drops a worst-case stall from ~700ms to under 2ms, and `zsmalloc` sees less lock contention when several processes free compressed memory at once.

**Sources:** [Phoronix: Linux 7.3 features overview](https://www.phoronix.com/review/linux-73-features) · [Phoronix: Linux 7.3 "flattens the pick" (scheduler)](https://www.phoronix.com/news/Linux-7.3-Flattens-The-Pick) · [9to5Linux: Linux 7.3-rc1 announced](https://9to5linux.com/linus-torvalds-announces-first-linux-kernel-7-3-release-candidate)


## Additional Resources

- [asus-linux.org](https://asus-linux.org/): official project site
- [asusctl on GitHub](https://github.com/OpenGamingCollective/asusctl): source code and issue tracker
- Upstream installation docs: [Arch](https://opengamingcollective.github.io/asusctl/distributions/arch.html) · [Bazzite](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) · [Fedora Atomic](https://opengamingcollective.github.io/asusctl/distributions/fedora-atomic.html)
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/): CachyOS-specific documentation
- NVIDIA driver setup and known issues: [CachyOS]({{< relref "/docs/cachyos/nvidia" >}}) · [Bazzite]({{< relref "/docs/bazzite/nvidia" >}})
