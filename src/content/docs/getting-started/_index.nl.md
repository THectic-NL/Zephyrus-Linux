---
title: "Aan de slag"
weight: 1
next: docs/getting-started/cachyos
---

Dit is mijn persoonlijke setup-documentatie voor de ROG Zephyrus G16 (GA605WV). Ik ben geen software-engineer of developer, gewoon iemand die overgestapt is naar Linux en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen niet hetzelfde hoeven uit te zoeken als ik.

Als iets hier je helpt: mooi. Loop je ergens tegenaan wat ik niet behandeld heb, laat het gerust weten; ik denk graag mee.

## Twee distributies

Na het testen van een aantal distributies op deze laptop zijn er twee die de moeite van het documenteren waard zijn: **CachyOS** en **Bazzite**. Ze kiezen tegenovergestelde uitgangspunten, en welke bij je past hangt af van hoe je de machine wilt gebruiken, niet van welke beter is.

| | CachyOS | Bazzite |
|---|---|---|
| **Basis** | Arch, rolling release | Fedora Atomic, gebouwd door [Universal Blue](https://universal-blue.org/) |
| **Systeembestanden** | Beschrijfbaar | `/usr` is read-only; het systeem wordt als één image bijgewerkt |
| **Software installeren** | `pacman` en de AUR, direct | Eerst Flatpak, daarna Homebrew en distrobox; `rpm-ostree`-layering als laatste redmiddel, en dat vraagt een herstart |
| **Kernel** | Je kiest er zelf een (CachyOS Kernel Manager) | Zit in de image |
| **Home-map** | `/home` | `/var/home`, met `/home` als symlink daarnaartoe |
| **NVIDIA-driver** | Geconfigureerd door de installer | Zit in de `-nvidia-open`-image |
| **Een slechte update terugdraaien** | Packages met de hand downgraden | `rpm-ostree rollback`, of de vorige image kiezen bij het opstarten |
| **Past bij je als** | Je de machine wilt tunen en het onderhoud niet erg vindt | Je een machine wilt die zichzelf bijwerkt en moeilijk stuk gaat |

Allebei draaien ze deze laptop prima. Alles wat op de G16 telt — de Radeon 890M, de RTX 4060, het ROG Nebula Display, `asusctl` — werkt op beide.

{{< callout type="info" >}}
Kernel 6.19 of nieuwer is het enige dat ze allebei nodig hebben. Daar is de `asus-armoury`-driver in mainline geland, en dat is wat de Ryzen AI 9 HX 370 wil. CachyOS zit er ruim voorbij; Bazzite levert een recente kernel mee in de image.
{{< /callout >}}

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

→ [CachyOS]({{< relref "/docs/getting-started/cachyos" >}}) — op Arch gebaseerd en rolling. Kies je eigen kernel en scheduler, tune wat je wilt.
→ [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) — Fedora Atomic. Read-only systeem, image-updates, terugdraaien vanuit het bootmenu.

Elk van beide eindigt met de volgorde die ik op die distributie zou aanhouden.
