---
title: "NVIDIA Driver: CachyOS"
weight: 1
prev: docs/getting-started/bazzite
next: docs/hardware/nvidia-bazzite
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. De open-source Nouveau driver werkt niet goed op moderne NVIDIA-hardware, dus proprietary drivers zijn nodig.

**Driver die ik gebruik (op het moment van schrijven):**
- Versie: 610.43.02
- CUDA-versie: 13.3

## Er valt niets te installeren

CachyOS detecteert je hardware automatisch tijdens de installatie en installeert de NVIDIA-driver zonder handmatige stappen. Je hoeft zelf niets te selecteren; als de installer klaar is, is de driver al actief en volledig geconfigureerd.

Daarmee is de driver zelf klaar. Wat overblijft is controleren of hij geladen is, plus twee energie-instellingen die specifiek voor deze laptop zijn en *niet* voor je gezet worden.

## Verificatie Na Installatie

{{% steps %}}

### NVIDIA-driver verifiëren

Controleer de driverstatus:

```bash
nvidia-smi
```

Je ziet de NVIDIA driver- en CUDA-versies in de output.

### Controleer geladen kernelmodules

```bash
lsmod | grep nvidia
```

Als de modules zichtbaar zijn, is de driver geladen en functioneel.

{{% /steps %}}

## Energiebeheer

{{% steps %}}

### Zet de NVIDIA power services aan

Activeer de NVIDIA power services voor beter suspend/resume-gedrag en energiebeheer:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**Wat deze services doen:**
- `nvidia-hibernate.service` - Slaat de GPU state correct op vóór hibernation
- `nvidia-suspend.service` - Beheert GPU state tijdens system suspend
- `nvidia-resume.service` - Herstelt GPU state na resume

Deze services voorkomen GPU state problemen na suspend/resume cycli.

### Maskeer `nvidia-powerd` permanent

De `nvidia-powerd.service` beheert NVIDIA Dynamic Boost, waarmee extra wattage (~5-15W) van de CPU naar de GPU geschoven wordt tijdens zware GPU-belasting. Hoewel nuttig op Intel-gebaseerde laptops, conflicteert het met AMD ATPX power management op de Zephyrus G16 en veroorzaakt soft lockups en "GPU has fallen off the bus" fouten.

Op deze laptop wordt GPU-vermogensbeheer geregeld via ATPX (AMD-gestuurd via ACPI). De NVIDIA suspend/hibernate/resume services beheren power states correct zonder `nvidia-powerd`.

**Wat je verliest door het uit te zetten:** Minimaal. Iets minder FPS bij zware GPU workloads. De ~5-15W Dynamic Boost is de instabiliteit niet waard op AMD ATPX hardware.

```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Maskeren maakt een symlink naar `/dev/null`, waardoor geen enkel proces — ook een driver-update via `pacman` niet — de service opnieuw kan activeren.

**Als je het later opnieuw wilt proberen** (bijv. na een kernel- of driver-update die het ATPX-conflict mogelijk verhelpt):

```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

**Referentie:**
- [NVIDIA Power Management Documentatie](https://download.nvidia.com/XFree86/Linux-x86_64/610.43.02/README/powermanagement.html)

{{% /steps %}}

## Kernelupdates

De driver is een DKMS-module, dus een kernelupdate zet via pacman-hooks twee dingen in gang:

1. DKMS herbouwt de NVIDIA-modules tegen de nieuwe kernel
2. Heb je Secure Boot ingesteld, dan ondertekent sbctl de nieuwe kernel-EFI-image opnieuw

Geen van beide vraagt handmatig ingrijpen. Wat de kernel *niet* doet is modulehandtekeningen afdwingen, en daarom blijft de NVIDIA-module werken terwijl de kernel als tainted wordt gemarkeerd — zie [Secure Boot op CachyOS]({{< relref "/docs/hardware/secure-boot-cachyos" >}}).

{{< callout type="info" >}}
Bekende problemen en troubleshooting voor de NVIDIA-driver staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}

## Meer lezen

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
