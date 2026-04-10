# Zephyrus-Linux

English | [Nederlands](README.nl.md)

CachyOS on the ASUS ROG Zephyrus G16 GA605WV (2024). My personal setup log: documenting what worked, what didn't, and how I fixed it.

**Browse the full documentation site: [zephyrus-linux.stensel.nl](https://zephyrus-linux.stensel.nl/)**


## System information

```
❯ fish
					 .-------------------------:                    sten@Sten-Laptop
					.+=========================.                    ----------------
				 :++===++==================-       :++-           OS: CachyOS x86_64
				:*++====+++++=============-        .==:           Host: ROG Zephyrus G16 GA605WV_GA605WV (1.0)
			 -*+++=====+***++==========:                        Kernel: Linux 6.19.11-1-cachyos
			=*++++========------------:                         Uptime: 3 hours, 49 mins
		 =*+++++=====-                     ...                Packages: 1695 (pacman), 22 (flatpak)
	 .+*+++++=-===:                    .=+++=:              Shell: fish 4.6.0
	:++++=====-==:                     -*****+              Display (LQ160R1JW02): 2560x1600 @ 1.33x in 16", 240 Hz [Built-in]
 :++========-=.                      .=+**+.              DE: GNOME 50.0
.+==========-.                          .                 WM: Mutter (Wayland)
 :+++++++====-                                .--==-.     WM Theme: Adwaita
	:++==========.                             :+++++++:    Theme: Adwaita [GTK2/3/4]
	 .-===========.                            =*****+*+    Icons: Adwaita [GTK2/3/4]
		.-===========:                           .+*****+:    Font: Adwaita Sans (11pt) [GTK2/3/4]
			-=======++++:::::::::::::::::::::::::-:  .---:      Cursor: Adwaita (24px)
			 :======++++====+++******************=.             Terminal: GNOME Console 50.0
				:=====+++==========++++++++++++++*-               Terminal Font: Adwaita Mono (11pt)
				 .====++==============++++++++++*-                CPU: AMD Ryzen AI 9 HX 370 (24) @ 5.16 GHz
					.===+==================+++++++:                 GPU 1: AMD Radeon 890M Graphics [Integrated]
					 .-=======================+++:                  GPU 2: NVIDIA GeForce RTX 4060 Max-Q / Mobile [Discrete]
						 ..........................                   Memory: 10.24 GiB / 28.98 GiB (35%)
																													Swap: 1.28 MiB / 28.98 GiB (0%)
																													Disk (/): 270.70 GiB / 951.85 GiB (28%) - btrfs
																													Local IP (wlan0): 192.168.0.72/24
																													Battery (A32-K55): 100% [AC Connected]
																													Locale: en_US.UTF-8

                                                                                  
                                                                                  
~
❯ 
```


## About this project

This is my personal setup log for running CachyOS on this laptop. I'm not a software engineer or developer: just someone who switched to Linux and ran into a lot of things that didn't work out of the box. I figured I'd write it all down so others don't have to go through the same trial and error I did.

I'm still actively testing and experimenting: things may change, break, or turn out to be wrong. Everything here is based on my own experience and should be taken as-is, at your own risk.

I am not affiliated with, endorsed by, or acting on behalf of ASUS, NVIDIA, Microsoft, CachyOS, or any other company or project mentioned here.

![System information overview](static/images/system-info.avif)


## Building the site locally

This documentation site is built with [Hugo](https://gohugo.io/) using the [Hextra](https://imfing.github.io/hextra/) theme. The theme is managed as a Hugo module (via Go modules, no git submodules).

**Prerequisites:**
- [Hugo extended](https://gohugo.io/installation/) v0.157.0 (built with this version)
- [Go](https://go.dev/dl/) (required for Hugo modules)
- Git

On Arch Linux / CachyOS:
```bash
sudo pacman -S hugo go
```

**Clone the repository:**
```bash
git clone https://github.com/Stensel8/Zephyrus-Linux.git
cd Zephyrus-Linux
```

Hugo automatically downloads the theme module on first run.

**Run the development server:**
```bash
hugo server
```

The site is available at `http://localhost:1313/`. Hugo watches for file changes and reloads automatically.

**Build for production:**
```bash
hugo --gc --minify
```

The output is written to `./public/`. On push to `main`, GitHub Actions builds and deploys to GitHub Pages automatically.


## Image assets

All images in this repository use the [AVIF](https://en.wikipedia.org/wiki/AVIF) format: open, royalty-free, and more efficient than PNG or JPEG at equivalent quality. AVIF is the modern standard for web images.

To convert PNG screenshots to AVIF, install `avifenc` from the `libavif` package:

```bash
sudo pacman -S libavif
```

Batch convert all PNGs in `static/images/` (converts and removes originals):

```bash
cd static/images
for f in *.png; do avifenc -q 80 -s 6 "$f" "${f%.png}.avif" && rm "$f"; done
```

- `-q 80`: 80% quality (0–100 scale, 100 = lossless)
- `-s 6`: encoder speed (0 = best compression, 10 = fastest)


## Credits & resources

This project wouldn't exist without the work of these people and communities:

- **[ASUS Linux community](https://asus-linux.org/)**: The project behind `asusctl` and `rog-control-center`. Luke Jones has been a major driving force, but numerous contributors have submitted kernel patches, many of which are now merged into mainline Linux, making modern ASUS ROG laptops genuinely usable on Linux.
- **[CachyOS](https://cachyos.org/)**: The distribution powering this setup. CachyOS is an Arch-based distro with extensive hardware-specific optimizations: an improved scheduler (BORE/EEVDF), better power management, dynamic refresh rate support, and built-in drivers for both the AMD iGPU and NVIDIA dGPU, including integrated GPU switching. Of all the distributions I tested (including Fedora, which came close), CachyOS is by far the strongest on this device.
- **[Foxboron/sbctl](https://github.com/Foxboron/sbctl)**: Secure Boot key management tool used to enroll custom keys and sign the kernel and EFI binaries. Essential for keeping Secure Boot enabled with a custom kernel.
- **[sched-ext / scx_lavd](https://github.com/sched-ext/scx)**: The Linux scheduler extensibility framework powering the `scx_lavd` CPU scheduler. Excellent latency and responsiveness for desktop and gaming workloads.
- **[lz42/libinput-config](https://github.com/lz42/libinput-config)**: Kernel-level workaround for GNOME/Wayland's missing scroll speed setting, intercepting libinput events before they reach the compositor.
- **[Yubico/pam-u2f](https://github.com/Yubico/pam-u2f)**: PAM module enabling FIDO2/WebAuthn hardware token authentication for sudo and the lock screen. Used alongside `systemd-cryptenroll` for full-disk encryption unlock via YubiKey.
- **[Looking Glass](https://looking-glass.io/)**: Low-latency GPU passthrough display project. Didn't work on this hardware, but the project and documentation are excellent.
- **[Hugo](https://gohugo.io/)**: The static site generator used to build the documentation site.
- **[Hextra](https://imfing.github.io/hextra/)**: The Hugo theme powering the documentation site.


## License

This project is licensed under the [MIT License](LICENSE).
