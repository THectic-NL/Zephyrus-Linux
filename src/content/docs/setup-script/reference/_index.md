---
title: "Reference"
weight: 1
---

Every row in the [setup script]({{< relref "/docs/setup-script" >}}) has an entry here: the exact commands that ticking it runs, the exact commands that unticking it runs to put things back, and a link to the code behind them. The window shows the same commands before it applies anything. This is where you can read them without running anything.

The pages are generated from the script. [`quicksetup.py`](https://github.com/THectic-NL/Zephyrus-Linux/blob/main/src/static/scripts/quicksetup.py) is imported and the same functions the window runs are run for every item, so the pages cannot drift from what the window does. The quality checks fail when a change to the script has not been carried over into them.

## The sections

One page per section of the window, with an entry per item.

- [ASUS hardware]({{< relref "/docs/setup-script/reference/hardware" >}}): asusctl, battery limit, power profiles, brightness
- [Graphics]({{< relref "/docs/setup-script/reference/gpu" >}}): NVIDIA services, PRIME offload, display freezes
- [Display]({{< relref "/docs/setup-script/reference/display" >}}): color modes and the factory color profiles
- [Network]({{< relref "/docs/setup-script/reference/network" >}}): Wi-Fi tuning, eduroam
- [GNOME desktop]({{< relref "/docs/setup-script/reference/desktop" >}}): window buttons, shortcuts, extensions, touchpad
- [Security and login]({{< relref "/docs/setup-script/reference/security" >}}): autologin, YubiKey, Secure Boot
- [Development]({{< relref "/docs/setup-script/reference/dev" >}}): git, signing, editors, cloud tools
- [Applications]({{< relref "/docs/setup-script/reference/apps" >}}): browser, messaging, office, utilities
- [Gaming]({{< relref "/docs/setup-script/reference/gaming" >}}): Steam, Proton tools, overlays
- [Virtual machines and containers]({{< relref "/docs/setup-script/reference/virt" >}}): KVM, Podman, Distrobox, Windows apps

## How to read an entry

- **Turning it on** and **Turning it off (the way back)** list what the window runs, in the order it runs it. The headings in the code say who runs it: *As root* is one script behind one password prompt, *As you* is your own user, and *In a terminal window* is for the AUR, where you read each PKGBUILD before it builds.
- A file that gets edited comes with its diff. The diffs here are made on the files a fresh Arch install ships. The window makes the diff against your own files before it applies anything, and shows it in the review.
- A file the window edits is prepared in your cache folder first, so you can see the diff. Root installs it only while its SHA-256 still matches what was prepared (the `sha256sum -c` line), so nothing can swap the file while the password prompt is open.
- **Source** links to the exact lines of the script on GitHub: the entry in the catalogue and the functions it uses. The links follow the `main` branch, which is the script you download.
- `your-username` stands for your login name, and `/home/your-username` for your home folder.
- The window leaves out what is already in place. It does not install a package that is installed, and a few steps only exist when they apply, such as the `ufw` rules, which are there when ufw is running. An entry shows everything an item can run.
- A package from the AUR is a `paru` line, unless a repository you use has the package. Then it is the `pacman` line.
- The commands and their descriptions are what the window shows, so they are in English on every language of this site.

## The way back

Unticking an item is its way back, and every entry lists it. It removes what ticking installed, puts settings back to the GNOME default (only while they still have the value the script gave them) and puts an edited file back from the backup that was made.

What it does not touch is yours: your own files and settings, such as the settings of an extension you removed, your containers and virtual machines, and a package something else still needs. The notes under an entry say what stays.

Two rows have no checkbox, because a mistake in their steps can stop the machine from booting: the AMD display freeze fix and Secure Boot. Their entries list the steps for setting them up and for undoing them by hand.

## The dedicated scripts

Three items run a script of their own: the brightness fix, the Wi-Fi tuning and eduroam. The setup runs one only when its SHA-256 is the one built into the setup, and that hash is in the entry, with a summary of what the script changes. The scripts are published next to the setup script: [zephyrus-backlight.py](/scripts/zephyrus-backlight.py), [mt7925-tune.py](/scripts/mt7925-tune.py) and [saxion-eduroam.py](/scripts/saxion-eduroam.py). The first two run their steps as root, as one script behind one password prompt. The eduroam script runs as you. Each has its own guide.

## Keeping it in step

After a change to `quicksetup.py`, run `.github/scripts/check-doc-checksums.sh --apply` and then `.github/scripts/generate-setup-reference.py`. The second one rewrites these pages from the script, and `--check` makes it fail instead, which is what the quality checks do.
