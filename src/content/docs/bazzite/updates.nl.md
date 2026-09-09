---
title: "Bijwerken"
weight: 2
prev: docs/bazzite/getting-started
next: docs/bazzite/nvidia
distro: bazzite
---

Een update op Bazzite is een hele nieuwe image, geen set packages. Hij wordt op de achtergrond gedownload en werkt na de volgende herstart, dus hij kan je nooit halverwege laten stranden.

```bash
ujust update
```

Desktop-images werken zichzelf op de achtergrond bij, dus in de praktijk draai je dit zelden met de hand — vooral vanaf een TTY of via SSH. `ujust update` dekt de image, de Flatpaks en de distrobox-containers in één keer.

Breekt een update iets, dan staat de vorige image nog op schijf:

```bash
rpm-ostree rollback
systemctl reboot
```

Hij staat ook in het bootmenu, en dat is wat je redt als het probleem je niet meer bij een terminal laat komen. Dit is verreweg het grootste praktische verschil met een rolling distributie.

## Klaargezet, niet toegepast

```bash
rpm-ostree status
```

`rpm-ostree upgrade` (en `bootc upgrade`, waar bootc gebruikt wordt) **zet** de volgende image **klaar**. Je bent niet bijgewerkt als het commando klaar is — je bent bijgewerkt na de volgende herstart. Dat is het gedrag van `rpm-ostree`, en het meest verwarrende aan het bijwerken van een atomic systeem.

## De rest, in één keer

`ujust update` doet de image, Flatpaks en distrobox. Wat het niet aanraakt is Homebrew en containers die je zelf opzet. [Topgrade](https://github.com/topgrade-rs/topgrade) dekt het allemaal achter elkaar en vertelt je wat het gedaan heeft.

### Wat het hier draait

| Stap | Wat het draait |
|---|---|
| Systeem-image | `rpm-ostree upgrade`, en `bootc upgrade` waar bootc gebruikt wordt |
| Flatpak | `flatpak update` |
| Homebrew | `brew upgrade` |
| Distrobox | werkt bij binnen elke container |
| Firmware | `fwupdmgr` |
| Taal-tools | `cargo`, `npm`, `pipx` en dergelijke, als ze er zijn |

Topgrade herkent Bazzite bij naam — het leest `VARIANT` uit `/etc/os-release` en behandelt Bazzite, Bluefin, Aurora, Silverblue en Kinoite als één familie — dus het grijpt naar `rpm-ostree` in plaats van te proberen met `dnf` een read-only `/usr` binnen te komen.

{{< callout type="warning" >}}
De systeemstap **zet een image klaar en past hem niet toe**. Topgrade die klaar is, is niet hetzelfde als bijgewerkt zijn; dat ben je na de volgende herstart.
{{< /callout >}}

### Installeren

Topgrade is één commandline-binary, dus Homebrew — geen layering, geen herstart, en hij werkt zichzelf bij samen met alles wat hij beheert:

```bash
brew install topgrade
```

Layer hem **niet** met `rpm-ostree`. Een tool die als enige taak heeft om updates te draaien hoort geen onderdeel te zijn van de image die hij bijwerkt.

### Draaien

```bash
topgrade
```

Handige vlaggen:

```bash
topgrade --dry-run          # laat zien wat er zou draaien, draait niets
topgrade --only system      # alleen de systeem-image
topgrade --disable firmware # sla een stap over voor deze run
topgrade -y                 # niet vragen voor elke stap
```

### Configuratie

Het configuratiebestand wordt bij de eerste run aangemaakt op `~/.config/topgrade.toml`.

Sla firmware over — `fwupdmgr` wil op de G16 herstarten naar de firmware-updater, zelden wat je midden in een update wilt:

```toml
[misc]
disable = ["firmware"]
ignore_failures = ["containers"]
assume_yes = true
```

Wil je liever dat Topgrade de systeem-image met rust laat en alleen de lagen erboven doet (Flatpaks, Homebrew, containers), zet de systeemstap dan uit en houd `ujust update` aan voor de image:

```toml
[misc]
disable = ["system", "firmware"]
```

Dat is een redelijke verdeling — de image werkt zichzelf toch al op de achtergrond bij.

### Is het de moeite waard?

Eerlijk gezegd minder dan op CachyOS. De image werkt zichzelf bij, `ujust update` dekt image plus Flatpaks plus distrobox al, en door het klaarzetten-maar-niet-toepassen is Topgrades uitvoer hier makkelijker verkeerd te lezen. Het verdient zijn plek als je op Homebrew en zelfgemaakte containers leunt; doe je dat niet, dan is `ujust update` genoeg.

## Referenties

- [Topgrade op GitHub](https://github.com/topgrade-rs/topgrade)
- [rpm-ostree-documentatie](https://coreos.github.io/rpm-ostree/)
- [Bazzite-documentatie](https://docs.bazzite.gg/)
