# Zephyrus-Linux

English | [Nederlands](README.nl.md)

Linux on the ASUS ROG Zephyrus G16 GA605WV (2024). My personal setup log for the two distributions I run on it, CachyOS and Bazzite: what worked, what didn't, and how I fixed it.

**Browse the full documentation site: [zephyrus-linux.thectic.nl](https://zephyrus-linux.thectic.nl/)**


## About this project

This is my personal setup log for this laptop. I'm not a developer, just someone who switched to Linux and ran into a lot of things that didn't work out of the box. I wrote it all down so others don't have to go through the same trial and error.

The guides cover CachyOS (Arch) and Bazzite (Fedora Atomic). I've daily-driven both and switch between them; I'm on Bazzite at the moment. The site's [Getting Started](https://zephyrus-linux.thectic.nl/docs/) page explains the choice, and a switcher at the top of every page moves between the two sets of guides.

I'm still actively testing and experimenting: things may change, break, or turn out to be wrong. Everything here is based on my own experience and should be taken as-is, at your own risk.

I am not affiliated with, endorsed by, or acting on behalf of ASUS, NVIDIA, Microsoft, CachyOS, Universal Blue, or any other company or project mentioned here.

![System information overview](src/static/images/system-info.avif)


## Building the site locally

This documentation site is built with [Hugo](https://gohugo.io/) using the [Hextra](https://imfing.github.io/hextra/) theme. The theme is managed as a Hugo module (via Go modules, no git submodules).

**Prerequisites:**
- [Hugo extended](https://gohugo.io/installation/) v0.160.0 (or greater)
- [Go](https://go.dev/dl/) (required for Hugo modules)
- Git
- VS Code

On Arch Linux / CachyOS:
```bash
sudo pacman -S hugo go
```

**Clone the repository:**
```bash
git clone https://github.com/THectic-NL/Zephyrus-Linux.git
cd Zephyrus-Linux
```

Hugo automatically downloads the theme module on first run.

**Run the development server:**
```bash
cd src
hugo server
```

The site is available at `http://localhost:1313/`. Hugo watches for file changes and reloads automatically.

**Build for production:**
```bash
cd src
hugo --gc --minify
```

The output is written to `./src/public/`. On push to `main`, GitHub Actions builds the site and deploys it to Bunny.net (Storage zone + Pull Zone) at [zephyrus-linux.thectic.nl](https://zephyrus-linux.thectic.nl/).


## Image assets

All images in this repository use the [AVIF](https://en.wikipedia.org/wiki/AVIF) format: open, royalty-free, and more efficient than PNG or JPEG at equivalent quality. AVIF is the modern standard for web images.

To convert PNG screenshots to AVIF, install `avifenc` from the `libavif` package:

```bash
sudo pacman -S libavif
```

Batch convert all PNGs in `src/static/images/` (converts and removes originals):

```bash
cd src/static/images
for f in *.png; do avifenc -q 80 -s 6 "$f" "${f%.png}.avif" && rm "$f"; done
```

- `-q 80`: 80% quality (0-100 scale, 100 = lossless)
- `-s 6`: encoder speed (0 = best compression, 10 = fastest)


## Credits & resources

This project wouldn't exist without the work of these people and communities:

- **[ASUS Linux community](https://asus-linux.org/)**: The project behind `asusctl` and `rog-control-center`, now maintained under the [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl). Luke Jones has been a major driving force, and numerous contributors have submitted kernel patches, many of which are now merged into mainline Linux, making modern ASUS ROG laptops genuinely usable on Linux.
- **[CachyOS](https://cachyos.org/)**: An Arch-based distribution with extensive hardware-specific tuning: an improved scheduler (BORE/EEVDF), better power management, dynamic refresh rate support, and built-in drivers for both the AMD iGPU and NVIDIA dGPU, including integrated GPU switching. One of the two distributions these guides cover.
- **[Bazzite / Universal Blue](https://universal-blue.org/)**: The people who make the atomic Fedora images this laptop runs well on, and who have contributed many of the patches that make it perform better. The other distribution these guides cover.
- **[Foxboron/sbctl](https://github.com/Foxboron/sbctl)**: Secure Boot key management tool used to enroll custom keys and sign the kernel and EFI binaries. Essential for keeping Secure Boot enabled with a custom kernel.
- **[sched-ext / scx_lavd](https://github.com/sched-ext/scx)**: The Linux scheduler extensibility framework powering the `scx_lavd` CPU scheduler. Excellent latency and responsiveness for desktop and gaming workloads.
- **[lz42/libinput-config](https://github.com/lz42/libinput-config)**: Kernel-level workaround for GNOME/Wayland's missing scroll speed setting, intercepting libinput events before they reach the compositor.
- **[Yubico/pam-u2f](https://github.com/Yubico/pam-u2f)**: PAM module enabling FIDO2/WebAuthn hardware token authentication for sudo and the lock screen. Used alongside `systemd-cryptenroll` for full-disk encryption unlock via YubiKey.
- **[Looking Glass](https://looking-glass.io/)**: Low-latency GPU passthrough display project. Didn't work on this hardware, but the project and documentation are excellent.
- **[Hugo](https://gohugo.io/)**: The static site generator used to build the documentation site.
- **[Hextra](https://imfing.github.io/hextra/)**: The Hugo theme powering the documentation site.


## License

This project is licensed under the [MIT License](LICENSE).
