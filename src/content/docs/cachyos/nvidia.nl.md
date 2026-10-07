---
title: "NVIDIA-driver"
weight: 3
prev: docs/cachyos/updates
next: docs/cachyos/secure-boot
distro: cachyos
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. De RTX 4060 is Ada, dus hij draait op NVIDIA's open kernelmodules (`nvidia-open`), en die installeert CachyOS standaard. Dit is niet Nouveau, en het is niets dat je zelf opzet.

**Driver die ik gebruik (op het moment van schrijven):**
- Versie: 615.71.09
- CUDA-versie: 13.4

## Er valt niets te installeren

CachyOS detecteert de kaart tijdens de installatie en zet `nvidia-open` op zonder handmatige stappen. Als de installer klaar is, is de driver actief en geconfigureerd.

Daarmee is de driver klaar. Wat overblijft is controleren of hij geladen is, een Secure Boot-sleutel inschrijven als je Secure Boot draait, en weten welke NVIDIA-services je wel en niet hoeft aan te raken.

## Verificatie Na Installatie

{{% steps %}}

### Controleer of de open module geladen is

```bash
cat /proc/driver/nvidia/version
```

De eerste regel zegt `NVIDIA UNIX Open Kernel Module` bij `nvidia-open`. De gesloten module zegt in plaats daarvan `NVIDIA UNIX x86_64 Kernel Module`.

### Controleer de driver- en CUDA-versie

```bash
nvidia-smi
```

Toont de driver- en CUDA-versies en bevestigt dat de kaart gezien wordt.

### Controleer geladen kernelmodules

```bash
lsmod | grep nvidia
```

Als de modules zichtbaar zijn, is de driver geladen. Zo niet, en Secure Boot staat aan, regel dan eerst [Secure Boot]({{< relref "/docs/cachyos/secure-boot" >}}).

{{% /steps %}}

## Energiebeheer

### Suspend en resume: er valt niets aan te zetten

Andere handleidingen zeggen dat je `nvidia-suspend.service`, `nvidia-resume.service` en `nvidia-hibernate.service` moet aanzetten. Op `nvidia-open` hoeft dat niet. [NVIDIA's README](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) zegt dat die units bedoeld zijn voor de closed driver met `NVreg_PreserveVideoMemoryAllocations=1` (of geavanceerde CUDA-functies), en dat het bewaren van videogeheugen met de open kernelmodules "automatisch wordt afgehandeld als `NVreg_UseKernelSuspendNotifiers=1` aanstaat" (vrij vertaald uit "is handled automatically if `NVreg_UseKernelSuspendNotifiers=1` is enabled"). Arch's `nvidia-utils` zet precies dat in `/usr/lib/modprobe.d/nvidia-utils.conf`, dus op CachyOS staat het al aan en blijven de units uit. GDM zoekt de units ook niet: ik vond geen verwijzing ernaar in het GDM 51.0-pakket.

Controleer het met de dGPU wakker (Hybrid of Ultimate), of lees het config-bestand in elke modus:

```bash
grep -E "UseKernelSuspendNotifiers|PreserveVideoMemoryAllocations" /proc/driver/nvidia/params
grep -r UseKernelSuspendNotifiers /usr/lib/modprobe.d /etc/modprobe.d
```

Je wilt `UseKernelSuspendNotifiers: 1` in de eerste en `NVreg_UseKernelSuspendNotifiers=1` in de tweede zien.

{{< callout type="info" >}}
**Waarom andere handleidingen iets anders zeggen.** De [asus-linux.org Arch-gids](https://asus-linux.org/guides/arch-guide/) en de [Arch-gids van het Open Gaming Collective](https://opengamingcollective.github.io/asusctl/distributions/arch.html) zeggen allebei: draai `systemctl enable nvidia-suspend.service nvidia-hibernate.service nvidia-resume.service`. Ze zeggen niet welke driver ze veronderstellen, en die units heeft de closed module nodig, dus volg ze als je `nvidia-dkms` draait of zelf `NVreg_PreserveVideoMemoryAllocations=1` hebt gezet. Ik vond niets dat zegt dat het aanzetten ervan op `nvidia-open` iets kapotmaakt, maar niets heeft ze daar ook nodig. Beide gidsen zeggen ook dat je `nvidia-suspend-then-hibernate.service` met rust moet laten tenzij je die slaapstand gebruikt, dus deze pagina zet hem niet aan.
{{< /callout >}}

### nvidia-powerd (Dynamic Boost)

`nvidia-powerd` is NVIDIA's Dynamic Boost-daemon, die het energiebudget tussen CPU en GPU verschuift. [NVIDIA's README](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html) noemt wat het nodig heeft: een notebook met een Ampere-GPU of nieuwer, een AMD Renoir-platform (of nieuwer) of Intel Comet Lake (of nieuwer), en SBIOS-ondersteuning. De firmware blijft de baas: Dynamic Boost wordt "automatisch ingeschakeld als de firmware de driver meldt dat de omstandigheden gunstig zijn" (vrij vertaald), en op de accu kan het soms prestaties kosten. NVIDIA, de [asus-linux.org FAQ](https://asus-linux.org/faq/graphics-switching/nvidia-dynamic-boost/) en de [Arch-gids van het Open Gaming Collective](https://opengamingcollective.github.io/asusctl/distributions/arch.html) zetten het allemaal aan met `systemctl enable --now nvidia-powerd`, en asus-linux.org voegt toe dat het het Performance-profiel wil.

asusd regelt de accukant zelf. `disable_nvidia_powerd_on_battery` in `/etc/asusd/asusd.ron` staat standaard aan en staat in ROG Control Center op de tab GPU Configuration als **Disable nvidia-powerd on battery**. Het stopt de service als je de stekker eruit trekt. De [asusctl changelog](https://github.com/OpenGamingCollective/asusctl/blob/main/CHANGELOG.md) dateert dat op 4.5.6: "nvidia-powerd.service will now enable or disable depending on the AC power state".

Op deze laptop staat de service aan. In Integrated mode stopt hij direct bij het opstarten met `Allocate Root client failed 0x59`, wat waarschijnlijk komt doordat de dGPU dan van de PCI-bus af is. Ik heb niet gecontroleerd wat hij in Hybrid of Ultimate doet, of de firmware van dit model Dynamic Boost überhaupt aanzet. Volgens NVIDIA's README meldt `/proc/driver/nvidia/gpus/*/power` of Dynamic Boost ondersteund wordt, wat je met de dGPU wakker kunt lezen. Dynamic Boost lost niets op, dus uit laten staan is prima. Eén reactie in een [CachyOS-forumthread](https://discuss.cachyos.org/t/nvidia-dynamic-boost-setup-for-notebooks/3785) meldt extra stotteren als het aanstaat, dus beoordeel het op je eigen frametimes. Het [soft-lockup-onderdeel in Bekende problemen]({{< relref "/docs/known-issues" >}}) legt uit waarom mensen de service vroeger maskeerden en waarom dat niet meer nodig is.

## Kernelupdates

De NVIDIA-modules komen voorgebouwd: `linux-cachyos-nvidia-open` vereist precies de bijbehorende `linux-cachyos`, dus pacman werkt ze samen bij. Met Secure Boot laat een pacman-hook sbctl de nieuwe kernel opnieuw ondertekenen. Er wordt lokaal niets gebouwd, dus er is geen DKMS-stap. Wat de kernel *niet* doet is modulehandtekeningen afdwingen, en daarom blijft de NVIDIA-module werken terwijl de kernel als tainted wordt gemarkeerd. Zie [Secure Boot op CachyOS]({{< relref "/docs/cachyos/secure-boot" >}}).

{{< callout type="info" >}}
Bekende problemen en troubleshooting voor de NVIDIA-driver staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}

## Meer lezen

- [CachyOS Wiki: Dual GPU Setup](https://wiki.cachyos.org/configuration/dual_gpu/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [NVIDIA driver README: Power Management](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html)
- [NVIDIA driver README: Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/posts/linux_asus_g16_2024/)
