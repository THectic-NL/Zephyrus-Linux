---
title: "Aan de slag"
weight: 1
next: docs/getting-started/cachyos
---

Dit is mijn persoonlijke setup-documentatie voor de ROG Zephyrus G16 (GA605WV). Ik ben geen software-engineer of developer, gewoon iemand die overgestapt is naar Linux en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen niet hetzelfde hoeven uit te zoeken als ik.

Als iets hier je helpt: mooi. Loop je ergens tegenaan wat ik niet behandeld heb, laat het gerust weten; ik denk graag mee.

## Welke van de twee moet je draaien?

Ik heb ze allebei echt op deze laptop gedraaid, niet als weekendexperiment, en dit is de eerlijke versie van het advies dat ik in het echt zou geven. Maak deze keuze eerst — de rest van deze handleidingen hangt eraan op.

### Kies CachyOS als je de machine zelf in handen wilt

Je wilt weten hoe het systeem in elkaar zit, en je hebt liever de mogelijkheid om iets te veranderen dan bescherming tegen het stukmaken ervan. Je kiest je eigen kernel, tunet de scheduler en installeert uit `pacman` of de AUR zonder iemand om toestemming te vragen. Daar staat tegenover dat het onderhoud van jou is: updates doe je bewust, en als er een misgaat repareer je hem met de hand.

Dit is wat ik dagelijks draai.

### Kies Bazzite als je gamet, of als je juist níét wilt sleutelen

Bazzite is voor gaming gebouwd — Steam, Proton en de controller-stack zitten in de image, geconfigureerd, nog voordat je voor het eerst inlogt. Het is ook het betere antwoord als sleutelen aan je OS geen hobby is: het systeem is read-only, updates komen als hele image binnen, en een slechte draai je terug vanuit het bootmenu. Het is echt moeilijk stuk te krijgen, en dat is precies de bedoeling.

De ruil is echt. Je kiest de kernel niet, iets op systeemniveau installeren betekent layeren plus een herstart, en gewoontes van een normale distributie moet je afleren. Klinkt dat irritant in plaats van geruststellend, dan wil je CachyOS.

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

Allebei draaien ze deze laptop prima. Alles wat op de G16 telt — de Radeon 890M, de RTX 4060, het ROG Nebula Display, `asusctl` — werkt op beide. Je kiest niet tussen een goede en een slechte optie; je kiest hoeveel van de machine je zelf wilt beheren.

{{< callout type="info" >}}
Kernel 6.19 of nieuwer is het enige dat ze allebei nodig hebben. Daar is de `asus-armoury`-driver in mainline geland, en dat is wat de Ryzen AI 9 HX 370 wil. CachyOS zit er ruim voorbij; Bazzite levert een recente kernel mee in de image.
{{< /callout >}}

### En gewoon Fedora dan?

Dat werkt prima op deze laptop — niets hier is een waarschuwing ertegen. Alleen: na het testen van meerdere distributies op déze machine kwamen deze twee er duidelijk bovenuit, en dat zijn dus de twee die ik uit ervaring kan documenteren in plaats van van horen zeggen. Goed om te weten dat Bazzite onderhuids gewoon Fedora *is*, de atomic editie met de gaming- en hardware-onderdelen al in elkaar gezet, dus daarvoor kiezen betekent niet echt afscheid nemen van Fedora.

Deze handleidingen geven alleen commando's voor CachyOS en Bazzite. Er is geen derde set om correct te houden.

## Hoe deze handleidingen zijn ingedeeld

Het meeste hieronder geldt voor allebei en staat op één pagina, met een tab om de stukken die verschillen:

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S example
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.example.App
```

{{< /tab >}}
{{< /tabs >}}

De tabs lopen gelijk: kies je distributie één keer en alle andere tabs op de pagina volgen.

Een paar onderwerpen werken zo verschillend dat een gedeelde pagina het alleen maar troebel zou maken. Die krijgen een pagina per distributie — het systeem installeren, de NVIDIA-driver en Secure Boot. Ze staan duidelijk gelabeld naast elkaar in het menu.

## Kies je startpunt

→ [CachyOS]({{< relref "/docs/getting-started/cachyos" >}}) — je wilt controle, en het onderhoud neem je erbij.
→ [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) — je gamet, of je wilt gewoon dat het OS je met rust laat.

Elk van beide eindigt met de volgorde die ik op die distributie zou aanhouden.
