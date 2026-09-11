---
title: "NVIDIA-driver"
weight: 3
prev: docs/cachyos/updates
next: docs/cachyos/secure-boot
distro: cachyos
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. De RTX 4060 is Ada, dus hij draait op NVIDIA's open kernelmodules (`nvidia-open`), en die installeert CachyOS standaard. Dit is niet Nouveau, en het is niets dat je zelf opzet.

**Driver die ik gebruik (op het moment van schrijven):**
- Versie: 610.57.04
- CUDA-versie: 13.3

## Er valt niets te installeren

CachyOS detecteert de kaart tijdens de installatie en zet `nvidia-open` op zonder handmatige stappen. Als de installer klaar is, is de driver actief en geconfigureerd.

Daarmee is de driver klaar. Wat overblijft is controleren of hij geladen is, een Secure Boot-sleutel inschrijven als je Secure Boot draait, en twee energie-instellingen die specifiek voor deze laptop zijn en *niet* voor je gezet worden.

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

{{% /steps %}}

## Kernelupdates

De driver is een DKMS-module, dus een kernelupdate zet via pacman-hooks twee dingen in gang:

1. DKMS herbouwt de NVIDIA-modules tegen de nieuwe kernel
2. Heb je Secure Boot ingesteld, dan ondertekent sbctl de nieuwe kernel-EFI-image opnieuw

Geen van beide vraagt handmatig ingrijpen. Wat de kernel *niet* doet is modulehandtekeningen afdwingen, en daarom blijft de NVIDIA-module werken terwijl de kernel als tainted wordt gemarkeerd. Zie [Secure Boot op CachyOS]({{< relref "/docs/cachyos/secure-boot" >}}).

{{< callout type="info" >}}
Bekende problemen en troubleshooting voor de NVIDIA-driver staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}

## Meer lezen

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
