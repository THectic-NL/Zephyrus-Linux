---
title: ""
weight: 1
toc: false
---

# Mijn setup-notities

Alles wat ik heb opgeschreven tijdens het draaien van Linux op de ROG Zephyrus G16 (GA605WV), voor de twee distributies die ik erop zou aanraden: **CachyOS** en **Bazzite**.

Ik ben geen developer, gewoon iemand die overstapte naar Linux en tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen dat niet hoeven uit te zoeken. Als iets hier je helpt: mooi. Loop je ergens tegenaan wat ik niet behandeld heb, laat het weten.

## Kies eerst een distributie

De rest van deze handleidingen volgt uit die ene keuze. Elke distributie heeft eigen pagina's voor het installeren, de NVIDIA-driver, Secure Boot en bijwerken. De switcher bovenaan elke pagina brengt je tussen de twee.

{{< cards >}}
  {{< card link="/docs/cachyos/getting-started" title="CachyOS" subtitle="Arch, rolling. Je wilt de machine zelf in handen en het onderhoud neem je erbij." >}}
  {{< card link="/docs/bazzite/getting-started" title="Bazzite" subtitle="Fedora Atomic. Je gamet, of je wilt gewoon dat het OS je met rust laat." >}}
{{< /cards >}}

Alles wat niet van de distributie afhangt (eduroam, de YubiKey, GNOME-tweaks, de VM-setup, applicaties) staat in de gedeelde secties hieronder en werkt op allebei.

## Welke van de twee moet je draaien?

Ik heb ze allebei echt op deze laptop gedraaid, niet als weekendexperiment. Dit is het advies dat ik in het echt zou geven.

**Kies CachyOS als je de machine zelf in handen wilt.** Je wilt weten hoe het systeem in elkaar zit, en je verandert liever iets dan dat je beschermd wordt tegen het stukmaken ervan. Je kiest je eigen kernel, tunet de scheduler en installeert uit `pacman` of de AUR zonder iemand om toestemming te vragen. Daar staat tegenover dat het onderhoud van jou is. Updates doe je bewust, en als er een misgaat repareer je hem met de hand.

**Kies Bazzite als je gamet, of als je juist niet wilt sleutelen.** Steam, Proton en de controller-stack zitten in de image, al geconfigureerd, nog voordat je voor het eerst inlogt. Het is ook het betere antwoord als sleutelen aan je OS geen hobby is: het systeem is read-only, updates komen als hele image binnen, en een slechte draai je terug vanuit het bootmenu. Het is moeilijk stuk te krijgen, en dat is de bedoeling. De ruil is echt. Je kiest de kernel niet, iets op systeemniveau installeren betekent layeren plus een herstart, en gewoontes van een normale distributie moet je afleren. Klinkt dat irritant in plaats van geruststellend, dan wil je CachyOS.

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

Allebei draaien ze deze laptop prima. Alles wat op de G16 telt (de Radeon 890M, de RTX 4060, het ROG Nebula Display, `asusctl`) werkt op beide. Je kiest niet tussen een goede en een slechte optie. Je kiest hoeveel van de machine je zelf wilt beheren.

{{< callout type="info" >}}
Kernel 6.19 of nieuwer is het enige dat ze allebei nodig hebben. Daar is de `asus-armoury`-driver in mainline geland, en dat is wat de Ryzen AI 9 HX 370 wil. CachyOS zit er ruim voorbij; Bazzite levert een recente kernel mee in de image.
{{< /callout >}}

### En gewoon Fedora dan?

Dat werkt prima op deze laptop. Niets hier is een waarschuwing ertegen. Na het testen van meerdere distributies op deze machine kwamen deze twee er duidelijk bovenuit, en dat zijn dus de twee die ik uit ervaring kan documenteren in plaats van van horen zeggen. Bazzite is onderhuids gewoon Fedora, de atomic editie met de gaming- en hardware-onderdelen al in elkaar gezet, dus daarvoor kiezen is niet echt afscheid nemen van Fedora.

## Ze wisselen elkaar af

Ik heb er niet één gekozen en het daarbij gelaten. Ik heb ze allebei als dagelijks systeem op deze laptop gedraaid en ben meer dan eens heen en weer geswitcht. Terwijl ik dit schrijf zit ik op Bazzite. Geen van beide blijft lang voorop lopen.

Het gaat in golven. De ene maand landt er in Bazzite een kernel-bump of een Mesa-fix en is het de soepelste van de twee. Een maand later levert CachyOS een scheduler-wijziging of een `asusctl`-update en klapt de voorsprong terug. Het gat is nooit groot en het houdt nooit aan, want de dingen die er echt toe doen worden sowieso ge-backport. Een fix die in de kernel van de ene distributie of in mainline opduikt, zit meestal binnen een release of twee ook in de andere. Geef het een paar weken en ze lopen weer gelijk.

Zit er dus niet te lang over te dubben. Kies degene waarvan de afwegingen passen bij hoe je de machine wilt gebruiken, niet degene die deze week twee patches voorloopt. Kom je er later achter dat je verkeerd koos, dan is overstappen een herinstallatie en een middag werk, en alles in deze handleidingen dekt allebei.
