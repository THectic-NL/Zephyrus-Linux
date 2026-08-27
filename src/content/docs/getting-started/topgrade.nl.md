---
title: "Topgrade"
weight: 3
prev: docs/getting-started/bazzite
next: docs/hardware/nvidia-cachyos
---

Deze laptop bijwerken is nooit één commando. Je hebt de systeempackages, de Flatpaks, wat Homebrew in je home-map heeft gezet, de distrobox-containers, de firmware, en een handvol tools die zichzelf bijwerken. [Topgrade](https://github.com/topgrade-rs/topgrade) draait ze allemaal achter elkaar en vertelt je wat het gedaan heeft.

Het is een gemak, geen package manager. Alles wat het doet kun je met de hand doen; de winst is dat je de Flatpaks niet meer drie weken vergeet.

## Wat het hier daadwerkelijk draait

Topgrade detecteert wat er op het systeem staat in plaats van dat je het vertelt. Op deze laptop komt dat ongeveer hierop neer:

{{< tabs >}}
{{< tab name="CachyOS" >}}

| Stap | Wat het draait |
|---|---|
| Systeempackages | `pacman` (via je AUR-helper als je die hebt, dus inclusief de AUR) |
| Flatpak | `flatpak update` |
| Firmware | `fwupdmgr` |
| Containers | haalt nieuwere images op voor de containers die je hebt |
| Distrobox | werkt bij binnen elke container |
| Taal-tools | `cargo`, `rustup`, `npm`, `pipx` en dergelijke, als ze er zijn |

De systeemstap is hier de belangrijkste: het is een rolling distributie, dus dit *is* de update.

{{< /tab >}}
{{< tab name="Bazzite" >}}

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
De systeemstap **zet hier een image klaar en past hem niet toe**. Topgrade die klaar is, is niet hetzelfde als bijgewerkt zijn; dat ben je na de volgende herstart. Dat is het gedrag van `rpm-ostree` en geen eigenaardigheid van Topgrade, en het is verreweg het meest verwarrende aan Topgrade op een atomic systeem.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Installeren

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S topgrade
```

Zit hij niet in de repos op jouw installatie, dan heeft de AUR zowel `topgrade` als `topgrade-bin`.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Topgrade is één commandline-binary, dus Homebrew — geen layering, geen herstart, en hij werkt zichzelf bij samen met alles wat hij beheert:

```bash
brew install topgrade
```

Layer hem **niet** met `rpm-ostree`. Een tool die als enige taak heeft om updates te draaien hoort geen onderdeel te zijn van de image die hij bijwerkt.

{{< /tab >}}
{{< /tabs >}}

## Draaien

```bash
topgrade
```

Dat is de hele interface. Handige vlaggen:

```bash
topgrade --dry-run          # laat zien wat er zou draaien, draait niets
topgrade --only system      # alleen de systeempackages
topgrade --disable firmware # sla een stap over voor deze run
topgrade -y                 # niet vragen voor elke stap
```

`--dry-run` is op een nieuwe installatie één keer de moeite waard. Het print de stappen die het gedetecteerd heeft, en dat is de snelste manier om te ontdekken dat het iets níét oppikt.

## Configuratie

Het configuratiebestand wordt bij de eerste run aangemaakt op `~/.config/topgrade.toml`.

De instelling die op deze laptop het meest oplevert is firmware overslaan, want `fwupdmgr` wil op de G16 herstarten naar de firmware-updater en dat is zelden wat je midden in een update wilt:

```toml
[misc]
disable = ["firmware"]
```

Andere dingen die hun plek verdienen:

```toml
[misc]
# Doorgaan als een stap faalt in plaats van de run stoppen
ignore_failures = ["containers"]

# Niet vragen voor elke stap
assume_yes = true
```

{{< tabs >}}
{{< tab name="CachyOS" >}}

Wijs hem naar je AUR-helper zodat de AUR meegaat in plaats van overgeslagen wordt:

```toml
[linux]
arch_package_manager = "paru"
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Er is niets distributie-specifieks nodig — de `rpm-ostree`-stap wordt automatisch opgepikt.

Wil je liever dat Topgrade de systeem-image met rust laat en alleen de lagen erboven doet (Flatpaks, Homebrew, containers), zet de systeemstap dan uit en houd `ujust update` aan voor de image:

```toml
[misc]
disable = ["system"]
```

Dat is een redelijke verdeling: de image werkt zichzelf toch al op de achtergrond bij.

{{< /tab >}}
{{< /tabs >}}

## Is het de moeite waard?

{{< tabs >}}
{{< tab name="CachyOS" >}}

Ja, en hier levert Topgrade het meeste op. Updates zijn van jou om te draaien, ze komen uit vier of vijf verschillende hoeken, en er eentje vergeten is precies hoe je eindigt met een Flatpak die een half jaar achterloopt op het systeem waarop hij draait.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Eerlijk gezegd minder dan op CachyOS. De image werkt zichzelf op de achtergrond bij, `ujust update` dekt de image plus Flatpaks plus distrobox al, en door het klaarzetten-maar-niet-toepassen hierboven is Topgrades uitvoer hier makkelijker verkeerd te lezen.

Het blijft nuttig als je op Homebrew en containers leunt, want die vallen buiten wat `ujust update` aanraakt. Doe je dat niet, dan is `ujust update` genoeg en is deze pagina optioneel.

{{< /tab >}}
{{< /tabs >}}

## Referenties

- [Topgrade op GitHub](https://github.com/topgrade-rs/topgrade)
- [Topgrade: configuratiereferentie](https://github.com/topgrade-rs/topgrade/blob/main/config.example.toml)
- [rpm-ostree-documentatie](https://coreos.github.io/rpm-ostree/)
