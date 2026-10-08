---
title: "Setup-script"
weight: 1
---

Ik had er genoeg van om na elke herinstallatie dezelfde setup opnieuw te doen, dus nu zit alles in één venster. Je vinkt aan wat je wilt, leest het plan en past het toe. Het venster laat ook zien wat er op jouw machine al klaar is, en elk onderdeel verwijst naar de handleiding die het uitlegt.

Het richt een machine in zoals ik die zelf graag heb. Het is gebouwd en getest op de Zephyrus G16 (GA605WV), maar slechts een paar onderdelen hangen af van welk model je hebt: de ASUS-tools, de helderheidsfix, de Wi-Fi-tuning en de kleurprofielen. De rest, de GNOME-instellingen, extensies, apps en virtuele machines, werkt op elke laptop.

{{< callout type="warning" >}}
Het verandert je systeem. Er gebeurt niets voordat je het plan hebt gelezen en op Apply hebt gedrukt. Zoals alles hier is het op eigen risico.
{{< /callout >}}

## Uitvoeren

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/quicksetup.py
echo "69ddba17a168ae1b4d852e86c7652529e7567cab502198b37877fe44927ec338  quicksetup.py" | sha256sum -c
python3 quicksetup.py
```

Bron: [quicksetup.py](/scripts/quicksetup.py). SHA-256 `69ddba17a168ae1b4d852e86c7652529e7567cab502198b37877fe44927ec338`.

Je hebt Python 3.14 of nieuwer nodig en de GTK 4-bindings. Een standaard CachyOS-GNOME-installatie heeft die al. Zo niet: `sudo pacman -S python-gobject gtk4 libadwaita`.

Er zijn geen opdrachten of opties, het script opent gewoon een venster. Het brengt alleen wijzigingen aan op CachyOS en andere Arch-systemen. Overal elders, bijvoorbeeld op Bazzite, is het venster alleen-lezen: je kunt rondkijken en de handleidingen openen.

## Het venster

Links staan de secties, rechts één rij per onderdeel. Een aangevinkt vakje betekent dat het onderdeel op deze machine klaar is, een streepje dat het gedeeltelijk klaar is. Vink een vakje aan om iets aan te zetten, haal het vinkje weg om het weer uit te zetten.

- De twee kleine knoppen op een rij tonen de exacte opdrachten die aan- en uitvinken draaien, en openen de handleiding.
- `AUR` markeert rijen die een pakket uit de AUR nodig hebben. `Advanced`-rijen blijven buiten **Select recommended**.
- Als je iets aanvinkt, vinkt het venster ook aan wat daarvoor nodig is, en vermeldt dat erbij. Een rij die op deze machine niet van toepassing is, is grijs, met de reden erbij.
- GNOME-extensies komen van extensions.gnome.org, dus je hebt geen browserplug-in nodig. Heeft een extensie nog geen build voor jouw GNOME-versie, dan wordt toch de nieuwste geïnstalleerd en markeert GNOME Shell hem als verouderd totdat de maker bijwerkt. GNOME Shell zoekt alleen naar extensies als hij opstart, dus een net geïnstalleerde verschijnt pas nadat je uit- en weer inlogt, en het venster zegt dat erbij.
- In het menu staan **Select recommended**, **Check again** en het logbestand.

Er verandert niets voordat je op **Review and apply** drukt. Die controle toont de pakketten, wat als root draait, wat een herstart of opnieuw inloggen nodig heeft en wat er voor jou overblijft. Als er iets mis is, blijft Apply grijs en staat de reden bovenaan.

## Precies wat er draait

Niets in het venster is een black box. Elke opdracht staat op het scherm voordat er iets gebeurt, en op deze site:

- De **infoknop** op een rij toont, voor jouw machine, de exacte opdrachten die aanvinken draait en die uitvinken draait, met een diff voor elk bestaand bestand dat ze wijzigen (een bestand dat ze aanmaken staat in het commando zelf). Hij verwijst naar de handleiding en naar de regel van het onderdeel in de [referentie]({{< relref "/docs/setup-script/reference" >}}).
- In de controle toont **Show the exact commands** alles wat de run start, op volgorde, en er wordt niets afgekapt. **Show the root script, word for word** toont het ene script dat naar `pkexec` gaat.
- De [referentie]({{< relref "/docs/setup-script/reference" >}}) heeft voor elk onderdeel een regel: de opdrachten voor beide richtingen, de diffs en links naar de exacte regels van het script erachter. Ze wordt uit het script zelf gegenereerd, dus er kan niets op staan wat het venster niet doet.
- Een stap die Python is in plaats van een opdracht moet als opdrachten zeggen waar hij op neerkomt. Het script weigert een stap te bouwen die dat niet doet.

## De weg terug

Uitvinken is de weg terug. Het venster toont wat het draait voordat het dat doet, en de referentie toont het voor elk onderdeel. Het haalt weg wat aanvinken installeerde, zet instellingen terug naar de GNOME-standaard en zet een bewerkt bestand terug uit de back-up die gemaakt is. Je eigen bestanden en instellingen blijven staan, en een pakket dat iets anders nog nodig heeft ook.

Twee rijen hebben geen vinkje, omdat een fout in hun stappen ervoor kan zorgen dat de machine niet meer opstart: de AMD-fix tegen schermvastlopers en Secure Boot. Hun regels in de referentie noemen de stappen om ze in te richten en om ze met de hand terug te draaien. Het venster verwijdert `sbctl` niet zolang Secure Boot aan staat, omdat dat elke nieuwe kernel ondertekent.

## Kleurstanden

De sectie Display heeft een schakelaar die meteen werkt, zonder toepassen: **Native**, de levendige, en **sRGB**. De rij **What a switch runs** daar toont de twee aanroepen erachter. G-Helper heeft er op Windows nog twee, DCI-P3 en Display P3, maar op Linux zouden die hetzelfde beeld tonen als Native, dus ze zijn er niet. De pagina [Kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}}) legt dat uit, en waarom een ander profiel kiezen in de GNOME-instellingen niets doet.

## Wat het controleert en wat het met rust laat

- **Eén wachtwoordprompt.** Alles wat root nodig heeft draait als één script via `pkexec`. AUR-pakketten worden door `paru` gebouwd in een terminalvenster, zodat je eerst elke PKGBUILD kunt lezen.
- **Downloads worden gecontroleerd waar dat kan.** De eigen scripts, de kleurprofielen en Archi worden vergeleken met een SHA-256 die in het script zit, en een bestand dat niet klopt wordt nooit gebruikt. Een extensie-zip wordt gecontroleerd voordat hij wordt uitgepakt. pacman en Flatpak controleren hun eigen pakketten. De VirtIO-ISO heeft geen vaste hash, omdat Fedora hem bij elke release vervangt, dus die krijgt alleen een groottecontrole.
- **Controles vooraf.** Pakketten uit de repositories moeten bestaan en samen te installeren zijn, wat het test met een proefrun. Het waarschuwt als pacman bezig is, als je offline bent en als je pakketdatabases oud zijn.
- **Uitvinken is voorzichtig.** Pakketten worden één voor één verwijderd, en een pakket dat iets anders nog nodig heeft blijft staan. Instellingen gaan terug naar de GNOME-standaard, maar alleen als ze nog de waarde hebben die het script ze gaf. Pakketten die het systeem of het venster zelf nodig heeft worden nooit verwijderd. Je eigen bestanden blijven staan.
- **Sommige dingen blijven handwerk.** Kernelparameters en Secure Boot-sleutels kunnen ervoor zorgen dat de machine niet meer opstart als het misgaat, dus de AMD PSR-fix en Secure Boot zijn handleidingen zonder vinkje. De helderheidsfix is de uitzondering: die draait zijn eigen script, dat een back-up bewaart en die terugzet als je het vinkje weghaalt. De YubiKey is de andere uitzondering en de enige PAM-wijziging die het venster doet: het voegt één `sufficient`-regel toe, bewaart het oude bestand, controleert het resultaat en zet het oude bestand terug als die controle faalt. De [YubiKey-pagina]({{< relref "/docs/security/yubikey" >}}) heeft de details.
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

Wat een kwestie van smaak is, zit er niet in: de Windows-achtige sneltoetsen, de andere extensies, de apps en de virtualisatiestack staan wel in het venster, maar niet in de aanbevolen set. Dat geldt ook voor de geavanceerde onderdelen: YubiKey, Secure Boot, VMware en de AMD-fix tegen het vastlopen van het scherm.

## Waar de keuzes vandaan komen

Ik volg upstream waar upstream een mening heeft. De handleiding achter elk onderdeel geeft de redenering en de bronnen.

- **ASUS-tools en energieprofielen:** de [asusctl-documentatie van het Open Gaming Collective](https://opengamingcollective.github.io/asusctl/) en de [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md). `power-profiles-daemon` maskeren is wat de [Arch-](https://opengamingcollective.github.io/asusctl/distributions/arch.html) en [Bazzite-gids](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) zeggen. De [asusctl-pagina]({{< relref "/docs/hardware/asusctl-rog-control" >}}) legt uit waarom oudere gidsen het tegenovergestelde zeggen.
- **NVIDIA suspend en `nvidia-powerd`:** NVIDIA's driver-README over [energiebeheer](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) en [Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html). `nvidia-open` bewaart het videogeheugen zelf, dus daar worden de suspend-units overgeslagen. De [NVIDIA-pagina]({{< relref "/docs/cachyos/nvidia" >}}) heeft de details.
- **Kleurstanden:** [G-Helper](https://github.com/seerge/g-helper), dat op Windows de ASUS-paneelprofielen laat zien.
- **Autologin en de YubiKey:** de [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) en de [pam-u2f README](https://github.com/Yubico/pam-u2f).
- **De helderheidsfix:** uitgezocht op deze laptop, zie [Bekende problemen]({{< relref "/docs/known-issues" >}}).

## Een onderdeel toevoegen of aanpassen

Elk onderdeel is één regel in `build_items()` in het script: een id, een sectie, een korte samenvatting, de handleiding waar het naar linkt, een functie die zijn status bepaalt, een functie die zegt wat aanvinken doet en een voor wat uitvinken doet. Een set pakketten is een one-liner. Pas je het script aan, draai dan `.github/scripts/check-doc-checksums.sh --apply` zodat de hashes in het script en op deze pagina worden bijgewerkt. De [referentie]({{< relref "/docs/setup-script/reference" >}}) hoeft niets: ze wordt bij het bouwen van de site uit het script geschreven.
