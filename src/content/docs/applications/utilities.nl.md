---
title: "Utilities"
weight: 5
prev: docs/applications/gaming-media
next: docs/networking/eduroam-network-installation
---

### Smile: emoji picker

[Smile](https://mijorus.it/projects/smile) van Lorenzo Paderi is een eenvoudige emoji picker voor Linux met custom tags ondersteuning. Beschikbaar op Flathub.

```bash
flatpak install flathub it.mijorus.smile
```

![Smile emoji picker in Flathub](/images/smile-flathub.avif)

**Instellingen**

Zet "Run in the background" en "Minimize on exit" in op Smile's instellingen. Dit houdt de picker instant en sluit hem schoon na het selecteren van een emoji:

![Smile instellingen - run in background, minimize on exit](/images/smile-settings.avif)

**GNOME extensie**

Installeer de [Smile complementaire extensie](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) om automatisch emoji plakken op Wayland in te schakelen. Zonder het kan Smile alleen naar clipboard kopiëren.

{{< callout type="warning" >}}
In de Smile instellingen onder "Paste emojis automatically", zorg dat de extensie toggle is ingeschakeld na installatie.
{{< /callout >}}

**Sneltoets: de Copilot-toets hergebruiken**

De Copilot-toets op de Zephyrus G16 is anders waardeloos op Linux. GNOME registreert het als `Shift+Super+TouchpadOff`. Hergebruik het als emoji picker sneltoets:

Ga naar **Settings → Keyboard → Custom Shortcuts** en voeg toe:

- **Name:** Emoji picker
- **Command:** `flatpak run it.mijorus.smile`
- **Shortcut:** druk de Copilot-toets in

![Custom shortcuts list met Emoji picker entry](/images/smile-custom-shortcuts.avif)

![Custom shortcut dialog voor Smile - Copilot key binding](/images/smile-shortcut-dialog.avif)

### Solaar voor Logitech-apparaten

[Solaar](https://github.com/pwr-Solaar/Solaar) beheert Logitech toetsenborden, muizen en andere randapparatuur.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Beschikbaar in de [CachyOS extra repository](https://packages.cachyos.org/package/extra/any/solaar).

```bash
sudo pacman -S solaar
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub io.github.pwr_solaar.solaar
```

Solaar praat met de receiver via HID, dus de Flatpak heeft de udev rules op de host nodig om je gebruiker toegang tot het device te geven. Deze rules schepen met de image; als Solaar start maar geen devices ziet, dat is het om te controleren.

{{< /tab >}}
{{< /tabs >}}

![Solaar package pagina in de CachyOS repository](/images/solaar-docs.avif)

Draait in de system tray met battery notificaties. Je kunt ook DPI, polling rate en knoppen van daaruit configureren.

![Solaar about screen - versie 1.1.19](/images/solaar-about.avif)

### LocalSend

[LocalSend](https://localsend.org/) is een open-source, cross-platform file sharing app. Ik gebruik het om bestanden over te dragen tussen mijn Samsung S24 Ultra en de Zephyrus. Als je van Windows of Android komt, is het eigenlijk de open-source equivalent van Quick Share: het ontdekt devices op het lokale netwerk en zet bestanden rechtstreeks over, geen cloud betrokken.

Het enige wat het niet kan is bestanden over verschillende netwerken overhevelen. Quick Share kon transfers via Google/Samsung's cloud routeren wanneer verzender en ontvanger op verschillende netwerken waren, maar dat was mobiel-only. Desktop Quick Share was onbetrouwbaar genoeg dat het zelden de moeite waard was. Snelheidsmatig is LocalSend iets langzamer, maar niet merkbaar in de praktijk.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Beschikbaar native in de [CachyOS package repository](https://packages.cachyos.org/package/cachyos/x86_64/localsend), specifiek gebouwd voor CachyOS. Geen AUR nodig, wat echt een plus is.

```bash
sudo pacman -S localsend
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.localsend.localsend_app
```

{{< /tab >}}
{{< /tabs >}}

De app verschijnt in de GNOME launcher na installatie. Open het en het ontdekt automatisch andere LocalSend-instanties op je netwerk.

<img src="/images/localsend-desktop.avif" width="700" alt="LocalSend op het desktop">

<img src="/images/localsend-cachyos-package.avif" width="600" alt="LocalSend in de CachyOS package repository">

**Firewall rules**

LocalSend gebruikt port 53317 (TCP en UDP) voor beide device discovery en file transfer. Als je firewall actief hebt, moet je deze port openen.

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

De Android app werkt hetzelfde. Open het op je telefoon en het verschijnt onmiddellijk als een ontdekt device op desktop side, en vice versa.

<img src="/images/localsend-android-1.avif" width="320" alt="LocalSend op Android (Samsung S24 Ultra)">

Bestanden selecteren is eenvoudig. Kies wat je wilt sturen, kies het target device en de transfer start.

<img src="/images/localsend-android-2.avif" width="320" alt="LocalSend op Android - bestanden selecteren om te verzenden">

<img src="/images/localsend-android-3.avif" width="320" alt="LocalSend op Android - transfer in progress">

### Mission Center: GNOME-native taakbeheer

[Mission Center](https://missioncenter.io/) is een GNOME-native systeemmonitor en taakbeheerder, gebouwd met Rust, GTK4 en Libadwaita. CPU, geheugen, schijven, netwerk en GPU links, een detailweergave met live grafieken rechts, plus een Apps/Services-weergave vergelijkbaar met het Processen-tabblad van Windows Taakbeheer.

```bash
flatpak install flathub io.missioncenter.MissionCenter
```

Open source onder de GPLv3, broncode op [GitLab](https://gitlab.com/mission-center-devs/mission-center). Versie 1.2.0 op het moment van schrijven.

![Mission Center - CPU performance detail](/images/mission-center-cpu.avif)

Op deze hardware leest het beide NVMe-schijven uit, alle vier fan-sensoren (`cpu_fan`, `gpu_fan`, `mid_fan`, plus één ongelabelde), en beide GPU's, met GPU/GPU-geheugengebruik per app uitgesplitst in de Apps-weergave:

![Mission Center - Apps-weergave](/images/mission-center-apps.avif)

{{< callout type="info" >}}
GPU-monitoring is upstream als experimenteel gemarkeerd. NVIDIA wordt volledig ondersteund (inclusief VRAM en stroomverbruik per app); AMD wordt ondersteund; Intel-iGPU's ouder dan Broadwell krijgen geen VRAM-, stroom- of temperatuuruitlezing.
{{< /callout >}}

### TMOG: de Task Manager van Dave Plummer

[Task Manager TMOG](https://tmog.org/) is een native Qt6-taakbeheerder voor Windows, macOS en Linux van Dave Plummer, die halverwege de jaren '90 bij Microsoft de originele Windows Taakbeheer schreef. Volgens [Tom's Hardware](https://www.tomshardware.com/software/windows/windows-veterans-vibe-coded-task-manager-now-also-runs-on-mac-and-linux-downloadable-app-is-the-result-of-a-107-page-spec-fed-to-claude-code) is deze rebuild "vibe coded" vanuit een spec van 107 pagina's, gevoerd aan Claude Code. Zie ook [Plummers eigen video erover](https://youtu.be/c3EEs-O3bGE).

Het is proprietary en closed-source, uitgebracht onder een betalicentie: persoonlijk gebruik mag, herdistributie niet. De meeste functies zijn gratis; een handvol (Power & Freq, Flight Recorder, Connections, Installed Apps, Drivers, Disk Space, Benchmarks) zit achter een **PRO**-badge in de zijbalk.

**Installeren (aanbevolen: de officiële AppImage van [tmog.org](https://tmog.org/)):**

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S fuse2
```

Download de AppImage van tmog.org, en dan:

```bash
chmod +x TaskManagerOG-*.AppImage
./TaskManagerOG-*.AppImage
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Nog niet getest op deze hardware. AppImages hebben doorgaans `libfuse2` nodig tijdens het draaien; wat de schoonste manier is om daaraan te komen op een atomic image (Homebrew, een distrobox, of anders) is hier niet bevestigd.

{{< /tab >}}
{{< /tabs >}}

{{< callout type="warning" >}}
Er bestaan ook unofficial AUR-packages (`tmog-bin`, `tmog-appimage`), maar de officiële AppImage is de veiligere keuze. Dezelfde algemene kanttekening als bij elke AUR-package: ongeauditeerde community build scripts. Daar komt bij dat `tmog-bin` op het moment van schrijven nog op 0.1.1 zat terwijl tmog.org zelf al bij 0.1.3 was — nog iets dat stilletjes uit sync kan raken.
{{< /callout >}}

![Task Manager TMOG - Summary](/images/tmog-summary.avif)

Retro vormgegeven, animeert op 60 Hz in plaats van de gebruikelijke eens-per-seconde refresh, en geeft een behoorlijk diepe per-proces uitsplitsing, tot en met schijf- en netwerk-I/O per PID:

![Task Manager TMOG - Processes](/images/tmog-processes.avif)
