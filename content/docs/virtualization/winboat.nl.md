---
title: "WinBoat: Windows via Podman Container"
weight: 3
next: docs/virtualization/podman
---

WinBoat is een open-source project dat Windows draait in een Podman-container op Linux. Het idee: Windows-apps gewoon als losse vensters op je Linux-desktop, zonder dat je een volledige VM nodig hebt. Ik heb het getest met Podman.

> **Status: Beta.** WinBoat is vroege beta. Getest op v0.9.0. Bugs zijn te verwachten, het project zegt het zelf ook.

![WinBoat feature-overzicht van de projectwebsite](/images/winboat-features.avif)


## Installatie

{{< callout type="info" >}}
Sinds de [CachyOS-release van maart 2026](https://cachyos.org/blog/2603-march-release/) bevat **CachyOS Hello** een knop om WinBoat direct te installeren en in te schakelen. Nieuwe gebruikers kunnen de handmatige stappen hieronder overslaan en de welkomst-app gebruiken.
{{< /callout >}}

![CachyOS Hello: Install Winboat-knop onder Utilities](/images/cachyos-hello-winboat.avif)

WinBoat staat in de CachyOS-packagerepository:

```bash
sudo pacman -S winboat
```

Packagebron: [packages.cachyos.org/winboat](https://packages.cachyos.org/package/cachyos/x86_64/winboat)

Op de WinBoat-website staat ook een AUR-package (`winboat-bin`) voor andere Arch-gebaseerde distro's. Op CachyOS is het gewoon via de repo.

![WinBoat downloadpagina met Arch/AUR-installatieopties](/images/winboat-download.avif)


## Setup

Bij de eerste start doorloop je een wizard: je kiest de installatiemap, stelt een Windows-gebruikersnaam en wachtwoord in, en geeft aan hoeveel CPU, RAM en schijfruimte de container mag gebruiken. Daarna regelt WinBoat zelf de rest: Windows 11 downloaden en installeren via Podman. Dat duurt een tijdje; de voortgang is te volgen in de browser. De port kan per keer wisselen, dus zo vraag je de huidige URL op:

```bash
# Podman
podman port WinBoat | grep "8006" | awk '{print "http://" $3}'
# Docker
docker port WinBoat | grep "8006" | awk '{print "http://" $3}'
```

De demo hieronder laat een volledige sessie zien: door de wizard, de installatie, WinBoat dat daadwerkelijk met Windows opkomt, en daarna mijn pogingen om Notepad en de Verkenner te openen.

![WinBoat setup en eerste sessie van wizard tot Windows draaiend, gevolgd door de startup loop](/images/winboat-demo.avif)

Na een schone setup werkt het gewoon. **WinBoat Guest API - Online** en **Container - Running** in de interface, het Windows-app-scherm laadde, en via FreeRDP verscheen er een Windows 11-inlogscherm in de browser. Dat deel ging goed.

Het probleem zit hem in het opnieuw opstarten daarna, zonder steeds de hele setup opnieuw te moeten doen.

## Eerste start

Na het installeren start je WinBoat vanuit het app-menu of de terminal. Bij de eerste keer installeert het automatisch Windows 11 via Podman.

![WinBoat app: startscherm met containerstatus](/images/winboat-app.avif)

Wat ik het vaakst zag: **WinBoat Guest API - Offline** en **Container - Exited**. Windows 11 Pro staat in de interface, maar de container start nooit echt op.


## Bugs

Het grootste probleem is de startup loop. De container probeert steeds opnieuw op te starten, maar het lukt nooit, hoe lang je ook wacht. Dit is niet alleen een eenmalig iets, het gebeurt regelmatig.

WinBoat resetten en de setup opnieuw doorlopen werkt wel, maar dat is geen werkbare oplossing als je hem gewoon wilt gebruiken.

![WinBoat vastgelopen in een startup loop, bereikt nooit een werkende staat](/images/winboat-startup-failure.avif)

Andere dingen die ik tegenkwam:

- Container stopt zomaar ("Container - Exited")
- De Guest API verbindt nooit ("WinBoat Guest API - Offline")
- Windows-apps verschijnen niet als losse vensters op de desktop

Als WinBoat wel opstart, probeerde ik eerst iets eenvoudigs: Notepad en de Verkenner openen. Microsoft 365 had ik nog niet geïnstalleerd via `winget`, dus ik begon gewoon klein. In plaats van die apps kreeg ik rare vakjes en glitches op mijn scherm. Daarna heb ik de container gereboot en wat processen gekilld, maar ook dat hielp niet. Dat is ook terug te zien in de demo hierboven.

{{< callout type="warning" >}}
WinBoat is vroege beta. Het project zegt zelf dat je wat troubleshootingervaring moet hebben. De huidige versie is niet representatief voor het eindproduct.
{{< /callout >}}


## Ok, en wat nu?

Eerlijk gezegd is dit een van de gaafste app-concepten die ik in tijden heb gezien. Windows-apps gewoon als desktopvensters, zonder volledige VM. Dat kan Bottles of Wine ook niet, zeker niet voor Microsoft 365. Ik zou dit super graag stabiel werkend willen krijgen.

Maar zo ver zijn we nog niet. Voor dagelijks Windows-gebruik geeft [VMware Workstation]({{< relref "/docs/virtualization/vmware-workstation" >}}) momenteel de beste ervaring op deze hardware. De [KVM/QEMU-setup]({{< relref "/docs/virtualization/vm-setup" >}}) is een goed open-source alternatief. Ik zou WinBoat graag nog een keer willen proberen als het stabieler is; de Docker-backend doet het misschien beter dan de Podman-versie die ik getest heb.


## Referenties

- [WinBoat: officiële website](https://winboat.app)
- [WinBoat: GitHub (TibixDev/winboat)](https://github.com/TibixDev/winboat)
- [WinBoat: CachyOS package](https://packages.cachyos.org/package/cachyos/x86_64/winboat)
- [WinBoat: AUR package (winboat-bin)](https://aur.archlinux.org/packages/winboat-bin)
