---
title: "Touchpad-scrollsnelheid"
weight: 3
prev: docs/desktop/astra-monitor
next: docs/security/autologin
---

Sinds GNOME 50 is er nog steeds geen manier om de trackpad-scrollsnelheid op Linux native in te stellen. Niet in Instellingen, nergens. KDE Plasma heeft dit al jaren. De gemeenschap vraagt er al lang naar, met merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) en [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) die eigenlijk nergens heen gaan. Zie de [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) voor de complete geschiedenis.

Twee third-party tools vullen deze leemte. **wayland-scroll-factor** is de aanbevolen optie; **libinput-config** is het oudere systeemwijde alternatief dat moeilijker in te stellen is.

## wayland-scroll-factor (aanbevolen)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) van daniel-g-carrasco onderschept libinput-functieaanroepen in `gnome-shell` en past een scrollvermenigvuldiger toe. Hij heeft nu een eigen package voor beide distributies, dus zelf bouwen is niet meer de makkelijkste manier om hem aan de praat te krijgen.

**Installatie:**

{{< tabs >}}
{{< tab name="CachyOS" >}}

Vanuit de AUR:

```bash
paru -S wayland-scroll-factor
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Via de eigen COPR-repo van het project, gelaagd met `rpm-ostree`:

```bash
sudo curl -fsSL -o /etc/yum.repos.d/daniel-g-carrasco-wayland-scroll-factor.repo \
  "https://copr.fedorainfracloud.org/coprs/daniel-g-carrasco/wayland-scroll-factor/repo/fedora-$(rpm -E %fedora)/daniel-g-carrasco-wayland-scroll-factor-fedora-$(rpm -E %fedora).repo"
sudo rpm-ostree refresh-md
sudo rpm-ostree install wayland-scroll-factor
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

{{< callout type="info" >}}
Zelf bouwen kan nog steeds, voor de `-git`-build (`paru -S wayland-scroll-factor-git` op CachyOS) of op een distributie zonder package. Daarvoor heb je een C-compiler, `meson`, `ninja` en `pkgconf` nodig, die op geen van beide distributies hier standaard geïnstalleerd zijn. De eigen [dependencies](https://github.com/daniel-g-carrasco/wayland-scroll-factor/blob/main/docs/dependencies.md)- en [install](https://github.com/daniel-g-carrasco/wayland-scroll-factor/blob/main/docs/install.md)-docs van het project hebben de exacte packagenamen en buildstappen.
{{< /callout >}}

**Configuratie:**

```bash
wsf set 0.2     # 1.0 = standaardsnelheid, lager = langzamer; ik gebruik 0.2
wsf enable      # vereist één logout/login om van kracht te worden
wsf status      # controleer of het actief is
```

`wsf set 0.2` regelt de scrollgevoeligheid. Pinch zoom en pinch rotate hebben hun eigen factor, apart bij te stellen met `wsf set --pinch-zoom` en `wsf set --pinch-rotate` als de standaard niet bevalt.

Instellingen worden opgeslagen in `~/.config/wayland-scroll-factor/config`. Na de eerste `wsf enable` en opnieuw aanmelden, geeft `wsf set` live effect zonder een volgende logout.

`wsf status` laat zien of de preload-library daadwerkelijk in `gnome-shell` is geladen. Waar die naar wijst hangt af van hoe je hem installeerde: `/usr/lib/wayland-scroll-factor/` bij de package, `~/.local/lib/wayland-scroll-factor/` als je hem zelf bouwde. Pikt hij het na een logout/login nog steeds niet op, draai dan `wsf doctor` voor een diagnose en `wsf repair` als die een verouderde preload-instelling meldt, en log daarna nog een keer uit en in.

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
**Alleen CachyOS.** Dit installeert in `/usr`, wat read-only is op Bazzite. Daar is geen nette manier voor. Gebruik wayland-scroll-factor hierboven, die op beide distributies een werkende installatieroute heeft.
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
