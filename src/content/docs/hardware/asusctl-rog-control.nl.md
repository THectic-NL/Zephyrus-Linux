---
title: "asusctl & ROG Control Center"
weight: 1
prev: docs/hardware
next: docs/hardware/color-profiles
---

De Zephyrus G16 heeft veel hardware-functies die op Linux niet zomaar werken: fan curves, performance-profielen, de Slash LED op het deksel, GPU-switching, batterijlaadlimiet. Op deze pagina staat hoe ik dat allemaal werkend heb gekregen met asusctl en de tools van het ASUS Linux-project. Alles onder de installatiestap is op beide distributies identiek, want het is dezelfde daemon die dezelfde hardware uitleest. Alleen het installeren verschilt.

{{< callout type="warning" >}}
**supergfxctl is verlaten.** Kom je gidsen tegen die `supergfxctl` of `supergfxd` noemen voor GPU-switching op ASUS-laptops: gebruik ze niet. Het project wordt niet meer onderhouden en vormt een beveiligingsrisico. Alles wat het vroeger deed zit nu in `asusctl` en ROG Control Center, die actief worden bijgehouden door het asus-linux team.
{{< /callout >}}

**Pakketinformatie (op het moment van schrijven):**
- `asusctl` 6.4.0: CLI frontend voor fan curves, profielen, batterijlimiet, RGB, Slash LED, GPU-switching. Levert ook `asusd` mee, het achtergrondproces dat daadwerkelijk met de hardware praat, plus de bijbehorende systemd-service — er is geen los `asusd`-pakket om te installeren, `pacman -Q asusd` / `rpm -q asusd` komt leeg terug terwijl de daemon er wel degelijk is.
- `rog-control-center` 6.4.0: grafische frontend, communiceert met asusd
- Bron: [asusctl releases](https://github.com/OpenGamingCollective/asusctl/releases) · in de CachyOS/Arch-repos, en in [Terra](https://terra.fyralabs.com/) voor Fedora

{{< callout type="info" >}}
Controleer wat er daadwerkelijk geïnstalleerd is met `asusctl info` (toont de asusctl-versie samen met gedetecteerde hardware) of `pacman -Q asusctl rog-control-center` / `rpm -q asusctl rog-control-center`.
{{< /callout >}}

{{< callout type="info" >}}
Het project is in 2026 verhuisd. De ontwikkeling zat vroeger in de `asus-linux`-organisatie op GitLab (nu gearchiveerd, read-only); `asusctl`, `asusd` en `rog-control-center` worden nu onderhouden onder het [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl) op GitHub. [asus-linux.org](https://asus-linux.org/) is nog steeds de projectsite. Oudere gidsen die naar `gitlab.com/asus-linux` of de `lukenukem`-COPR voor Fedora wijzen zijn verouderd.
{{< /callout >}}

ROG Control Center omschrijft zichzelf, via het eigen **About**-tabblad, als "a powerful graphical interface for managing ASUS ROG, TUF, and ProArt laptops on Linux... the official GUI for the asusctl toolset." Het vereist momenteel kernel 6.19, wordt uitgebracht onder de MPL-2.0-licentie, en noemt een eigen work-in-progress-lijst (widget-theming, een CPU/GPU temp/fan-infobalk, Screenpad- en ROG Ally-specifieke instellingen) — de moeite waard om daar zelf te checken voordat je een ontbrekende functie als bug bestempelt.

![ROG Control Center - About-tabblad](/images/rog-control-about.avif)


## Installatie

{{% steps %}}

### asusctl en ROG Control Center installeren

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S asusctl rog-control-center
```

Beide packages komen direct uit de repos en alles werkt meteen. Geen kernel patches of diepe systeemconfiguratie vereist.

{{< /tab >}}
{{< tab name="Bazzite" >}}

`asusd` is een systeemdaemon die tegen de kernel aan praat, dus dit is een van de weinige gevallen waarin layeren het juiste antwoord is en niet het laatste redmiddel. Hij zit niet in Fedora's eigen repositories; de ASUS Linux-packages staan in [Terra](https://terra.fyralabs.com/).

Voeg de Terra-repository toe en layer daarna de packages:

```bash
curl -fsSL https://github.com/terrapkg/subatomic-repos/raw/main/terra.repo | pkexec tee /etc/yum.repos.d/terra.repo
rpm-ostree install terra-release
systemctl reboot
```

```bash
rpm-ostree install asusctl rog-control-center
systemctl reboot
```

Twee keer herstarten, want een gelaagd package wordt op de volgende image toegepast en niet op de draaiende.

{{< callout type="warning" >}}
Kijk eerst voordat je layert. Bazzite-images voor ASUS-handhelds leveren `asusctl` al mee, en een package layeren dat in de image zit is een conflict en geen upgrade:

```bash
rpm -q asusctl
ujust
```

Staat `asusctl` er al, of noemt `ujust` een ASUS-recept, gebruik dat dan.
{{< /callout >}}

De oudere `lukenukem/asus-linux`-COPR waar de meeste gidsen naar wijzen wordt niet meer onderhouden. Gebruik Terra.

{{< /tab >}}
{{< /tabs >}}

Hiermee krijg je:
- `asusd`: het achtergrondproces (backend) dat alle ASUS hardware-functies beheert
- `asusctl`: CLI-frontend die communiceert met asusd
- `rog-control-center`: grafische frontend die communiceert met asusd

### Services activeren

```bash
sudo systemctl enable --now asusd.service
```

Herstart om te zorgen dat alle services correct opstarten:
```bash
sudo reboot
```

### Hardwaredetectie verifiëren

Na de herstart, verifieer dat asusctl je hardware correct heeft gedetecteerd:

```bash
asusctl info
```

Verwachte output bevat:
```
Product family: ROG Zephyrus G16
Board name: GA605WV
```

### Monitoring tools installeren (optioneel)

Handige tools voor hardwaremonitoring naast asusctl:

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S nvtop powertop s-tui lm_sensors i2c-tools
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Dit zijn commandline-tools, dus Homebrew of een distrobox-container is er de juiste plek voor, niet de image:

```bash
brew install nvtop powertop s-tui
```

`lm_sensors` en `i2c-tools` lezen hardware rechtstreeks uit en horen op de host thuis. `lm_sensors` is er meestal al; layer `i2c-tools` als je het nodig hebt:

```bash
rpm-ostree install i2c-tools
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

| Package | Beschrijving |
|---------|--------------|
| `nvtop` | GPU-procesmonitor (AMD + NVIDIA tegelijk) |
| `powertop` | Stroomverbruikanalyse per proces/apparaat |
| `s-tui` | TUI-dashboard: CPU-frequentie, temperatuur, belasting, stresstest |
| `lm_sensors` | Hardware-temperatuursensor uitlezen |
| `i2c-tools` | Low-level hardware bus diagnostics |

{{% /steps %}}


## Configuratie

{{% details title="Batterijlaadlimiet instellen (aanbevolen: 80%)" closed="true" %}}

Het beperken van het laden tot 80% verlengt de levensduur van de batterij aanzienlijk. De laptop werkt normaal op netstroom ongeacht deze instelling.

**Instellen via CLI:**
```bash
asusctl battery --charge-limit 80
```

**Instellen via GUI:**
Open ROG Control Center (`rog-control-center`) → System Control → Battery Charge Limit.

**Verifieer:**
```bash
asusctl battery
```

Deze instelling blijft behouden na herstarten en wordt beheerd door `asusd`.

{{% /details %}}

{{% details title="Slash LED configureren (de lichtbalk op het deksel)" closed="true" %}}

De Slash LED is de diagonale lichtbalk op het deksel van de G16. Deze ondersteunt meerdere animaties en kan worden ingesteld om uit te gaan op batterij.

**Beschikbare animaties tonen:**
```bash
asusctl slash --list
```

Beschikbare animaties: `Static`, `Bounce`, `Slash`, `Loading`, `BitStream`, `Transmission`, `Flow`, `Flux`, `Phantom`, `Spectrum`, `Hazard`, `Interfacing`, `Ramp`, `GameOver`, `Start`, `Buzzer`

**Aanbevolen setup (alleen op netstroom, uit op batterij en tijdens slaapstand):**
```bash
asusctl slash --enable -b false -s false
```

**Wat deze opties doen:**
- `--enable`: Slash LED inschakelen
- `-b false`: uitschakelen op batterijstroom
- `-s false`: uitschakelen tijdens slaapstand

**Animatie instellen:**
```bash
asusctl slash --mode Spectrum
```

**Helderheid instellen (0–255):**
```bash
asusctl slash -l 128
```

![ROG Control Center - Slash Lighting](/images/rog-control-slash-lighting.avif)

{{% /details %}}

{{% details title="Prestatieprofielen" closed="true" %}}

asusctl biedt drie prestatieprofielen die de CPU/GPU-vermogensgrenzen en het ventilatorgedrag bepalen:

| Profiel | Beschrijving |
|---------|--------------|
| `Silent` | Laag vermogen, stille ventilatoren, beperkte prestaties |
| `Balanced` | Standaard. Gematigd vermogen en geluid |
| `Performance` | Maximaal CPU/GPU-vermogen, agressieve ventilatoren |

**Profiel instellen:**
```bash
asusctl profile -P Balanced
asusctl profile -P Silent
asusctl profile -P Performance
```

**Door profielen heen wisselen:**
```bash
asusctl profile --next
```

**Huidig profiel bekijken:**
```bash
asusctl profile
```

> **Let op:** Profielwisseling vereist dat `power-profiles-daemon` actief is. Zie de installatiestappen hierboven.

{{% /details %}}

{{% details title="GPU mode switching (ROG Control Center / asusctl armoury)" closed="true" %}}

De GA605WV heeft een hybride GPU-setup mét een fysieke MUX-switch: zowel de AMD Radeon 890M (iGPU) als de NVIDIA RTX 4060 (dGPU) kunnen het interne display aansturen, niet alleen de iGPU zoals eerdere versies van deze pagina aannamen.

GPU-switching wordt beheerd via ROG Control Center (GUI, tabblad **GPU Configuration**) of `asusctl armoury` (CLI), die direct communiceren met de `asus-armoury` kernel driver (beschikbaar vanaf kernel 6.19).

**Bevestigd op deze hardware, huidige ROG Control Center build:** het tabblad GPU Configuration biedt drie modes:

| Mode | Beschrijving |
|------|--------------|
| Hybrid | Beide GPU's actief. NVIDIA verwerkt GPU-werklast, AMD stuurt het display aan. Het beste voor gaming. |
| Integrated | Alleen AMD iGPU. Lager stroomverbruik, geen NVIDIA. Goed voor batterij. |
| Ultimate | dGPU stuurt het display rechtstreeks aan via de fysieke MUX. Hoogste NVIDIA-prestaties, geen iGPU-overhead — maar de AMD iGPU is niet beschikbaar zolang deze mode actief is. |

{{< callout type="warning" >}}
**De drie modes komen neer op twee firmware-attributen**, `dgpu_disable` en `gpu_mux_mode`, beide onder `/sys/class/firmware-attributes/asus-armoury/attributes/<naam>/current_value`. Bevestigd tegen de broncode van asusd zelf (de testsuite van `asus-shutdown`) en gecontroleerd tegen de echte sysfs-waarden op deze hardware:

| Mode | `dgpu_disable` | `gpu_mux_mode` |
|------|------|------|
| Ultimate | 0 | 0 |
| Hybrid | 0 | 1 |
| Integrated | 1 | 1 |

Hybrid ↔ Integrated verandert alleen `dgpu_disable`; Ultimate is de enige mode die ook `gpu_mux_mode` omzet.

**Modewisselingen kunnen stilletjes niet toegepast worden.** Een bekende upstream-bug (zie [Bekende Problemen]({{< relref "/docs/known-issues" >}})) kan de mode-write tijdens shutdown afbreken zonder dat je een foutmelding ziet — de dropdown toont na een herstart gewoon weer de oude mode, zowel vanuit de GUI als via `asusctl armoury`. Lijkt een wissel niet aan te slaan, dan is dit de meest waarschijnlijke oorzaak. Alleen het attribuut wegschrijven dat daadwerkelijk moet veranderen, rechtstreeks naar het sysfs-pad hierboven (buiten asusd om), omzeilt de bug — ten koste van dat asusd/de GUI de wijziging niet meekrijgt totdat het weer bijtrekt.
{{< /callout >}}

**Wisselen via GUI (ROG Control Center):**

Open ROG Control Center en ga naar **GPU Configuration** in de zijbalk. Kies een mode via de **GPU mode**-dropdown.

![ROG Control Center - GPU Configuration met Integrated/Ultimate/Hybrid](/images/rog-control-gpu-configuration.avif)

> De dropdown toont altijd de huidige mode; wijzigingen worden pas na een herstart actief. Je kan (nog) niet live wisselen zoals Windows-tools als G-Helper dat doen.

**Wisselen via CLI (asusctl armoury) — alleen Hybrid en Integrated:**

**Huidige dGPU status bekijken:**
```bash
asusctl armoury get dgpu_disable
```

**Overschakelen naar iGPU-only (dGPU uitschakelen):**
```bash
asusctl armoury set dgpu_disable 1
```

**Overschakelen naar Hybrid (dGPU inschakelen):**
```bash
asusctl armoury set dgpu_disable 0
```

> **Let op:** Na het wisselen van mode kan een herstart of uitloggen/inloggen vereist zijn.

> **Belangrijk:** Houd `nvidia-powerd.service` gemaskeerd op deze laptop, ongeacht de GPU-mode — zie [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor waarom.

{{% /details %}}

{{% details title="App-instellingen (achtergrond- en tray-gedrag)" closed="true" %}}

ROG Control Center heeft een tabblad **App Settings** dat bepaalt hoe de app zelf draait, los van de hardwareconfiguratie:

- **Run in background after closing** — houdt `asusd`/het tray-icoon actief als het venster gesloten wordt
- **Start app in background (UI closed)** — geminimaliseerd naar de tray opstarten
- **Enable system tray icon**
- **Enable dGPU notifications** — toont een melding zodra de dGPU wordt gepauzeerd/hervat (dit is de "dGPU status changed: suspended"-melding die je ziet na het wisselen van GPU-mode of als de dGPU idle wordt)

![ROG Control Center - App Settings](/images/rog-control-app-settings.avif)

De app markeert dit tabblad zelf als **work in progress**; met name de notificaties zijn nog niet compleet.

{{% /details %}}

{{% details title="Toetsenbord RGB (Aura)" closed="true" %}}

**Toetsenbordverlichting helderheid aanpassen:**
```bash
asusctl led-brighter
asusctl led-dimmer
```

**Aura configuratie openen in ROG Control Center:**
```bash
rog-control-center
```

Ga naar de sectie "Keyboard Aura" voor animatie, kleur en per-toets configuratie.

![ROG Control Center - Keyboard Aura](/images/rog-control-keyboard-aura.avif)

{{% /details %}}

{{% details title="Aangepaste fan curves" closed="true" %}}

Fan curves kunnen per prestatieprofiel worden geconfigureerd in ROG Control Center of via de CLI.

**ROG Control Center openen:**
```bash
rog-control-center
```

Ga naar "Fan Curves" om temperatuur/snelheidscurven per profiel in te stellen (Silent, Balanced, Performance).

**CLI fan curve formaat:**
```bash
# Huidige fan curve data voor een profiel tonen
asusctl fan-curve -m Balanced

# Aangepaste curve instellen (8 temperatuur/snelheid paren: temp:speed,temp:speed,...)
asusctl fan-curve -m Balanced -D 30:0,40:10,50:30,60:50,70:70,80:85,90:100,100:100
```

![ROG Control Center - Fan Curves](/images/rog-control-fan-curves.avif)

> **Let op:** Fan curve aanpassing vereist de `asus-armoury` kernel driver. Op kernel < 6.19 is de driver niet beschikbaar en worden curves die je in de GUI instelt mogelijk niet correct opgeslagen. Zie de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor details.

{{% /details %}}


## Monitoring

{{% details title="Hardware monitoring commando's" closed="true" %}}

**GPU monitor (AMD + NVIDIA):**
```bash
nvtop
```

**CPU-frequentie, temperatuur, belastingsdashboard:**
```bash
s-tui
```

**Stroomverbruik per proces/apparaat:**
```bash
sudo powertop
```

**Hardware-temperaturen:**
```bash
sensors
```

**asusd service logs bekijken:**
```bash
sudo journalctl -b -u asusd
```

{{% /details %}}


{{< callout type="info" >}}
Bekende problemen en probleemoplossing voor asusctl & ROG Control Center staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}


## CLI Snelreferentie

| Commando | Beschrijving |
|----------|--------------|
| `asusctl info` | Gedetecteerde hardware tonen |
| `asusctl battery --charge-limit 80` | Batterijlaadlimiet instellen op 80% |
| `asusctl battery` | Huidig laadlimiet tonen |
| `asusctl profile` | Huidig prestatieprofiel tonen |
| `asusctl profile -P Balanced` | Prestatieprofiel instellen |
| `asusctl profile --next` | Naar volgend profiel wisselen |
| `asusctl slash --list` | Beschikbare Slash LED animaties tonen |
| `asusctl slash --enable -b false -s false` | Slash LED aan, uit op batterij en slaapstand |
| `asusctl slash --mode Spectrum` | Slash LED animatie instellen |
| `asusctl slash -l 128` | Slash LED helderheid instellen (0–255) |
| `asusctl armoury get dgpu_disable` | Huidige dGPU status tonen (0=aan, 1=uit) |
| `asusctl armoury set dgpu_disable 1` | Overschakelen naar iGPU-only (dGPU uitschakelen) |
| `asusctl armoury set dgpu_disable 0` | Overschakelen naar Hybrid mode (dGPU inschakelen) |
| `rog-control-center` | ROG Control Center GUI openen |


## Kernel Updates

### Kernel 6.19: asus-armoury driver in mainline Linux

De `asus-armoury` driver is [gemerged in Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). Deze nieuwe `platform/x86` driver vervangt delen van de oudere `asus-wmi` met een schonere sysfs-gebaseerde API, waarmee o.a. paneelmodusschakeling, APU-geheugentoewijzing, PPT-tuning en meer mogelijk wordt direct vanuit de kernel. De driver is volledig door de community ontwikkeld door het [asus-linux team](https://asus-linux.org/), zonder enige betrokkenheid van ASUS zelf. Deze driver zit in elke CachyOS-kernel vanaf 6.19. De huidige kernel op het moment van schrijven is 7.2.4-1-cachyos.

**Voor**: basale asusctl-bediening zonder Armoury-instellingen:

![ROG Control voor asus-armoury in mainline](/images/rog-control-armoury.avif)

**Na**: volledige Armoury-instellingen zichtbaar, inclusief PPT/vermogenslimiet tuning:

![ROG Control System Control met Armoury-instellingen en vermogenslimieten](/images/rog-control-system-control.avif)

**Bronnen:** [Phoronix artikel](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussie](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)

### Kernel 7.0: ASUS laptop quirks + nieuw AMDGPU-werk

Kernel 7.0 is in april 2026 uitgebracht en CachyOS pakte het snel op. Voor deze ASUS ROG G16 bracht het wat beloofd was: betere AMDGPU-ondersteuning voor nieuwere RDNA 3.5-klasse IP blocks (GFX11.5.4) en verder NVIDIA-werk. De gaming-performance op de Radeon 890M is merkbaar verbeterd, ruwweg in lijn met de ~20% uplift die werd verwacht. Samen met de verbeteringen uit 6.19 draait deze hardware eindelijk zoals het hoort op Linux. De huidige CachyOS-kernel is 7.2.4-1-cachyos.

**Bronnen:** [Linus bevestigt Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks voor ASUS ROG modellen](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)


## Aanvullende Bronnen

- [asus-linux.org](https://asus-linux.org/): officiële projectsite
- [asusctl op GitHub](https://github.com/OpenGamingCollective/asusctl): broncode en issue tracker
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/): CachyOS-specifieke documentatie
- NVIDIA driver setup en bekende problemen: [CachyOS]({{< relref "/docs/cachyos/nvidia" >}}) · [Bazzite]({{< relref "/docs/bazzite/nvidia" >}})
