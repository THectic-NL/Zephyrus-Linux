---
title: "Applicaties"
weight: 25
---

Alles wat ik heb geïnstalleerd na de initiële CachyOS-setup. Losjes georganiseerd per categorie. De meeste keuzes zijn persoonlijk, maar de secties over Brave en libinput-config bevatten niet-voor-de-hand-liggende workarounds die nergens anders gedocumenteerd staan.

## Packagebronnen

Op CachyOS zijn er drie plekken om software vandaan te halen. Zoek ze in deze volgorde:

1. **[CachyOS packages](https://packages.cachyos.org/)** — de eigen repository van CachyOS, gebouwd bovenop Arch. Packages hier zijn geoptimaliseerd voor moderne CPU's (x86-64-v3/v4) en bevatten CachyOS-specifieke patches. Installeren met `sudo pacman -S <package>`.

2. **[AUR](https://aur.archlinux.org/)** (Arch User Repository) — community-beheerde buildscripts voor software die niet in de officiële repos staat. Installeren met een AUR-helper zoals `paru -S <package>`. Kwaliteit verschilt per package, maar de AUR dekt vrijwel alles.

3. **[Flathub](https://flathub.org/)** — Flatpak-packages die hun eigen dependencies meebrengen. Installeren met `flatpak install flathub <app-id>`, starten met `flatpak run <app-id>`.

**Native (pacman/paru) vs Flatpak — wat kies je?**

| | Native (pacman/paru) | Flatpak |
|---|---|---|
| **Performance** | Beter — gebruikt gedeelde systeembibliotheken | Iets minder — bundelt eigen bibliotheken |
| **Integratie** | Nauw — volledige systeemtoegang | Sandbox — meer geïsoleerd |
| **Grootte** | Kleiner | Groter |
| **Compatibiliteit** | Afhankelijk van de distro | Consistent op alle distro's |
| **Veiligheid** | Standaard | Betere sandboxing |

Native packages bieden betere performance en systeemintegratie. Flatpaks ruilen wat efficiëntie in voor compatibiliteit en sandboxing. De keuze is per applicatie aan jou — beide werken prima op CachyOS.

## Initiële systeeminstellingen

### Hostname instellen

Gewoon de hostname instellen via Systeeminstellingen zodat de machine een fatsoenlijke naam heeft op het netwerk.

![Hostname instellen](/images/system-info.avif)

### GNOME-vensterknoppen — minimize en maximize terug

Standaard toont GNOME 49 alleen de sluitknop. Eén commando lost het op:

```bash
gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'
```

![Voorbeeld van hoe de nieuwe GNOME-vensters eruitzien](/images/window-controls.avif)

### GNOME-sneltoetsen — meer als Windows

Als je vanuit Windows komt, voelt een paar dingen meteen anders zonder de juiste sneltoetsen. Dit zijn de sneltoetsen die ik heb ingesteld.

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

GNOME heeft standaard geen sneltoetsen voor de bestandsbeheerder of een emoji-picker — die moet je handmatig aanmaken. Zie [Smile](#smile--emoji-picker) voor hoe de Copilot-toets wordt gebruikt.

### GNOME-vensterfocus — apps die op de achtergrond openen

Apps zoals Signal en Discord openen soms op de achtergrond, met een melding "Your app is ready" in plaats van het venster naar voren te brengen. Dit los je op met:

```bash
gsettings set org.gnome.desktop.wm.preferences focus-new-windows 'smart'
```

De standaard `strict`-modus brengt nieuwe vensters nooit automatisch naar voren. `smart` laat GNOME zelf beslissen — in de praktijk betekent dit dat nieuw geopende apps gewoon op de voorgrond verschijnen.

### Touchpad-scrollsnelheid — geen native GNOME-instelling (nog niet)

GNOME 49 heeft simpelweg **geen instelling** voor touchpad-scrollsnelheid. KDE Plasma heeft dat al jaren. Er zijn merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) en [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991), maar die staan al jaren open. Zie de [GNOME Discourse-discussie](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) voor meer context.

[libinput-config](https://github.com/lz42/libinput-config) van lz42 is een third-party workaround die libinput events onderschept en een scrollmultiplicator toepast.

**Installatie (eenmalig):**

```bash
# 1. Dependencies installeren
sudo pacman -S meson ninja libinput git

# 2. libinput-config clonen
git clone https://github.com/lz42/libinput-config.git
cd libinput-config

# 3. Bouwen
meson setup build
ninja -C build

# 4. Systeembreed installeren
sudo ninja -C build install

# 5. Opruimen (optioneel)
cd ..
rm -rf libinput-config
```

**Configuratie voor langzamere touchpad-scroll:**

```bash
sudo tee /etc/libinput.conf >/dev/null << 'EOF'
# libinput-config configuration
override-compositor=enabled

# Touchpad-scroll langzamer (lager = langzamer)
# Standaard: 1.0, geteste waarde: 0.25
scroll-factor=0.25

# Muiswiel normaal houden
discrete-scroll-factor=1.0
EOF
```

Uitloggen en weer inloggen (of reboot), dan `scroll-factor` aanpassen naar voorkeur.

**Terugdraaien:**

```bash
sudo rm /etc/libinput.conf
```

---

## Browser

### Brave

Brave is mijn standaardbrowser. Ik begon met de Flatpak-versie maar ben overgestapt naar het native pakket — dat beter integreert met het systeem en betere prestaties biedt.

- **Native (pacman):** Betere integratie, betere prestaties. Dit gebruik ik.
- **Flatpak:** Kan in sommige situaties beter werken, maar voelt wat geïsoleerder.

**Installatie**

[brave-bin in CachyOS packages](https://packages.cachyos.org/package/cachyos/x86_64/brave-bin) — direct beschikbaar in de CachyOS-repo, geen AUR-helper nodig.

```bash
sudo pacman -S brave-bin
```

![Officiële Brave Linux installatie-instructies](/images/brave-linux-install.avif)

Hardware acceleration werkt prima met huidige Brave- en kernelversies. De crashbugs die Brave 1.82–1.86 troffen zijn opgelost — zie [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor de achtergrond.

**Flatpak-alternatief**

Als het native pakket problemen geeft:

```bash
flatpak install flathub com.brave.Browser
```

![Brave Flatpak in Flathub](/images/brave-flathub.avif)

---

## Communicatie & Productiviteit

### Bitwarden

Wachtwoordbeheerder. Beschikbaar via Flathub en werkt goed.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

### Signal Messenger

Signal is mijn belangrijkste berichtenapp. Officieel alleen ondersteund op Debian/Ubuntu, maar de Flatpak-versie werkt prima op CachyOS.

![Signal Messenger app in Flathub](/images/signal-flathub.avif)

### Proton Mail

De Proton Mail desktop-app is een wrapper rondom de webapp, geen native client. Werkt gewoon en staat in de app launcher zoals elke andere app.

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

---

## Ontwikkeling

### Git & GitHub CLI

```bash
sudo pacman -S git github-cli
```

### Visual Studio Code

```bash
sudo pacman -S code
```

{{< callout type="warning" >}}
Op kernel 6.18.x/6.19.x kan hardware acceleration in VS Code een amdgpu page fault veroorzaken waardoor het systeem bevriest. Zet hardware acceleration uit door dit toe te voegen aan `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```
Zie [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor details.
{{< /callout >}}

### Kleopatra & GPG commit signing

Ik onderteken mijn Git commits en tags met een GPG-sleutel. Kleopatra maakt het aanmaken en beheren van sleutels makkelijk via een GUI.

Na het installeren van VS Code en Git, installeer Kleopatra en maak je sleutels daarin aan. Daarna Git configureren:

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

[Archi](https://www.archimatetool.com/) is een gratis ArchiMate-modelleertool. Het Linux-pakket is een portable archief — geen installer. Om het netjes in GNOME te laten verschijnen met een icoon, moet je de bestanden zelf plaatsen en een desktop entry handmatig aanmaken.

{{< callout type="info" >}}
De downloadpagina van Archi waarschuwt voor mogelijke UI-problemen op Wayland. In mijn ervaring werkt hij prima op GNOME 49 Wayland.
{{< /callout >}}

![Archi downloadpagina — Linux versie met Wayland-opmerking](/images/archi-download.avif)

```bash
# Download en extraheer
cd /tmp
curl -L https://github.com/archimatetool/archi.io/releases/download/5.7.0/Archi-Linux64-5.7.0.tgz | tar -xz

# Verplaats naar /opt
sudo mv Archi-Linux64-5.7.0/Archi /opt/

# Opruimen
rm -rf Archi-Linux64-5.7.0
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
Icon=/opt/Archi/plugins/com.archimatetool.editor_5.7.0.202509230807/img/app-128.png
Terminal=false
Categories=Development;IDE;
StartupWMClass=Archi
```

Na het opslaan verschijnt Archi in de GNOME-app launcher:

![Archi in de GNOME-app launcher](/images/archi-launcher.avif)

![Archi draaiend op Wayland met GNOME 49](/images/archi-running.avif)

---

## Games & Media

### Steam

Op CachyOS is Steam beschikbaar vanuit de `multilib` repository — geen extra repos nodig.

```bash
sudo pacman -S steam
```

![Steam in GNOME Software](/images/steam-gnome-software.avif)

Herstart na installatie. Steam bevat Proton standaard voor het draaien van Windows-games op Linux.

{{< callout type="info" >}}
Als Steam niet wil starten, probeer het dan vanuit de terminal:
```bash
__GL_CONSTANT_FRAME_RATE_HINT=3 steam
```
{{< /callout >}}

### Tidal Hi-Fi

Er is geen officiële Tidal-client voor Linux. [Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) van Rick van Lieshout is een community-Electron-wrapper rondom de Tidal-webapp, met Hi-Fi en Max kwaliteitsondersteuning.

![Tidal Hi-Fi in de Flathub store](/images/tidal-hifi-flathub.avif)

---

## Hulpprogramma's

### Bottles — Windows-software draaien

[Bottles](https://usebottles.com/) laat je Windows-software draaien via Wine. Installeer via Flathub — versie 61 of nieuwer.

- Open GNOME Software Center, zoek naar "Bottles", selecteer de **Flathub** bron

Voor wat niet werkt onder Wine — zoals Microsoft 365 — gebruik ik een Windows VM. Zie [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in de Flathub store](/images/bottles-flathub.avif)

### Smile — emoji-picker

[Smile](https://mijorus.it/projects/smile) van Lorenzo Paderi is een eenvoudige emoji-picker voor Linux met ondersteuning voor aangepaste tags. Beschikbaar via Flathub.

```bash
flatpak install flathub it.mijorus.smile
```

![Smile emoji-picker in Flathub](/images/smile-flathub.avif)

**Instellingen**

Zet "Run in the background" en "Minimize on exit" aan in de Smile-instellingen — zo opent de picker direct en verdwijnt hij netjes na het kiezen van een emoji:

![Smile-instellingen — run in background, minimize on exit](/images/smile-settings.avif)

**GNOME-extensie**

Installeer de [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) om automatisch plakken van emoji's op Wayland mogelijk te maken. Zonder deze extensie kan Smile alleen naar het klembord kopiëren.

{{< callout type="warning" >}}
Zorg er na het installeren van de extensie voor dat de extensie-toggle in de Smile-instellingen onder "Paste emojis automatically" is ingeschakeld.
{{< /callout >}}

**Sneltoets — de Copilot-toets hergebruiken**

De Copilot-toets op de Zephyrus G16 doet op Linux standaard niets nuttigs. GNOME registreert hem als `Shift+Super+TouchpadOff`. Hergebruik hem als sneltoets voor de emoji-picker:

Ga naar **Instellingen → Toetsenbord → Aangepaste sneltoetsen** en voeg toe:

- **Naam:** Emoji picker
- **Commando:** `flatpak run it.mijorus.smile`
- **Sneltoets:** druk op de Copilot-toets

![Overzicht aangepaste sneltoetsen met Emoji picker](/images/smile-custom-shortcuts.avif)

![Dialoog voor aangepaste sneltoets voor Smile — Copilot-toets](/images/smile-shortcut-dialog.avif)

### Solaar voor Logitech-apparaten

[Solaar](https://github.com/pwr-Solaar/Solaar) beheert Logitech-toetsenborden, muizen en andere randapparatuur. Versie 1.1.19 of nieuwer.

```bash
sudo pacman -S solaar
```

![Solaar in GNOME Software](/images/solaar-flathub.avif)

Draait in het systray met batterijnotificaties. Je kunt er ook DPI, polling rate en knoppen mee configureren.

![Solaar about screen — version 1.1.19](/images/solaar-about.avif)
