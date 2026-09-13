---
title: "Touchpad-scrollsnelheid"
weight: 3
prev: docs/desktop/astra-monitor
next: docs/security/autologin
---

Sinds GNOME 50 is er nog steeds geen manier om de trackpad-scrollsnelheid op Linux native in te stellen. Niet in Instellingen, nergens. KDE Plasma heeft dit al jaren. De gemeenschap vraagt er al lang naar, met merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) en [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) die eigenlijk nergens heen gaan. Zie de [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) voor de complete geschiedenis.

Twee third-party tools vullen deze leemte. **wayland-scroll-factor** is de aanbevolen optie; **libinput-config** is het oudere systeemwijde alternatief dat moeilijker in te stellen is.

## wayland-scroll-factor (aanbevolen)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) van daniel-g-carrasco is een user-level tool die libinput-functieaanroepen in `gnome-shell` onderschept en een scrollvermenigvuldiger toepast. Geen root-toegang nodig; alles zit in je home directory.

**Installatie:**

```bash
git clone https://github.com/daniel-g-carrasco/wayland-scroll-factor.git
cd wayland-scroll-factor
meson setup build --prefix="$HOME/.local"
ninja -C build
meson install -C build
cd ..
rm -rf wayland-scroll-factor
```

{{< callout type="info" >}}
**Op Bazzite:** het resultaat belandt in `$HOME/.local`, wat prima is, maar de build heeft een toolchain en `libinput`-headers nodig, en de library die het produceert wordt voorgeladen in de *host's* `gnome-shell`. Bouw het in een Fedora distrobox van dezelfde release als je image, of laag de build-afhankelijkheden:

```bash
rpm-ostree install meson ninja-build gcc libinput-devel
systemctl reboot
```

Een container gebouwd tegen een ander Fedora-release kan een library produceren die `gnome-shell` weigert te laden.
{{< /callout >}}

**Configuratie:**

```bash
wsf set 0.2     # 1.0 = standaardsnelheid, lager = langzamer; ik gebruik 0.2
wsf enable      # vereist één logout/login om van kracht te worden
wsf status      # controleer of het actief is
```

Instellingen worden opgeslagen in `~/.config/wayland-scroll-factor/config`. Na de eerste `wsf enable` en opnieuw aanmelden, geeft `wsf set` live effect zonder een volgende logout.

Wanneer alles werkt, bevestigt `wsf status` dat de library in gnome-shell is ingespoten:

```
gnome-shell LD_PRELOAD: ~/.local/lib/wayland-scroll-factor/libwsf_preload.so (includes WSF)
gnome-shell library mapped: yes
runtime config reload: active (factor changes should apply live)
```

Als de status aangeeft dat het env-bestand aanwezig is, maar systemd het nog niet heeft opgepikt, voer dan `systemctl --user daemon-reexec` uit en log uit/in.

**Optionele GUI** (`wsf-gui`, vereist libadwaita ≥ 1.4):

```bash
wsf-gui
```

Laat je verticale en horizontale scrollsnelheid apart aanpassen, naast pinch zoom en pinch rotate. De System integration-toggle mappt naar `wsf enable`/`wsf disable`.

![Wayland Scroll Factor GUI met scrollgevoeligheidsschuivers](/images/wayland-scroll-factor-gui.avif)

**Terugrollen:**

```bash
wsf disable
```

## libinput-config (alternatief)

[libinput-config](https://github.com/lz42/libinput-config) van lz42 is een systeemwijde workaround die source-compilatie en root-toegang vereist. Gebruik dit als wayland-scroll-factor niet voor je setup werkt.

{{< callout type="warning" >}}
**Alleen CachyOS.** Dit installeert in `/usr`, wat read-only is op Bazzite. Daar is geen nette manier voor. Gebruik wayland-scroll-factor hierboven, die in je home directory blijft.
{{< /callout >}}

**Installatie (eenmalig):**

```bash
sudo pacman -S meson ninja libinput git

git clone https://github.com/lz42/libinput-config.git
cd libinput-config
meson setup build
ninja -C build
sudo ninja -C build install
cd ..
rm -rf libinput-config
```

**Configuratie:**

```bash
sudo tee /etc/libinput.conf >/dev/null << 'EOF'
override-compositor=enabled
scroll-factor=0.25
discrete-scroll-factor=1.0
EOF
```

Log uit en weer in, pas dan `scroll-factor` naar je voorkeur aan.

**Terugrollen:**

```bash
sudo rm /etc/libinput.conf
```
