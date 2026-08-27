---
title: "Astra Monitor"
weight: 2
prev: docs/desktop/kde
next: docs/security/autologin
---

[Astra Monitor](https://github.com/AstraExt/astra-monitor) is een GNOME Shell-extensie die CPU, geheugen, schijf, netwerk en GPU in de bovenbalk zet, met een uitklapmenu voor de details. Op een laptop met twee GPU's en een fan curve waar je echt om geeft, is het permanent zien van die cijfers nuttiger dan het klinkt.

De reden dat dit een eigen pagina verdient en geen regel op de applicatiepagina, is dat het op deze machine **beide** GPU's naast elkaar uitleest — de Radeon 890M en de RTX 4060 — en dat is precies wat je wilt als je probeert vast te stellen of iets daadwerkelijk op de discrete kaart draait.

## Vereisten

GNOME Shell 45 of nieuwer, dus beide distributies zoals hier beschreven zijn prima.

De extensie werkt zonder enige dependency. Alles hieronder is optioneel en elk onderdeel ontsluit één specifieke uitlezing — bepaal vooraf wat je wilt, zeker op Bazzite waar elk onderdeel je een herstart kost.

| Dependency | Levert je | De moeite waard op de G16? |
|---|---|---|
| **Libgtop** | Nauwkeuriger CPU-, geheugen- en procesdata | Ja — dit is degene om te installeren |
| **amdgpu_top** | Uitlezen van de Radeon 890M | Ja, als je iGPU-cijfers wilt |
| **nvidia-smi** | Uitlezen van de RTX 4060 | Zit al bij de NVIDIA-driver |
| **Nethogs** | Netwerkgebruik per proces | Alleen als je netwerk per proces wilt |

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
GNOME-extensies staan in `~/.local/share/gnome-shell/extensions/`, dus in je home-map en niet in de image. De extensie zelf overleeft image-updates en rebases dus zonder layering — alleen de optionele dependencies hieronder raken het systeem aan.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Optionele dependencies

### Libgtop

Degene om te installeren. Zonder valt de extensie terug op het rechtstreeks lezen van `/proc`, wat werkt maar hem minder te bieden heeft.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S libgtop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Kijk eerst — GNOME gebruikt libgtop zelf, dus vaak zit hij al in de image:

```bash
rpm -q libgtop2
```

Zit hij er niet in, dan is dit een systeembibliotheek die de extensie via GObject introspection laadt, dus moet hij gelaagd worden:

```bash
rpm-ostree install libgtop2-devel
systemctl reboot
```

Het `-devel`-package is wat upstream documenteert: daar zit de introspection-typelib in die de extensie nodig heeft, niet alleen headers.

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

Niets te doen. `nvidia-smi` komt op allebei mee met de driver — het is wat je op de [NVIDIA]({{< relref "/docs/hardware/nvidia-cachyos" >}})-pagina's draait om te controleren of de driver geladen is. Laat Astra Monitor geen NVIDIA-sectie zien, dan is de driver niet geladen, en dat is een driverprobleem en geen extensieprobleem.

### Nethogs

Netwerkcijfers per proces. Het heeft verhoogde rechten nodig om verkeer te inspecteren, en dat is goed om te weten voordat je het installeert.

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

- **Zet uit wat je niet bekijkt.** Standaard staan de meeste sensoren aan. Op een laptopscherm is er geen ruimte voor allemaal, en elke sensor is een poll-interval.
- **Stel het update-interval per sensor in.** De standaard is vaak genoeg om in `powertop` op te duiken. De schijf- en netwerksensor naar een paar seconden zetten kost je niets wat je merkt.
- **Kies welke GPU de primaire is** onder het GPU-onderdeel. Met twee kaarten moet de balk kiezen; de RTX 4060 is de interessantste als je wilt weten of een game of CUDA-taak daar ook echt terechtkwam.
- **Compacte modus** als je meer extensies in de balk hebt staan — de standaardindeling is breed.

{{< callout type="warning" >}}
Een monitor in de bovenbalk pollt per definitie continu, dus gratis is het op accu niet. Ben je op zoek naar idle-verbruik, dan is dit een van de eerste dingen om met `powertop` te controleren, naast het [`asusctl`-energieprofiel]({{< relref "/docs/hardware/asusctl-rog-control" >}}).
{{< /callout >}}

## Op KDE Plasma

Niet van toepassing — het is een GNOME Shell-extensie. Plasma heeft ingebouwde systeemmonitor-widgets; voeg er een toe aan de balk via de widgetlijst. Zie [KDE Plasma]({{< relref "/docs/desktop/kde" >}}).

## Referenties

- [Astra Monitor op GitHub](https://github.com/AstraExt/astra-monitor)
- [Astra Monitor op extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/)
- [amdgpu_top](https://github.com/Umio-Yasuno/amdgpu_top)
