---
title: "Communication & Productivity"
weight: 2
prev: docs/applications/browser
next: docs/applications/development
---

### Password manager

Bitwarden and Proton Pass are both open source. Use the tabs to switch between them.

{{< tabs >}}
{{< tab name="Bitwarden" >}}

Available via Flathub and works well. Bitwarden publishes this Flatpak itself (Flathub marks it as verified) and it updates itself.

```bash
flatpak install flathub com.bitwarden.desktop
```

CachyOS and Arch also ship a `bitwarden` package, but the distribution builds that one and it trails Bitwarden's releases. At the time of writing it is 2026.3.1, which Arch has flagged as out of date, against 2026.9.1 for the Flatpak.

[Bitwarden's feature table](https://bitwarden.com/help/desktop-app-feature-support/) lists one catch for the Flatpak: unlocking the desktop app with biometrics needs a Polkit policy that you install by hand.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

{{< /tab >}}
{{< tab name="Proton Pass" >}}

Proton Pass is made by Proton, the company behind Proton Mail (below). It has a free plan.

**CachyOS / Arch (recommended):**

The [CachyOS repository](https://packages.cachyos.org/package/cachyos/x86_64/proton-pass) ships `proton-pass`, built from source. It runs on the system Electron, so Electron updates come with the rest of your system.

```bash
sudo pacman -S proton-pass
```

**Flatpak (Bazzite, or an alternative):**

```bash
flatpak install flathub me.proton.Pass
```

Flathub does not list this Flatpak as verified, so it is not confirmed to come from Proton. Proton's own [Linux guide](https://proton.me/support/set-up-proton-pass-linux) only offers `.deb` and `.rpm` files.

![Proton Pass desktop app](/images/proton-pass.avif)

**Browser extension**

The extension is what fills in logins in your browser. Get it from the [Chrome Web Store](https://chromewebstore.google.com/detail/proton-pass-free-password/ghmbeldphafepmbegfdlkpapadhbakde) for Brave and other Chromium browsers, or from [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/proton-pass/). Proton then opens a page that tells you to pin it to the toolbar and sign in.

![The page Proton opens after installing the extension](/images/proton-pass-extension.avif)

{{< /tab >}}
{{< /tabs >}}

### Signal Messenger

Signal is my main messaging app. On CachyOS the [extra repository](https://packages.cachyos.org/package/extra/x86_64/signal-desktop) ships a native package, which is what I use; it works better than the Flatpak. On Bazzite the Flatpak is the option.

**CachyOS / Arch (recommended):**

```bash
sudo pacman -S signal-desktop
```

**Flatpak (alternative):**

```bash
flatpak install flathub org.signal.Signal
```

![Signal Messenger app in Flathub](/images/signal-flathub.avif)

### Proton Mail

Proton Mail desktop app is a wrapper around the web app rather than a native client. On CachyOS the [repository](https://packages.cachyos.org/package/cachyos/any/proton-mail-bin) ships `proton-mail-bin`, which integrates more natively into the desktop than the Flatpak: better tray icon behavior, system notifications, and no Flatpak sandbox overhead.

**CachyOS / Arch (recommended):**

```bash
sudo pacman -S proton-mail-bin
```

**Flatpak (alternative):**

```bash
flatpak install flathub me.proton.Mail
```

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

#### Proton's own .rpm

Proton publishes a `.deb` and an `.rpm` itself, linked from [its Linux setup article](https://proton.me/support/set-up-proton-mail-linux). On ordinary Fedora, install it with dnf:

```bash
sudo dnf install ./ProtonMail-desktop-*.rpm
```

That gives you dependency handling and a clean `dnf remove`, but not updates. No Proton repository sits behind the file, so nothing shows up in `dnf upgrade` and every release means downloading the RPM again.

Bazzite has no `dnf` on the host, so the same file means `rpm-ostree install` on a local RPM: a layered package and a reboot, repeated per release. The [WinBoat]({{< relref "/docs/virtualization/winboat" >}}) page runs into the same thing. The Flatpak updates in the background and costs no reboots, so it stays the better option on Bazzite.

### Standard Notes

Standard Notes is part of the Proton ecosystem, with the same privacy-first philosophy as Proton Mail and end-to-end encrypted notes that sync across all your devices. It was [acquired by Proton in 2022](https://proton.me/blog/proton-standard-notes-join-forces).

The feel is somewhere between a minimal text editor and OneNote: clean sidebar, quick note switching, tags, no bloat. Everything is encrypted before it leaves your device. The sync to Android (Samsung S24 in my case) is seamless and instant.

What makes it stand out is exactly what's *not* there. No unnecessary UI chrome, no subscription upsell banners everywhere, no slow startup. It's just fast.

```bash
flatpak install flathub org.standardnotes.standardnotes
```

The Flatpak is the same on both distributions. There is also a `standardnotes-bin` package in the AUR, but running a community build script for an app this simple is a risk I don't see the point of.

![Standard Notes running on the desktop](/images/standard-notes-desktop.avif)

![Standard Notes editor view](/images/standard-notes-editor.avif)

![Standard Notes on Android (Samsung S24)](/images/standard-notes-android.avif)

### Office suites

No official Microsoft 365 client exists for Linux. Two solid alternatives cover most use cases.

#### OnlyOffice

[OnlyOffice](https://packages.cachyos.org/package/cachyos/x86_64/onlyoffice-bin) is the closest thing to Microsoft 365 on Linux. The UI is nearly identical, with Word, Excel, and PowerPoint equivalents that look and behave like the Microsoft originals. Good compatibility with `.docx`, `.xlsx`, and `.pptx` files.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S onlyoffice-bin
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.onlyoffice.desktopeditors
```

{{< /tab >}}
{{< /tabs >}}

![OnlyOffice running on GNOME](/images/only-office.avif)

**Missing: APA-style references**

One thing that is missing: OnlyOffice has no built-in citation manager or APA reference style support out of the box.

![OnlyOffice - references feature missing](/images/only-office-missing_references.avif)

There are workarounds via plugins. The [OnlyOffice help center documents reference management](https://helpcenter.onlyoffice.com/docs/userguides/plugins/InsertReferences.aspx) through integrations like Zotero or Mendeley, both citation managers that can hook into the editor. I haven't set this up myself yet, so I can't assess how well it actually works in practice.

#### LibreOffice

[LibreOffice Fresh](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/libreoffice-fresh) is the most actively developed open-source office suite and the most Linux-native option. More development effort goes into it than any alternative.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S libreoffice-fresh
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.libreoffice.LibreOffice
```

The Flathub build tracks the Fresh series too, so this is the same LibreOffice.

{{< /tab >}}
{{< /tabs >}}

**APA references: built in**

Unlike OnlyOffice, LibreOffice has a built-in bibliography database and reference insertion. You can manage your sources and insert citations in APA format directly from the menus:

![LibreOffice bibliography manager](/images/libreoffice-bibliograpy.avif)

![LibreOffice - inserting references](/images/libreoffice-inserting_references.avif)

**Caveat: Microsoft format compatibility**

LibreOffice can open and save `.docx`/`.xlsx`/`.pptx` files, but there are known rendering differences with documents created in Microsoft Word. This comes down to how Microsoft and LibreOffice have each implemented the OpenXML standard, not always identically. For documents that stay within LibreOffice's own ODF format, there are no issues.
