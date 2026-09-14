---
title: "MT7925 Wi-Fi Performance"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

The G16 GA605WV ships a MediaTek Wi-Fi 7 MT7925 card. Dropped connections, sluggish mesh roaming, or download speeds well below what the connection should give: this page covers all three.

This is a script that applies three fixes at once (NetworkManager power saving, PCIe ASPM, and a wireless-stack queue limit), each with a real effect measured on this hardware, plus an optional extra (Bluetooth off) you can opt into. It needs Python 3.14+ (standard library only) and `pkexec` for the privileged steps -- one password prompt per command, covering every privileged step in that command, not one prompt per step.

{{< callout type="info" >}}
**Verified on this hardware.** Tested with `iperf3` against a local server on a 2.5GbE UniFi network. Stock: ~300 Mbit/s. Tuned: 500-608 Mbit/s, usually 560+. Your numbers will vary with AP, signal strength, and kernel version, but the fixes themselves are confirmed, not theoretical.

Test conditions, since they affect the numbers: a UniFi U7 Pro access point, in a wooden cabinet, roughly 10 meters from the laptop with a wall in between. 6GHz band, 160MHz channel (this card's max), signal ranging -62 to -71 dBm across runs, mostly -63 to -66 dBm. That's a realistic everyday distance, not a best-case same-room test, so treat the numbers above as a reasonable baseline rather than a ceiling.
{{< /callout >}}

{{< callout type="warning" >}}
**Is this still worth doing?** Yes, for now -- every fix below has a measured, reproducible effect and costs nothing but a reboot. But don't mistake it for having fixed the card. These are workarounds for driver defaults that shouldn't have needed tuning in the first place, not a rewrite of what the silicon can do. Set against a two-year-old phone's Wi-Fi chip (see [Results](#results) below), the honest summary is that the MT7925 itself is a mediocre Wi-Fi 7 part, and no amount of tuning changes that. The upside: this isn't a dead end. MediaTek's Wi-Fi 7 stack is still under active upstream development, with patches landing as recently as this page's own testing window -- see [References](#references) below. If you'd rather wait for the driver to mature than tune it by hand, that's a reasonable call too.
{{< /callout >}}

## Setup

{{% steps %}}

### Download and verify

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.py
echo "cf5aa114d872c6480525b55f637fab346337f9cbbdce9657e0688fd48cac1247  mt7925-tune.py" | sha256sum -c
```

### Apply

```bash
python3 mt7925-tune.py enable
```

Reboot afterward. One of the three fixes (PCIe ASPM) is a kernel module parameter, only read at module load time.

Want the optional Bluetooth-off extra too (see the table below)?

```bash
python3 mt7925-tune.py enable --bluetooth-off
```

{{% /steps %}}

Source: [mt7925-tune.py](/scripts/mt7925-tune.py). SHA-256 `cf5aa114d872c6480525b55f637fab346337f9cbbdce9657e0688fd48cac1247`.

| Fix (applied by `enable`) | What it does |
|---|---|
| Disable NetworkManager's Wi-Fi power saving | The most common cause of drops and slow mesh roaming |
| Disable PCIe ASPM for the card | The PCIe link's own power state, not the radio. The main throughput fix |
| Raise the AQL Best Effort queue limit | `mac80211` caps how much data can be queued per traffic class to keep latency low under contention. The stock limit favors fairness over saturating a single stream. Trade-off: less headroom for latency-sensitive traffic (calls, gaming) sharing the radio under load |

| Optional extra (`--bluetooth-off`, not applied by default) | What it does |
|---|---|
| Bluetooth off | The MT7925 is a combo Wi-Fi+Bluetooth chip sharing the same silicon and antenna paths. Removes a source of variance, at the cost of Bluetooth. Not one of the measured fixes above, so it's your call, not the script's |

`python3 mt7925-tune.py status` shows exactly what's active right now, what still needs a reboot, and the detected hardware and driver/firmware version. `python3 mt7925-tune.py disable` reverts everything, Bluetooth included.

{{< callout type="info" >}}
**Left out on purpose:** `disable_eht=1` shows up in some third-party guides, but only exists in out-of-tree patch sets, not the mainline driver this G16 runs. CPU governor and power-profile changes also helped in testing, but that's a system-wide trade-off, not a Wi-Fi-specific one, so the script doesn't touch them. Older guides also mention pinning the driver's own `power_save` module parameter; on this G16's kernel (7.2.4) that parameter no longer exists (`dmesg` shows `mt7925e: unknown parameter 'power_save' ignored`), so the script skips it too.
{{< /callout >}}

## Results

| Configuration | Throughput |
|---|---|
| Stock | ~300 Mbit/s |
| ASPM disabled + NM powersave off only | 410-450 Mbit/s |
| Everything, including the optional Bluetooth-off extra (`enable --bluetooth-off`) | 500-608 Mbit/s, usually 560+ |

For reference, a phone (Samsung Galaxy S24 Ultra) on the same AP measured 439-811 Mbit/s across several runs, average around 545 Mbit/s, so the tuned G16 is now in the same range as a modern phone's Wi-Fi radio here. On a stronger/closer AP the same phone hit 1.24 Gbit/s, well above what the MT7925's 160MHz ceiling can ever reach regardless of signal quality (see [hardware ceiling](#the-hardware-ceiling) below).

Worth sitting with: that phone launched in January 2024. A purpose-built M.2 2230 Wi-Fi 7 card in a 2024/2025 gaming laptop, tuned to its actual ceiling, still loses to a two-year-old phone's Wi-Fi chip. That's not a config problem this script can tune away -- the MT7925 is, on this evidence, a mediocre card. The fixes above get it to where it should have been out of the box, not to where it should be.

{{< callout type="warning" >}}
Expect run-to-run variance even in a stable, tuned state (repeated 20s runs ranged 509-598 Mbit/s back to back with nothing changed). Right after a reboot or reconnect it's worse: retries can spike hard before the link settles (seen: 3000+ retries in one run). Judge the fix on a few runs, not one, and never on the very first test after rebooting.
{{< /callout >}}

**On UniFi:** if you have multiple APs, the default 6GHz roaming RSSI threshold (-88 dBm) is permissive enough that a client can stay on a weak signal well past the point retries start climbing (noticeable below roughly -62 dBm in testing). Tightening it to around -70 dBm (your SSID → Advanced → Roaming Assistance → Handoff Suggestions) helped.

## The hardware ceiling

The MT7925 is hardware-limited to 160MHz channel width and 2×2 MIMO, confirmed via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, no `EHT-MCS Map (BW = 320)` entry at all. A Wi-Fi 7 access point may offer 320MHz 6GHz channels; this card can only ever use half of that. No driver, firmware, or setting changes that. Expect roughly double the out-of-the-box throughput with the fixes above, not multi-gigabit Wi-Fi.

## When your numbers don't match this page's

The numbers above assume a reasonably strong 6GHz signal. 6GHz has less range and wall penetration than 5GHz, and the MT7925 will silently drop from 2 spatial streams to 1 well before the link actually disconnects -- which roughly halves the ceiling on top of whatever the weaker signal already costs.

Real example, same laptop and access point, only the distance changed:

| | Farther from the AP | Closer to the AP |
|---|---|---|
| Signal | -70 to -73 dBm | -63 dBm |
| Negotiated rate (also in `status`'s "Current link") | `EHT-NSS 1`, 432-576 Mbit/s | `EHT-NSS 2`, 1152.8 Mbit/s |
| `iperf3 -P 4` throughput | ~170-260 Mbit/s | 583-594 Mbit/s |

Same script, same tuning, same everything else -- the only variable was distance. `python3 mt7925-tune.py status` prints signal and `EHT-NSS` in its "Current link" section for exactly this reason: before assuming a fix isn't working, check whether you're actually looking at a signal problem instead. If moving closer brings `EHT-NSS` back to 2 and throughput climbs, that's range, not a broken card.

## Diagnosing drops and roaming issues

```bash
journalctl -k -f | grep -iE "mt7925|deauth|disassoc|beacon loss"
```

Leave this running during normal use, before and after, to compare how often anything shows up.

For roaming specifically, ping a mesh node's LAN IP continuously while walking between nodes (not an internet host, to keep WAN issues out of the picture):

```bash
ping -D -i 0.2 <mesh-node-ip>
```

`iw dev <iface> link` shows which node you're currently associated with, useful for telling an actual roam apart from a "sticky" client that won't let go of a weak node.

For throughput, `iperf3` against something on your own LAN beats a speed test against the internet since it removes your ISP and WAN path as variables:

```bash
iperf3 -s                              # on any other machine on the network
iperf3 -c <that-machine> -P 4          # from the laptop
```

## Should you replace the card?

Probably not yet. The card is socketed (M.2 2230, key E) and ROG laptops don't enforce a BIOS whitelist, so a swap is physically possible.

{{% details title="Why not, in more detail" closed="true" %}}

The obvious candidate, MT7927, adds 320MHz support and has mainline Linux support since kernel 7.2, but real-world reports show *higher* TX retransmission rates than MT7925 on otherwise identical hardware, described as firmware-level and not fixable by a driver patch. The driver is also young, merged into mainline in 2026. This same MT7925 driver was considerably worse in January 2026 than it is now; MT7927 today looks like it's roughly where MT7925 was a year ago.

Qualcomm's current Wi-Fi 7 card (QCNCM865/FastConnect 7800) isn't better either: reports of the 6GHz band not showing up in scans, non-functional MLO, and ~33% lower throughput than Windows on the same hardware. Qualcomm's more interesting announcement, the FastConnect 8800 (Wi-Fi 8, 4×4 radio, up to 11.6 Gbit/s), doesn't ship until late 2026 at the earliest.

{{% /details %}}

{{% details title="Checking your driver and firmware version" closed="true" %}}

`python3 mt7925-tune.py status` shows all of this automatically (kernel/driver version, the firmware version and build time from `dmesg`, and the `linux-firmware-mediatek` package version on Arch-based distros). To check by hand instead:

```bash
uname -r                                                          # kernel = driver version, ships in-tree
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"          # firmware version
pacman -Qi linux-firmware-mediatek | grep Version                  # firmware package version
```

{{% /details %}}

{{% details title="Where to follow active development" closed="true" %}}

The chip is still actively worked on; patches landed as recently as this week during testing for this page. `python3 mt7925-tune.py status` prints these same links, so you don't have to remember them.

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/): the official patch mailing list. Search "mt7925".
- [ratatoskr.run](https://ratatoskr.run/): a more readable web archive of the same mailing lists.
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76): mirror of the driver source, easier to browse than the kernel.org tree.

Recent proof that this is moving, not stalled: a [patch skipping scans during suspend](https://ratatoskr.run/linux-mediatek/2026/04/3520789) landed in April 2026 to stop command timeouts on resume, and an [mt7925 firmware update](https://ratatoskr.run/linux-wireless/2026/08/17426467/t) went out in August 2026. Neither is life-changing on its own, but the cadence is the point: this driver gets touched most months, not once a year.

{{% /details %}}

## References

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/): the December 2023 patch that flipped the driver's default.
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches): a more invasive third-party driver patch set for the same chip. Background reading, not something this page recommends installing wholesale.
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html): upstream work on the same ASPM issue for the newer MT7927.
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/): the community reverse-engineering effort behind MT7927 support.
- [Known Issues, Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/): a running list of chip-level issues and their status.
- [From "Replace It with Intel" to Upstream: Bringing MediaTek Bluetooth/WiFi 7 to Linux](https://www.linaro.org/blog/from-replace-it-with-intel-to-upstream-bringing-mediatek-bluetooth-wifi-7-to-linux/): Linaro's account of how MediaTek's Wi-Fi 7 support went from an "unsupportable, replace the card" state to actively upstreamed, useful context for why this chip's situation looks better a year from now than it does today.
- [MT7925 WiFi Driver Fixes, now packaged as DKMS](https://community.frame.work/t/mt7925-wifi-driver-fixes-now-available-as-dkms-package/79777): the community fix set from the "Where to follow active development" list above, now installable without hand-patching -- a sign the fixes are stabilizing enough to package.
