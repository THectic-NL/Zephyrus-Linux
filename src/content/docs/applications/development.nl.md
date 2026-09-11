---
title: "Development"
weight: 3
prev: docs/applications/productivity
next: docs/applications/gaming-media
---

### Git & GitHub CLI

Installeer zowel versiebeheer als GitHub's command-line interface om repositories, PR's en issues vanuit de terminal te beheren.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Beide zijn in CachyOS-repositories:

```bash
sudo pacman -S git github-cli
```

- `git` is in de core repo (meestal pre-geïnstalleerd)
- `github-cli` is in `cachyos-extra` of `extra`

{{< /tab >}}
{{< tab name="Bazzite" >}}

`git` zit al in de image. Voor GitHub CLI gebruik je Homebrew (CLI-tool, geen layering nodig):

```bash
brew install gh
```

{{< /tab >}}
{{< /tabs >}}

**Authenticeer je bij GitHub:**

Na installatie log je in op je GitHub-account:

```bash
gh auth login
```

Dit opent een browser-gebaseerde authenticatiestroom. Je wordt gevraagd:
1. Welk accounttype (GitHub.com of GitHub Enterprise)
2. Of je HTTPS of SSH wilt gebruiken
3. Of je `git` wilt authenticeren met je GitHub-credentials

Kies **HTTPS** voor eenvoud (GitHub CLI handelt credentials af via `git credential helper`). Als je al SSH-sleutels gebruikt, werkt SSH ook prima.

**Controleer setup:**

```bash
gh auth status
```

Toont je geverifieerde account en welk protocol is geconfigureerd.

**Veel voorkomende `gh` commando's:**

- `gh repo create` — create een nieuwe repository
- `gh pr list` — list pull requests
- `gh pr view <number>` — bekijk een specifieke PR
- `gh pr checkout <number>` — check out een PR-branch lokaal
- `gh issue list` — list open issues
- `gh issue create` — create een nieuwe issue
- `gh release create <tag>` — create een release

Voor volledig referentie, voer `gh --help` uit of bezoek [cli.github.com](https://cli.github.com).

### Visual Studio Code

Er zijn drie package-varianten beschikbaar op Arch/CachyOS — ze hebben vergelijkbare namen maar fundamenteel verschillende doeleinden:

| Package | Bron | Wat het is | Marketplace | Belangrijk verschil |
|---------|------|-----------|-------------|----------------------|
| `code` | CachyOS extra-repo | Code - OSS: open-source build van VS Code source | Open VSX | Microsoft branding en telemetrie verwijderd |
| `vscodium` | CachyOS-repo | Onafhankelijke OSS-build, zelfde source, ander fundament | Open VSX | Community-alternatief voor Code - OSS |
| `visual-studio-code-bin` | AUR | Officiële Microsoft-binary, ongewijzigd | Microsoft | Volledige proprietary extensies, Settings Sync via Microsoft-account |

**Kritiek: Packagenaam betekent niet Microsoft.** De standaard `code` package in CachyOS/Arch repos is **niet** de Microsoft-build—het is de open-source variant. Voor Microsoft's officiële build met volledige marketplace-toegang heb je `visual-studio-code-bin` uit de AUR nodig.

#### Waarom het verschil ertoe doet

**Ontbrekende proprietary extensies in Code - OSS en VSCodium:**

Microsoft's licentievoorwaarden verbieden de opname van proprietary extensies in open-source builds. Deze extensies zijn alleen beschikbaar in de officiële Microsoft Marketplace:

- **GitHub Copilot** — AI-aangedreven code completion (Microsoft-exclusief)
- **Remote - SSH** — op afstand machines ontwikkelen alsof ze lokaal zijn
- **Dev Containers / Remote - Containers** — naadloze containergebaseerde ontwikkeling
- **C/C++ Tools** — Microsoft's geoptimaliseerde C/C++-ondersteuning
- **Pylance** — Python language server met type hints en intelligente aanvullingen

Als je workflow afhankelijk is van deze—vooral remote development, containerized omgevingen of taalspecifieke tooling—is de Microsoft-build de pragmatische keus.

**Settings Sync:**
- **Microsoft-build:** Synchroniseert via Microsoft/GitHub-account, cross-device sync werkt out of the box
- **OSS-builds:** Settings Sync niet beschikbaar; vereist handmatige configuratie met third-party services

**Draagbare config:** Zowel OSS als Microsoft-variant lezen `~/.config/Code`, dus je kunt wisselen tussen packages en je instellingen en extensies behouden.

#### Installatie & Wisselen

{{< tabs >}}
{{< tab name="CachyOS" >}}

**Installeer de Microsoft-build (aanbevolen voor volledige feature-pariteit):**

1. Als je de OSS-build hebt, verwijder deze:
   ```bash
   sudo pacman -R code
   ```

2. Zorg dat je een AUR-helper hebt. CachyOS levert meestal `paru` pre-geïnstalleerd:
   ```bash
   sudo pacman -Syu paru
   ```

3. Installeer vanuit de AUR:
   ```bash
   paru -S visual-studio-code-bin
   ```

Dit downloadt en herpackages het officiële Microsoft-binary lokaal. Paru toont de PKGBUILD ter review voor het bouwen—een voordeel op het gebied van beveiliging ten opzichte van helpers die deze stap overslaan.

**Of blijf bij de open-source variant:**

```bash
sudo pacman -S code       # Code - OSS uit CachyOS extra
# of
sudo pacman -S vscodium   # VSCodium uit CachyOS repo
```

Beide behouden je bestaande instellingen als je later naar de Microsoft-build overschakelt.

{{< /tab >}}
{{< tab name="Bazzite" >}}

**Installeer Microsoft's build:**

```bash
flatpak install flathub com.visualstudio.code
```

**Of kies een open-source build:**

```bash
flatpak install flathub com.visualstudio.code.oss    # Code - OSS
flatpak install flathub com.vscodium.codium          # VSCodium
```

{{< callout type="info" >}}
**Flatpak sandboxing:** De Flatpak sandbox beperkt wat extensies kunnen benaderen. Extensies die externe toolchains aanroepen (compilers, linters, language servers op je host) zien alleen het bestandssysteem van de sandbox, niet dat van jou.

**Workaround op Bazzite:** Voer VS Code uit vanuit een distrobox-container:

```bash
distrobox-export --app code
```

Dit geeft extensies toegang tot host-tools terwijl de isolatie van de container behouden blijft. Dit is het standaardpatroon op atomic systemen.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

### Kleopatra & GPG commit signing

Ik onderteken mijn Git commits en tags met een GPG-sleutel. Kleopatra maakt het aanmaken en beheren van sleutels makkelijk via een GUI. Het is ook handig om je GPG-sleutels op één plek te houden en subsleutels te beheren.

Installeer Kleopatra eerst, maak dan je sleutels daarin aan of importeer ze.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S kleopatra
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.kde.kleopatra
```

{{< /tab >}}
{{< /tabs >}}

**Je sleutel-ID vinden in Kleopatra:**

In Kleopatra, vouw je sleutel uit, klik rechts op een subsleutel en selecteer "Copy fingerprint". De laatste 16 tekens zijn je sleutel-ID.

**Configureer Git om het te gebruiken:**

```bash
git config --global user.name "Sten T."
git config --global user.email "your-email@example.com"
git config --global user.signingkey FB7273DE88E0E759
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.program gpg
```

Controleer je configuratie:

```bash
git config --global --list | grep -E "user.name|user.email|user.signingkey|commit.gpgsign"
```

**In VS Code:**

Na Git-configuratie met GPG ondertekenen commits in VS Code's source control UI automatisch je geconfigureerde sleutel. Geen aanvullende instelling nodig in VS Code.

### Archi (ArchiMate modeling tool)

[Archi](https://www.archimatetool.com/) is een gratis ArchiMate modeling tool. Het Linux package is een draagbare archive zonder installer. Om het in GNOME met een icoon te laten zien, moet je de bestanden zelf plaatsen en handmatig een desktop entry creëren.

{{< callout type="info" >}}
Archi's download pagina waarschuwt voor mogelijke UI-problemen op Wayland. In mijn ervaring draait het prima op GNOME 50 Wayland.
{{< /callout >}}

![Archi download pagina - Linux versie met Wayland notitie](/images/archi-download.avif)

```bash
# Download en extract
cd /tmp
curl -L https://github.com/archimatetool/archi.io/releases/download/5.9.0/Archi-Linux64-5.9.0.tgz | tar -xz

# Verplaats naar /opt
sudo mv Archi-Linux64-5.9.0/Archi /opt/

# Cleanup
rm -rf Archi-Linux64-5.9.0
cd ~

# Maak symlink zodat je 'archi' kunt aanroepen vanuit de terminal
sudo ln -s /opt/Archi/Archi /usr/local/bin/archi
```

{{< callout type="info" >}}
**Op Bazzite** de extractie en symlink werken ongewijzigd: `/opt` en `/usr/local` zijn symlinks naar `/var/opt` en `/var/usrlocal` op een atomic systeem, dus beide zijn beschrijfbaar en overleven image updates. De desktop entry hieronder is de uitzondering, omdat `/usr/share/applications` read-only is. Plaats hem in `~/.local/share/applications/archi.desktop` in plaats daarvan, zonder `sudo`.
{{< /callout >}}

Maak een desktop entry zodat Archi in GNOME verschijnt:
```bash
sudo nano /usr/share/applications/archi.desktop
```

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Archi
Comment=ArchiMate Modelling Tool
Exec=/opt/Archi/Archi
Icon=__ICON__
Terminal=false
Categories=Development;IDE;
StartupWMClass=Archi
```

Vervang `__ICON__` met het werkelijke pad (het bevat een build-timestamp die per release verandert):

```bash
find /opt/Archi/plugins -name "app-128.png" | head -1
```

Na opslaan verschijnt Archi in de GNOME app launcher:

![Archi in de GNOME application launcher](/images/archi-launcher.avif)

![Archi draait op Wayland met GNOME 50](/images/archi-running.avif)

### Podman & Podman Desktop

Voor container workloads gebruik ik Podman in plaats van Docker. Podman is daemonless, draait containers rootless standaard, en levert een Docker-compatibele CLI zodat bestaande workflows blijven werken. `podman-docker` vervangt het `docker` package volledig.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Alle drie de packages zijn beschikbaar in de CachyOS repositories: [podman](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman), [podman-docker](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman-docker), [podman-desktop](https://packages.cachyos.org/package/extra/x86_64/podman-desktop).

```bash
sudo pacman -S podman podman-docker podman-desktop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

`podman` en `podman-docker` zitten al in de image; alleen Podman Desktop ontbreekt:

```bash
flatpak install flathub io.podman_desktop.PodmanDesktop
```

{{< /tab >}}
{{< /tabs >}}

Voor de volledige setup (inclusief registry-configuratie en verbinding met Docker Hub en GitHub), zie [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}}) in de Virtualization sectie.
