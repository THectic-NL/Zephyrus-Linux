---
title: "Setup script"
weight: 1
---

I got tired of redoing the same setup by hand every time I reinstalled. So the settings the guides describe, the software I actually use and my own recommended defaults are in one script with a menu. It shows what is already done on your machine, what is still open, what applying an item would do, and it links to the page of the guide that explains it.

It sets up *my* idea of a good Linux machine. It is built and tested on the Zephyrus G16 GA605WV, but only the items that talk to this hardware care about the model: the ASUS tools, the brightness fix, the Wi-Fi tuning and the factory color profile. Everything else, the GNOME settings, the shortcuts, the applications, containers and virtualization, is the same on any laptop. On other machines the hardware items show as not applicable and are skipped.

{{< callout type="warning" >}}
The script changes your system. It always shows the plan first and does nothing until you confirm it, but read that plan. Like everything else here, it is at your own risk.
{{< /callout >}}

## Run it

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/zephyrus-setup.py
echo "d7804d07c353f8d904436262754e095ed7891edbe9887b06c1e56ee6691a44aa  zephyrus-setup.py" | sha256sum -c
python3 zephyrus-setup.py
```

Source: [zephyrus-setup.py](/scripts/zephyrus-setup.py). SHA-256 `d7804d07c353f8d904436262754e095ed7891edbe9887b06c1e56ee6691a44aa`.

It needs Python 3.14 or newer and nothing else from Python's side (standard library only). Applying things is built for CachyOS and other Arch-based systems, with GNOME. On Bazzite, `list`, `show` and `learn` work and `apply` says why it won't run. The menu uses dialogs when `zenity` is installed and the terminal otherwise; `--terminal` forces the terminal.

## The menu

Every item has a status, worked out from the machine itself:

| Symbol | Meaning |
|---|---|
| `[x]` | Done |
| `[~]` | Partly done |
| `[ ]` | Still to do |
| `[-]` | Not applicable here, for example an ASUS tool on a different laptop |
| `[?]` | Unknown, or something only you can finish |

Pick a section, tick what you want and apply it. Next to every item are four more things: **Details** (what exactly it would do and what undoing it would do), **Learn more** (opens the page of this guide that covers it), **Undo** (puts the ticked items back, see [Undoing](#undoing)) and, for the items that have their own script, **Open tool**. In the terminal menu, `u2` or `u 2 4-6` undoes items by number.

## From the command line

| Command | What it does |
|---|---|
| `list` | Every item and where it stands. `--todo` for only what is left, `--section` for one section, `--urls` to add the guide link of each |
| `show asus-tools` | One item in detail: status, plan, manual steps, how to undo it, and its link. A unique start of an id is enough |
| `learn wsf` | Print the guide link and open it in the browser |
| `apply asus-tools nvidia-prime` | Plan, confirm and apply those items |
| `apply --recommended` | Everything recommended that is not done yet |
| `apply --section dev` | Every open, non-advanced item of a section |
| `apply --dry-run ...` | Show the plan and stop. Works with every form of `apply` |
| `undo wsf gnome-focus` | Plan, confirm and put those items back to the stock state. `--dry-run` shows the plan and stops |
| `tool backlight-fix` | Open the dedicated script of an item, for example the brightness fix |
| `color set srgb` | Switch the built-in screen to an ASUS color mode: `native`, `srgb`, `dcip3` or `displayp3`. `color` alone lists them |

`--yes` skips the confirmation and `--silent` turns every dialog and question off, which is how you run it from a script. `--silent` needs `--yes` for `apply` and `undo`.

## What happens when you apply

- **The plan comes first.** It lists the packages (pacman, AUR, Flathub), the steps that need root, the steps that run as you, what needs a reboot or a new login, and what is left for you to do by hand.
- **One password prompt.** Every step that needs root goes into one script under one `pkexec` call. AUR packages are built by `paru`, which shows each PKGBUILD for review, so they need a terminal.
- **The dedicated scripts are checked.** The brightness fix, the Wi-Fi tuning and the eduroam setup are scripts of their own, each with a SHA-256 published on its guide page. The setup script uses the copy next to it, or downloads the script from this repository, and compares it with that published hash. A script that does not match is never run. `--ref` picks another branch or tag to fetch from, for example to try a change before it is merged.
- **As little AUR as possible.** Only four items need a package from the AUR, and they are tagged `AUR` in the menu: Visual Studio Code (the Microsoft build), Desktop Plus, wayland-scroll-factor and VMware. Apps that exist on Flathub, like Standard Notes and High Tide, come from there instead. The AUR is only used for a package that no repository has: if one of them lands in a repository later, the script installs it with pacman instead.
- **Anything risky stays manual.** The script does not edit the bootloader or kernel parameters, PAM files or Secure Boot keys, and it does not register a YubiKey. A mistake in any of those can lock you out. Those items show the steps for your bootloader instead, with a link to the guide.
- **Almost everything can be undone.** See below.

## Undoing

Undo puts an item back to the stock state, with the same rules as applying: the plan comes first, it asks before it does anything, and every step that needs root goes into one script under one `pkexec` call. Only items that are done or partly done can be undone.

- **It restores stock, not your previous value.** A setting you changed yourself is reset to the GNOME or system default, not to what it was before. A setting that no longer has the value this script gave it is left alone, because you changed it since.
- **Packages are removed one by one** with `pacman -Rs` or `flatpak uninstall`. A package that something else still needs is kept and reported, instead of breaking the removal of the rest. Your own data and config in your home directory stay.
- **Some things need a login or reboot afterwards**, for example wayland-scroll-factor. The result says so.
- **Five items have no automatic undo:** the AMD PSR fix, the GNOME extensions, Secure Boot, Archi and Tmog. They are manual or touch things a script should not guess at. Where there is a by-hand way back, `show <id>` prints it.
- **The YubiKey item is blocked while it is in use.** If `pam_u2f` is in `/etc/pam.d/sudo`, `polkit-1` or `gdm-password`, the script refuses to remove the packages, because that would lock you out of your own login. Take it out of PAM first.

Try it without risk: `undo --dry-run <id>` prints the plan and stops.

## The recommended preset

`apply --recommended` is what I would set up on any fresh install:

| Item | What it does |
|---|---|
| `asus-tools` | asusctl and ROG Control Center |
| `asus-battery-limit` | Stops charging at 80% |
| `asus-ppd-mask` | Lets asusd own the power profiles |
| `backlight-fix` | Brightness in every GPU mode |
| `nvidia-power-services` | NVIDIA suspend and resume units, only for a driver that doesn't save video memory itself (not `nvidia-open`) |
| `nvidia-prime` | `prime-run` |
| `display-color-modes` | The panel's factory profile plus the ASUS sRGB, DCI-P3 and Display P3 profiles, for color-managed apps. They do not change how the desktop looks |
| `wifi-mt7925` | Wi-Fi throughput tuning |
| `gnome-window-buttons` | Minimize and maximize buttons |
| `gnome-focus` | New windows come to the front |
| `gnome-extension-manager` | Extension Manager |
| `wsf` | Touchpad scroll speed |
| `git-github-cli` | Git and the GitHub CLI |
| `git-gpg-signing` | Kleopatra and signed commits |

Things that are a matter of taste, such as the Windows-like shortcuts, the applications and the virtualization stack, are in the menu but not in the preset. So are the advanced items: YubiKey, Secure Boot, VMware and the AMD display freeze fix.

## Where the choices come from

The items follow upstream wherever upstream has an opinion, and the guide page behind each item gives the reasoning and the sources.

- **ASUS tools, profiles and `power-profiles-daemon`:** the [Open Gaming Collective's asusctl documentation](https://opengamingcollective.github.io/asusctl/) and its [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md). Masking `power-profiles-daemon` is what its [Arch](https://opengamingcollective.github.io/asusctl/distributions/arch.html) and [Bazzite](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) guides say. The [asusctl page]({{< relref "/docs/hardware/asusctl-rog-control" >}}) explains why older guides tell you the opposite.
- **NVIDIA suspend units and `nvidia-powerd`:** NVIDIA's driver README on [power management](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) and [Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html). The suspend units are skipped on `nvidia-open`, which saves video memory itself; the [NVIDIA page]({{< relref "/docs/cachyos/nvidia" >}}) has the details.
- **Color modes:** modeled on [G-Helper](https://github.com/seerge/g-helper), which lists the ASUS panel profiles on Windows.
- **Autologin and the YubiKey:** the [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) and the [pam-u2f README](https://github.com/Yubico/pam-u2f).
- **The brightness fix:** worked out on this laptop, with the reasoning on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.

## Adding or changing an item

Every item is one entry in `build_items()` in the script: an id, the section it belongs to, a one-line summary, the guide page it links to, a function that works out its status, and a function that says what applying it does. A set of packages is a one-liner. If you change the script, run `.github/scripts/check-doc-checksums.sh --apply` so the hash on this page follows.
