---
title: "MT7925 Wifi-prestaties"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

De G16 GA605WV heeft een MediaTek Wi-Fi 7 MT7925-kaart. Wegvallende verbindingen, traag roamen tussen mesh-nodes, of downloadsnelheden ruim onder wat de verbinding zou moeten geven: deze pagina behandelt alle drie.

{{< callout type="info" >}}
**Geverifieerd op deze hardware.** Getest met `iperf3` tegen een lokale server op een 2,5GbE-netwerk met UniFi. Stock: ~300 Mbit/s. Getuned: een stabiele 600+ Mbit/s. Jouw cijfers variëren met AP, signaalsterkte en kernelversie, maar de fixes zelf zijn bevestigd, niet theoretisch.
{{< /callout >}}

## De fixes

| Fix | Wat het doet |
|---|---|
| NetworkManager's wifi-powersave uitzetten | De meest voorkomende oorzaak van drops en traag roamen op mesh-netwerken. |
| PCIe ASPM voor de kaart uitzetten | De energiestatus van de PCIe-link zelf, niet de radio. De belangrijkste doorvoerfix, bevestigd in `dmesg`. Vereist een herstart; het is een moduleparameter. |
| Bluetooth uit | De MT7925 is een combo Wi-Fi+Bluetooth-chip die dezelfde silicon en antennepaden deelt. Haalt een bron van variatie weg. |
| AQL Best Effort-limiet verhogen | `mac80211` begrenst hoeveel data per verkeersklasse in de wachtrij mag staan om latency laag te houden onder congestie. De standaardlimiet kiest voor eerlijkheid boven het verzadigen van één stream; verhogen doet het omgekeerde. Trade-off: minder marge voor latency-gevoelig verkeer (calls, gaming) dat de radio deelt onder belasting. |

{{< callout type="info" >}}
Oudere gidsen noemen ook het vastzetten van de `power_save`-moduleparameter van de `mt7925e`-driver zelf. Op de kernel van deze G16 (7.2.4) bestaat die parameter niet meer; `dmesg` toont `mt7925e: unknown parameter 'power_save' ignored`. Staat niet in de lijst hierboven omdat er niets in te stellen valt.
{{< /callout >}}

Een script past alle vier toe en maakt ze weer ongedaan, met één commando:

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.sh
echo "17464ccb7a5a892c61bc0e93e5e719d90f477b9c351156e918b7bc25c85e8cd6  mt7925-tune.sh" | sha256sum -c
chmod +x mt7925-tune.sh

./mt7925-tune.sh enable    # alles toepassen
./mt7925-tune.sh status    # zie precies wat er nu actief is
./mt7925-tune.sh disable   # terug naar stock
```

Bron: [mt7925-tune.sh](/scripts/mt7925-tune.sh). `status` laat zien welke wijzigingen direct actief zijn en welke een herstart nodig hebben (alleen ASPM doet dat). Herstart na `enable` zodat ASPM ook echt wordt toegepast.

{{< callout type="info" >}}
**Bewust weggelaten:** `disable_eht=1` duikt op in sommige externe gidsen, maar bestaat alleen in out-of-tree patchsets, niet in de mainline-driver die deze G16 draait. CPU-governor- en power-profile-wijzigingen hielpen ook in tests, maar dat is een systeembrede afweging, geen wifi-specifieke, dus het script raakt ze niet aan.
{{< /callout >}}

## Resultaten

| Configuratie | Doorvoer |
|---|---|
| Stock | ~300 Mbit/s |
| ASPM uit + NM-powersave uit | 410-450 Mbit/s |
| Alles (script `enable`) | 500-608 Mbit/s, meestal 560+ |

Ruwweg het dubbele van stock, soms meer. Ter referentie: een telefoon (Samsung Galaxy S24 Ultra) op dezelfde AP mat 439-811 Mbit/s over meerdere runs (gemiddeld rond de 545 Mbit/s), dus de getunede G16 zit nu in hetzelfde bereik als de wifi-radio van een moderne telefoon hier. Op een sterkere/dichterbije AP haalde diezelfde telefoon 1,24 Gbit/s, ruim boven wat het 160MHz-plafond van de MT7925 ooit kan bereiken, ongeacht signaalkwaliteit.

{{< callout type="warning" >}}
Verwacht variatie tussen runs, ook in een stabiele, getunede staat (herhaalde runs van 20s liepen uiteen van 509-598 Mbit/s zonder dat er iets veranderde). Direct na een herstart of reconnect is het erger: retries kunnen fors pieken voordat de verbinding settelt (gezien: 3000+ retries in één run). Beoordeel de fix op een paar runs, niet op één, en nooit op de allereerste test na een herstart.
{{< /callout >}}

**Op UniFi:** heb je meerdere AP's, dan is de standaard 6GHz roaming RSSI-drempel (-88 dBm) permissief genoeg dat een client op een zwak signaal blijft hangen ruim voorbij het punt waar retries beginnen op te lopen (merkbaar onder ongeveer -62 dBm in tests). Aanscherpen naar ongeveer -70 dBm (jouw SSID → Advanced → Roaming Assistance → Handoff Suggestions) hielp.

## Het hardware-plafond

De MT7925 is hardware-gelimiteerd tot 160MHz-kanaalbreedte en 2×2 MIMO, bevestigd via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, helemaal geen `EHT-MCS Map (BW = 320)`-vermelding. Een Wi-Fi 7 access point kan 320MHz 6GHz-kanalen aanbieden; deze kaart kan daar altijd maar de helft van gebruiken. Geen driver, firmware of instelling verandert dat. Verwacht met de fixes hierboven ruwweg een verdubbeling van de doorvoer uit de doos, geen multi-gigabit wifi.

## Moet je de kaart vervangen?

Waarschijnlijk nog niet. De kaart zit in een socket (M.2 2230, key E) en ROG-laptops hanteren geen BIOS-whitelist, dus een swap is fysiek mogelijk. De voor de hand liggende kandidaat, MT7927, voegt 320MHz-support toe en heeft mainline Linux-support sinds kernel 7.2, maar praktijkmeldingen tonen *hogere* TX-retransmissiepercentages dan MT7925 op verder identieke hardware, omschreven als firmware-niveau en niet op te lossen met een driverpatch. De driver is ook jong, gemerged in mainline in 2026. Deze zelfde MT7925-driver was in januari 2026 aanzienlijk slechter dan hij nu is; MT7927 staat er nu ongeveer voor zoals MT7925 er ongeveer een jaar geleden voor stond.

Qualcomm's huidige Wi-Fi 7-kaart (QCNCM865/FastConnect 7800) is ook niet beter: meldingen dat de 6GHz-band niet verschijnt in scans, niet-functionerende MLO, en ~33% lagere doorvoer dan Windows op dezelfde hardware. Qualcomm's interessantere aankondiging, de FastConnect 8800 (Wi-Fi 8, 4×4-radio, tot 11,6 Gbit/s), zit ten vroegste eind 2026 in producten.

## Je driver- en firmwareversie checken

```bash
uname -r                                                          # kernel = driverversie, zit in-tree
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"          # firmwareversie
pacman -Qi linux-firmware-mediatek | grep Version                  # firmware-packageversie
```

## Waar je actieve ontwikkeling volgt

Er wordt nog steeds actief aan deze chip gewerkt; er landden patches nog deze week tijdens het testen voor deze pagina.

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/): de officiële patch-mailinglist. Zoek op "mt7925".
- [ratatoskr.run](https://ratatoskr.run/): een beter leesbaar webarchief van dezelfde mailinglists.
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76): spiegel van de driverbroncode, makkelijker te doorbladeren dan de kernel.org-tree.

## Drops en roaming-problemen diagnosticeren

```bash
journalctl -k -f | grep -iE "mt7925|deauth|disassoc|beacon loss"   # drops, live
```

Voor roaming specifiek: ping continu naar het LAN-IP van een mesh-node terwijl je tussen nodes loopt (geen internet-host, om WAN-problemen buiten beeld te houden): `ping -D -i 0.2 <ip-mesh-node>`. `iw dev <iface> link` laat zien met welke node je op dat moment verbonden bent, handig om een echte roam te onderscheiden van een "sticky" client die een zwakke node niet loslaat.

Voor doorvoersnelheid: `iperf3` tegen iets op je eigen LAN is beter dan een speedtest tegen het internet, want het haalt je ISP en WAN-pad als variabelen weg: `iperf3 -s` op een andere machine op het netwerk, `iperf3 -c <die-machine> -P 4` vanaf de laptop.

## Meer lezen

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/): de patch uit december 2023 die de driver-default omzette.
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches): een ingrijpendere driverpatch van derden voor dezelfde chip. Achtergrondinformatie, geen aanbeveling van deze pagina om zomaar te installeren.
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html): upstream-werk aan hetzelfde ASPM-probleem voor de nieuwere MT7927.
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/): de community reverse-engineering-inspanning achter MT7927-support.
- [Known Issues, Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/): een lopende lijst van chip-niveau issues en hun status.
