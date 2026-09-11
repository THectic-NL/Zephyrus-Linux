---
title: "Communication & Productivity"
weight: 2
prev: docs/applications/browser
next: docs/applications/development
---

### Bitwarden

Password manager. Available via Flathub and works well.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

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

Proton Mail desktop app is a wrapper around the web app rather than a native client. On CachyOS the [repository](https://packages.cachyos.org/package/cachyos/any/proton-mail-bin) ships `proton-mail-bin`, which integrates more natively into the desktop than the Flatpak: better tray icon behavior, system notifications, and no Flatpak sandbox overhead. On Bazzite the Flatpak is the option.

**CachyOS / Arch (recommended):**

```bash
sudo pacman -S proton-mail-bin
```

**Flatpak (alternative):**

```bash
flatpak install flathub me.proton.Mail
```

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

### Standard Notes

Standard Notes is part of the Proton ecosystem, with the same privacy-first philosophy as Proton Mail and end-to-end encrypted notes that sync across all your devices. It was [acquired by Proton in 2022](https://proton.me/blog/proton-standard-notes-join-forces).

The feel is somewhere between a minimal text editor and OneNote: clean sidebar, quick note switching, tags, no bloat. Everything is encrypted before it leaves your device. The sync to Android (Samsung S24 in my case) is seamless and instant.

What makes it stand out is exactly what's *not* there. No unnecessary UI chrome, no subscription upsell banners everywhere, no slow startup. It's just fast.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
paru -S standardnotes-bin
```

Available on the [AUR](https://aur.archlinux.org/packages/standardnotes-bin) (`standardnotes-bin`). No native CachyOS/Arch package exists yet.

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.standardnotes.standardnotes
```

{{< /tab >}}
{{< /tabs >}}

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
