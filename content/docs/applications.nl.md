---
title: "Applicaties"
weight: 25
---

Alles wat ik heb geïnstalleerd na de initiële CachyOS-setup. Losjes georganiseerd per categorie. De meeste keuzes zijn persoonlijk, maar de secties over Brave en libinput-config bevatten niet-voor-de-hand-liggende workarounds die nergens anders gedocumenteerd staan.

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

GNOME heeft standaard geen sneltoets voor de bestandsbeheerder, dus die moet je handmatig aanmaken.

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

Brave is mijn standaardbrowser. Ik begon met de Flatpak-versie maar ben overgestapt naar het native pakket — dat voelt nativer en biedt betere prestaties. Er is alleen een addertje: Brave 1.82+ heeft twee crashbugs op GNOME Wayland waarvoor workarounds nodig zijn.

- **Native (pacman):** Nativer gevoel, betere prestaties. Dit gebruik ik.
- **Flatpak:** Kan in sommige situaties beter werken, maar voelt wat geïsoleerder.

**Installatie**

{{< callout type="warning" >}}
Op CachyOS/Arch met GNOME + Wayland heeft Brave 1.82+ twee bekende crashbugs waarvoor workarounds nodig zijn. De eerste wordt via de desktop entry toegepast; de tweede vereist een instelling in `brave://flags`.
{{< /callout >}}

```bash
sudo pacman -S brave-bin
```

![Brave installatie-instructies](/images/brave-install.avif)

**Workaround 1: de desktop entry patchen**

Kopieer de systeem-desktop entry naar je gebruikersmap zodat hij niet wordt overschreven bij updates:
```bash
sudo cp /usr/share/applications/brave-browser.desktop ~/.local/share/applications/
```

Patch alle drie de `Exec=` regels met de flag:
```bash
sed -i \
  's|Exec=/usr/bin/brave-browser-stable %U|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1 %U|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable$|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable --incognito$|Exec=/usr/bin/brave-browser-stable --incognito --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop
```

Controleer of het gelukt is — je zou exact drie `Exec=` regels moeten zien:
```bash
grep "^Exec" ~/.local/share/applications/brave-browser.desktop
```

**Wat deze flag doet:**

`--disable-features=WaylandWpColorManagerV1` — Brave 1.82+ introduceerde een Wayland color management extensie die conflicteert met de AMD amdgpu-driver op GNOME Wayland. Zonder deze flag veroorzaakt Brave GPU ring timeouts die de volledige GNOME Shell-sessie neerhalen.

**Een noot over `--ozone-platform=x11`:** Geprobeerd als workaround voor een crash bij Bitwarden-bijlagen. Bleek een erger probleem te veroorzaken: gnome-shell met `SIGABRT` bij Picture-in-Picture video — zie [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625). De flag is weg. Brave draait nu op native Wayland. De Bitwarden-bijlage-crash bestaat nog, maar een Brave-crash is te verkiezen boven het verliezen van de hele sessie.

**Workaround 2: hardware video decode uitschakelen in `brave://flags`**

{{< callout type="warning" >}}
Hardware video decode veroorzaakt nog steeds crashes, ook met de flag hierboven. Zolang de AMD VCN decoder actief is, crasht GNOME Shell met SIGABRT bij Picture-in-Picture video. Zie [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625). Hardware video decode is **nog niet stabiel** op de AMD Radeon 890M met GNOME Wayland.
{{< /callout >}}

Ga naar `brave://flags` en schakel uit:

- **Hardware-accelerated video decode** → `Disabled`

![Brave flags — hardware video decode uitgeschakeld](/images/brave-flags.avif)

Video wordt nu via software gedecodeerd. In `brave://gpu` staat daarna:

- `Video Decode: Software only. Hardware acceleration disabled`
- `Video Encode: Software only. Hardware acceleration disabled`

![Brave hardware acceleration config](/images/brave-gpu-config.avif)

**Flatpak alternatief**

Geeft het native pakket problemen:

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
Zie de [NVIDIA Driver Installatie]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) sectie Bekende Problemen voor details.
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

### Solaar voor Logitech-apparaten

[Solaar](https://github.com/pwr-Solaar/Solaar) beheert Logitech-toetsenborden, muizen en andere randapparatuur. Versie 1.1.19 of nieuwer.

```bash
sudo pacman -S solaar
```

![Solaar in GNOME Software](/images/solaar-flathub.avif)

Draait in het systray met batterijnotificaties. Je kunt er ook DPI, polling rate en knoppen mee configureren.

![Solaar about screen — version 1.1.19](/images/solaar-about.avif)
