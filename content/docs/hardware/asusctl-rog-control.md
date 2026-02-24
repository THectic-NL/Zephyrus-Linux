---
title: "asusctl & ROG Control Center"
weight: 22
---

The Zephyrus G16 has a lot of hardware features that don't work out of the box on Linux — fan curves, performance profiles, the Slash LED on the lid, GPU switching, battery charge limiting. This page documents how I got all of it working using asusctl and the ASUS Linux project tools. On CachyOS, these tools are available directly from the package repos.

**Package Information:**
- `asusctl` 6.3.2-1 — CLI for fan curves, profiles, battery limit, RGB, Slash LED
- `asusctl-rog-gui` 6.3.2 — ROG Control Center GUI
- `supergfxctl` 5.2.7-8 — GPU mode switching
- Source: CachyOS/Arch repos (packages maintained by Luke Jones, primary asusctl developer)


## Installation

{{% steps %}}

### Install asusctl, ROG Control Center, and supergfxctl

```bash
sudo pacman -S asusctl supergfxctl power-profiles-daemon rog-control-center
```

This installs:
- `asusctl` — main CLI daemon and client
- `asusctl-rog-gui` — ROG Control Center GUI
- `supergfxctl` — GPU mode switching daemon

### Enable services

```bash
sudo systemctl enable --now asusd.service
sudo systemctl enable supergfxd.service
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

```bash
sudo pacman -S nvtop powertop s-tui lm_sensors i2c-tools
```

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
- `--enable` — turn on the Slash LED
- `-b false` — disable on battery power
- `-s false` — disable during sleep

**Set animation:**
```bash
asusctl slash --mode Spectrum
```

**Set brightness (0–255):**
```bash
asusctl slash -l 128
```

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

{{% details title="GPU mode switching (supergfxctl)" closed="true" %}}

The GA605WV has a hybrid GPU setup: the AMD Radeon 890M (iGPU) drives the internal display, and the NVIDIA RTX 4060 (dGPU) handles GPU workloads.

`supergfxctl` manages which GPU mode is active:

| Mode | Description |
|------|-------------|
| `Hybrid` | Both GPUs active. NVIDIA handles GPU workloads, AMD drives the display. Best for gaming. |
| `Integrated` | Only AMD iGPU. Lower power consumption, no NVIDIA. Good for battery. |
| `AsusMuxDgpu` | NVIDIA directly drives the display via hardware MUX switch. Lowest latency for gaming. Requires reboot. |

**Check current mode:**
```bash
supergfxctl --mode
```

**Switch mode:**
```bash
supergfxctl --mode Hybrid
supergfxctl --mode Integrated
```

> **Note:** Switching between Hybrid and Integrated requires a logout/login. Switching to AsusMuxDgpu requires a reboot.

> **Important:** `nvidia-powerd.service` must remain disabled and **masked** on this laptop. It conflicts with AMD ATPX power management and causes soft lockups and reboot hangs (black screen, backlights stay on). Masking is essential because `supergfxd` directly calls `systemctl start nvidia-powerd.service` during GPU mode switches — `disable` alone does not prevent this. The mask (symlink to `/dev/null`) blocks both `supergfxd` and NVIDIA driver updates from re-enabling it. GPU power is managed via ATPX (via ACPI). See [NVIDIA Driver Installation Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) for diagnosis details and commands.

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

> **Note:** Fan curve customization requires the `asus-armoury` kernel driver. On kernel < 6.19, the driver is not available and curves set in the GUI may not persist as expected. See the Known Issues section below.

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

**Check supergfxd service logs:**
```bash
sudo journalctl -b -u supergfxd
```

{{% /details %}}


## Known Issues

{{% details title="ROG Control Center warning: \"The asus-armoury driver is not loaded\"" closed="true" %}}

**Problem:**
ROG Control Center shows a warning that the `asus-armoury` kernel driver is not loaded. Some advanced features (PPT power limits, APU memory allocation, MUX switch control) are unavailable.

**Cause:**
The `asus-armoury` driver was merged into the Linux mainline kernel in version 6.19. CachyOS ships kernel 6.19.3-2 which includes this driver, so it should be available.

**What still works without the driver:**
- Fan curves (basic)
- Performance profiles (Silent / Balanced / Performance)
- Battery charge limit
- Slash LED
- Keyboard Aura / RGB
- GPU switching via supergfxctl

**Solution:**
Verify the driver is loaded:
```bash
lsmod | grep asus_armoury
```

If it loads, reopen ROG Control Center — the warning should be gone and advanced features will be available.

> **Note on GA605WV support:** The initial 6.19 release lists GA403-series models explicitly. If the GA605WV is not yet in the DMI table, some model-specific features (PPT tuning, APU memory) may still not appear even on 6.19. This is expected to be resolved via follow-up kernel patches.

{{% /details %}}


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
| `supergfxctl --mode` | Show current GPU mode |
| `supergfxctl --mode Hybrid` | Switch to Hybrid GPU mode |
| `supergfxctl --mode Integrated` | Switch to integrated GPU only |
| `rog-control-center` | Open ROG Control Center GUI |


## Additional Resources

- [asus-linux.org](https://asus-linux.org/) — Official project site
- [asusctl GitLab](https://gitlab.com/asus-linux/asusctl) — Source code and issue tracker
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/) — CachyOS-specific documentation
- [NVIDIA Driver Installation Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) — NVIDIA driver setup and known issues
