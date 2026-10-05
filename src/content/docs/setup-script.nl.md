---
title: "Setup-script"
weight: 1
---

Ik had er genoeg van om na elke herinstallatie dezelfde setup met de hand opnieuw te doen. Daarom staan de instellingen uit de handleidingen, de software die ik echt gebruik en mijn eigen aanbevolen standaarden in één script met een menu. Het laat zien wat er op jouw machine al klaar is, wat er nog openstaat en wat het toepassen van een onderdeel precies zou doen, en het verwijst naar de pagina uit de handleiding die het uitlegt.

Het richt een machine in zoals *ik* vind dat een goede Linux-machine eruit hoort te zien. Het is gebouwd en getest op de Zephyrus G16 GA605WV, maar alleen de onderdelen die met deze hardware praten maken uit welk model je hebt: de ASUS-tools, de helderheidsfix, de Wi-Fi-tuning en het fabrieks-kleurprofiel. Al het andere, de GNOME-instellingen, de sneltoetsen, de applicaties, containers en virtualisatie, is op elke laptop hetzelfde. Op andere machines staan de hardware-onderdelen als niet van toepassing en worden ze overgeslagen.

{{< callout type="warning" >}}
Het script verandert je systeem. Het toont altijd eerst het plan en doet niets totdat je dat bevestigt, maar lees dat plan wel. Zoals alles hier is het op eigen risico.
{{< /callout >}}

## Uitvoeren

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/zephyrus-setup.py
echo "d7804d07c353f8d904436262754e095ed7891edbe9887b06c1e56ee6691a44aa  zephyrus-setup.py" | sha256sum -c
python3 zephyrus-setup.py
```

Bron: [zephyrus-setup.py](/scripts/zephyrus-setup.py). SHA-256 `d7804d07c353f8d904436262754e095ed7891edbe9887b06c1e56ee6691a44aa`.

Het heeft Python 3.14 of nieuwer nodig en verder niets van Python (alleen de standaardbibliotheek). Toepassen is gebouwd voor CachyOS en andere Arch-systemen, met GNOME. Op Bazzite werken `list`, `show` en `learn`, en zegt `apply` waarom het niet draait. Het menu gebruikt dialogen als `zenity` is geïnstalleerd en anders de terminal; met `--terminal` forceer je de terminal.

## Het menu

Elk onderdeel heeft een status, bepaald op basis van de machine zelf:

| Symbool | Betekenis |
|---|---|
| `[x]` | Klaar |
| `[~]` | Gedeeltelijk klaar |
| `[ ]` | Nog te doen |
| `[-]` | Niet van toepassing, bijvoorbeeld een ASUS-tool op een andere laptop |
| `[?]` | Onbekend, of iets wat alleen jij kunt afmaken |

Kies een sectie, vink aan wat je wilt en pas het toe. Bij elk onderdeel zitten nog vier dingen: **Details** (wat het precies zou doen en wat terugdraaien zou doen), **Learn more** (opent de pagina in deze handleiding die het behandelt), **Undo** (zet de aangevinkte onderdelen terug, zie [Terugdraaien](#terugdraaien)) en, voor onderdelen met een eigen script, **Open tool**. In het terminalmenu draai je onderdelen op nummer terug met `u2` of `u 2 4-6`.

## Vanaf de opdrachtregel

| Opdracht | Wat het doet |
|---|---|
| `list` | Elk onderdeel en hoe het ervoor staat. `--todo` voor alleen wat er nog open staat, `--section` voor één sectie, `--urls` om de link naar de handleiding erbij te zetten |
| `show asus-tools` | Eén onderdeel in detail: status, plan, handmatige stappen, hoe je het terugdraait en de link. Het begin van een unieke id is genoeg |
| `learn wsf` | Print de link naar de handleiding en opent hem in de browser |
| `apply asus-tools nvidia-prime` | Plan, bevestig en pas die onderdelen toe |
| `apply --recommended` | Alles wat aanbevolen is en nog niet klaar is |
| `apply --section dev` | Elk open, niet-geavanceerd onderdeel van een sectie |
| `apply --dry-run ...` | Toon het plan en stop. Werkt bij elke vorm van `apply` |
| `undo wsf gnome-focus` | Plan, bevestig en zet die onderdelen terug naar de fabrieksstand. `--dry-run` toont het plan en stopt |
| `tool backlight-fix` | Open het eigen script van een onderdeel, bijvoorbeeld de helderheidsfix |
| `color set srgb` | Zet het ingebouwde scherm op een ASUS-kleurstand: `native`, `srgb`, `dcip3` of `displayp3`. `color` alleen toont ze |

`--yes` slaat de bevestiging over en `--silent` zet alle dialogen en vragen uit, zodat je het vanuit een script kunt draaien. `--silent` heeft bij `apply` en `undo` ook `--yes` nodig.

## Wat er gebeurt als je iets toepast

- **Eerst het plan.** Dat noemt de pakketten (pacman, AUR, Flathub), de stappen met root, de stappen als jezelf, wat een herstart of opnieuw inloggen nodig heeft en wat er voor jou met de hand overblijft.
- **Eén wachtwoordprompt.** Elke stap die root nodig heeft gaat in één script onder één `pkexec`-aanroep. AUR-pakketten worden gebouwd door `paru`, die elke PKGBUILD laat nakijken, dus daarvoor heb je een terminal nodig.
- **De eigen scripts worden gecontroleerd.** De helderheidsfix, de Wi-Fi-tuning en de eduroam-setup zijn scripts op zich, elk met een SHA-256 die op de eigen pagina staat. Het setup-script gebruikt de kopie ernaast, of downloadt het script uit deze repository, en vergelijkt het met die gepubliceerde hash. Een script dat niet klopt wordt nooit uitgevoerd. Met `--ref` kies je een andere branch of tag om van op te halen, bijvoorbeeld om een wijziging te proberen voordat die gemerged is.
- **Zo min mogelijk AUR.** Slechts vier onderdelen hebben een pakket uit de AUR nodig, en die staan in het menu gemarkeerd met `AUR`: Visual Studio Code (de Microsoft-build), Desktop Plus, wayland-scroll-factor en VMware. Apps die op Flathub staan, zoals Standard Notes en High Tide, komen daarvandaan. De AUR wordt alleen gebruikt voor een pakket dat in geen enkele repository staat: komt er later een in een repository terecht, dan installeert het script het met pacman.
- **Riskante dingen blijven handmatig.** Het script past de bootloader of kernelparameters, PAM-bestanden en Secure Boot-sleutels niet aan en registreert geen YubiKey. Een fout in een van die dingen kan je buitensluiten. Die onderdelen tonen in plaats daarvan de stappen voor jouw bootloader, met een link naar de handleiding.
- **Bijna alles is terug te draaien.** Zie hieronder.

## Terugdraaien

Terugdraaien zet een onderdeel terug naar de fabrieksstand, met dezelfde regels als toepassen: eerst het plan, het vraagt voordat het iets doet en elke stap die root nodig heeft gaat in één script onder één `pkexec`-aanroep. Alleen onderdelen die klaar of gedeeltelijk klaar zijn kun je terugdraaien.

- **Het herstelt de fabrieksstand, niet je vorige waarde.** Een instelling die je zelf had aangepast gaat terug naar de standaard van GNOME of het systeem, niet naar wat het ervoor was. Een instelling die niet meer de waarde heeft die dit script gaf, blijft met rust, want die heb je sindsdien zelf veranderd.
- **Pakketten worden één voor één verwijderd** met `pacman -Rs` of `flatpak uninstall`. Een pakket dat iets anders nog nodig heeft blijft staan en wordt gemeld, in plaats van dat het verwijderen van de rest mislukt. Je eigen data en config in je thuismap blijven staan.
- **Sommige dingen vragen daarna om opnieuw inloggen of een herstart**, bijvoorbeeld wayland-scroll-factor. Het resultaat zegt dat erbij.
- **Vijf onderdelen hebben geen automatische undo:** de AMD PSR-fix, de GNOME-extensies, Secure Boot, Archi en Tmog. Ze zijn handmatig of raken dingen die een script niet moet gokken. Waar er een weg terug met de hand is, print `show <id>` die.
- **Het YubiKey-onderdeel is geblokkeerd zolang het in gebruik is.** Staat `pam_u2f` in `/etc/pam.d/sudo`, `polkit-1` of `gdm-password`, dan weigert het script de pakketten te verwijderen, want daarmee sluit je jezelf buiten je eigen login. Haal het eerst uit PAM.

Zonder risico proberen kan met `undo --dry-run <id>`: dat print het plan en stopt.

## De aanbevolen set

`apply --recommended` is wat ik op elke verse installatie zou instellen:

| Onderdeel | Wat het doet |
|---|---|
| `asus-tools` | asusctl en ROG Control Center |
| `asus-battery-limit` | Stopt met laden op 80% |
| `asus-ppd-mask` | Laat asusd de energieprofielen beheren |
| `backlight-fix` | Helderheid in elke GPU-modus |
| `nvidia-power-services` | NVIDIA suspend- en resume-units, alleen voor een driver die het videogeheugen niet zelf bewaart (niet `nvidia-open`) |
| `nvidia-prime` | `prime-run` |
| `display-color-modes` | Het fabrieksprofiel van het paneel plus de ASUS sRGB-, DCI-P3- en Display P3-profielen, voor color-managed apps. Ze veranderen niet hoe het bureaublad eruitziet |
| `wifi-mt7925` | Wi-Fi-doorvoer tunen |
| `gnome-window-buttons` | Minimaliseer- en maximaliseerknoppen |
| `gnome-focus` | Nieuwe vensters komen naar voren |
| `gnome-extension-manager` | Extension Manager |
| `wsf` | Scrollsnelheid van het touchpad |
| `git-github-cli` | Git en de GitHub CLI |
| `git-gpg-signing` | Kleopatra en ondertekende commits |

Dingen die een kwestie van smaak zijn, zoals de Windows-achtige sneltoetsen, de applicaties en de virtualisatiestack, staan wel in het menu maar niet in de set. Dat geldt ook voor de geavanceerde onderdelen: YubiKey, Secure Boot, VMware en de AMD-fix tegen het vastlopen van het scherm.

## Waar de keuzes vandaan komen

De onderdelen volgen upstream waar upstream een mening heeft, en de handleidingspagina achter elk onderdeel geeft de redenering en de bronnen.

- **ASUS-tools, profielen en `power-profiles-daemon`:** de [asusctl-documentatie van het Open Gaming Collective](https://opengamingcollective.github.io/asusctl/) en de [manual](https://github.com/OpenGamingCollective/asusctl/blob/main/MANUAL.md). `power-profiles-daemon` maskeren is wat de [Arch-](https://opengamingcollective.github.io/asusctl/distributions/arch.html) en [Bazzite-gids](https://opengamingcollective.github.io/asusctl/distributions/bazzite.html) zeggen. De [asusctl-pagina]({{< relref "/docs/hardware/asusctl-rog-control" >}}) legt uit waarom oudere gidsen het tegenovergestelde zeggen.
- **NVIDIA suspend-units en `nvidia-powerd`:** NVIDIA's driver-README over [energiebeheer](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) en [Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html). De suspend-units worden overgeslagen op `nvidia-open`, dat het videogeheugen zelf bewaart; de [NVIDIA-pagina]({{< relref "/docs/cachyos/nvidia" >}}) heeft de details.
- **Kleurstanden:** naar het voorbeeld van [G-Helper](https://github.com/seerge/g-helper), dat op Windows de ASUS-paneelprofielen laat zien.
- **Autologin en de YubiKey:** de [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) en de [pam-u2f README](https://github.com/Yubico/pam-u2f).
- **De helderheidsfix:** uitgezocht op deze laptop, met de redenering op de pagina [Bekende problemen]({{< relref "/docs/known-issues" >}}).

## Een onderdeel toevoegen of aanpassen

Elk onderdeel is één regel in `build_items()` in het script: een id, de sectie waar het bij hoort, een korte samenvatting, de pagina in de handleiding waar het naar linkt, een functie die zijn status bepaalt en een functie die zegt wat toepassen doet. Een set pakketten is een one-liner. Pas je het script aan, draai dan `.github/scripts/check-doc-checksums.sh --apply` zodat de hash op deze pagina meegaat.
