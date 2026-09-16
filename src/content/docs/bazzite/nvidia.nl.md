---
title: "NVIDIA-driver"
weight: 3
prev: docs/bazzite/updates
next: docs/bazzite/secure-boot
distro: bazzite
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. Op Bazzite is de driver niets dat je installeert. Hij is onderdeel van de image waarmee je opstart, dus het werk hier bestaat uit de juiste image kiezen, één Secure Boot-sleutel inschrijven en controleren dat suspend al geregeld is.

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

De CachyOS-pagina heeft hier een handmatige stap: Arch's `nvidia-utils`-pakket levert suspend- en resume-afhandeling als losse systemd-units, en die pagina zet ze met de hand aan. De driver op Bazzite wordt door negativo17 verpakt en is anders ingericht. Met de open kernelmodules laat `NVreg_UseKernelSuspendNotifiers=1` de driver zelf het videogeheugen bewaren en herstellen, dus die units worden helemaal niet meegeleverd. Hij staat al aan. Er is hier niets om aan te zetten.

{{< callout type="warning" >}}
Zet je hier `nvidia-suspend.service` aan, een stap die je in andere handleidingen tegenkomt, waaronder de CachyOS-pagina in deze repo, dan mislukt dat met `Unit nvidia-suspend.service could not be found`. De unit staat helemaal niet op deze image. Hij is niet alleen uitgeschakeld.
{{< /callout >}}

{{% steps %}}

### Controleer of de suspend-override actief is

```bash
systemctl show systemd-suspend.service -p Environment
```

Je zou `Environment=SYSTEMD_SLEEP_FREEZE_USER_SESSIONS=false` moeten zien. Dat komt uit `nvidia-suspend-nofreeze.conf`, een drop-in die het `nvidia-driver`-pakket op `systemd-suspend.service` zet (en op de hibernate- en suspend-then-hibernate-units), om een VT-switch deadlock tijdens suspend te voorkomen.

### Controleer de suspend-instellingen van de driver

```bash
grep -E "UseKernelSuspendNotifiers|PreserveVideoMemoryAllocations|EnableS0ixPowerManagement" /proc/driver/nvidia/params
```

Verwacht:

```
PreserveVideoMemoryAllocations: 1
UseKernelSuspendNotifiers: 1
EnableS0ixPowerManagement: 1
```

Dit leest wat de geladen driver echt gebruikt, en dat is betrouwbaarder dan een config-bestand: nieuwere images zetten `NVreg_UseKernelSuspendNotifiers` niet meer in `/usr/lib/modprobe.d/nvidia.conf`, terwijl hij toch aan staat. Het bestand bestaat alleen zolang de NVIDIA-module geladen is, dus controleer in Hybrid of Ultimate mode. In Integrated mode staat de dGPU van de bus.

`NVreg_UseKernelSuspendNotifiers=1` is wat de losse suspend- en resume-units vervangt. Met de open kernelmodules bewaart de driver het videogeheugen via de eigen suspend- en resume-notifiers van de kernel, in plaats van via een systemd-unit die `nvidia-sleep.sh` aanroept.

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
