---
title: ""
weight: 1
toc: false
---

# Mijn Linux-setup

Dit is Linux zoals ik het graag heb, opgeschreven zodat ik het snel opnieuw kan opbouwen en zodat jij hetzelfde kunt opzetten. Het is gebouwd rond de enige laptop die ik heb, de ROG Zephyrus G16 (GA605WV), en dekt de twee distributies die ik erop zou aanraden: **CachyOS** en **Bazzite**.

Het is eigenzinnig. Dit zijn mijn favoriete instellingen en de software die ik echt gebruik, geen overzicht van alle opties, en het meeste is omgezet in een setup-venster. Als iets hier je helpt: mooi. Kom je iets tegen dat ik niet heb behandeld, laat het dan weten.

## Richt een machine in zoals de mijne

{{< cards >}}
  {{< card link="/docs/setup-script" title="Setup-script" subtitle="Een checklist die laat zien wat er op jouw machine klaar is en wat nog openstaat, en die mijn aanbevolen instellingen toepast. Bij elk onderdeel staat een link naar de handleiding." >}}
{{< /cards >}}

## Wat is specifiek voor deze laptop

Je hebt niet precies dit model nodig. Alleen de pagina's over de hardware van de laptop zelf zijn specifiek voor de G16. Al het andere werkt op elke machine.

| Specifiek voor de Zephyrus G16 | Werkt op elke machine |
|---|---|
| [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}}), [kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}}), [MT7925 Wi-Fi-tuning]({{< relref "/docs/networking/mt7925-wifi-performance" >}}), de helderheidsfix in [Bekende problemen]({{< relref "/docs/known-issues" >}}) | [GNOME-bureaublad]({{< relref "/docs/desktop" >}}), [beveiliging]({{< relref "/docs/security" >}}), [applicaties]({{< relref "/docs/applications" >}}), [virtualisatie]({{< relref "/docs/virtualization" >}}), [gaming]({{< relref "/docs/gaming" >}}), [eduroam]({{< relref "/docs/networking/eduroam-network-installation" >}}) |

## Kies eerst een distributie

De rest van deze handleidingen volgt uit die ene keuze. Elke distributie heeft eigen pagina's voor het installeren, de NVIDIA-driver, Secure Boot en bijwerken. Met de schakelaar bovenaan elke pagina wissel je tussen de twee.

{{< cards >}}
  {{< card link="/docs/cachyos/getting-started" title="CachyOS" subtitle="Arch, rolling release. Je wilt de machine zelf beheren en neemt het onderhoud op de koop toe." >}}
  {{< card link="/docs/bazzite/getting-started" title="Bazzite" subtitle="Fedora Atomic. Je gamet, of je wilt gewoon dat het OS je met rust laat." >}}
{{< /cards >}}

Alles wat niet van de distributie afhangt (eduroam, de YubiKey, GNOME-tweaks, de VM-setup, applicaties) staat in de gedeelde secties hieronder en werkt op allebei.

## Welke van de twee moet je draaien?

Ik heb ze allebei echt op deze laptop gedraaid, niet als weekendexperiment. Dit is het advies dat ik in het echt zou geven.

**Kies CachyOS als je de machine zelf in handen wilt.** Je wilt weten hoe het systeem in elkaar zit, en je verandert liever iets dan dat je beschermd wordt tegen het stukmaken ervan. Je kiest je eigen kernel, tunet de scheduler en installeert uit `pacman` of de AUR zonder iemand om toestemming te vragen. Daar staat tegenover dat het onderhoud van jou is. Updates doe je bewust, en als er een misgaat, repareer je die met de hand.

**Kies Bazzite als je gamet, of als je juist niet wilt sleutelen.** Steam, Proton en de controller-stack zitten in de image, al geconfigureerd, nog voordat je voor het eerst inlogt. Het is ook het betere antwoord als sleutelen aan je OS geen hobby is: het systeem is read-only, updates komen als hele image binnen, en een slechte update draai je terug vanuit het bootmenu. Het is moeilijk stuk te krijgen, en dat is de bedoeling. Dat is wel een echte ruil. Je kiest de kernel niet, iets op systeemniveau installeren betekent layeren plus een herstart, en gewoontes van een normale distributie moet je afleren. Klinkt dat irritant in plaats van geruststellend, dan wil je CachyOS.

### De verschillen die je echt merkt

| | CachyOS | Bazzite |
|---|---|---|
| **Basis** | Arch, rolling release | Fedora Atomic, gebouwd door [Universal Blue](https://universal-blue.org/) |
| **Systeembestanden** | Beschrijfbaar | `/usr` is read-only; het systeem wordt als één image bijgewerkt |
| **Software installeren** | `pacman` en de AUR, direct | Eerst Flatpak, daarna Homebrew en distrobox; `rpm-ostree`-layering als laatste redmiddel, en dat vraagt een herstart |
| **Kernel** | Je kiest er zelf een (CachyOS Kernel Manager) | Zit in de image |
| **Home-map** | `/home` | `/var/home`, met `/home` als symlink daarnaartoe |
| **NVIDIA-driver** | Geconfigureerd door de installer | Zit in de `-nvidia-open`-image |
| **Gaming** | Werkt goed, je zet het zelf op | De reden dat de distributie bestaat |
| **Een slechte update terugdraaien** | Packages met de hand downgraden | `rpm-ostree rollback`, of de vorige image kiezen bij het opstarten |

Ze draaien allebei prima op deze laptop. Alles wat op de G16 telt (de Radeon 890M, de RTX 4060, het ROG Nebula Display, `asusctl`) werkt op beide. Je kiest niet tussen een goede en een slechte optie. Je kiest hoeveel van de machine je zelf wilt beheren.

{{< callout type="info" >}}
Kernel 6.19 of nieuwer is het enige dat ze allebei nodig hebben. Daar is de `asus-armoury`-driver in mainline geland, en die heeft de Ryzen AI 9 HX 370 nodig. CachyOS zit er ruim voorbij; Bazzite levert een recente kernel mee in de image.
{{< /callout >}}

### En gewoon Fedora dan?

Dat werkt prima op deze laptop. Niets hier is een waarschuwing ertegen. Na het testen van meerdere distributies op deze machine kwamen deze twee er duidelijk bovenuit, en dat zijn dus de twee die ik uit ervaring kan documenteren in plaats van op basis van horen zeggen. Bazzite is onderhuids gewoon Fedora, de atomic editie met de gaming- en hardware-onderdelen al ingebouwd, dus daarvoor kiezen is niet echt afscheid nemen van Fedora.

## Ze wisselen elkaar af

Ik heb er niet één gekozen en het daarbij gelaten. Ik heb ze allebei als dagelijks systeem op deze laptop gedraaid en ben meer dan eens heen en weer geswitcht. Tegenwoordig is CachyOS mijn daily driver, vooral omdat een deel van wat ik doe die extra systeemcontrole vraagt. Bazzite draaide ik vroeger in dualboot op dezelfde machine, en ik ging er af en toe uit nieuwsgierigheid op terug en gebruikte het dan weer een tijdje voordat ik terugschakelde. Geen van beide blijft lang voorop lopen.

Het gaat in golven. De ene maand landt er in Bazzite een kernel-bump of een Mesa-fix en is het de soepelste van de twee. Een maand later levert CachyOS een scheduler-wijziging of een `asusctl`-update en is de voorsprong weer weg. Het verschil is nooit groot en duurt nooit lang, want de dingen die er echt toe doen worden sowieso gebackport. Een fix die in de kernel van de ene distributie of in mainline opduikt, zit meestal binnen een release of twee ook in de andere. Geef het een paar weken en ze lopen weer gelijk.

Dub er dus niet te lang over. Kies degene waarvan de afwegingen passen bij hoe je de machine wilt gebruiken, niet degene die deze week twee patches voorloopt. Kom je er later achter dat je verkeerd koos, dan is overstappen een herinstallatie en een middag werk, en alles in deze handleidingen dekt allebei.
