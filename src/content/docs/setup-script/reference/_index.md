---
title: "Reference"
weight: 1
---

Every row in the [setup script]({{< relref "/docs/setup-script" >}}) has an entry here: the exact commands that ticking it runs, the exact commands that unticking it runs to put things back, and a link to the code behind them. The window shows the same commands before it applies anything. This is where you can read them without running anything.

The pages are generated from the script each time the site is built: [`quicksetup.py`](https://github.com/THectic-NL/Zephyrus-Linux/blob/main/src/static/scripts/quicksetup.py) is imported and the functions the window runs are run for every item, so the pages cannot drift from what the window does. To read them from a checkout, run `.github/scripts/generate-setup-reference.py` before `hugo server`.

## The sections

- [ASUS hardware](hardware/): asusctl, battery limit, power profiles, brightness
- [Graphics](gpu/): NVIDIA services, PRIME offload, display freezes
- [Display](display/): the factory color profile of the built-in screen
- [Network](network/): Wi-Fi tuning, eduroam
- [GNOME desktop](desktop/): window buttons, shortcuts, extensions, touchpad
- [Security and login](security/): autologin, YubiKey, Secure Boot
- [Development](dev/): git, signing, editors, cloud tools
- [Applications](apps/): browser, messaging, office, utilities
- [Gaming](gaming/): Steam, Proton tools, overlays
- [Virtual machines and containers](virt/): KVM, Podman, Distrobox, Windows apps

## How to read an entry

- **Turning it on** and **Turning it off (the way back)** list what the window runs, in the order it runs it. The comment headings say who runs it: *As root* is one script behind one password prompt, *As you* is your own user, and *As you, in a terminal window* is for the AUR, where you read each PKGBUILD before it builds.
- A file that already exists and gets changed comes with its diff, made on the file a fresh Arch install ships. The window makes it against your own file and shows it in the review. A file that gets created is written out in the command itself. Root installs the prepared file only while its SHA-256 still matches (the `sha256sum -c` line), so nothing can swap it while the password prompt is open.
- **Source** links to the exact lines of the script, at the commit this site was built from.
- `your-username` stands for your login name. The window leaves out what is already in place, while an entry shows everything an item can run. A package from the AUR is a `paru` line, unless a repository you use has the package: then it is the `pacman` line.
- The commands and their descriptions are what the window shows, so they are in English on every language of this site.

## The way back

Unticking an item is its way back, and every entry lists it. It removes what ticking installed, puts settings back to the GNOME default (only while they still have the value the script gave them) and puts an edited file back from the backup that was made. What is yours stays: your own files and settings, your containers and virtual machines, and a package something else still needs. The notes under an entry say what stays.

Two rows have no checkbox, because a mistake in their steps can stop the machine from booting: the AMD display freeze fix and Secure Boot. Their entries list the steps for setting them up and for undoing them by hand.

## The dedicated scripts

Three items run a script of their own: the brightness fix, the Wi-Fi tuning and eduroam. The setup runs one only when its SHA-256 is the one built into the setup. That hash is in the entry, with a link to the guide that says what the script changes. The scripts are published next to the setup script: [zephyrus-backlight.py](/scripts/zephyrus-backlight.py), [mt7925-tune.py](/scripts/mt7925-tune.py) and [saxion-eduroam.py](/scripts/saxion-eduroam.py).
