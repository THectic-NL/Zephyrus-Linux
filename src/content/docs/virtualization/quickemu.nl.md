---
title: "Quickemu"
weight: 2
prev: docs/virtualization/vm-setup
next: docs/virtualization/winboat
---

[Quickemu](https://github.com/quickemu-project/quickemu) is de kortste route van "ik heb een VM nodig om dit in te proberen" naar een draaiend bureaublad. Het verpakt QEMU met verstandige standaardinstellingen, en het bijbehorende `quickget` haalt de ISO voor je op.

Twee commando's en je hebt een Windows 11-VM:

```bash
quickget windows 11
quickemu --vm windows-11.conf
```

Geen virt-manager, geen XML, geen wizard doorlopen. De ruil is controle: het kiest de hardware-indeling voor je.

## Waar het past

Er zijn vier manieren om iets anders dan Linux op deze laptop te draaien, en ze zijn voor verschillende dingen:

| | Het beste voor | Niet voor |
|---|---|---|
| **Quickemu** | Wegwerp-VM's, een distributie proberen, een Windows-installatie die je volgende week weggooit | Een VM die je jarenlang tunet en houdt |
| [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}) | De VM die je houdt — passthrough, snapshots, exacte apparaatcontrole | Even ergens naar kijken |
| [WinBoat]({{< relref "/docs/virtualization/winboat" >}}) | Losse Windows-applicaties in je Linux-sessie | Een compleet Windows-bureaublad |
| [VMware Workstation]({{< relref "/docs/virtualization/vmware-workstation" >}}) | Beste prestaties, makkelijkste interface (alleen CachyOS) | Bazzite — daar is geen ondersteunde route |

Eronder zit dezelfde hypervisor als bij virt-manager, dus een Quickemu-VM is niet trager. Het is een andere voorkant, geen andere techniek.

## Installeren

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S quickemu
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Quickemu stuurt QEMU op de host aan en wil bij `/dev/kvm`, dus dit is er een om te layeren en niet om in een container te zetten:

```bash
rpm-ostree install quickemu
systemctl reboot
```

Heb je virtualisatie nog niet opgezet, doe dat dan eerst — dat haalt QEMU en libvirt binnen en zet je in de juiste groep:

```bash
ujust setup-virtualization
systemctl reboot
```

Beide vanuit één herstart doen mag; layer ze desnoods in dezelfde `rpm-ostree install`.

{{< callout type="info" >}}
Een distrobox-container kan Quickemu ook draaien — `/dev/kvm` is daarbinnen beschikbaar — maar het VM-venster hoort dan bij de container, en bestandspaden worden dan snel verwarrend. Layeren is hier het minst vervelende antwoord.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Gebruiken

{{% steps %}}

### Kijken wat er is

```bash
quickget --list
```

Dat is een lange lijst: de meeste Linux-distributies, Windows, macOS en de BSD's.

### Downloaden en een config genereren

```bash
quickget ubuntu 24.04
```

Dit downloadt de ISO in een map naast je huidige map en schrijft een klein `.conf`-bestand dat de VM beschrijft. Op deze hardware is de ISO meestal het trage deel.

### Opstarten

```bash
quickemu --vm ubuntu-24.04.conf
```

Er opent een venster en de VM start op. Dat is de hele workflow.

### Weggooien als je klaar bent

De VM is een map plus een configbestand. Verwijder allebei en hij is weg — geen libvirt-definitie die achterblijft, nergens iets geregistreerd:

```bash
rm -rf ubuntu-24.04 ubuntu-24.04.conf
```

Dit is de eigenlijke reden om Quickemu te gebruiken. Een wegwerp-VM hoort ook echt wegwerp te zijn.

{{% /steps %}}

## Windows 11

`quickget windows 11` regelt de ISO, de VirtIO-driverschijf en de TPM-eis, en dat is het grootste deel van wat een handmatige Windows 11-opzet vervelend maakt.

```bash
quickget windows 11
quickemu --vm windows-11.conf
```

Alles op de pagina [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}) over Windows-licenties en ISO-keuzes geldt hier ook — de evaluatie-ISO, de Media Creation Tool en AtlasOS zijn allemaal gewoon ISO's, en Quickemu start ze allemaal op.

{{< callout type="warning" >}}
`swtpm` moet aanwezig zijn voor het TPM 2.0-apparaat waar Windows 11 op controleert. Die zit in de CachyOS-packagelijst op de virt-manager-pagina, en in `ujust setup-virtualization` op Bazzite. Klaagt Windows Setup dat de pc niet aan de eisen voldoet, kijk daar dan naar.
{{< /callout >}}

## Configuratie die je wilt kennen

De gegenereerde `.conf` is een handvol shellvariabelen. Degene die op deze laptop uitmaken:

```bash
cpu_cores="8"
ram="8G"
disk_size="64G"
gpu_accel="on"
```

- **`cpu_cores` en `ram`.** Quickemu schat dit op basis van de host. De HX 370 heeft cores genoeg, maar de schatting laten staan is meestal prima.
- **`gpu_accel`.** Gebruikt de AMD iGPU voor het beeld van de VM. Dat is wat je wilt — dezelfde redenering als het SPICE GL-stuk op de virt-manager-pagina. De RTX 4060 hoort geen VM-venster te tekenen.
- **`disk_size`.** Groeit mee in plaats van vooraf te worden gereserveerd, dus royaal zijn kost niets tot het gebruikt wordt.

## Specifiek voor de G16

- **Hybride graphics.** Laat de VM op de iGPU renderen. Hem met `prime-run` naar de discrete kaart duwen levert voor een bureaublad-VM niets op en kost accu.
- **Schermschaling.** VM-vensters komen op in de resolutie uit de config, en op een 2560x1600-paneel is dat klein. Zet de resolutie binnen de gast in plaats van te vechten met het venster op de host.
- **Accu.** Een draaiende VM houdt cores bezig en maakt het Silent-[`asusctl`-profiel]({{< relref "/docs/hardware/asusctl-rog-control" >}}) zinloos. Prima op netstroom, merkbaar op accu.

## Referenties

- [Quickemu op GitHub](https://github.com/quickemu-project/quickemu)
- [Quickgui](https://github.com/quickemu-project/quickgui) — een grafische voorkant voor Quickemu
- [QEMU-documentatie](https://www.qemu.org/docs/master/)
