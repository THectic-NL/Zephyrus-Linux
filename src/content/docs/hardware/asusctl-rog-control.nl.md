---
title: "asusctl & ROG Control Center"
weight: 3
next: docs/security/autologin
---

De Zephyrus G16 heeft veel hardware-functies die op Linux niet zomaar werken: fan curves, performance-profielen, de Slash LED op het deksel, GPU-switching, batterijlaadlimiet. Op deze pagina staat hoe ik dat allemaal werkend heb gekregen met asusctl en de tools van het ASUS Linux-project. Op CachyOS zijn deze tools direct beschikbaar vanuit de package repos.

{{< callout type="warning" >}}
**supergfxctl is verlaten.** Kom je gidsen tegen die `supergfxctl` of `supergfxd` noemen voor GPU-switching op ASUS-laptops: gebruik ze niet. Het project wordt niet meer onderhouden en vormt een beveiligingsrisico. Alles wat het vroeger deed zit nu in `asusctl` en ROG Control Center, die actief worden bijgehouden door het asus-linux team.
{{< /callout >}}

**Pakketinformatie (op het moment van schrijven):**
- `asusd` 6.3.8: achtergrondproces (backend) dat alle hardware-functies beheert
- `asusctl` 6.3.8: CLI frontend voor fan curves, profielen, batterijlimiet, RGB, Slash LED, GPU-switching
- `rog-control-center` 6.3.8: grafische frontend, onderdeel van de asusctl/asusd suite
- Bron: [asus-linux releases](https://gitlab.com/asus-linux/asusctl/-/releases) · beschikbaar in CachyOS/Arch repos


## Installatie

{{% steps %}}

### asusctl en ROG Control Center installeren

```bash
sudo pacman -S asusctl rog-control-center
```

Dit installeert:
- `asusd`: het achtergrondproces (backend) dat alle ASUS hardware-functies beheert
- `asusctl`: CLI-frontend die communiceert met asusd
- `rog-control-center`: grafische frontend die communiceert met asusd

Op CachyOS is dit alles wat je nodig hebt; beide packages zijn direct beschikbaar vanuit de repos en alles werkt meteen. Geen kernel patches of diepe systeemconfiguratie vereist.

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

```bash
sudo pacman -S nvtop powertop s-tui lm_sensors i2c-tools
```

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

De GA605WV heeft een hybride GPU-setup: de AMD Radeon 890M (iGPU) stuurt het interne display aan en de NVIDIA RTX 4060 (dGPU) verwerkt GPU-werklast.

GPU-switching wordt beheerd via ROG Control Center (GUI) of `asusctl armoury` (CLI), die direct communiceren met de `asus-armoury` kernel driver (beschikbaar vanaf kernel 6.19).

| Mode | Beschrijving |
|------|--------------|
| Hybrid (`dgpu_disable 0`) | Beide GPU's actief. NVIDIA verwerkt GPU-werklast, AMD stuurt het display aan. Het beste voor gaming. |
| Integrated (`dgpu_disable 1`) | Alleen AMD iGPU. Lager stroomverbruik, geen NVIDIA. Goed voor batterij. |

**Wisselen via GUI (ROG Control Center):**

Open ROG Control Center (`rog-control-center`) en navigeer naar de GPU-switching sectie om te wisselen tussen de Hybrid- en Integrated-modus.

![ROG Control Center - GPU switching](/images/rog-control-gpu-switching.avif)

**Wisselen via CLI (asusctl armoury):**

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

> **Belangrijk:** `nvidia-powerd.service` moet uitgeschakeld en **gemaskeerd** blijven op deze laptop. Het conflicteert met AMD ATPX power management en veroorzaakt soft lockups en reboot hangs (zwart scherm, backlights blijven aan). GPU-vermogensbeheer loopt via ATPX (via ACPI). Zie de [NVIDIA Driver Installatie Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) voor diagnosedetails en commando's.

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

De `asus-armoury` driver is [gemerged in Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). Deze nieuwe `platform/x86` driver vervangt delen van de oudere `asus-wmi` met een schonere sysfs-gebaseerde API, waarmee o.a. paneelmodusschakeling, APU-geheugentoewijzing, PPT-tuning en meer mogelijk wordt direct vanuit de kernel. De driver is volledig door de community ontwikkeld door het [asus-linux team](https://asus-linux.org/), zonder enige betrokkenheid van ASUS zelf. Deze driver zit in elke CachyOS-kernel vanaf 6.19. De huidige kernel op het moment van schrijven is 7.0.12-1-cachyos.

**Voor**: basale asusctl-bediening zonder Armoury-instellingen:

![ROG Control voor asus-armoury in mainline](/images/rog-control-armoury.avif)

**Na**: volledige Armoury-instellingen zichtbaar, inclusief PPT/vermogenslimiet tuning:

![ROG Control System Control met Armoury-instellingen en vermogenslimieten](/images/rog-control-system-control.avif)

**Bronnen:** [Phoronix artikel](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussie](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)

### Kernel 7.0: ASUS laptop quirks + nieuw AMDGPU-werk

Kernel 7.0 is in april 2026 uitgebracht en CachyOS pakte het snel op. Voor deze ASUS ROG G16 bracht het wat beloofd was: betere AMDGPU-ondersteuning voor nieuwere RDNA 3.5-klasse IP blocks (GFX11.5.4) en verder NVIDIA-werk. De gaming-performance op de Radeon 890M is merkbaar verbeterd, ruwweg in lijn met de ~20% uplift die werd verwacht. Samen met de verbeteringen uit 6.19 draait deze hardware eindelijk zoals het hoort op Linux. De huidige CachyOS-kernel is 7.0.12-1-cachyos.

**Bronnen:** [Linus bevestigt Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks voor ASUS ROG modellen](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)


## Aanvullende Bronnen

- [asus-linux.org](https://asus-linux.org/): officiële projectsite
- [asusctl GitLab](https://gitlab.com/asus-linux/asusctl): broncode en issue tracker
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/): CachyOS-specifieke documentatie
- [NVIDIA Driver Installatie Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}): NVIDIA driver setup en bekende problemen
