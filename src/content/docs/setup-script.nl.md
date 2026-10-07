---
title: "Setup-script"
weight: 1
---

Ik had er genoeg van om na elke herinstallatie dezelfde setup opnieuw te doen, dus nu zit alles in één venster. Je vinkt aan wat je wilt, leest het plan en past het toe. Het venster laat ook zien wat er op jouw machine al klaar is, en elk onderdeel verwijst naar de handleiding die het uitlegt.

Het richt een machine in zoals ik die zelf graag heb. Het is gebouwd en getest op de Zephyrus G16 (GA605WV), maar slechts een paar onderdelen maken uit welk model je hebt: de ASUS-tools, de helderheidsfix, de Wi-Fi-tuning en de kleurprofielen. De rest, de GNOME-instellingen, extensies, apps en virtuele machines, werkt op elke laptop.

{{< callout type="warning" >}}
Het verandert je systeem. Er gebeurt niets voordat je het plan hebt gelezen en op Apply hebt gedrukt. Zoals alles hier is het op eigen risico.
{{< /callout >}}

## Uitvoeren

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/zephyrus-setup.py
echo "fe7e8bf50f9da7260bd5e6ec17e63b3fbbaddc6b04b9fa74ae41a75a6ee21b77  zephyrus-setup.py" | sha256sum -c
python3 zephyrus-setup.py
```

Bron: [zephyrus-setup.py](/scripts/zephyrus-setup.py). SHA-256 `fe7e8bf50f9da7260bd5e6ec17e63b3fbbaddc6b04b9fa74ae41a75a6ee21b77`.

Je hebt Python 3.14 of nieuwer nodig en de GTK 4-bindings. Een standaard CachyOS-GNOME-installatie heeft die al. Zo niet: `sudo pacman -S python-gobject gtk4 libadwaita`.

Er zijn geen opdrachten of opties, het opent gewoon een venster. Wijzigingen werken op CachyOS en andere Arch-systemen. Overal elders, bijvoorbeeld op Bazzite, is het venster alleen-lezen: je kunt rondkijken en de handleidingen openen.

## Het venster

Links staan de secties, rechts één rij per onderdeel. Een aangevinkt vakje betekent dat het onderdeel op deze machine klaar is, een streepje dat het gedeeltelijk klaar is. Vink een vakje aan om iets aan te zetten, haal het vinkje weg om het weer uit te zetten.

- De twee kleine knoppen op een rij openen de handleiding en laten zien wat aan- en uitvinken zou doen.
- `AUR` markeert rijen die een pakket uit de AUR nodig hebben. `Advanced`-rijen blijven buiten **Select recommended**.
- Als je iets aanvinkt, vinkt het venster ook aan wat dat nodig heeft, en het zegt dat erbij. Een rij die hier niet van toepassing is, is grijs met de reden erbij.
- GNOME-extensies komen van extensions.gnome.org, dus je hebt geen browserplug-in nodig. Een extensie zonder build voor jouw GNOME-versie zegt dat, bijvoorbeeld "No build for GNOME 51 yet".
- In het menu staan **Select recommended**, **Check again** en het logbestand.

Er verandert niets voordat je op **Review and apply** drukt. Die controle toont de pakketten, wat als root draait, wat een herstart of opnieuw inloggen nodig heeft en wat er voor jou overblijft. **Show the exact commands** toont elke opdracht volledig. Als er iets mis is, blijft Apply grijs en staat de reden bovenaan.

## Kleurstanden

De sectie Display heeft een schakelaar die meteen werkt, zonder toepassen: **Native**, de levendige, en **sRGB**. G-Helper heeft er op Windows nog twee, DCI-P3 en Display P3, maar op Linux zouden die hetzelfde beeld tonen als Native, dus ze zijn er niet. De pagina [Kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}}) legt dat uit, en waarom een ander profiel kiezen in GNOME's Instellingen niets doet.

## Wat het controleert en wat het met rust laat

- **Eén wachtwoordprompt.** Alles wat root nodig heeft draait als één script via `pkexec`. AUR-pakketten worden door `paru` gebouwd in een terminalvenster, zodat je eerst elke PKGBUILD kunt lezen.
- **Downloads worden gecontroleerd waar dat kan.** De eigen scripts, de kleurprofielen en Archi worden vergeleken met een SHA-256 die in het script zit, en een bestand dat niet klopt wordt nooit gebruikt. Een extensie-zip wordt gecontroleerd voordat hij wordt uitgepakt. pacman en Flatpak controleren hun eigen pakketten. De VirtIO-ISO heeft geen vaste hash, omdat Fedora hem bij elke release vervangt, dus die krijgt alleen een groottecontrole.
- **Controles vooraf.** Pakketten uit de repositories moeten bestaan en samen te installeren zijn, wat het test met een proefrun. Het waarschuwt als pacman bezig is, als je offline bent en als je pakketdatabases oud zijn.
- **Uitvinken is voorzichtig.** Pakketten worden één voor één verwijderd, en een pakket dat iets anders nog nodig heeft blijft staan. Instellingen gaan terug naar de GNOME-standaard, maar alleen als ze nog de waarde hebben die het script ze gaf. Pakketten die het systeem of het venster zelf nodig heeft worden nooit verwijderd. Je eigen bestanden blijven staan.
- **Sommige dingen blijven handwerk.** Kernelparameters, PAM-bestanden en Secure Boot-sleutels kunnen je buitensluiten als het misgaat, dus de AMD PSR-fix, de YubiKey-PAM-setup en Secure Boot zijn handleidingen zonder vinkje. De helderheidsfix is de uitzondering: die draait zijn eigen script, dat een back-up bewaart en die terugzet als je het vinkje weghaalt.
- **Een logboek.** Alles wat het draait staat in `~/.local/state/zephyrus-setup/setup.log`. Het venster kan niet worden gesloten terwijl er wijzigingen lopen.

## Aanbevolen

**Select recommended** vinkt deze aan, voor zover ze nog niet klaar zijn en op jouw machine van toepassing zijn:

| Onderdeel | Wat het doet |
|---|---|
| asusctl and ROG Control Center | Fancurves, profielen en de Slash LED |
| Battery charge limit of 80% | Stopt met laden op 80% |
| Let asusd own the power profiles | Maskeert `power-profiles-daemon` |
| Brightness in every GPU mode | De helderheidsfix, een herstart is nodig |
| NVIDIA suspend and resume services | Alleen voor een driver die het videogeheugen niet zelf bewaart, dus niet `nvidia-open` |
| prime-run | Draait een programma op de RTX 4060 |
| ASUS color profiles | Het fabrieksprofiel van jouw paneel en het ASUS sRGB-profiel |
| Wi-Fi throughput tuning | Voor de MT7925-kaart |
| Minimize and maximize buttons | GNOME toont standaard alleen de sluitknop |
| New windows come to the front | Samen met Just Perfection |
| Touchpad scroll speed | `wayland-scroll-factor`, uit de AUR |
| Extension Manager en Just Perfection | Extensies zonder browserplug-in |
| Git, de GitHub CLI en GPG-ondertekende commits | |

Smaak blijft erbuiten: de Windows-achtige sneltoetsen, de andere extensies, de apps en de virtualisatiestack staan wel in het venster, maar niet in de set. Net als de geavanceerde onderdelen: YubiKey, Secure Boot, VMware en de AMD-fix tegen het vastlopen van het scherm.

## Waar de keuzes vandaan komen

Ik volg upstream waar upstream een mening heeft. De handleiding achter elk onderdeel geeft de redenering en de bronnen.

- **ASUS-tools en energieprofielen:** de [asusctl-documentatie van het Open Gaming Collective](https://opengamingcollective.github.io/asusctl/) en de [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md). `power-profiles-daemon` maskeren is wat de [Arch-](https://opengamingcollective.github.io/asusctl/distributions/arch.html) en [Bazzite-gids](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) zeggen. De [asusctl-pagina]({{< relref "/docs/hardware/asusctl-rog-control" >}}) legt uit waarom oudere gidsen het tegenovergestelde zeggen.
- **NVIDIA suspend en `nvidia-powerd`:** NVIDIA's driver-README over [energiebeheer](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) en [Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html). `nvidia-open` bewaart het videogeheugen zelf, dus daar worden de suspend-units overgeslagen. De [NVIDIA-pagina]({{< relref "/docs/cachyos/nvidia" >}}) heeft de details.
- **Kleurstanden:** [G-Helper](https://github.com/seerge/g-helper), dat op Windows de ASUS-paneelprofielen laat zien.
- **Autologin en de YubiKey:** de [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) en de [pam-u2f README](https://github.com/Yubico/pam-u2f).
- **De helderheidsfix:** uitgezocht op deze laptop, zie [Bekende problemen]({{< relref "/docs/known-issues" >}}).

## Een onderdeel toevoegen of aanpassen

Elk onderdeel is één regel in `build_items()` in het script: een id, een sectie, een korte samenvatting, de handleiding waar het naar linkt, een functie die zijn status bepaalt en een functie die zegt wat aanvinken doet. Een set pakketten is een one-liner. Pas je het script aan, draai dan `.github/scripts/check-doc-checksums.sh --apply` zodat de hashes in het script en die op deze pagina meegaan.
