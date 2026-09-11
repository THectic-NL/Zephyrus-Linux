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

### Touchpad-scrollsnelheid: nog steeds geen native GNOME-instelling

Sinds GNOME 50 is er nog steeds geen manier om de trackpad-scrollsnelheid op Linux native in te stellen. Niet in Instellingen, nergens. KDE Plasma heeft dit al jaren. De gemeenschap vraagt er al lang naar, met merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) en [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) die eigenlijk nergens heen gaan. Zie de [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) voor de complete geschiedenis.

Twee third-party tools vullen deze leemte. **wayland-scroll-factor** is de aanbevolen optie; **libinput-config** is het oudere systeemwijde alternatief dat moeilijker in te stellen is.

#### wayland-scroll-factor (aanbevolen)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) van daniel-g-carrasco is een user-level tool die libinput-functieaanroepen in `gnome-shell` onderschept en een scrollvermenigvuldiger toepast. Geen root-toegang nodig; alles zit in je home directory.

**Installatie:**

```bash
git clone https://github.com/daniel-g-carrasco/wayland-scroll-factor.git
cd wayland-scroll-factor
meson setup build --prefix="$HOME/.local"
ninja -C build
meson install -C build
cd ..
rm -rf wayland-scroll-factor
```

{{< callout type="info" >}}
**Op Bazzite:** het resultaat belandt in `$HOME/.local`, wat prima is, maar de build heeft een toolchain en `libinput`-headers nodig, en de library die het produceert wordt voorgeladen in de *host's* `gnome-shell`. Bouw het in een Fedora distrobox van dezelfde release als je image, of laag de build-afhankelijkheden:

```bash
rpm-ostree install meson ninja-build gcc libinput-devel
systemctl reboot
```

Een container gebouwd tegen een ander Fedora-release kan een library produceren die `gnome-shell` weigert te laden.
{{< /callout >}}

**Configuratie:**

```bash
wsf set 0.2     # 1.0 = standaardsnelheid, lager = langzamer; ik gebruik 0.2
wsf enable      # vereist één logout/login om van kracht te worden
wsf status      # controleer of het actief is
```

Instellingen worden opgeslagen in `~/.config/wayland-scroll-factor/config`. Na de eerste `wsf enable` en opnieuw aanmelden, geeft `wsf set` live effect zonder een volgende logout.

Wanneer alles werkt, bevestigt `wsf status` dat de library in gnome-shell is ingespoten:

```
gnome-shell LD_PRELOAD: ~/.local/lib/wayland-scroll-factor/libwsf_preload.so (includes WSF)
gnome-shell library mapped: yes
runtime config reload: active (factor changes should apply live)
```

Als de status aangeeft dat het env-bestand aanwezig is, maar systemd het nog niet heeft opgepikt, voer dan `systemctl --user daemon-reexec` uit en log uit/in.

**Optionele GUI** (`wsf-gui`, vereist libadwaita ≥ 1.4):

```bash
wsf-gui
```

Laat je verticale en horizontale scrollsnelheid apart aanpassen, naast pinch zoom en pinch rotate. De System integration-toggle mappt naar `wsf enable`/`wsf disable`.

![Wayland Scroll Factor GUI met scrollgevoeligheidsschuivers](/images/wayland-scroll-factor-gui.avif)

**Terugrollen:**

```bash
wsf disable
```

#### libinput-config (alternatief)

[libinput-config](https://github.com/lz42/libinput-config) van lz42 is een systeemwijde workaround die source-compilatie en root-toegang vereist. Gebruik dit als wayland-scroll-factor niet voor je setup werkt.

{{< callout type="warning" >}}
**Alleen CachyOS.** Dit installeert in `/usr`, wat read-only is op Bazzite. Daar is geen nette manier voor. Gebruik wayland-scroll-factor hierboven, die in je home directory blijft.
{{< /callout >}}

**Installatie (eenmalig):**

```bash
sudo pacman -S meson ninja libinput git

git clone https://github.com/lz42/libinput-config.git
cd libinput-config
meson setup build
ninja -C build
sudo ninja -C build install
cd ..
rm -rf libinput-config
```

**Configuratie:**

```bash
sudo tee /etc/libinput.conf >/dev/null << 'EOF'
override-compositor=enabled
scroll-factor=0.25
discrete-scroll-factor=1.0
EOF
```

Log uit en weer in, pas dan `scroll-factor` naar je voorkeur aan.

**Terugrollen:**

```bash
sudo rm /etc/libinput.conf
```
