---
title: "MT7925 Wi-Fi Performance"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

The G16 GA605WV ships a MediaTek Wi-Fi 7 MT7925 card. Dropped connections, sluggish mesh roaming, or download speeds well below what the connection should give: this page covers all three.

This is a script that applies four fixes at once (NetworkManager power saving, PCIe ASPM, Bluetooth, and a wireless-stack queue limit), each with a real effect measured on this hardware.

{{< callout type="info" >}}
**Verified on this hardware.** Tested with `iperf3` against a local server on a 2.5GbE UniFi network. Stock: ~300 Mbit/s. Tuned: 500-608 Mbit/s, usually 560+. Your numbers will vary with AP, signal strength, and kernel version, but the fixes themselves are confirmed, not theoretical.
{{< /callout >}}

## Setup

{{% steps %}}

### Download and verify

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.sh
echo "17464ccb7a5a892c61bc0e93e5e719d90f477b9c351156e918b7bc25c85e8cd6  mt7925-tune.sh" | sha256sum -c
chmod +x mt7925-tune.sh
```

### Apply

```bash
./mt7925-tune.sh enable
```

Reboot afterward. One of the four fixes (PCIe ASPM) is a kernel module parameter, only read at module load time.

{{% /steps %}}

Source: [mt7925-tune.sh](/scripts/mt7925-tune.sh). SHA-256 `17464ccb7a5a892c61bc0e93e5e719d90f477b9c351156e918b7bc25c85e8cd6`.

| Fix | What it does |
|---|---|
| Disable NetworkManager's Wi-Fi power saving | The most common cause of drops and slow mesh roaming |
| Disable PCIe ASPM for the card | The PCIe link's own power state, not the radio. The main throughput fix |
| Bluetooth off | The MT7925 is a combo Wi-Fi+Bluetooth chip sharing the same silicon and antenna paths. Removes a source of variance |
| Raise the AQL Best Effort queue limit | `mac80211` caps how much data can be queued per traffic class to keep latency low under contention. The stock limit favors fairness over saturating a single stream. Trade-off: less headroom for latency-sensitive traffic (calls, gaming) sharing the radio under load |

`./mt7925-tune.sh status` shows exactly what's active right now and what still needs a reboot. `./mt7925-tune.sh disable` reverts everything.

{{< callout type="info" >}}
**Left out on purpose:** `disable_eht=1` shows up in some third-party guides, but only exists in out-of-tree patch sets, not the mainline driver this G16 runs. CPU governor and power-profile changes also helped in testing, but that's a system-wide trade-off, not a Wi-Fi-specific one, so the script doesn't touch them. Older guides also mention pinning the driver's own `power_save` module parameter; on this G16's kernel (7.2.4) that parameter no longer exists (`dmesg` shows `mt7925e: unknown parameter 'power_save' ignored`), so the script skips it too.
{{< /callout >}}

## Results

| Configuration | Throughput |
|---|---|
| Stock | ~300 Mbit/s |
| ASPM disabled + NM powersave off only | 410-450 Mbit/s |
| Everything (script `enable`) | 500-608 Mbit/s, usually 560+ |

For reference, a phone (Samsung Galaxy S24 Ultra) on the same AP measured 439-811 Mbit/s across several runs, average around 545 Mbit/s, so the tuned G16 is now in the same range as a modern phone's Wi-Fi radio here. On a stronger/closer AP the same phone hit 1.24 Gbit/s, well above what the MT7925's 160MHz ceiling can ever reach regardless of signal quality (see [hardware ceiling](#the-hardware-ceiling) below).

{{< callout type="warning" >}}
Expect run-to-run variance even in a stable, tuned state (repeated 20s runs ranged 509-598 Mbit/s back to back with nothing changed). Right after a reboot or reconnect it's worse: retries can spike hard before the link settles (seen: 3000+ retries in one run). Judge the fix on a few runs, not one, and never on the very first test after rebooting.
{{< /callout >}}

**On UniFi:** if you have multiple APs, the default 6GHz roaming RSSI threshold (-88 dBm) is permissive enough that a client can stay on a weak signal well past the point retries start climbing (noticeable below roughly -62 dBm in testing). Tightening it to around -70 dBm (your SSID → Advanced → Roaming Assistance → Handoff Suggestions) helped.

## The hardware ceiling

The MT7925 is hardware-limited to 160MHz channel width and 2×2 MIMO, confirmed via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, no `EHT-MCS Map (BW = 320)` entry at all. A Wi-Fi 7 access point may offer 320MHz 6GHz channels; this card can only ever use half of that. No driver, firmware, or setting changes that. Expect roughly double the out-of-the-box throughput with the fixes above, not multi-gigabit Wi-Fi.

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

```bash
uname -r                                                          # kernel = driver version, ships in-tree
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"          # firmware version
pacman -Qi linux-firmware-mediatek | grep Version                  # firmware package version
```

{{% /details %}}

{{% details title="Where to follow active development" closed="true" %}}

The chip is still actively worked on; patches landed as recently as this week during testing for this page.

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/): the official patch mailing list. Search "mt7925".
- [ratatoskr.run](https://ratatoskr.run/): a more readable web archive of the same mailing lists.
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76): mirror of the driver source, easier to browse than the kernel.org tree.

{{% /details %}}

## References

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/): the December 2023 patch that flipped the driver's default.
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches): a more invasive third-party driver patch set for the same chip. Background reading, not something this page recommends installing wholesale.
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html): upstream work on the same ASPM issue for the newer MT7927.
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/): the community reverse-engineering effort behind MT7927 support.
- [Known Issues, Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/): a running list of chip-level issues and their status.
