---
title: "Communicatie & Productiviteit"
weight: 2
prev: docs/applications/browser
next: docs/applications/development
---

### Bitwarden

Wachtwoord manager. Beschikbaar via Flathub en werkt prima.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

### Signal Messenger

Signal is mijn main messaging app. Op CachyOS levert de [extra repository](https://packages.cachyos.org/package/extra/x86_64/signal-desktop) een native package, wat ik gebruik; het werkt beter dan de Flatpak. Op Bazzite is de Flatpak de optie.

**CachyOS / Arch (aanbevolen):**

```bash
sudo pacman -S signal-desktop
```

**Flatpak (alternatief):**

```bash
flatpak install flathub org.signal.Signal
```

![Signal Messenger app in Flathub](/images/signal-flathub.avif)

### Proton Mail

Proton Mail desktop app is een wrapper rond de web app in plaats van een native client. Op CachyOS levert de [repository](https://packages.cachyos.org/package/cachyos/any/proton-mail-bin) `proton-mail-bin`, die sneller integreert dan de Flatpak: beter tray icon behavior, system notifications, en geen Flatpak sandbox overhead. Op Bazzite is de Flatpak de optie.

**CachyOS / Arch (aanbevolen):**

```bash
sudo pacman -S proton-mail-bin
```

**Flatpak (alternatief):**

```bash
flatpak install flathub me.proton.Mail
```

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

### Standard Notes

Standard Notes maakt deel uit van het Proton-ecosysteem, met dezelfde privacy-first filosofie als Proton Mail en end-to-end versleutelde notities die op al je apparaten synnen. Het werd [in 2022 overgenomen door Proton](https://proton.me/blog/proton-standard-notes-join-forces).

Het voelt ergens tussen een minimale teksteditor en OneNote: schoon sidebar, snelle notitiewisseling, tags, geen rommel. Alles is versleuteld voordat het je apparaat verlaat. De sync naar Android (Samsung S24 in mijn geval) is naadloos en instant.

Wat het onderscheidt is precies wat er *niet* is. Geen onnodig UI-rommel, geen subscription upsell banners overal, geen trage startup. Het is gewoon snel.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
paru -S standardnotes-bin
```

Beschikbaar op de [AUR](https://aur.archlinux.org/packages/standardnotes-bin) (`standardnotes-bin`). Er bestaat nog geen native CachyOS/Arch package.

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.standardnotes.standardnotes
```

{{< /tab >}}
{{< /tabs >}}

![Standard Notes op het desktop](/images/standard-notes-desktop.avif)

![Standard Notes editorweergave](/images/standard-notes-editor.avif)

![Standard Notes op Android (Samsung S24)](/images/standard-notes-android.avif)

### Office suites

Er bestaat geen officiële Microsoft 365-client voor Linux. Twee solide alternatieven dekken de meeste use cases.

#### OnlyOffice

[OnlyOffice](https://packages.cachyos.org/package/cachyos/x86_64/onlyoffice-bin) is het dichtst in de buurt van Microsoft 365 op Linux. De UI is bijna identiek, met Word, Excel en PowerPoint-equivalenten die op de Microsoft-originalen lijken. Goede compatibiliteit met `.docx`, `.xlsx` en `.pptx` files.

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

![OnlyOffice op GNOME](/images/only-office.avif)

**Ontbrekend: APA-stijl-referenties**

Eén ding dat ontbreekt: OnlyOffice heeft geen ingebouwde citation manager of APA-referentiestijl ondersteuning uit de doos.

![OnlyOffice - referenties feature ontbreekt](/images/only-office-missing_references.avif)

Er zijn workarounds via plugins. Het [OnlyOffice help center documenteert reference management](https://helpcenter.onlyoffice.com/docs/userguides/plugins/InsertReferences.aspx) via integraties zoals Zotero of Mendeley, beide citation managers die in de editor kunnen haken. Ik heb dit zelf nog niet ingesteld, dus ik kan niet beoordelen hoe goed het in de praktijk werkt.

#### LibreOffice

[LibreOffice Fresh](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/libreoffice-fresh) is de meest actief ontwikkelde open-source office suite en de meest Linux-native optie. Er gaat meer ontwikkelingsinspanning in dan in alternatief.

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

De Flathub-build volgt ook de Fresh series, dus dit is dezelfde LibreOffice.

{{< /tab >}}
{{< /tabs >}}

**APA-referenties: ingebouwd**

Anders dan OnlyOffice heeft LibreOffice een ingebouwde bibliografiedatabase en referentie-invoeging. Je kunt je bronnen beheren en citaties in APA-format rechtstreeks vanuit de menu's invoegen:

![LibreOffice bibliography manager](/images/libreoffice-bibliograpy.avif)

![LibreOffice - referenties invoegen](/images/libreoffice-inserting_references.avif)

**Kanttekening: Microsoft-format compatibiliteit**

LibreOffice kan `.docx`/`.xlsx`/`.pptx` files openen en opslaan, maar er zijn bekende weergaveverschillen met documenten gemaakt in Microsoft Word. Dit komt neer op hoe Microsoft en LibreOffice elk de OpenXML-standaard anders hebben geïmplementeerd. Voor documenten die in LibreOffice's eigen ODF-format blijven zijn er geen problemen.
