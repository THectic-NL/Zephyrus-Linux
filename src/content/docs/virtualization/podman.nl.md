---
title: "Podman & Podman Desktop"
weight: 4
prev: docs/virtualization/winboat
next: docs/virtualization/vmware-workstation
---

Ik gebruikte Docker hiervoor, maar wilde eens wat anders proberen. De filosofie achter Podman sprak me genoeg aan om volledig over te stappen.

Podman draait containers standaard **rootless**, als gewone gebruiker zonder verhoogde rechten. Het heeft ook geen **daemon**: Docker heeft altijd een achtergrondproces (`dockerd`) dat als root draait; bij Podman zit er niets tussen, dus minder overhead.

Podman heeft ook goede **systemd-integratie**, wat logisch is want het is gemaakt door Red Hat en is de standaard container-runtime op Fedora en RHEL. Daar merk je dit het meest, maar op CachyOS werkt het prima.

Voor mij dekt het alles wat ik nodig heb. Compose, Kubernetes en rootless networking zijn al ingebouwd. Docker-compatibiliteit betekent dat ik gewoon de `docker` CLI en bestaande `docker-compose` bestanden kan blijven gebruiken zonder wijzigingen.

> Zie het [Ontwikkeling]({{< relref "/docs/applications#podman--podman-desktop" >}}) onderdeel in Applicaties voor een korte samenvatting van de installatie.

---

## Installatie

Drie pakketten vormen de volledige setup:

| Pakket | Doel |
|---|---|
| `podman` | De container-runtime |
| `podman-docker` | Drop-in `docker` CLI-vervanging; verwijdert Docker als het geïnstalleerd is |
| `podman-desktop` | GUI voor het beheren van containers, images, volumes en registries |

```bash
sudo pacman -S podman podman-docker podman-desktop
```

{{< callout type="warning" >}}
`podman-docker` **conflicteert met** `docker`. Pacman vraagt je Docker te verwijderen voor de installatie. Dit is opzettelijk: `podman-docker` levert het `docker` commando als wrapper die Podman aanroept, zodat al je bestaande `docker`-commando's gewoon blijven werken.
{{< /callout >}}

Elk `docker` commando loopt nu via Podman en toont eenmalig een melding:

```
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
```

Om die melding permanent te onderdrukken:

```bash
sudo touch /etc/containers/nodocker
```

---

## Podman Desktop onboarding

Bij de eerste keer opstarten doorloopt Podman Desktop een wizard voor het instellen van Podman, kubectl (voor Kubernetes) en Compose.

![Podman Desktop welkomstscherm - v1.25.1 met Podman, kubectl en Compose extensies](/images/podman-desktop-welcome.avif)

Podman zelf wordt direct herkend omdat het al via pacman was geïnstalleerd. De wizard bevestigt dit en laat je autostart instellen:

![Podman Desktop setup - Podman herkend en correct geconfigureerd](/images/podman-desktop-containers.avif)

---

## Registryconfiguratie

Dit is het gedeelte dat wat extra opzet vergt buiten de pakketinstallatie.

### Het probleem: niet-gekwalificeerde imagenamen

Standaard weet Podman niet welke registry het moet doorzoeken als je een korte imagenaam gebruikt zoals `stensel8/my-image:latest`. Docker gebruikte Docker Hub als standaard; Podman doet dat niet tenzij je het expliciet instelt.

Een korte naam ophalen zonder configuratie mislukt:

```
$ podman pull stensel8/public-cloud-concepts:latest
Error: short-name "stensel8/public-cloud-concepts:latest" did not resolve to an alias
and no unqualified-search registries are defined in "/etc/containers/registries.conf"
```

Dezelfde fout treedt op via de `docker` shim:

```
$ docker pull stensel8/public-cloud-concepts:latest
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
Error: short-name "stensel8/public-cloud-concepts:latest" did not resolve to an alias
and no unqualified-search registries are defined in "/etc/containers/registries.conf"
```

### Oplossing: unqualified-search-registries toevoegen

Bewerk `/etc/containers/registries.conf` en verwijder het commentaar van de `unqualified-search-registries` regel:

```bash
sudo nano /etc/containers/registries.conf
```

Zoek en pas deze regel aan:

```toml
unqualified-search-registries = ["docker.io", "ghcr.io"]
```

Na het opslaan worden korte namen correct omgezet:

```
$ docker pull stensel8/public-cloud-concepts:latest
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
✔ docker.io/stensel8/public-cloud-concepts:latest
Trying to pull docker.io/stensel8/public-cloud-concepts:latest...
```

---

## Docker Hub en GitHub Container Registry koppelen

Ook met geconfigureerde zoekregistries heb je authenticatie nodig voor **privé**-repositories. Podman Desktop regelt dit via Instellingen → Registries.

![Podman Desktop Instellingen - Registries, Docker Hub inlogformulier](/images/podman-desktop-registries.avif)

De interface laat je inloggen bij Docker Hub, GitHub Container Registry, Red Hat Quay en Google Container Registry. Je wachtwoord direct invullen wordt afgeraden, gebruik in plaats daarvan Personal Access Tokens (PATs).

### Docker Hub PAT aanmaken

Ga naar [hub.docker.com](https://hub.docker.com) → Account Settings → Personal access tokens → New access token.

![Docker Hub - Personal Access Token aanmaken voor Podman Desktop](/images/podman-docker-hub-pat.avif)

Geef het token een duidelijke naam (bijv. `Podman Desktop - Sten-Laptop`) en kies de benodigde rechten. Gebruik dit token als wachtwoord in Podman Desktop.

### GitHub PAT aanmaken

Ga naar GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token.

Selecteer het `read:packages` scope (en `write:packages` als je images pusht). Kopieer het token direct, GitHub toont het maar één keer.

![GitHub - Personal Access Token aangemaakt, direct kopiëren](/images/podman-desktop-registries-configured.avif)

### Tokens invoeren in Podman Desktop

Gebruik bij Instellingen → Registries je gebruikersnaam en het PAT als wachtwoord voor zowel Docker Hub als GitHub. Na het opslaan zijn beide registries geauthenticeerd:

![Podman Desktop Registries - Docker Hub en GitHub gekoppeld via PATs](/images/podman-desktop-registries-configured.avif)

Daarna worden images van privérepositories op beide registries zonder problemen opgehaald.

---

## Images en containers beheren

De Images-weergave toont alle lokaal opgehaalde images met hun registry, grootte en architectuur:

![Podman Desktop Images-weergave - ghcr.io images in de lijst](/images/podman-desktop-images.avif)

Podman Desktop bevat ook standaard Kubernetes-ondersteuning via de kubectl-extensie, en ondersteunt Docker Compose-bestanden native via `podman compose`.
