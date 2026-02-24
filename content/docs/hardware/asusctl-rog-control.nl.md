---
title: "asusctl & ROG Control Center"
weight: 22
---

De Zephyrus G16 heeft veel hardware-functies die op Linux niet zomaar werken — fan curves, performance-profielen, de Slash LED op het deksel, GPU-switching, batterijlaadlimiet. Op deze pagina staat hoe ik dat allemaal werkend heb gekregen met asusctl en de tools van het ASUS Linux-project. Op CachyOS zijn deze tools direct beschikbaar vanuit de package repos.

**Package informatie:**
- `asusctl` 6.3.2 — CLI voor fan curves, profielen, batterijlimiet, RGB, Slash LED
- `asusctl-rog-gui` 6.3.2 — ROG Control Center GUI
- `supergfxctl` 5.2.7 — GPU mode switching
- Bron: CachyOS/Arch repos (packages beheerd door Luke Jones, primaire asusctl developer)


## Installatie

{{% steps %}}

### asusctl, ROG Control Center en supergfxctl installeren

```bash
sudo pacman -S asusctl supergfxctl power-profiles-daemon rog-control-center
```

Dit installeert:
- `asusctl` — hoofd CLI daemon en client
- `asusctl-rog-gui` — ROG Control Center GUI
- `supergfxctl` — GPU mode switching daemon

### Services activeren

```bash
sudo systemctl enable --now asusd.service
sudo systemctl enable supergfxd.service
```

Herstart om te zorgen dat alle services correct opstarten:
```bash
sudo reboot
```

### Hardware detectie verifiëren

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

Handige tools voor hardware monitoring naast asusctl:

```bash
sudo pacman -S nvtop powertop s-tui lm_sensors i2c-tools
```

| Package | Beschrijving |
|---------|--------------|
| `nvtop` | GPU procesmonitor (AMD + NVIDIA tegelijk) |
| `powertop` | Stroomverbruik analyse per proces/apparaat |
| `s-tui` | TUI dashboard: CPU frequentie, temperatuur, load, stress test |
| `lm_sensors` | Hardware temperatuursensor uitlezen |
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
- `--enable` — Slash LED inschakelen
- `-b false` — uitschakelen op batterijstroom
- `-s false` — uitschakelen tijdens slaapstand

**Animatie instellen:**
```bash
asusctl slash --mode Spectrum
```

**Helderheid instellen (0–255):**
```bash
asusctl slash -l 128
```

{{% /details %}}

{{% details title="Performance profielen" closed="true" %}}

asusctl biedt drie performance profielen die de CPU/GPU-vermogensgrenzen en ventilatorgedrag bepalen:

| Profiel | Beschrijving |
|---------|--------------|
| `Silent` | Laag vermogen, stille ventilatoren, beperkte prestaties |
| `Balanced` | Standaard. Gematigd vermogen en geluid |
| `Performance` | Maximaal CPU/GPU vermogen, agressieve ventilatoren |

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

{{% details title="GPU mode switching (supergfxctl)" closed="true" %}}

De GA605WV heeft een hybrid GPU setup: de AMD Radeon 890M (iGPU) stuurt het interne display aan en de NVIDIA RTX 4060 (dGPU) verwerkt GPU workloads.

`supergfxctl` beheert welke GPU mode actief is:

| Mode | Beschrijving |
|------|--------------|
| `Hybrid` | Beide GPU's actief. NVIDIA verwerkt GPU workloads, AMD stuurt het display aan. Het beste voor gaming. |
| `Integrated` | Alleen AMD iGPU. Lager stroomverbruik, geen NVIDIA. Goed voor batterij. |
| `AsusMuxDgpu` | NVIDIA stuurt het display direct aan via hardware MUX switch. Laagste latency voor gaming. Vereist herstart. |

**Huidige mode bekijken:**
```bash
supergfxctl --mode
```

**Mode wisselen:**
```bash
supergfxctl --mode Hybrid
supergfxctl --mode Integrated
```

> **Let op:** Wisselen tussen Hybrid en Integrated vereist uitloggen/inloggen. Overstappen naar AsusMuxDgpu vereist een herstart.

> **Belangrijk:** `nvidia-powerd.service` moet uitgeschakeld en **gemaskt** blijven op deze laptop. Het conflicteert met AMD ATPX power management en veroorzaakt soft lockups en reboot hangs (zwart scherm, backlights blijven aan). Masken is essentieel omdat `supergfxd` direct `systemctl start nvidia-powerd.service` aanroept tijdens GPU mode switches — `disable` alleen voorkomt dit niet. De mask (symlink naar `/dev/null`) blokkeert zowel `supergfxd` als NVIDIA driver updates. GPU-vermogensbeheer loopt via ATPX (via ACPI). Zie de [NVIDIA Driver Installatie Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) voor diagnosedetails en commando's.

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

Fan curves kunnen per performance profiel worden geconfigureerd in ROG Control Center of via de CLI.

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

> **Let op:** Fan curve aanpassing vereist de `asus-armoury` kernel driver. Op kernel < 6.19 is de driver niet beschikbaar en worden curves die je in de GUI instelt mogelijk niet correct opgeslagen. Zie de sectie Bekende Problemen hieronder.

{{% /details %}}


## Monitoring

{{% details title="Hardware monitoring commando's" closed="true" %}}

**GPU monitor (AMD + NVIDIA):**
```bash
nvtop
```

**CPU frequentie, temperatuur, load dashboard:**
```bash
s-tui
```

**Stroomverbruik per proces/apparaat:**
```bash
sudo powertop
```

**Hardware temperaturen:**
```bash
sensors
```

**asusd service logs bekijken:**
```bash
sudo journalctl -b -u asusd
```

**supergfxd service logs bekijken:**
```bash
sudo journalctl -b -u supergfxd
```

{{% /details %}}


## Bekende Problemen

{{% details title="ROG Control Center melding: \"The asus-armoury driver is not loaded\"" closed="true" %}}

**Probleem:**
ROG Control Center toont een melding dat de `asus-armoury` kernel driver niet geladen is. Geavanceerde functies (PPT vermogensgrenzen, APU geheugenallocatie, MUX switch besturing) zijn niet beschikbaar.

**Oorzaak:**
De `asus-armoury` driver is samengevoegd in de Linux mainline kernel in versie 6.19. CachyOS levert kernel 6.19.3-2 inclusief deze driver, dus hij zou beschikbaar moeten zijn.

**Wat nog wel werkt zonder de driver:**
- Fan curves (basis)
- Performance profielen (Silent / Balanced / Performance)
- Batterijlaadlimiet
- Slash LED
- Toetsenbord Aura / RGB
- GPU switching via supergfxctl

**Oplossing:**
Verifieer dat de driver geladen is:
```bash
lsmod | grep asus_armoury
```

Als hij laadt, heropen ROG Control Center — de melding zou verdwenen moeten zijn en geavanceerde functies zijn beschikbaar.

> **Let op voor GA605WV ondersteuning:** De initiële 6.19 release vermeldt GA403-serie modellen expliciet. Als de GA605WV nog niet in de DMI-tabel staat, zijn sommige model-specifieke functies (PPT-afstemming, APU-geheugen) mogelijk nog steeds niet beschikbaar, zelfs op 6.19. Dit zal worden opgelost via follow-up kernel patches.

{{% /details %}}


## CLI Snelreferentie

| Commando | Beschrijving |
|----------|--------------|
| `asusctl info` | Gedetecteerde hardware tonen |
| `asusctl battery --charge-limit 80` | Batterijlaadlimiet instellen op 80% |
| `asusctl battery` | Huidig laadlimiet tonen |
| `asusctl profile` | Huidig performance profiel tonen |
| `asusctl profile -P Balanced` | Performance profiel instellen |
| `asusctl profile --next` | Naar volgend profiel wisselen |
| `asusctl slash --list` | Beschikbare Slash LED animaties tonen |
| `asusctl slash --enable -b false -s false` | Slash LED aan, uit op batterij en slaapstand |
| `asusctl slash --mode Spectrum` | Slash LED animatie instellen |
| `asusctl slash -l 128` | Slash LED helderheid instellen (0–255) |
| `supergfxctl --mode` | Huidige GPU mode tonen |
| `supergfxctl --mode Hybrid` | Overschakelen naar Hybrid GPU mode |
| `supergfxctl --mode Integrated` | Overschakelen naar geïntegreerde GPU |
| `rog-control-center` | ROG Control Center GUI openen |


## Aanvullende Bronnen

- [asus-linux.org](https://asus-linux.org/) — Officiële projectsite
- [asusctl GitLab](https://gitlab.com/asus-linux/asusctl) — Broncode en issue tracker
- [CachyOS Wiki: ASUS](https://wiki.cachyos.org/) — CachyOS-specifieke documentatie
- [NVIDIA Driver Installatie Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) — NVIDIA driver setup en bekende problemen
