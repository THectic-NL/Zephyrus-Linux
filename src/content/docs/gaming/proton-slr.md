---
title: "Proton & the Steam Linux Runtime"
weight: 2
prev: docs/gaming/steamos
next: docs/known-issues
---

Windows games run on this laptop through two layers that people routinely confuse: **Proton**, which translates the game, and the **Steam Linux Runtime**, which provides the environment Proton runs in.

Knowing which is which is the difference between fixing a broken game in five minutes and reinstalling your graphics driver for no reason.

## Proton

Proton is Valve's build of Wine with their patches on top, plus **DXVK** and **VKD3D-Proton** to translate Direct3D calls into Vulkan. Steam picks a version per game; you can override it.

The versions you'll see:

| Version | What it is |
|---|---|
| **Proton 11** | The current stable major at the time of writing. Fine default |
| **Proton Experimental** | Where fixes land first. Try this when a game misbehaves |
| **Proton Hotfix** | Targeted fixes for specific titles, usually shortly after a game update breaks them |
| **Proton-GE** | A community build with extra media codecs and patches Valve hasn't merged. Often the answer for games with video cutscenes |
| **Proton 8, 9, 10…** | Older majors, kept because some games only work on one specific version |

Setting one:

- **Per game:** right-click the game → **Properties** → **Compatibility** → *Force the use of a specific Steam Play compatibility tool*.
- **Everything:** **Steam → Settings → Compatibility** → *Enable Steam Play for all other titles*.

Per game is almost always what you want. A global override means one bad version affects your whole library.

{{< callout type="info" >}}
Check [ProtonDB](https://www.protondb.com/) before troubleshooting anything. Most "this game doesn't work" problems are a known one-line launch option or a specific Proton version, and someone has already written it down.
{{< /callout >}}

## The Steam Linux Runtime

Those "Steam Linux Runtime 3.0 (sniper)" entries that appear in your library, that you never installed and can't play — that's the second layer, and it's not a mistake.

Proton doesn't run against your system's libraries. It runs inside a **container** that carries a fixed, known set of them. Valve builds and tests Proton against that environment, so a game behaves the same whether it's running on Debian, Arch or an atomic Fedora image.

This is worth understanding on both of the distributions here, for opposite reasons:

{{< tabs >}}
{{< tab name="CachyOS" >}}

Rolling means your system libraries move constantly. Without the runtime, a game that worked last week could break because something unrelated updated underneath it.

The runtime is what stops that. Proton is insulated from your host, so `pacman -Syu` does not put your library at risk — which is a real benefit on a distribution that updates as often as this one.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Here the host libraries barely move at all — they're part of the image. That could be a problem the other way around: a game needing something newer than the image carries.

Again the runtime handles it. Proton brings its own environment, so the age of the image is irrelevant to whether a game runs. It's also why gaming on an atomic system doesn't need any layering: the pieces games need aren't taken from `/usr` in the first place.

{{< /tab >}}
{{< /tabs >}}

**Do not delete the runtime entries**, and don't try to run them. Steam manages them, and removing one breaks every game using it.

## Proton-GE

For games Valve's builds struggle with — usually media codecs, sometimes anti-cheat. Install it with **ProtonUp-Qt**, which works identically on both distributions:

```bash
flatpak install flathub net.davidotek.pupgui2
```

Open it, choose Steam, add the latest GE-Proton. It installs into `~/.steam/root/compatibilitytools.d/`, and it shows up in the per-game compatibility list after a Steam restart.

That path is in your home directory on both distributions, so it needs no layering on Bazzite and survives image updates and rebases untouched.

## Making sure the RTX 4060 is doing the work

This is the one that actually bites on this laptop. The internal panel is driven by the Radeon 890M, so a game that isn't explicitly pointed at the discrete GPU can quietly render on the iGPU — it runs, it just runs badly.

Set it as a launch option (right-click the game → **Properties** → **Launch Options**):

{{< tabs >}}
{{< tab name="CachyOS" >}}

```
prime-run %command%
```

`prime-run` is a wrapper that sets the NVIDIA offload variables for you. It comes with the `nvidia-prime` package.

{{< /tab >}}
{{< tab name="Bazzite" >}}

There is no `prime-run` here, so set the variables directly:

```
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia %command%
```

Same thing, spelled out — that's exactly what `prime-run` does on the other tab.

{{< /tab >}}
{{< /tabs >}}

Confirm which GPU is being used while the game runs:

```bash
nvidia-smi
```

The game should appear in the process list. If it doesn't, it's on the iGPU regardless of what the frame rate suggests.

## Launch options worth knowing

Combine them in one line, with `%command%` last:

| Option | Does |
|---|---|
| `mangohud %command%` | Frame rate and temperature overlay |
| `gamemoderun %command%` | Applies performance governor tweaks while the game runs |
| `PROTON_LOG=1 %command%` | Writes `~/steam-<appid>.log` — the first thing to look at when a game won't start |
| `gamescope -f -- %command%` | Runs the game inside gamescope; useful for resolution and scaling problems on the 2560x1600 panel |

Example, all together:

```
gamemoderun mangohud prime-run %command%
```

## Where things live

| | Path |
|---|---|
| Proton prefixes (the per-game C: drive) | `~/.steam/steam/steamapps/compatdata/<appid>/pfx` |
| Custom Proton builds | `~/.steam/root/compatibilitytools.d/` |
| Proton logs | `~/steam-<appid>.log` |

Deleting a game's `compatdata` directory resets its Windows environment without touching the game files. It's the Proton equivalent of clearing a config, and it fixes a surprising number of games that stop launching after an update.

All of these are inside your home directory, which is `/var/home/<user>` on Bazzite with `/home` symlinked to it — Steam handles that fine, but it's worth knowing if you go looking for these paths in a script.

## References

- [ProtonDB](https://www.protondb.com/) — per-game reports and launch options
- [Proton on GitHub](https://github.com/ValveSoftware/Proton)
- [Steam Linux Runtime](https://gitlab.steamos.cloud/steamrt/steam-runtime-tools/-/blob/main/docs/container-runtime.md)
- [ProtonUp-Qt](https://davidotek.github.io/protonup-qt/)
- [GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom)
