---
title: "GNOME"
weight: 4
toc: false
---

Deze laptop draait GNOME op Wayland, versies 50 en 51 op het moment van schrijven. Dat is het enige bureaublad dat deze handleidingen behandelen.

Draai je KDE Plasma (een Bazzite `-nvidia-open`-image zonder `-gnome`, of Plasma op CachyOS), dan gelden de hardwarepagina's onverkort. Wat GNOME veronderstelt zijn de [autologin]({{< relref "/docs/security/autologin" >}})-handleiding (GDM, geen SDDM), de schermvergrendel-helft van de [YubiKey]({{< relref "/docs/security/yubikey" >}})-handleiding, de [GNOME Shell-extensies]({{< relref "/docs/desktop/gnome-extensions" >}}), de fix voor de [touchpad-scrollsnelheid]({{< relref "/docs/desktop/touchpad-scroll-speed" >}}), en de vensterknop-aanpassingen op de [applicaties]({{< relref "/docs/applications" >}})-pagina. Plasma heeft voor de meeste daarvan ingebouwde instellingen.

## GNOME 51

GNOME 51 verscheen in september 2026. Dit is wat voor deze handleidingen telt:

- **Extensies.** extensions.gnome.org toont per extensie welke GNOME-versies ze ondersteunt, en GNOME Shell negeert een build die jouw versie niet noemt. Op het moment van schrijven hebben [Just Perfection]({{< relref "/docs/applications" >}}) en [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}) een build voor GNOME 51. [PiP on Top]({{< relref "/docs/desktop/gnome-extensions" >}}) en de [Smile complementary extension]({{< relref "/docs/applications/utilities" >}}) houden op bij GNOME 50, dus op 51 blijven ze verouderd totdat hun auteurs een update publiceren. Het setup-venster maakt ze grijs met "No build for GNOME 51 yet". Smile zelf blijft werken, het kan alleen de emoji niet meer voor je plakken.
- **NVIDIA.** mutter 51 schrapt de ondersteuning voor oude NVIDIA-drivers. De RTX 4060 draait op de huidige open driver, dus hier verandert niets.
- **Helderheid.** GNOME 51 onthoudt de schermhelderheid tussen sessies, en mutter 51 verbetert de herkenning van de backlight. Of dat de [helderheidsfix]({{< relref "/docs/known-issues" >}}) overbodig maakt, is nog niet bekend.
- **Inloggen.** GDM 51 dicht een autologin-gat waarbij een gecompromitteerde greeter autologin voor elk lokaal account kon aanvragen, en de vingerafdrukscanner kan alleen nog opnieuw authenticeren, niet meer zelfstandig inloggen. Zie de handleidingen voor [autologin]({{< relref "/docs/security/autologin" >}}) en [YubiKey]({{< relref "/docs/security/yubikey" >}}) als je daarop leunt.
- **Kleur.** De kleurmodus `sdr-native` achter de sRGB-stand in het [setup-venster]({{< relref "/docs/hardware/color-profiles" >}}) kwam met GNOME 50 en zit ook in 51.
