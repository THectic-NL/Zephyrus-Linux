---
title: "NVIDIA-driver"
weight: 3
prev: docs/bazzite/updates
next: docs/bazzite/secure-boot
distro: bazzite
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. Op Bazzite is de driver niets dat je installeert. Hij is onderdeel van de image waarmee je opstart, dus het werk hier bestaat uit de juiste image kiezen, één Secure Boot-sleutel inschrijven en twee energie-instellingen die deze laptop nodig heeft.

{{< callout type="warning" >}}
Als je hier kwam voor RPM Fusion, `akmod-nvidia`, `akmods --force` en een MOK-inschrijfscherm: dat is hier allemaal niet van toepassing. Dat is de procedure voor gewoon Fedora. Op een atomic image is het op zijn best overbodig en op zijn slechtst breekt het je volgende update.
{{< /callout >}}

## Gebruik een `-nvidia-open`-image

De RTX 4060 is Ada en valt dus onder NVIDIA's open kernelmodules, en dat is wat de `-nvidia-open`-images meeleveren. Kijk waar je nu op zit:

```bash
rpm-ostree status
```

De image-ref staat op de eerste regel. Staat `nvidia-open` er niet in, rebase dan:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-gnome-nvidia-open:stable
systemctl reboot
```

Zie [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) voor de volledige lijst met images en wat een rebase precies doet. Deze handleidingen gaan uit van een `-gnome-`-image.

## Schrijf eerst de Secure Boot-sleutel in

De NVIDIA-kernelmodules zijn ondertekend met de sleutel van Universal Blue. Staat Secure Boot aan en is die sleutel niet ingeschreven, dan weigeren de modules te laden en beland je in een sessie zonder versnelling, wat er precies uitziet als een kapotte driver.

```bash
ujust enroll-secure-boot-key
```

Het wachtwoord is `universalblue`. De volledige procedure, inclusief het blauwe MokManager-scherm: [Secure Boot op Bazzite]({{< relref "/docs/bazzite/secure-boot" >}}).

## Verificatie Na Installatie

{{% steps %}}

### NVIDIA-driver verifiëren

```bash
nvidia-smi
```

Je ziet de NVIDIA driver- en CUDA-versies in de output.

### Controleer geladen kernelmodules

```bash
lsmod | grep nvidia
```

Als de modules zichtbaar zijn, is de driver geladen en functioneel. Staan ze er niet en is Secure Boot aan, schrijf dan eerst de sleutel hierboven in voordat je ergens anders gaat zoeken.

### Controleer dat de open module gebruikt wordt

```bash
cat /proc/driver/nvidia/version
```

De eerste regel zegt `NVIDIA UNIX Open Kernel Module` op een `-nvidia-open`-image. `modinfo nvidia | grep -i license` is een andere manier: de open module meldt een dubbele `MIT/GPL`-licentie, de gesloten meldt `NVIDIA`.

{{% /steps %}}

## Energiebeheer

Deze instelling gaat over deze laptop en niet over de driver, dus die geldt hier precies zoals op CachyOS. `systemctl` schrijft naar `/etc`, en dat is op een atomic systeem van jou, dus dat overleeft image-updates.

{{% steps %}}

### Zet de NVIDIA power services aan

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**Wat deze services doen:**
- `nvidia-hibernate.service` - Slaat de GPU state correct op vóór hibernation
- `nvidia-suspend.service` - Beheert GPU state tijdens system suspend
- `nvidia-resume.service` - Herstelt GPU state na resume

Deze services voorkomen GPU state problemen na suspend/resume cycli. Controleer eerst of de image ze al heeft aangezet:

```bash
systemctl is-enabled nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service
```

{{% /steps %}}

## Kernel- en driverupdates

Er valt niets te herbouwen. De kernel en de NVIDIA-modules worden samen in de image gebouwd en tegen elkaar getest voordat die wordt gepubliceerd, en dat is de belangrijkste reden dat deze pagina zoveel korter is dan zijn CachyOS-tegenhanger. Je kiest de driverversie ook niet zelf; die beweegt mee met de image.

Gaat de GPU toch stuk na een image-update, dan staat de vorige er nog:

```bash
rpm-ostree rollback
systemctl reboot
```

{{< callout type="info" >}}
Bekende problemen en troubleshooting voor de NVIDIA-driver staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}

## Meer lezen

- [Bazzite-documentatie](https://docs.bazzite.gg/)
- [Bazzite op GitHub](https://github.com/ublue-os/bazzite)
- [NVIDIA open kernel modules](https://github.com/NVIDIA/open-gpu-kernel-modules)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [Fedora Discussion: Zephyrus External Monitor Issues](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)
