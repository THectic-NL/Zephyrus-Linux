---
title: "MT7925 Wi-Fi Performance"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

The G16 GA605WV ships a MediaTek Wi-Fi 7 MT7925 card. If you occasionally see dropped connections, sluggish roaming between mesh nodes, or download speeds well below what the connection should give, this page is for you.

{{< callout type="warning" >}}
**Not yet verified on this hardware.** Everything below is based on well-documented reports for the same MT7925 chip on other laptops (Framework 13, other ASUS ROG models, various Arch/CachyOS forum threads), not on testing done on this specific G16. Treat it as a starting point, not a confirmed fix, until this notice is updated.
{{< /callout >}}

## Three separate causes, not one

Symptoms like these usually get blamed on "Wi-Fi power saving," but on this chip there are three independent layers that can each cause exactly this behavior, and a fix for one doesn't touch the others:

1. **The `mt7925e` driver's own power saving.** A December 2023 patch changed the driver's default to power saving *off*. On a current kernel this is almost certainly already off, but it's worth pinning explicitly rather than trusting the default.
2. **NetworkManager's own 802.11 power saving.** This is a separate layer, independent of what the driver defaults to. NetworkManager can still put the radio into standard power-save mode regardless of the driver setting, and this is the most commonly reported cause of drops and slow mesh roaming.
3. **PCIe ASPM (Active State Power Management).** A different mechanism entirely, about the PCIe link's own power state rather than the radio. This one is still an active area of upstream work in 2026 and is the more likely explanation for mediocre throughput specifically (reports range from "noticeably slower" to a near-total throughput collapse).

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

### Pin the driver's own power saving off

```bash
echo "options mt7925e power_save=0" | sudo tee /etc/modprobe.d/mt7925e.conf
```

Belt-and-braces: makes the setting explicit instead of relying on the driver default staying the way it is across kernel updates.

### Check for a driver-level ASPM toggle before touching anything system-wide

```bash
modinfo mt7925e | grep -i aspm
```

If this lists a parameter (e.g. `disable_aspm`), add it to the same file from the previous step, for example:

```bash
echo "options mt7925e disable_aspm=1" | sudo tee -a /etc/modprobe.d/mt7925e.conf
```

If nothing shows up, the only remaining lever is the kernel-wide `pcie_aspm=off` boot parameter. That disables ASPM for **every** PCIe device, not just Wi-Fi, trading some battery life for throughput — worth trying only if the two steps above don't fix things.

### Reboot

```bash
sudo reboot
```

{{% /steps %}}

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

**Throughput:** the same speed test (e.g. `fast.com`, `speedtest-cli`), same spot, same time of day, before and after each step.

## References

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/) — the December 2023 patch that flipped the driver's default
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches) — a more invasive third-party driver patch set for the same chip (disconnects, throughput, instability); useful background reading, not something this page recommends installing wholesale
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html) — upstream work on the same ASPM throughput issue for the newer MT7927
