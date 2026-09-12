---
title: "MT7925 Wi-Fi Performance"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

The G16 GA605WV ships a MediaTek Wi-Fi 7 MT7925 card. If you occasionally see dropped connections, sluggish roaming between mesh nodes, or download speeds well below what the connection should give, this page is for you.

{{< callout type="info" >}}
**Verified on this hardware.** Everything below has been tested and measured on this G16, against a local iperf3 server on a 2.5GbE-backed UniFi network (U7 Pro access points). Baseline was 300 Mbit/s; with the fixes and tuning below, a stable 600+ Mbit/s. Your numbers will vary with AP, signal strength, and kernel version, but the mechanism and the fixes are confirmed, not theoretical.
{{< /callout >}}

## Two separate causes, not one

Symptoms like these usually get blamed on "Wi-Fi power saving," but on this chip there are two independent layers that can each cause exactly this behavior, and a fix for one doesn't touch the other:

1. **NetworkManager's own 802.11 power saving.** The most commonly reported cause of drops and slow mesh roaming.
2. **PCIe ASPM (Active State Power Management).** About the PCIe link's own power state rather than the radio. This is the one that actually matters on this hardware — confirmed in `dmesg` (`mt7925e 0000:63:00.0: disabling ASPM L1`) and the main real fix below.

{{< callout type="info" >}}
Older guides also mention pinning the `mt7925e` driver's own `power_save` module parameter. On this G16's kernel (7.2.4) that parameter no longer exists — `dmesg` shows `mt7925e: unknown parameter 'power_save' ignored`. Skip it.
{{< /callout >}}

## The fix

{{% steps %}}

### Disable NetworkManager's Wi-Fi power saving

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf << 'EOF'
[connection]
wifi.powersave = 2
EOF
sudo systemctl restart NetworkManager
```

`2` disables power saving outright. `0` (the default) defers to the driver, `3` forces it on.

### Disable PCIe ASPM for the card

```bash
modinfo mt7925e | grep -i aspm
```

This lists `disable_aspm` on current kernels. Set it:

```bash
echo "options mt7925e disable_aspm=1" | sudo tee /etc/modprobe.d/mt7925e.conf
```

{{< callout type="info" >}}
This is a **module parameter**, read only at module load time — it needs a **reboot** to take effect, not just a service restart. After rebooting, confirm it actually applied:

```bash
sudo dmesg | grep -i "mt7925e.*ASPM"
# should show: mt7925e 0000:63:00.0: disabling ASPM L1
```
{{< /callout >}}

If `disable_aspm` isn't listed for your kernel, the only remaining lever is the kernel-wide `pcie_aspm=off` boot parameter. That disables ASPM for **every** PCIe device, not just Wi-Fi, trading some battery life for throughput — worth trying only if the module parameter isn't available.

### Reboot

```bash
sudo reboot
```

{{% /steps %}}

This pair — NetworkManager powersave off + ASPM disabled — is the baseline fix. On its own it took this G16 from roughly 300 Mbit/s to 410-450 Mbit/s in testing. Everything past this point is optional, further tuning with real trade-offs.

## Going further: the tuning script

Beyond the baseline fix, three more knobs made a measurable difference in testing, stacking up to a stable **600+ Mbit/s** (from a 300 Mbit/s starting point — see [Verified results](#verified-results) below). None of them are MT7925-specific hacks; they're standard Linux wireless-stack (mac80211) and RF-coexistence knobs that happen to matter a lot on this chip:

- **Bluetooth off.** The MT7925 is a combo Wi-Fi+Bluetooth chip sharing the same silicon and antenna paths. Disabling BT removed a source of variance in testing.
- **AQL (Airtime Queue Limit) tuning.** `mac80211`'s AQL mechanism caps how much data can be queued per traffic class, measured in airtime (microseconds), to keep latency low under contention. The stock Best Effort limit (5000/12000 µs) is tuned for fairness under multi-client congestion, not for saturating a single high-bitrate stream. Raising it gives a single TCP stream more room to fill the pipe between bursts.

{{< callout type="warning" >}}
**AQL tuning is a trade-off, not a free win.** AQL exists specifically to keep latency low when the radio is busy — a video call or a game alongside a large download, for example. Raising the Best Effort limit improves single-stream throughput but reduces that headroom. Fine for a dedicated throughput test or a mostly-single-purpose connection; think twice if you regularly do latency-sensitive things *while* saturating the link.
{{< /callout >}}

A ready-to-use script applies and reverts all of this — the baseline fix plus BT and AQL — in one command, so you can A/B test rather than take any of these numbers on faith:

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.sh
echo "17464ccb7a5a892c61bc0e93e5e719d90f477b9c351156e918b7bc25c85e8cd6  mt7925-tune.sh" | sha256sum -c
chmod +x mt7925-tune.sh

./mt7925-tune.sh enable    # apply everything
./mt7925-tune.sh status    # see exactly what's active right now
./mt7925-tune.sh disable   # back to stock
```

Source: [mt7925-tune.sh](/scripts/mt7925-tune.sh).

The script is intentionally conservative in scope: it only touches the Wi-Fi card, NetworkManager's Wi-Fi config, Bluetooth, and mac80211's AQL settings — nothing CPU-wide (no governor changes, no power-profile switching). Those are real levers too, but they affect the whole system's power/performance balance, not just this card, so they're out of scope for a Wi-Fi tuning script. `status` tells you which changes are live immediately and which need a reboot (ASPM is the only one that does).

{{< callout type="info" >}}
**What didn't make the cut:** `disable_eht=1` shows up in some third-party guides as an EHT-overhead workaround, but it only exists in out-of-tree patch sets, not the mainline driver this G16 runs — using it means maintaining a custom-built kernel module. CPU governor / power-profile changes gave a real, measurable boost in testing too, but they're a system-wide power/performance trade-off, not a Wi-Fi-specific one, so they're deliberately left out of this page and the script.
{{< /callout >}}

## Verified results

Measured with `iperf3` (4 parallel streams, 20-30s) against a local server on a 2.5GbE-backed UniFi network (U7 Pro access points, 6GHz, 160MHz channel — the max this card supports; see [hardware ceiling](#the-hardware-ceiling-what-tuning-cant-fix) below).

| Configuration | Throughput | Notes |
|---|---|---|
| Stock | ~300 Mbit/s | Baseline, no changes |
| + ASPM disabled + NM powersave off | 410-450 Mbit/s | The core fix above |
| + fresh association after reboot | — | **Important:** right after a reboot/reconnect, retries can spike hard (seen: 3000+ retries in one run) before the link settles. Don't judge the fix on the very first test after rebooting — reconnect once and retest. |
| + AP roam-threshold tuned, BT off, AQL raised | **598-608 Mbit/s** | Stable across repeated 30s runs |

That's roughly **double** the stock throughput. For reference, a phone (Samsung Galaxy S24 Ultra) on the same network measured 439-487 Mbit/s — so the tuned G16 is now in the same range as a modern phone's Wi-Fi 7/6E radio on this network, not far behind it.

### On the AP side, if you're on UniFi

Two settings unrelated to the laptop itself helped in testing, worth checking regardless of client hardware:

- **6GHz roaming RSSI threshold:** if you have multiple APs, UniFi's default (-88 dBm) is quite permissive — a client can stay associated to a weak 6GHz signal well past the point where retries start climbing (we saw retries increase noticeably below roughly -62 dBm). Tightening it to around **-70 dBm** (Wi-Fi settings → your SSID → Advanced → Roaming Assistance → Handoff Suggestions) nudges clients toward a stronger AP sooner.
- **Fast Roaming (802.11r) / Handoff Suggestions (802.11v):** worth enabling if you have more than one AP; not relevant with a single AP.

## The hardware ceiling: what tuning can't fix

The MT7925 is hardware-limited to **160MHz channel width and 2×2 MIMO** (confirmed via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, and no `EHT-MCS Map (BW = 320)` entry at all). A Wi-Fi 7 access point may offer 320MHz 6GHz channels — this G16's UniFi network does — but this card can only ever use half of that. The successor chip, MT7927, is architecturally almost identical but adds 320MHz support; that's the one hardware difference between the two.

No driver update, firmware update, or setting in this guide changes that ceiling. What tuning *can* do is get the card closer to what its own hardware allows — which is the gap this page addresses. Don't expect multi-gigabit Wi-Fi from this chip even with everything above applied; do expect roughly double the out-of-the-box throughput, which matches what was measured.

## Should you replace the card?

Short answer: **probably not yet.** Longer version:

The MT7925 card in this laptop is socketed (M.2 2230, key E), not soldered, and ROG laptops don't appear to enforce a BIOS Wi-Fi-card whitelist — so a swap is physically possible. The obvious upgrade candidate is the **MT7927**, MediaTek's 320MHz-capable successor with mainline Linux support since kernel 7.2 (this G16's kernel). But as of testing:

- The MT7927 driver is young — merged into mainline in 2026, without MediaTek's direct involvement in the community reverse-engineering that got it there (MediaTek reviewed and signed off once it was ready for upstream, but didn't proactively help beforehand).
- Real-world reports show **higher TX retransmission rates on MT7927 than MT7925 on otherwise identical hardware** — and it's described as firmware-level, not something a driver patch can fix.
- One independent 320MHz/6GHz test over a 2.5GbE backhaul (same setup as this page's testing) measured 2.01 Gbit/s — a genuinely large number — but that's a best-case result on different hardware, not a guarantee.

The pattern worth noticing: this same MT7925 driver was considerably worse in January 2026 than it is now (September 2026) — regressions fixed, stability patches landed, throughput bugs resolved. MT7927 today looks like it's roughly where MT7925 was a year or so ago: real hardware potential, young and still-settling software around it.

**Qualcomm's WiFi 7 card (QCNCM865/FastConnect 7800)** isn't a better alternative right now either — Linux reports for it include the 6GHz band not even showing up in scans, non-functional MLO, and roughly 33% lower throughput than Windows on the same hardware. Qualcomm's actually exciting announcement, the FastConnect 8800, is a **Wi-Fi 8** chip (4×4 radio, up to 11.6 Gbit/s) unveiled at MWC 2026 — but it's not shipping in products until late 2026 at the earliest, and there's no standalone M.2 laptop card for it yet.

If you do want more than this chip can give and are willing to accept some instability while the MT7927 driver matures, it's a real option — just go in knowing you're trading a known, tuned quantity for an unknown one.

## Checking your driver and firmware version

```bash
# Kernel version — the mt7925e driver ships in-tree, so kernel version = driver version
uname -r

# Firmware version, from dmesg after boot
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"

# linux-firmware package version
pacman -Qi linux-firmware-mediatek | grep Version
```

## Where to follow active development

The chip is still actively worked on — patches landed as recently as this week during testing for this page. Worth bookmarking if you want to track fixes as they land, or check whether a specific bug you're hitting is already known:

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/) — the official patch mailing list; search "mt7925"
- [ratatoskr.run](https://ratatoskr.run/) — a more readable web archive of the same mailing lists
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76) — mirror of the driver source, easier to browse than the kernel.org tree

## Checking before and after

**Current power-save state, before changing anything:**

```bash
iw dev $(iw dev | awk '/Interface/{print $2}') get power_save
nmcli connection show   # find your connection's exact name
nmcli -g 802-11-wireless.powersave connection show "<connection name>"
```

**Drops, live:**

```bash
journalctl -k -f | grep -iE "mt7925|deauth|disassoc|beacon loss"
```

Leave this running during normal use, before and after, and compare how often anything shows up.

**Roaming, specifically:** walk between mesh nodes with a continuous ping running against the router or a mesh node's LAN IP (not an internet host, to keep WAN issues out of the picture):

```bash
ping -D -i 0.2 <mesh-node-ip> | tee ping-test.log
```

Watch for gaps or latency spikes during the walk. `iw dev <iface> link` shows which node you're currently associated with — useful for telling an actual roam apart from a "sticky" client that never lets go of a weak node, which is a separate, common mesh problem unrelated to power saving.

**Throughput:** `iperf3` against something on your own LAN is far more reliable than a speed test against the internet — it removes your ISP and WAN path as variables. A cheap way to get a target: run `iperf3 -s` on any other machine on the network (a desktop, a NAS, a Raspberry Pi) and point `iperf3 -c <that-machine> -P 4` at it from the laptop, before and after each change.

## References

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/) — the December 2023 patch that flipped the driver's default
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches) — a more invasive third-party driver patch set for the same chip (disconnects, throughput, instability); useful background reading, not something this page recommends installing wholesale
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html) — upstream work on the same ASPM throughput issue for the newer MT7927
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/) — the community reverse-engineering effort behind MT7927 support
- [Known Issues — Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/) — a running list of chip-level issues and their status
