---
title: "Applicaties"
weight: 6
prev: docs/security/yubikey
next: docs/applications/browser
---

Alles wat ik heb geïnstalleerd na de initiële systeeminstallatie. Georganiseerd per categorie, met aparte pagina's voor elk programma en workflow.

De meeste applicaties hier zijn Flatpaks en installeren op beide distributies hetzelfde. Waar een installatiecommando verschilt, staan beide opties op de pagina.

## Packagebronnen

Waar je je software vandaan haalt is het grootste dagelijkse verschil tussen de twee distributies, dus het loont om je eigen tab te lezen voordat je verdergaat.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Drie plekken, in deze volgorde:

1. **[CachyOS packages](https://packages.cachyos.org/)**: de eigen repository van CachyOS, gebouwd bovenop Arch. Packages hier zijn geoptimaliseerd voor moderne CPU's (x86-64-v3/v4) en bevatten CachyOS-specifieke patches. Installeren met `sudo pacman -S <package>`.

2. **[AUR](https://aur.archlinux.org/)** (Arch User Repository): community-beheerde buildscripts voor software die niet in de officiële repos staat. Installeren met een AUR-helper zoals `paru -S <package>`. Kwaliteit verschilt per package, maar de AUR dekt vrijwel alles.

3. **[Flathub](https://flathub.org/)**: Flatpak-packages die hun eigen dependencies meebrengen. Installeren met `flatpak install flathub <app-id>`, starten met `flatpak run <app-id>`.

CachyOS levert ook **[Shelly](https://github.com/Seafoam-Labs/Shelly-ALPM)** mee als standaard grafische package manager, sinds de ISO van april 2026 de opvolger van het oudere Octopi. Het praat rechtstreeks met `libalpm` in plaats van `pacman` te omwikkelen, en zet alle drie bovenstaande bronnen in één GTK4-app: officiële packages, AUR-builds en Flathub, plus AppImages, achter de tabbladen **Recommended**, **Package**, **AUR**, **Flatpak**, **AppImage** en **Update**. Op een oudere installatie zonder Shelly haal je het binnen met `sudo pacman -S shelly`.

![Shelly bladert door Flathub-apps in het Flatpak-tabblad](/images/shelly-flatpak.avif)

**Native (pacman/paru) vs Flatpak: wat kies je?**

| | Native (pacman/paru) | Flatpak |
|---|---|---|
| **Performance** | Beter (gebruikt gedeelde systeembibliotheken) | Iets minder (bundelt eigen bibliotheken) |
| **Integratie** | Nauw (volledige systeemtoegang) | Sandbox (meer geïsoleerd) |
| **Grootte** | Kleiner | Groter |
| **Compatibiliteit** | Afhankelijk van de distro | Consistent op alle distro's |
| **Veiligheid** | Standaard | Betere sandboxing |

Native packages bieden betere performance en systeemintegratie. Flatpaks ruilen wat efficiëntie in voor compatibiliteit en sandboxing. De keuze is per applicatie aan jou; beide werken hier prima.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Vier plekken, en de volgorde telt hier zwaarder dan op CachyOS. Het is Bazzites eigen voorkeursvolgorde, van meest naar minst aanbevolen:

1. **[Flathub](https://flathub.org/)**: de belangrijkste manier om grafische applicaties te installeren. `flatpak install flathub <app-id>`. Bazzite levert **Bazaar** mee als grafische store.

2. **[Homebrew](https://brew.sh/)**: voor commandline-tools. `brew install <tool>`. Installeert in `/home/linuxbrew`, dus geen layering en geen herstart.

3. **[Distrobox](https://distrobox.it/)**: voor alles wat een echte package manager nodig heeft, en voor ontwikkelomgevingen. `distrobox enter <container>` en daarbinnen de package manager van die container. `distrobox-export --app <package>` zet een grafische app uit de container in je menu op de host.

4. **`rpm-ostree`-layering**: laatste redmiddel, voor wat onderdeel van het systeem moet zijn: drivers, kernelmodules, PAM-modules, systeemdiensten. Vraagt een herstart, en elk gelaagd package wordt opnieuw toegepast op elke nieuwe image.

**Wat kies je?**

| | Flatpak | Homebrew | Distrobox | Layering |
|---|---|---|---|---|
| **Herstart nodig** | Nee | Nee | Nee | Ja |
| **Overleeft image-updates** | Ja | Ja | Ja | Wordt elke keer opnieuw toegepast |
| **Goed voor** | GUI-apps | CLI-tools | Toolchains, ontwikkelomgevingen | Systeemonderdelen |
| **Isolatie** | Sandbox | Geen | Container | Geen |
| **Kan een update breken** | Nee | Nee | Nee | Ja |

Die laatste kolom is degene om te onthouden. Een Flatpak die stukgaat is een kapotte app; een gelaagd package dat niet meer bouwt tegen een nieuwere Fedora blokkeert de hele systeemupdate. Houd `rpm-ostree status` kort.

{{< /tab >}}
{{< /tabs >}}

## Initiële systeeminstellingen

### Hostname instellen

Gewoon de hostname instellen via Systeeminstellingen zodat de machine een fatsoenlijke naam heeft op het netwerk.

![Hostname instellen](/images/system-info.avif)

### GNOME-vensterknoppen: minimize en maximize terug

Standaard toont GNOME 50 alleen de sluitknop. Eén commando lost het op:

```bash
gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'
```

![Voorbeeld van hoe de nieuwe GNOME-vensters eruitzien](/images/window-controls.avif)

### GNOME-sneltoetsen: meer als Windows

Als je vanuit Windows komt, voelen een paar dingen meteen anders zonder de juiste sneltoetsen. Dit zijn de sneltoetsen die ik heb ingesteld.

**Ingebouwde sneltoetsen (via Settings > Keyboard > Keyboard Shortcuts):**

| # | Actie | Sneltoets |
|---|-------|-----------|
| 1 | Desktop tonen (alle vensters verbergen) | `Super+D` |
| 2 | Interactieve screenshot | `Shift+Super+S` |
| 3 | Interactieve schermopname | `Shift+Super+R` |
| 4 | Instellingen openen | `Super+I` |

**Custom shortcut (via Settings > Keyboard > Keyboard Shortcuts > Custom Shortcuts):**

| # | Actie | Commando | Sneltoets |
|---|-------|----------|-----------|
| 5 | Bestandsbeheer openen | `nautilus` | `Super+E` |
| 6 | Emoji-picker | `flatpak run it.mijorus.smile` | Copilot-toets |

GNOME heeft standaard geen sneltoetsen voor de bestandsbeheerder of een emoji-picker, die moet je handmatig aanmaken. Zie [Smile](/docs/applications/utilities/#smile-emoji-picker) voor hoe de Copilot-toets wordt gebruikt.

### GNOME-vensterfocus: apps die op de achtergrond openen

Standaard brengt GNOME een nieuw venster niet naar voren. In plaats daarvan zet hij het op de achtergrond klaar en toont een melding dat de app klaar is. De gedachte erachter is logisch: niet onderbreken wat je aan het doen bent. In de praktijk is het voornamelijk gewoon irritant.

Er is een `gsettings`-sleutel die dit zou moeten regelen:

```bash
gsettings set org.gnome.desktop.wm.preferences focus-new-windows 'smart'
```

De standaard is `strict` (nieuwe vensters nooit automatisch focussen). `smart` laat GNOME zelf beslissen en zou nieuwe vensters naar voren moeten brengen. In de praktijk **is dit alleen niet betrouwbaar**. Vensters belanden alsnog geminimaliseerd op de achtergrond in veel gevallen, omdat het onderliggende probleem is dat apps het [XDG Activation-protocol](https://wayland.app/protocols/xdg-activation-v1) moeten implementeren om focus correct aan te vragen, en veel doen dat niet. De GNOME Shell dev-blog heeft [een uitgebreide uitleg](https://blogs.gnome.org/shell-dev/2024/09/20/understanding-gnome-shells-focus-stealing-prevention/) over waarom dit voor een groot deel van het app-ecosysteem fundamenteel kapot is.

De oplossing die wel werkt is het toepassen van **beide** instellingen tegelijk: de `gsettings`-sleutel hierboven, plus **Window Demands Attention Focus** inschakelen in de [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) GNOME Shell-extensie. In het tabblad **Behavior**:

![Just Perfection extensie-instellingen, tabblad Behavior](/images/just-perfection-panel.avif)

![Just Perfection: Window Demands Attention Focus ingeschakeld](/images/just-perfection-window-raise.avif)

Alleen Just Perfection gebruiken zonder de `gsettings`-wijziging kan nog steeds randgevallen opleveren. Alleen `gsettings` is niet voldoende voor apps die het activatieprotocol niet implementeren. Beide samen dekt de grote meerderheid van de gevallen.
