---
title: "Applicaties"
weight: 4
prev: docs/security/yubikey
next: docs/networking/eduroam-network-installation
---

Alles wat ik heb geïnstalleerd na de initiële CachyOS-setup. Losjes georganiseerd per categorie. De meeste keuzes zijn persoonlijk, maar de secties over Brave en libinput-config bevatten niet-voor-de-hand-liggende workarounds die nergens anders gedocumenteerd staan.

## Packagebronnen

Op CachyOS zijn er drie plekken om software vandaan te halen. Zoek ze in deze volgorde:

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

Native packages bieden betere performance en systeemintegratie. Flatpaks ruilen wat efficiëntie in voor compatibiliteit en sandboxing. De keuze is per applicatie aan jou; beide werken prima op CachyOS.

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

GNOME heeft standaard geen sneltoetsen voor de bestandsbeheerder of een emoji-picker, die moet je handmatig aanmaken. Zie [Smile](#smile-emoji-picker) voor hoe de Copilot-toets wordt gebruikt.

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

Vanaf GNOME 50 is er nog steeds geen manier om de scrollsnelheid van het trackpad native aan te passen. Niet via Instellingen, niet ergens anders. KDE Plasma heeft dit al jaren. De community vraagt er ook al lang om, met merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) en [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) die jaren blijven liggen. Zie de [GNOME Discourse-discussie](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) voor de volledige geschiedenis.

Twee third-party tools vullen dit gat. **wayland-scroll-factor** is de aanbevolen optie; **libinput-config** is het oudere systeembrede alternatief dat wat omslachtiger in te stellen is.

#### wayland-scroll-factor (aanbevolen)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) van daniel-g-carrasco is een tool op gebruikersniveau die libinput-functieaanroepen binnen `gnome-shell` onderschept en een scrollmultiplicator toepast. Geen root nodig; alles staat in je eigen home-directory.

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

**Configuratie:**

```bash
wsf set 0.2     # 1.0 = standaardsnelheid, lager = langzamer; ik gebruik 0.2
wsf enable      # vereist één keer uitloggen en inloggen
wsf status      # controleer of het actief is
```

De instellingen worden opgeslagen in `~/.config/wayland-scroll-factor/config`. Na de eerste `wsf enable` en her-inloggen past `wsf set` de snelheid live aan zonder opnieuw uit te loggen.

Als alles werkt, bevestigt `wsf status` dat de library in gnome-shell is geïnjecteerd:

```
gnome-shell LD_PRELOAD: ~/.local/lib/wayland-scroll-factor/libwsf_preload.so (includes WSF)
gnome-shell library mapped: yes
runtime config reload: active (factor changes should apply live)
```

Als de status aangeeft dat het env-bestand aanwezig is maar systemd het nog niet heeft opgepakt, voer dan `systemctl --user daemon-reexec` uit en log daarna één keer uit en weer in.

**Optionele GUI** (`wsf-gui` - vereist libadwaita ≥ 1.4):

```bash
wsf-gui
```

Hiermee stel je de verticale en horizontale scrollsnelheid apart in, en ook pinch zoom en rotate. De System integration-schakelaar staat gelijk aan `wsf enable`/`wsf disable`.

![Wayland Scroll Factor GUI met scrollsnelheidsliders](/images/wayland-scroll-factor-gui.avif)

**Terugdraaien:**

```bash
wsf disable
```

#### libinput-config (alternatief)

[libinput-config](https://github.com/lz42/libinput-config) van lz42 is een systeembrede workaround die bouwen uit de broncode vereist en root-toegang nodig heeft. Gebruik dit als wayland-scroll-factor niet werkt voor jouw setup.

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

Uitloggen en weer inloggen, dan `scroll-factor` aanpassen naar voorkeur.

**Terugdraaien:**

```bash
sudo rm /etc/libinput.conf
```

---

## Browser

### Brave

Mijn standaardbrowser is [Brave Origin](https://packages.cachyos.org/package/cachyos/x86_64/brave-origin-bin). Ik begon met gewone Brave en ben daarna overgestapt. Brave Origin voelt merkbaar lichter en sneller, heeft minder ingebouwde functies en is voor de meeste mensen waarschijnlijk de betere keuze.

Brave Origin is de gestripte versie van Brave. Op Windows is het een betaald product ($60); op Linux is het gratis.

Zowel Brave als Brave Origin zijn beschikbaar via drie bronnen: de CachyOS-repositories, de AUR en Flathub. Het native CachyOS-pakket geeft de beste integratie. Brave geeft dit zelf ook al aan op hun website en raadt native pakketten aan waar mogelijk. Flatpak werkt maar voelt wat geïsoleerder.

**Brave Origin installeren (aanbevolen):**

```bash
sudo pacman -S brave-origin-bin
```

**Of gewone Brave, als je de volledige functieset wilt:**

```bash
sudo pacman -S brave-bin
```

![Officiële Brave Linux installatie-instructies](/images/brave-linux-install.avif)

Hardware-acceleratie werkt prima met huidige Brave- en kernelversies. De crashbugs die Brave 1.82–1.86 troffen zijn opgelost. Zie [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor de achtergrond.


---

## Communicatie & Productiviteit

### Bitwarden

Wachtwoordbeheerder. Beschikbaar via Flathub en werkt goed.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

### Signal Messenger

Signal is mijn belangrijkste berichtenapp. De [CachyOS extra-repository](https://packages.cachyos.org/package/extra/x86_64/signal-desktop) levert een native pakket dat ik gebruik; het werkt beter dan de Flatpak.

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

De Proton Mail desktop-app is een wrapper rondom de webapp, geen native client. De [CachyOS-repository](https://packages.cachyos.org/package/cachyos/any/proton-mail-bin) levert `proton-mail-bin`, dat natiever integreert in het bureaublad dan de Flatpak: beter systeemvak-gedrag, systeemnotificaties en geen Flatpak-sandboxoverhead.

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

Standard Notes maakt deel uit van het Proton-ecosysteem, met dezelfde privacy-first filosofie als Proton Mail en end-to-end versleutelde notities die synchroniseren over al je apparaten. Het werd in 2022 [overgenomen door Proton](https://proton.me/blog/proton-standard-notes-join-forces).

De feel zit ergens tussen een minimale teksteditor en OneNote in: een opgeruimde zijbalk, snelle notitie-navigatie, tags, geen rommel. Alles wordt versleuteld voordat het je apparaat verlaat. De sync met Android (Samsung S24 in mijn geval) werkt vlekkeloos en meteen.

Wat het onderscheidt is precies wat er _niet_ in zit. Geen onnodige UI-opsmuk, geen opdringerige abonnementsbanners, geen trage opstarttijd. Gewoon snel.

```bash
paru -S standardnotes-bin
```

Beschikbaar via de [AUR](https://aur.archlinux.org/packages/standardnotes-bin) (`standardnotes-bin`). Er bestaat nog geen native CachyOS/Arch-pakket.

![Standard Notes op de desktop](/images/standard-notes-desktop.avif)

![Standard Notes editor-weergave](/images/standard-notes-editor.avif)

![Standard Notes op Android (Samsung S24)](/images/standard-notes-android.avif)

### Kantoorpakketten

Er bestaat geen officiële Microsoft 365-client voor Linux. Twee goede alternatieven dekken de meeste use cases.

#### OnlyOffice

[OnlyOffice](https://packages.cachyos.org/package/cachyos/x86_64/onlyoffice-bin) lijkt het meest op Microsoft 365. De interface is bijna identiek, met Word-, Excel- en PowerPoint-equivalenten die er uitzien en werken als de Microsoft-originals. Goede compatibiliteit met `.docx`-, `.xlsx`- en `.pptx`-bestanden.

```bash
sudo pacman -S onlyoffice-bin
```

![OnlyOffice draaiend op GNOME](/images/only-office.avif)

**Ontbrekend: APA-stijl verwijzingen**

Wat ontbreekt: OnlyOffice heeft geen ingebouwde citatiebeheerder of APA-referentiestijl standaard.

![OnlyOffice - referenties-functie ontbreekt](/images/only-office-missing_references.avif)

Er zijn workarounds via plugins. Het [OnlyOffice helpcenter documenteert referentiebeheer](https://helpcenter.onlyoffice.com/docs/userguides/plugins/InsertReferences.aspx) via integraties zoals Zotero of Mendeley, beide citatiebeheerders die in de editor kunnen worden gekoppeld. Ik heb dit zelf nog niet opgezet, dus ik kan niet goed beoordelen hoe goed dit in de praktijk werkt.

#### LibreOffice

[LibreOffice Fresh](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/libreoffice-fresh) is de meest actief ontwikkelde open-source kantoorapplicatie en de meest Linux-native optie. Er gaat meer ontwikkelinspanning in dan in welk alternatief dan ook.

```bash
sudo pacman -S libreoffice-fresh
```

**APA-verwijzingen: ingebouwd**

Anders dan OnlyOffice heeft LibreOffice een ingebouwde bibliografiedatabase en referentie-invoegfunctie. Je kunt je bronnen beheren en citaten in APA-stijl invoegen direct vanuit de menu's:

![LibreOffice bibliografiebeheerder](/images/libreoffice-bibliograpy.avif)

![LibreOffice - verwijzingen invoegen](/images/libreoffice-inserting_references.avif)

**Kanttekening: Microsoft-formaatcompatibiliteit**

LibreOffice kan `.docx`/`.xlsx`/`.pptx`-bestanden openen en opslaan, maar er zijn bekende renderingsverschillen met documenten die in Microsoft Word zijn gemaakt. Dit komt doordat Microsoft en LibreOffice de OpenXML-standaard niet altijd identiek hebben geïmplementeerd, wat tot renderingsverschillen leidt. Voor documenten die binnen LibreOffice's eigen ODF-formaat blijven, zijn er geen problemen.

---

## Ontwikkeling

### Git & GitHub CLI

```bash
sudo pacman -S git github-cli
```

### Visual Studio Code

Er zijn twee builds beschikbaar. De **Microsoft-build** bevat de volledige Microsoft extension marketplace en proprietary extensies zoals GitHub Copilot. De **open-source build** (`code`) heeft geen Microsoft-telemetrie of branding, maar proprietary extensies zijn niet beschikbaar.

**Microsoft-build (aanbevolen, volledige extensie-ondersteuning):**

```bash
paru -S visual-studio-code-bin
```

Beschikbaar in de [AUR](https://aur.archlinux.org/packages/visual-studio-code-bin).

**Open-source build (geen Microsoft-telemetrie):**

```bash
sudo pacman -S code
```

Beschikbaar in de [CachyOS extra-repository](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/code).

### Kleopatra & GPG commit signing

Ik onderteken mijn Git commits en tags met een GPG-sleutel. Kleopatra maakt het aanmaken en beheren van sleutels makkelijk via een GUI.

Na het installeren van VS Code en Git, installeer Kleopatra en maak je sleutels daarin aan. Daarna configureer je Git:

```bash
git config --global user.name "JOUW_NAAM"
git config --global user.email "JOUW_EMAIL"
git config --global user.signingkey JOUW_GPG_KEY_ID
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.program gpg
```

Je sleutel-ID vinden:
```bash
gpg --list-secret-keys --keyid-format=long
```
Gebruik de ID van de `sec` regel (bijv. `rsa4096/JOUW_GPG_KEY_ID`).

### Archi (ArchiMate-modelleertool)

[Archi](https://www.archimatetool.com/) is een gratis ArchiMate-modelleertool. Het Linux-pakket is een portable archief zonder installer. Om het netjes in GNOME te laten verschijnen met een icoon, moet je de bestanden zelf plaatsen en een desktop entry handmatig aanmaken.

{{< callout type="info" >}}
De downloadpagina van Archi waarschuwt voor mogelijke UI-problemen op Wayland. In mijn ervaring werkt hij prima op GNOME 50 Wayland.
{{< /callout >}}

![Archi downloadpagina - Linux versie met Wayland-opmerking](/images/archi-download.avif)

```bash
# Download en extraheer
cd /tmp
curl -L https://github.com/archimatetool/archi.io/releases/download/5.9.0/Archi-Linux64-5.9.0.tgz | tar -xz

# Verplaats naar /opt
sudo mv Archi-Linux64-5.9.0/Archi /opt/

# Opruimen
rm -rf Archi-Linux64-5.9.0
cd ~

# Symlink zodat je 'archi' kunt starten vanuit de terminal
sudo ln -s /opt/Archi/Archi /usr/local/bin/archi
```

Desktop entry aanmaken zodat Archi in GNOME verschijnt:
```bash
sudo nano /usr/share/applications/archi.desktop
```

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Archi
Comment=ArchiMate Modelling Tool
Exec=/opt/Archi/Archi
Icon=__ICON__
Terminal=false
Categories=Development;IDE;
StartupWMClass=Archi
```

Vervang `__ICON__` door het werkelijke pad (dit bevat een buildtijdstempel die per versie verschilt):

```bash
find /opt/Archi/plugins -name "app-128.png" | head -1
```

Na het opslaan verschijnt Archi in de GNOME-app launcher:

![Archi in de GNOME-app launcher](/images/archi-launcher.avif)

![Archi draaiend op Wayland met GNOME 50](/images/archi-running.avif)

### Podman & Podman Desktop

Voor container workloads gebruik ik Podman in plaats van Docker. Podman heeft geen daemon, draait containers standaard rootless en levert een Docker-compatibele CLI zodat bestaande workflows gewoon blijven werken. `podman-docker` vervangt het `docker`-pakket volledig.

Alle drie de pakketten zijn beschikbaar in de CachyOS-repositories: [podman](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman), [podman-docker](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman-docker), [podman-desktop](https://packages.cachyos.org/package/extra/x86_64/podman-desktop).

```bash
sudo pacman -S podman podman-docker podman-desktop
```

Voor de volledige setup, inclusief registryconfiguratie en het koppelen van Docker Hub en GitHub, zie [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}}) in de Virtualisatie-sectie.

---

## Games & Media

### Steam

Op CachyOS is Steam beschikbaar vanuit de [CachyOS-repository](https://packages.cachyos.org/package/cachyos/x86_64/steam), geen extra repos nodig.

```bash
sudo pacman -S steam
```

![Steam in GNOME Software](/images/steam-website.avif)

Herstart na installatie. Steam bevat Proton standaard voor het draaien van Windows-games op Linux.

### Tidal

Er is geen officiële Tidal-client voor Linux. Er zijn twee community-alternatieven.

#### High Tide (aanbevolen)

[High Tide](https://aur.archlinux.org/packages/high-tide) is een native GTK4-frontend voor Tidal, geen Electron-wrapper, maar een echte applicatie gebouwd met een proper Linux-toolkit. Ziet er strak uit, integreert goed met GNOME en ondersteunt Hi-Fi kwaliteit.

```bash
paru -S high-tide
```

![High Tide draaiend op GNOME](/images/high-tide.avif)

#### Tidal Hi-Fi

[Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) van Rick van Lieshout is een Electron-wrapper rondom de Tidal-webapp. Werkt prima, maar het is in feite de webapp verpakt als desktopapp.

![Tidal Hi-Fi in de Flathub store](/images/tidal-hifi-flathub.avif)

---

## Hulpprogramma's

### Bottles: Windows-software draaien

[Bottles](https://usebottles.com/) laat je Windows-software draaien via Wine. Bottles wordt **uitsluitend officieel via Flatpak geleverd**; negeer eventuele andere versies in de AUR of elders, want die zijn niet officieel en worden niet ondersteund door de Bottles-ontwikkelaars.

```bash
flatpak install flathub com.usebottles.bottles
```

Je kunt ook GNOME Software Center openen, zoeken naar "Bottles" en er zeker van zijn dat je de **Flathub** bron selecteert.

Voor wat niet werkt onder Wine (zoals Microsoft 365), gebruik ik een Windows VM. Zie [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in de Flathub store](/images/bottles-flathub.avif)

### Smile: emoji-picker

[Smile](https://mijorus.it/projects/smile) van Lorenzo Paderi is een eenvoudige emoji-picker voor Linux met ondersteuning voor aangepaste tags. Beschikbaar via Flathub.

```bash
flatpak install flathub it.mijorus.smile
```

![Smile emoji-picker in Flathub](/images/smile-flathub.avif)

**Instellingen**

Zet "Run in the background" en "Minimize on exit" aan in de Smile-instellingen. Zo opent de picker direct en verdwijnt hij netjes na het kiezen van een emoji:

![Smile-instellingen - run in background, minimize on exit](/images/smile-settings.avif)

**GNOME-extensie**

Installeer de [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) om automatisch plakken van emoji's op Wayland mogelijk te maken. Zonder deze extensie kan Smile alleen naar het klembord kopiëren.

{{< callout type="warning" >}}
Zorg er na het installeren van de extensie voor dat de extensie-toggle in de Smile-instellingen onder "Paste emojis automatically" is ingeschakeld.
{{< /callout >}}

**Sneltoets: de Copilot-toets hergebruiken**

De Copilot-toets op de Zephyrus G16 doet op Linux standaard niets nuttigs. GNOME registreert hem als `Shift+Super+TouchpadOff`. Hergebruik hem als sneltoets voor de emoji-picker:

Ga naar **Instellingen → Toetsenbord → Aangepaste sneltoetsen** en voeg toe:

- **Naam:** Emoji picker
- **Commando:** `flatpak run it.mijorus.smile`
- **Sneltoets:** druk op de Copilot-toets

![Overzicht aangepaste sneltoetsen met Emoji picker](/images/smile-custom-shortcuts.avif)

![Dialoog voor aangepaste sneltoets voor Smile - Copilot-toets](/images/smile-shortcut-dialog.avif)

### Solaar voor Logitech-apparaten

[Solaar](https://github.com/pwr-Solaar/Solaar) beheert Logitech-toetsenborden, muizen en andere randapparatuur. Beschikbaar in de [CachyOS extra-repository](https://packages.cachyos.org/package/extra/any/solaar).

```bash
sudo pacman -S solaar
```

![Solaar-pakketpagina in de CachyOS-repository](/images/solaar-docs.avif)

Draait in het systray met batterijnotificaties. Je kunt er ook DPI, polling rate en knoppen mee configureren.

![Solaar about screen - version 1.1.19](/images/solaar-about.avif)

### LocalSend

[LocalSend](https://localsend.org/) is een open-source, platformonafhankelijke app voor het delen van bestanden. Ik gebruik het om bestanden over te zetten tussen mijn Samsung S24 Ultra en de Zephyrus. Als je gewend bent aan Windows of Android, is het in feite het open-source equivalent van QuickShare: het ontdekt apparaten op het lokale netwerk en stuurt bestanden direct door, zonder cloud.

Wat het niet kan, is bestanden versturen wanneer afzender en ontvanger op verschillende netwerken zitten. QuickShare kon dat wel via de cloud van Google en Samsung, maar dat was toch alleen beschikbaar via de mobiele app. De desktopversie van QuickShare werkte sowieso niet altijd even goed, dus in de praktijk mis je dat niet. Qua snelheid is LocalSend iets langzamer, maar dat merk je nauwelijks.

Beschikbaar als native pakket in de [CachyOS-packagerepository](https://packages.cachyos.org/package/cachyos/x86_64/localsend), native gebouwd voor CachyOS. Geen AUR nodig, wat echt een pluspunt is.

```bash
sudo pacman -S localsend
```

Na het installeren verschijnt de app in de GNOME-launcher. Open hem en hij ontdekt direct andere LocalSend-instanties op het netwerk.

<img src="/images/localsend-desktop.avif" width="700" alt="LocalSend draaiend op de desktop">

<img src="/images/localsend-cachyos-package.avif" width="600" alt="LocalSend in de CachyOS-packagerepository">

**Firewallregels**

LocalSend gebruikt poort 53317 (TCP en UDP) voor zowel apparaatdetectie als bestandsoverdracht. Als je een firewall actief hebt, moet je deze poort openstellen.

**ufw:**

```bash
sudo ufw allow 53317/tcp comment "LocalSend-App"
sudo ufw allow 53317/udp comment "LocalSend-App"
```

**firewalld:**

```bash
sudo firewall-cmd --permanent --add-port=53317/tcp
sudo firewall-cmd --permanent --add-port=53317/udp
sudo firewall-cmd --reload
```

De Android-app werkt op dezelfde manier. Open hem op je telefoon en hij verschijnt meteen als ontdekt apparaat aan de desktopkant, en andersom.

<img src="/images/localsend-android-1.avif" width="320" alt="LocalSend op Android (Samsung S24 Ultra)">

Bestanden selecteren gaat eenvoudig. Kies wat je wilt versturen, selecteer het doelapparaat en de overdracht begint.

<img src="/images/localsend-android-2.avif" width="320" alt="LocalSend op Android - bestanden selecteren">

<img src="/images/localsend-android-3.avif" width="320" alt="LocalSend op Android - overdracht bezig">
