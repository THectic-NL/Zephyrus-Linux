---
title: "Astra Monitor"
weight: 1
prev: docs/hardware/color-profiles
next: docs/security/autologin
---

[Astra Monitor](https://github.com/AstraExt/astra-monitor) is een GNOME Shell-extensie die CPU, geheugen, schijf, netwerk en GPU in de bovenbalk zet, met een uitklapmenu voor de details.

Het krijgt een eigen pagina omdat het op deze machine beide GPU's naast elkaar uitleest, de Radeon 890M en de RTX 4060. Dat is wat je wilt als je nagaat of iets echt op de discrete kaart draait.

## Vereisten

GNOME Shell 45 of nieuwer, dus beide distributies hier zijn prima.

De extensie heeft geen harde dependencies. Alles hieronder is optioneel en voegt één uitlezing toe. Bepaal vooraf wat je wilt, zeker op Bazzite waar elk onderdeel je een herstart kost.

| Dependency | Levert je | Op de G16 |
|---|---|---|
| **Libgtop** | Nauwkeuriger CPU-, geheugen- en procesdata | Installeren |
| **amdgpu_top** | Uitlezen van de Radeon 890M | Installeren als je iGPU-cijfers wilt |
| **nvidia-smi** | Uitlezen van de RTX 4060 | Zit al bij de NVIDIA-driver |
| **Nethogs** | Netwerkgebruik per proces | Alleen als je netwerk per proces nodig hebt |

## De extensie installeren

{{< tabs >}}
{{< tab name="CachyOS" >}}

Via Extension Manager, uit de repos of van Flathub:

```bash
sudo pacman -S extension-manager
```

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

Open hem, zoek op "Astra Monitor" en installeer. Of installeer via [extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/) in een browser.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Extension Manager is een Flatpak, dus voor de extensie zelf wordt er niets gelaagd:

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

Open hem, zoek op "Astra Monitor" en installeer. Of installeer via [extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/) in een browser.

{{< callout type="info" >}}
GNOME-extensies staan in `~/.local/share/gnome-shell/extensions/`, dus in je home-map en niet in de image. De extensie zelf overleeft image-updates en rebases zonder layering. Alleen de optionele dependencies hieronder raken het systeem aan.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Optionele dependencies

### Libgtop

Zonder valt de extensie terug op het rechtstreeks lezen van `/proc`, wat werkt maar hem minder te bieden heeft.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S libgtop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

GNOME gebruikt libgtop zelf, dus kijk eerst:

```bash
rpm -q libgtop2
```

Zit hij er niet in, dan moet hij gelaagd worden. De extensie laadt hem via GObject introspection, dus je hebt het package nodig met de typelib:

```bash
rpm-ostree install libgtop2-devel
systemctl reboot
```

Het `-devel`-package is wat upstream documenteert. Daar zit de introspection-typelib in die de extensie nodig heeft, niet alleen headers.

{{< /tab >}}
{{< /tabs >}}

### amdgpu_top (Radeon 890M)

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S amdgpu_top
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
rpm-ostree install amdgpu_top
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

### nvidia-smi (RTX 4060)

Niets te doen. `nvidia-smi` komt op allebei mee met de driver. Laat Astra Monitor geen NVIDIA-sectie zien, dan is de driver niet geladen, en dat is een driverprobleem en geen extensieprobleem. Zie de [NVIDIA]({{< relref "/docs/cachyos/nvidia" >}})-pagina.

### Nethogs

Netwerkcijfers per proces. Het heeft verhoogde rechten nodig om verkeer te inspecteren.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S nethogs
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
rpm-ostree install nethogs
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

## Instellingen die je wilt aanpassen

Open de instellingen van de extensie via Extension Manager, of via het tandwiel in het uitklapmenu.

- **Zet sensoren uit die je niet bekijkt.** Standaard staan de meeste aan. Elke sensor is een poll-interval, en op een laptopscherm is er toch geen ruimte voor allemaal.
- **Zet de schijf- en netwerksensor trager.** Een paar seconden is voor die twee prima en duikt minder op in `powertop`.
- **Kies de primaire GPU** onder het GPU-onderdeel. Met twee kaarten moet de balk er één kiezen. De RTX 4060 is meestal degene die je wilt zien.
- **Compacte modus** als je meer extensies in de balk hebt. De standaardindeling is breed.

{{< callout type="warning" >}}
Een monitor in de bovenbalk pollt continu, dus gratis is het op accu niet. Ben je op zoek naar idle-verbruik, controleer dit dan met `powertop` naast het [`asusctl`-energieprofiel]({{< relref "/docs/hardware/asusctl-rog-control" >}}).
{{< /callout >}}

## Referenties

- [Astra Monitor op GitHub](https://github.com/AstraExt/astra-monitor)
- [Astra Monitor op extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/)
- [amdgpu_top](https://github.com/Umio-Yasuno/amdgpu_top)
