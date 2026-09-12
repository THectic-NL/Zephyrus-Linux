---
title: "MT7925 Wifi-prestaties"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

De G16 GA605WV heeft een MediaTek Wi-Fi 7 MT7925-kaart. Zie je af en toe verbindingen wegvallen, traag roamen tussen mesh-nodes, of downloadsnelheden die duidelijk lager liggen dan wat de verbinding zou moeten geven? Dan is deze pagina voor jou.

{{< callout type="info" >}}
**Geverifieerd op deze hardware.** Alles hieronder is getest en gemeten op deze G16, tegen een lokale iperf3-server op een 2,5GbE-netwerk met UniFi (U7 Pro access points). Baseline was 300 Mbit/s; met de fixes en tuning hieronder een stabiele 600+ Mbit/s. Jouw cijfers variëren met AP, signaalsterkte en kernelversie, maar het mechanisme en de fixes zijn bevestigd, niet theoretisch.
{{< /callout >}}

## Drie losse oorzaken, geen één

Dit soort klachten wordt meestal op "wifi-powersave" geschoven, maar op deze chip zitten drie onafhankelijke lagen die elk dit gedrag kunnen veroorzaken, en een fix voor de één raakt de andere niet:

1. **De powersave van de `mt7925e`-driver zelf.** Een patch uit december 2023 zette de standaardinstelling van de driver op powersave *uit*. Op de kernel van deze G16 (7.2.4) bestaat de `power_save`-moduleparameter niet eens meer — hij is vervangen, en het instellen ervan in `modprobe.d` wordt stilzwijgend genegeerd (`mt7925e: unknown parameter 'power_save' ignored` in `dmesg`). Powersave staat al standaard uit; er valt hier niets meer vast te zetten.
2. **NetworkManager's eigen 802.11-powersave.** Dit is een aparte laag, los van wat de driver standaard doet. NetworkManager kan de radio nog steeds in standaard powersave-modus zetten ongeacht de driverinstelling, en dit is de meest gerapporteerde oorzaak van drops en traag roamen op mesh-netwerken.
3. **PCIe ASPM (Active State Power Management).** Een compleet ander mechanisme, over de energiestatus van de PCIe-link zelf, niet de radio. Dit is degene die er op deze hardware echt toe doet — bevestigd in `dmesg` (`mt7925e 0000:63:00.0: disabling ASPM L1`) en de belangrijkste echte fix hieronder.

## De fix

{{% steps %}}

### Zet NetworkManager's wifi-powersave uit

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf << 'EOF'
[connection]
wifi.powersave = 2
EOF
sudo systemctl restart NetworkManager
```

`2` schakelt powersave volledig uit. `0` (de standaard) laat het aan de driver over, `3` forceert het aan.

### Zet PCIe ASPM voor de kaart uit

```bash
modinfo mt7925e | grep -i aspm
```

Dit toont `disable_aspm` op actuele kernels. Zet 'm:

```bash
echo "options mt7925e disable_aspm=1" | sudo tee /etc/modprobe.d/mt7925e.conf
```

{{< callout type="info" >}}
Dit is een **moduleparameter**, die alleen bij het laden van de module wordt gelezen — dit vereist een **herstart**, niet alleen een service-restart. Bevestig na de herstart dat het echt is toegepast:

```bash
sudo dmesg | grep -i "mt7925e.*ASPM"
# zou moeten tonen: mt7925e 0000:63:00.0: disabling ASPM L1
```
{{< /callout >}}

Staat `disable_aspm` niet in de lijst voor jouw kernel? Dan is de enige overgebleven optie de systeembrede kernel-bootparameter `pcie_aspm=off`. Die zet ASPM uit voor **alle** PCIe-apparaten, niet alleen wifi — pas de moeite waard als de moduleparameter niet beschikbaar is.

### Herstart

```bash
sudo reboot
```

{{% /steps %}}

Dit paar — NetworkManager-powersave uit + ASPM uit — is de basisfix. Op zichzelf bracht dit deze G16 van ongeveer 300 Mbit/s naar 410-450 Mbit/s tijdens tests. Alles voorbij dit punt is optioneel, verdere tuning met echte trade-offs.

## Verder tunen: het tuning-script

Naast de basisfix maakten nog drie andere knoppen een meetbaar verschil in tests, samen goed voor een stabiele **600+ Mbit/s** (vanaf een startpunt van 300 Mbit/s — zie [Geverifieerde resultaten](#geverifieerde-resultaten) hieronder). Geen van deze zijn MT7925-specifieke hacks; het zijn standaard Linux wireless-stack (mac80211) en RF-coëxistentie-knoppen die toevallig flink uitmaken op deze chip:

- **Bluetooth uit.** De MT7925 is een combo Wi-Fi+Bluetooth-chip die dezelfde silicon en antennepaden deelt. BT uitschakelen verwijderde een bron van variatie in tests.
- **AQL (Airtime Queue Limit) tuning.** `mac80211`'s AQL-mechanisme begrenst hoeveel data per verkeersklasse in de wachtrij mag staan, gemeten in airtime (microseconden), om latency laag te houden onder congestie. De standaard Best Effort-limiet (5000/12000 µs) is afgesteld op eerlijkheid bij congestie met meerdere clients, niet op het verzadigen van één hoge-bitrate stream. Deze verhogen geeft één TCP-stream meer ruimte om de pijplijn tussen bursts door te vullen.

{{< callout type="warning" >}}
**AQL-tuning is een trade-off, geen gratis winst.** AQL bestaat specifiek om latency laag te houden wanneer de radio druk is — bijvoorbeeld een videocall of game naast een grote download. De Best Effort-limiet verhogen verbetert de single-stream doorvoer maar vermindert die marge. Prima voor een gerichte doorvoertest of een verbinding met vooral één doel; denk twee keer na als je regelmatig latency-gevoelige dingen doet *terwijl* je de link verzadigt.
{{< /callout >}}

Een kant-en-klaar script past dit allemaal toe en maakt het weer ongedaan — de basisfix plus BT en AQL — met één commando, zodat je kunt A/B-testen in plaats van deze cijfers zomaar te geloven:

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.sh
echo "17464ccb7a5a892c61bc0e93e5e719d90f477b9c351156e918b7bc25c85e8cd6  mt7925-tune.sh" | sha256sum -c
chmod +x mt7925-tune.sh

./mt7925-tune.sh enable    # alles toepassen
./mt7925-tune.sh status    # zie precies wat er nu actief is
./mt7925-tune.sh disable   # terug naar stock
```

Bron: [mt7925-tune.sh](/scripts/mt7925-tune.sh).

Het script is bewust beperkt van scope: het raakt alleen de wifi-kaart, NetworkManager's wifi-config, Bluetooth en mac80211's AQL-instellingen aan — niets systeembreeds (geen governor-wijzigingen, geen power-profile-schakelingen). Dat zijn ook echte hendels, maar ze beïnvloeden de power/performance-balans van het hele systeem, niet alleen deze kaart, dus vallen ze buiten scope voor een wifi-tuningscript. `status` laat zien welke wijzigingen direct actief zijn en welke een herstart nodig hebben (alleen ASPM doet dat).

{{< callout type="info" >}}
**Wat het niet heeft gehaald:** `disable_eht=1` duikt op in sommige externe gidsen als workaround voor EHT-overhead, maar bestaat alleen in out-of-tree patchsets, niet in de mainline-driver die deze G16 draait — het gebruiken betekent een zelfgebouwde kernelmodule onderhouden. CPU-governor / power-profile-wijzigingen gaven ook een echte, meetbare boost in tests, maar dat is een systeembrede power/performance-afweging, geen wifi-specifieke, dus die zijn bewust weggelaten van deze pagina en het script.
{{< /callout >}}

## Geverifieerde resultaten

Gemeten met `iperf3` (4 parallelle streams, 20-30s) tegen een lokale server op een 2,5GbE-netwerk met UniFi (U7 Pro access points, 6GHz, 160MHz-kanaal — het maximum dat deze kaart aankan; zie [hardware-plafond](#het-hardware-plafond-wat-tuning-niet-kan-oplossen) hieronder).

| Configuratie | Doorvoer | Opmerkingen |
|---|---|---|
| Stock | ~300 Mbit/s | Baseline, geen wijzigingen |
| + ASPM uit + NM-powersave uit | 410-450 Mbit/s | De kernfix hierboven |
| + verse associatie na herstart | — | **Belangrijk:** direct na een herstart/reconnect kunnen retries fors pieken (gezien: 3000+ retries in één run) voordat de verbinding settelt. Beoordeel de fix niet op de allereerste test na een herstart — reconnect eenmaal en test opnieuw. |
| + roam-threshold op AP getuned, BT uit, AQL verhoogd | **598-608 Mbit/s** | Stabiel over herhaalde runs van 30s |

Dat is ruwweg **het dubbele** van de stock-doorvoer. Ter referentie: een telefoon (Samsung Galaxy S24 Ultra) op hetzelfde netwerk mat 439-487 Mbit/s — de getunede G16 zit nu dus in hetzelfde bereik als de wifi-radio van een moderne telefoon op dit netwerk, niet ver erachter.

### Aan de AP-kant, als je UniFi gebruikt

Twee instellingen los van de laptop zelf hielpen in tests, de moeite waard om te checken ongeacht je client-hardware:

- **6GHz roaming RSSI-drempel:** heb je meerdere AP's, dan is UniFi's standaard (-88 dBm) behoorlijk permissief — een client kan geassocieerd blijven met een zwak 6GHz-signaal ruim voorbij het punt waar retries beginnen op te lopen (wij zagen retries merkbaar toenemen onder ongeveer -62 dBm). Deze aanscherpen naar ongeveer **-70 dBm** (Wifi-instellingen → jouw SSID → Advanced → Roaming Assistance → Handoff Suggestions) duwt clients eerder richting een sterkere AP.
- **Fast Roaming (802.11r) / Handoff Suggestions (802.11v):** de moeite waard om aan te zetten als je meer dan één AP hebt; niet relevant met een enkele AP.

## Het hardware-plafond: wat tuning niet kan oplossen

De MT7925 is hardware-gelimiteerd tot **160MHz-kanaalbreedte en 2×2 MIMO** (bevestigd via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, en helemaal geen `EHT-MCS Map (BW = 320)`-vermelding). Een Wi-Fi 7 access point kan 320MHz 6GHz-kanalen aanbieden — het UniFi-netwerk van deze G16 doet dat — maar deze kaart kan daar altijd maar de helft van gebruiken. De opvolger-chip, MT7927, is architecturaal bijna identiek maar voegt 320MHz-support toe; dat is het enige hardwareverschil tussen de twee.

Geen driverupdate, firmware-update of instelling in deze gids verandert dat plafond. Wat tuning *wel* kan doen, is de kaart dichter bij te brengen bij wat zijn eigen hardware toestaat — dat is de kloof die deze pagina aanpakt. Verwacht geen multi-gigabit wifi van deze chip, ook niet met alles hierboven toegepast; verwacht wel ruwweg een verdubbeling van de doorvoer uit de doos, wat overeenkomt met wat gemeten is.

## Moet je de kaart vervangen?

Kort antwoord: **waarschijnlijk nog niet.** Uitgebreider:

De MT7925-kaart in deze laptop zit in een socket (M.2 2230, key E), niet vastgesoldeerd, en ROG-laptops lijken geen BIOS-wifi-kaart-whitelist te hanteren — een swap is dus fysiek mogelijk. De voor de hand liggende upgrade-kandidaat is de **MT7927**, MediaTek's 320MHz-capabele opvolger met mainline Linux-support sinds kernel 7.2 (de kernel van deze G16). Maar op het moment van testen:

- De MT7927-driver is jong — gemerged in mainline in 2026, zonder directe betrokkenheid van MediaTek bij de community reverse-engineering die het daar bracht (MediaTek reviewde en gaf een sign-off toen het klaar was voor upstream, maar hielp niet proactief vooraf).
- Praktijkmeldingen tonen **hogere TX-retransmissiepercentages op MT7927 dan MT7925 op verder identieke hardware** — en dat wordt omschreven als firmware-niveau, niet iets wat een driverpatch kan oplossen.
- Eén onafhankelijke 320MHz/6GHz-test over een 2,5GbE-backhaul (dezelfde opzet als de tests op deze pagina) mat 2,01 Gbit/s — een oprecht groot getal — maar dat is een beste-geval-resultaat op andere hardware, geen garantie.

Het patroon dat de moeite waard is om op te merken: deze zelfde MT7925-driver was in januari 2026 aanzienlijk slechter dan hij nu (september 2026) is — regressies gefixt, stabiliteitspatches geland, doorvoerbugs opgelost. MT7927 staat er nu ongeveer voor zoals MT7925 er ongeveer een jaar geleden voor stond: echt hardwarepotentieel, jonge en nog settelende software eromheen.

**Qualcomm's Wi-Fi 7-kaart (QCNCM865/FastConnect 7800)** is op dit moment ook geen beter alternatief — Linux-meldingen erover omvatten dat de 6GHz-band niet eens in scans verschijnt, niet-functionerende MLO, en ruwweg 33% lagere doorvoer dan Windows op dezelfde hardware. Qualcomm's daadwerkelijk spannende aankondiging, de FastConnect 8800, is een **Wi-Fi 8**-chip (4×4-radio, tot 11,6 Gbit/s) onthuld op MWC 2026 — maar die zit ten vroegste eind 2026 in producten, en er is nog geen losse M.2-laptopkaart voor.

Wil je toch meer dan deze chip kan geven en ben je bereid wat instabiliteit te accepteren terwijl de MT7927-driver rijpt, dan is het een reële optie — ga er alleen bewust van in dat je een bekende, getunede grootheid inruilt voor een onbekende.

## Je driver- en firmwareversie checken

```bash
# Kernelversie — de mt7925e-driver zit in-tree, dus kernelversie = driverversie
uname -r

# Firmwareversie, uit dmesg na herstart
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"

# linux-firmware packageversie
pacman -Qi linux-firmware-mediatek | grep Version
```

## Waar je actieve ontwikkeling volgt

Er wordt nog steeds actief aan deze chip gewerkt — er landden patches nog deze week tijdens het testen voor deze pagina. De moeite waard om te bookmarken als je fixes wilt volgen zodra ze landen, of wilt checken of een specifieke bug die je tegenkomt al bekend is:

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/) — de officiële patch-mailinglist; zoek op "mt7925"
- [ratatoskr.run](https://ratatoskr.run/) — een beter leesbaar webarchief van dezelfde mailinglists
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76) — spiegel van de driverbroncode, makkelijker te doorbladeren dan de kernel.org-tree

## Controleren, voor en na

**Huidige powersave-status, voordat je iets aanpast:**

```bash
iw dev $(iw dev | awk '/Interface/{print $2}') get power_save
nmcli connection show   # zoek de exacte naam van je verbinding op
nmcli -g 802-11-wireless.powersave connection show "<naam-verbinding>"
```

**Drops, live meekijken:**

```bash
journalctl -k -f | grep -iE "mt7925|deauth|disassoc|beacon loss"
```

Laat dit open staan tijdens normaal gebruik, voor en na, en vergelijk hoe vaak er iets verschijnt.

**Roaming specifiek:** loop tussen de mesh-nodes door met een lopende ping naar de router of het LAN-IP van een mesh-node (geen internet-host, om WAN-problemen buiten beeld te houden):

```bash
ping -D -i 0.2 <ip-mesh-node> | tee ping-test.log
```

Let op gaten of latency-pieken tijdens het lopen. `iw dev <iface> link` laat zien met welke node je op dat moment verbonden bent — handig om een echte roam te onderscheiden van een "sticky" client die een zwakke node niet loslaat, een apart en veelvoorkomend meshprobleem los van powersave.

**Doorvoersnelheid:** `iperf3` tegen iets op je eigen LAN is veel betrouwbaarder dan een speedtest tegen het internet — het haalt je ISP en WAN-pad als variabelen weg. Een goedkope manier om een target te krijgen: draai `iperf3 -s` op een andere machine op het netwerk (een desktop, een NAS, een Raspberry Pi) en richt `iperf3 -c <die-machine> -P 4` erop vanaf de laptop, voor en na elke wijziging.

## Meer lezen

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/) — de patch uit december 2023 die de driver-default omzette
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches) — een ingrijpendere driverpatch van derden voor dezelfde chip (disconnects, doorvoer, instabiliteit); nuttige achtergrond, geen aanbeveling van deze pagina om zomaar te installeren
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html) — upstream-werk aan hetzelfde ASPM-doorvoerprobleem voor de nieuwere MT7927
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/) — de community reverse-engineering-inspanning achter MT7927-support
- [Known Issues — Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/) — een lopende lijst van chip-niveau issues en hun status
