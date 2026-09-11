---
title: "Development"
weight: 3
prev: docs/applications/productivity
next: docs/applications/gaming-media
---

### Git & GitHub CLI

{{< tabs >}}
{{< tab name="CachyOS" >}}

Both are available in CachyOS repositories:

```bash
sudo pacman -S git github-cli
```

Git is available in the core repo; GitHub CLI is in `cachyos-extra` or `extra`.

{{< /tab >}}
{{< tab name="Bazzite" >}}

`git` is already in the image. Install GitHub CLI via Homebrew (CLI tool rather than layering):

```bash
brew install gh
```

{{< /tab >}}
{{< /tabs >}}

After installing, authenticate GitHub CLI:

```bash
gh auth login
```

This opens a browser flow to connect your GitHub account.

### Visual Studio Code

Three package variants are available on Arch/CachyOS, which can be confusing — they have similar names but different purposes:

| Package | Source | What it is | Marketplace | Extension limits |
|---------|--------|-----------|-------------|------------------|
| `code` | CachyOS extra repo | Code - OSS: open-source build, no Microsoft branding or telemetry | Open VSX | Missing proprietary extensions |
| `vscodium` | CachyOS repo | Independent OSS build, same as Code - OSS, different marketplace | Open VSX | Missing proprietary extensions |
| `visual-studio-code-bin` | AUR | Official Microsoft binary, unchanged | Microsoft | Full access (Copilot, Remote SSH, etc.) |

**Key difference:** The package name `code` in the CachyOS/Arch repo is **not** Microsoft's build — it's the OSS variant. The actual Microsoft build is `visual-studio-code-bin` from the AUR.

#### Why the difference matters

**Code - OSS and VSCodium** miss Microsoft's proprietary extensions due to licensing:
- **GitHub Copilot** — Microsoft-exclusive AI assistant
- **Remote - SSH** — seamless remote development
- **Dev Containers / Remote - Containers** — containerized development environments
- **C/C++ Tools** — optimized C/C++ support
- **Pylance** — Python language server

If your workflow needs these (remote development, containers, specialized language tooling), the Microsoft build is the pragmatic choice.

**Settings Sync:** Microsoft build syncs directly via Microsoft/GitHub account. OSS builds need manual configuration with a third-party sync provider.

**Configuration:** Both OSS and Microsoft variants use the same config directory (`~/.config/Code`), so switching between packages preserves your settings and extensions.

{{< tabs >}}
{{< tab name="CachyOS" >}}

**Switch to the Microsoft build (recommended for full extension support):**

1. Remove the open-source variant:
   ```bash
   sudo pacman -R code
   ```

2. Install an AUR helper if not already present:
   ```bash
   sudo pacman -S paru
   ```

3. Install the Microsoft build:
   ```bash
   paru -S visual-studio-code-bin
   ```

This builds locally from a PKGBUILD (re-packaging the official binary, not source compilation). Paru displays the PKGBUILD for review before building — an important security advantage over helpers that skip this step.

**Staying on the open-source build:**

If you prefer the OSS variant, install `code` from the CachyOS extra repo or `vscodium` as an alternative:

```bash
sudo pacman -S code
# or
sudo pacman -S vscodium
```

Existing settings and extensions persist when you install the Microsoft build later, since both use the same config directory.

{{< /tab >}}
{{< tab name="Bazzite" >}}

**Microsoft build:**

```bash
flatpak install flathub com.visualstudio.code
```

**Open-source builds:**

- **Code - OSS:** `flatpak install flathub com.visualstudio.code.oss`
- **VSCodium:** `flatpak install flathub com.vscodium.codium`

{{< callout type="info" >}}
**Flatpak sandboxing note:** The Flatpak is sandboxed, which matters for an editor: extensions that run toolchains see the sandbox's filesystem, not yours. If you develop against tools installed on the host system, run VS Code from a distrobox container instead:

```bash
distrobox-export --app code
```

This runs VS Code with access to the tools of the host while keeping the container's isolation. It's the standard setup on atomic systems.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

### Kleopatra & GPG commit signing

I sign my Git commits and tags with a GPG key. Kleopatra makes generating and managing keys straightforward via a GUI instead of having to figure out the GPG command line. It's also useful to keep your GPG keys in one place and manage subkeys.

Install Kleopatra first, then create or import your keys there.

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

**Finding your key ID in Kleopatra:**

In Kleopatra, expand your key, right-click any subkey, and select "Copy fingerprint". The last 16 characters are your key ID.

**Configure Git to use it:**

```bash
git config --global user.name "Sten T."
git config --global user.email "your-email@example.com"
git config --global user.signingkey FB7273DE88E0E759
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.program gpg
```

Verify your configuration:

```bash
git config --global --list | grep -E "user.name|user.email|user.signingkey|commit.gpgsign"
```

**In VS Code:**

After configuring Git with GPG, commits signed in VS Code's source control UI automatically use your configured key. No additional setup needed in VS Code.

### Archi (ArchiMate modeling tool)

[Archi](https://www.archimatetool.com/) is a free ArchiMate modeling tool. The Linux package is a portable archive with no installer. To make it show up in GNOME with an icon, you have to place the files yourself and create a desktop entry manually.

{{< callout type="info" >}}
Archi's download page warns about possible UI issues on Wayland. In my experience it runs fine on GNOME 50 Wayland.
{{< /callout >}}

![Archi download page - Linux version with Wayland note](/images/archi-download.avif)

```bash
# Download and extract
cd /tmp
curl -L https://github.com/archimatetool/archi.io/releases/download/5.9.0/Archi-Linux64-5.9.0.tgz | tar -xz

# Move to /opt
sudo mv Archi-Linux64-5.9.0/Archi /opt/

# Cleanup
rm -rf Archi-Linux64-5.9.0
cd ~

# Create symlink so you can run 'archi' from the terminal
sudo ln -s /opt/Archi/Archi /usr/local/bin/archi
```

{{< callout type="info" >}}
**On Bazzite** the extraction and the symlink work unchanged: `/opt` and `/usr/local` are symlinks to `/var/opt` and `/var/usrlocal` on an atomic system, so both are writable and survive image updates. The desktop entry below is the exception, because `/usr/share/applications` is read-only. Put it in `~/.local/share/applications/archi.desktop` instead, without `sudo`.
{{< /callout >}}

Create a desktop entry so Archi shows up in GNOME:
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

Replace `__ICON__` with the actual path (it includes a build timestamp that changes per release):

```bash
find /opt/Archi/plugins -name "app-128.png" | head -1
```

After saving, Archi appears in the GNOME app launcher:

![Archi in the GNOME application launcher](/images/archi-launcher.avif)

![Archi running on Wayland with GNOME 50](/images/archi-running.avif)

### Podman & Podman Desktop

For container workloads I use Podman instead of Docker. Podman is daemonless, runs containers rootless by default, and ships a Docker-compatible CLI so existing workflows keep working. `podman-docker` replaces the `docker` package entirely.

{{< tabs >}}
{{< tab name="CachyOS" >}}

All three packages are available in the CachyOS repositories: [podman](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman), [podman-docker](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman-docker), [podman-desktop](https://packages.cachyos.org/package/extra/x86_64/podman-desktop).

```bash
sudo pacman -S podman podman-docker podman-desktop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

`podman` and `podman-docker` are already in the image; only Podman Desktop is missing:

```bash
flatpak install flathub io.podman_desktop.PodmanDesktop
```

{{< /tab >}}
{{< /tabs >}}

For the full setup (including registry configuration and connecting Docker Hub and GitHub), see [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}}) in the Virtualization section.
