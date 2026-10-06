---
title: "Setup script"
weight: 1
---

I got tired of redoing the same setup after every reinstall, so now it lives in one window. You tick what you want, read the plan and apply it. The window also shows what is already set up on your machine, and every item links to the guide that explains it.

It sets up my idea of a good machine. It is built and tested on the Zephyrus G16 (GA605WV), but only a few items care about the model: the ASUS tools, the brightness fix, the Wi-Fi tuning and the color profiles. The rest, the GNOME settings, extensions, apps and virtual machines, works on any laptop.

{{< callout type="warning" >}}
It changes your system. Nothing happens until you have read the plan and pressed Apply. Like everything else here, it is at your own risk.
{{< /callout >}}

## Run it

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/zephyrus-setup.py
echo "3ef6d3cffbb24e1348a42c216c73665a9861626cfc63c568dcf251f2348fe2fb  zephyrus-setup.py" | sha256sum -c
python3 zephyrus-setup.py
```

Source: [zephyrus-setup.py](/scripts/zephyrus-setup.py). SHA-256 `3ef6d3cffbb24e1348a42c216c73665a9861626cfc63c568dcf251f2348fe2fb`.

You need Python 3.14 or newer and the GTK 4 bindings. A stock CachyOS GNOME install has them. If not: `sudo pacman -S python-gobject gtk4 libadwaita`.

There are no commands or options, it just opens a window. Changes work on CachyOS and other Arch-based systems. Anywhere else, Bazzite for example, the window is read-only: you can look around and open the guides.

## The window

The sections are on the left, one row per item on the right. A ticked box means the item is set up on this machine, a dash means it is partly done. Tick a box to turn something on, untick it to turn it off again.

- The two small buttons on a row open the guide and show what ticking and unticking would do.
- `AUR` marks rows that need a package from the AUR. `Advanced` rows stay out of **Select recommended**.
- Ticking an item ticks what it needs, and the window says so. A row that does not apply here is greyed out with the reason.
- GNOME extensions come from extensions.gnome.org, so you do not need a browser add-on. An extension without a build for your GNOME version says so, for example "No build for GNOME 51 yet".
- The menu has **Select recommended**, **Check again** and the log file.

Nothing changes until you press **Review and apply**. The review lists the packages, what runs as root, what needs a reboot or a new login and what is left for you to do. **Show the exact commands** prints every command in full. If something is wrong, Apply stays greyed out and the reason is at the top.

## Color modes

The Display section has a switch that works right away, without applying: **Native**, which is vivid, and **sRGB**. G-Helper has two more on Windows, DCI-P3 and Display P3, but on Linux they would show the same picture as Native, so they are not here. The [Display Color Profiles]({{< relref "/docs/hardware/color-profiles" >}}) page explains that, and why picking another profile in GNOME's Settings does nothing.

## What it checks and what it leaves alone

- **One password prompt.** Everything that needs root runs as one script through `pkexec`. AUR packages are built by `paru` in a terminal window, so you can read each PKGBUILD first.
- **Downloads are checked where that is possible.** The dedicated scripts, the color profiles and Archi are compared with a SHA-256 built into the script, and a file that does not match is never used. An extension zip is checked before it is unpacked. pacman and Flatpak verify their own packages. The VirtIO ISO has no fixed hash, because Fedora replaces it with every release, so it only gets a size check.
- **Checks before it starts.** Packages from the repositories have to exist and install together, which it tests with a dry run. It warns when pacman is busy, when you are offline and when your package databases are old.
- **Unticking is careful.** Packages are removed one by one, and one that something else still needs is kept. Settings go back to the GNOME default, but only if they still have the value the script gave them. Packages the system or the window itself needs are never removed. Your own files stay.
- **Some things stay manual.** Kernel parameters, PAM files and Secure Boot keys can lock you out when they go wrong, so the AMD PSR fix, the YubiKey PAM setup and Secure Boot are guides without a checkbox. The brightness fix is the exception: it runs its own script, which keeps a backup and puts it back when you untick it.
- **A log.** Everything it runs is in `~/.local/state/zephyrus-setup/setup.log`. The window cannot be closed while changes are running.

## Recommended

**Select recommended** ticks these, as far as they are not done yet and apply to your machine:

| Item | What it does |
|---|---|
| asusctl and ROG Control Center | Fan curves, profiles and the Slash LED |
| Battery charge limit of 80% | Stops charging at 80% |
| Let asusd own the power profiles | Masks `power-profiles-daemon` |
| Brightness in every GPU mode | The brightness fix, needs a reboot |
| NVIDIA suspend and resume services | Only for a driver that does not save video memory itself, so not `nvidia-open` |
| prime-run | Runs a program on the RTX 4060 |
| ASUS color profiles | The factory profile of your panel and the ASUS sRGB profile |
| Wi-Fi throughput tuning | For the MT7925 card |
| Minimize and maximize buttons | GNOME only shows the close button |
| New windows come to the front | Together with Just Perfection |
| Touchpad scroll speed | `wayland-scroll-factor`, from the AUR |
| Extension Manager and Just Perfection | Extensions without a browser add-on |
| Git, the GitHub CLI and GPG commit signing | |

Taste is left out: the Windows-like shortcuts, the other extensions, the apps and the virtualization stack are in the window, but not in the preset. So are the advanced items: YubiKey, Secure Boot, VMware and the AMD display freeze fix.

## Where the choices come from

I follow upstream wherever upstream has an opinion. The guide behind each item has the reasoning and the sources.

- **ASUS tools and power profiles:** the [Open Gaming Collective's asusctl documentation](https://opengamingcollective.github.io/asusctl/) and its [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md). Masking `power-profiles-daemon` is what its [Arch](https://opengamingcollective.github.io/asusctl/distributions/arch.html) and [Bazzite](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) guides say. The [asusctl page]({{< relref "/docs/hardware/asusctl-rog-control" >}}) explains why older guides tell you the opposite.
- **NVIDIA suspend and `nvidia-powerd`:** NVIDIA's driver README on [power management](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) and [Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html). `nvidia-open` saves video memory itself, so it skips the suspend units. The [NVIDIA page]({{< relref "/docs/cachyos/nvidia" >}}) has the details.
- **Color modes:** [G-Helper](https://github.com/seerge/g-helper), which lists the ASUS panel profiles on Windows.
- **Autologin and the YubiKey:** the [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) and the [pam-u2f README](https://github.com/Yubico/pam-u2f).
- **The brightness fix:** worked out on this laptop, see [Known Issues]({{< relref "/docs/known-issues" >}}).

## Adding or changing an item

Every item is one entry in `build_items()` in the script: an id, a section, a one-line summary, the guide it links to, a function that works out its status and one that says what ticking it does. A set of packages is a one-liner. When you change the script, run `.github/scripts/check-doc-checksums.sh --apply` so the hashes built into it and the one on this page follow.
