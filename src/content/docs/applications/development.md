---
title: "Development"
weight: 3
prev: docs/applications/productivity
next: docs/applications/gaming-media
---

### Git & GitHub CLI

Install both version control and GitHub's command-line interface to manage repositories, PRs, and issues from the terminal.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Both are in CachyOS repositories:

```bash
sudo pacman -S git github-cli
```

- `git` is in the core repo (usually pre-installed)
- `github-cli` is in `cachyos-extra` or `extra`

{{< /tab >}}
{{< tab name="Bazzite" >}}

`git` is already in the image. For GitHub CLI, use Homebrew (CLI tool, no layering needed):

```bash
brew install gh
```

{{< /tab >}}
{{< /tabs >}}

**Authenticate with GitHub:**

After installing, log in to your GitHub account:

```bash
gh auth login
```

This opens a browser-based authentication flow. You'll be asked:
1. What account type (GitHub.com or GitHub Enterprise)
2. Whether to use HTTPS or SSH
3. Whether to authenticate `git` with your GitHub credentials

Choose **HTTPS** for simplicity (GitHub CLI handles credentials via `git credential helper`). If you already use SSH keys, SSH also works fine.

**Verify setup:**

```bash
gh auth status
```

Shows your authenticated account and which protocol is configured.

**Common `gh` commands:**

- `gh repo create` — create a new repository
- `gh pr list` — list pull requests
- `gh pr view <number>` — view a specific PR
- `gh pr checkout <number>` — check out a PR branch locally
- `gh issue list` — list open issues
- `gh issue create` — create a new issue
- `gh release create <tag>` — create a release

For full reference, run `gh --help` or visit [cli.github.com](https://cli.github.com).

### Visual Studio Code

Three package variants are available on Arch/CachyOS — they have similar names but fundamentally different purposes:

| Package | Source | What it is | Marketplace | Key difference |
|---------|--------|-----------|-------------|------------------|
| `code` | CachyOS extra repo | Code - OSS: open-source build from VS Code source | Open VSX | Microsoft branding and telemetry removed |
| `vscodium` | CachyOS repo | Independent OSS build, same source, different foundation | Open VSX | Community alternative to Code - OSS |
| `visual-studio-code-bin` | AUR | Official Microsoft binary, unmodified | Microsoft | Full proprietary extensions, Settings Sync via Microsoft account |

**Critical: Package name doesn't mean Microsoft.** The default `code` package in CachyOS/Arch repos is **not** Microsoft's build—it's the open-source variant. To get Microsoft's official build with full marketplace access, you need `visual-studio-code-bin` from the AUR.

#### Why the difference matters

**Missing proprietary extensions in Code - OSS and VSCodium:**

Microsoft's licensing terms prohibit the inclusion of proprietary extensions in open-source builds. These extensions are only available in the official Microsoft Marketplace:

- **GitHub Copilot** — AI-powered code completion (Microsoft-exclusive)
- **Remote - SSH** — develop on remote machines as if local
- **Dev Containers / Remote - Containers** — seamless containerized development
- **C/C++ Tools** — Microsoft's optimized C/C++ language support
- **Pylance** — Python language server with type hints and intelligent completions

If your workflow relies on any of these—especially remote development, containerized environments, or language-specific tooling—the Microsoft build is the pragmatic choice.

**Settings Sync:**
- **Microsoft build:** Syncs via Microsoft/GitHub account, cross-device sync works out of the box
- **OSS builds:** Settings Sync unavailable; requires manual configuration with third-party services

**Portable config:** Both OSS and Microsoft variants read `~/.config/Code`, so you can switch between packages and keep your settings and extensions intact.

#### Installation & Switching

{{< tabs >}}
{{< tab name="CachyOS" >}}

**Install the Microsoft build (recommended for full feature parity):**

1. If you have the OSS build installed, remove it:
   ```bash
   sudo pacman -R code
   ```

2. Ensure you have an AUR helper. CachyOS usually ships with `paru` pre-installed:
   ```bash
   sudo pacman -Syu paru
   ```

3. Install from AUR:
   ```bash
   paru -S visual-studio-code-bin
   ```

This downloads and re-packages the official Microsoft binary locally. Paru shows the PKGBUILD for review before building—a security advantage over helpers that skip this step.

**Or stay with the open-source variant:**

```bash
sudo pacman -S code       # Code - OSS from CachyOS extra
# or
sudo pacman -S vscodium   # VSCodium from CachyOS repo
```

Both keep your existing settings when you later switch to the Microsoft build.

{{< /tab >}}
{{< tab name="Bazzite" >}}

**Install Microsoft's build:**

```bash
flatpak install flathub com.visualstudio.code
```

**Or choose an open-source build:**

```bash
flatpak install flathub com.visualstudio.code.oss    # Code - OSS
flatpak install flathub com.vscodium.codium          # VSCodium
```

{{< callout type="info" >}}
**Flatpak sandboxing:** The Flatpak sandbox restricts what extensions can access. Extensions that invoke external toolchains (compilers, linters, language servers on your host) see only the sandbox's filesystem, not yours.

**Workaround on Bazzite:** Run VS Code from a distrobox container instead:

```bash
distrobox-export --app code
```

This gives extensions access to host tools while maintaining the container's isolation. It's the standard pattern on atomic systems.
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
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.program gpg
```

Replace `YOUR_GPG_KEY_ID` with the 16-character hex ID from your key's fingerprint.

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
