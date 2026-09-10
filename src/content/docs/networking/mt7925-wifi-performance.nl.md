---
title: "MT7925 Wifi-prestaties"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

De G16 GA605WV heeft een MediaTek Wi-Fi 7 MT7925-kaart. Zie je af en toe verbindingen wegvallen, traag roamen tussen mesh-nodes, of downloadsnelheden die duidelijk lager liggen dan wat de verbinding zou moeten geven? Dan is deze pagina voor jou.

{{< callout type="warning" >}}
**Nog niet geverifieerd op deze hardware.** Alles hieronder is gebaseerd op goed gedocumenteerde meldingen voor dezelfde MT7925-chip op andere laptops (Framework 13, andere ASUS ROG-modellen, diverse Arch/CachyOS-forumthreads), niet op tests op deze specifieke G16. Zie het als startpunt, niet als bevestigde fix, totdat deze melding is bijgewerkt.
{{< /callout >}}

## Drie losse oorzaken, geen één

Dit soort klachten wordt meestal op "wifi-powersave" geschoven, maar op deze chip zitten drie onafhankelijke lagen die elk dit gedrag kunnen veroorzaken, en een fix voor de één raakt de andere niet:

1. **De powersave van de `mt7925e`-driver zelf.** Een patch uit december 2023 zette de standaardinstelling van de driver op powersave *uit*. Op een actuele kernel staat dit vrijwel zeker al uit, maar het is de moeite waard om dit expliciet vast te zetten in plaats van op de default te vertrouwen.
2. **NetworkManager's eigen 802.11-powersave.** Dit is een aparte laag, los van wat de driver standaard doet. NetworkManager kan de radio nog steeds in standaard powersave-modus zetten ongeacht de driverinstelling, en dit is de meest gerapporteerde oorzaak van drops en traag roamen op mesh-netwerken.
3. **PCIe ASPM (Active State Power Management).** Een compleet ander mechanisme, over de energiestatus van de PCIe-link zelf, niet de radio. Dit is in 2026 nog steeds een actief punt van upstream-ontwikkeling en is de waarschijnlijkere verklaring voor specifiek matige doorvoersnelheid (meldingen variëren van "merkbaar trager" tot een vrijwel totale instorting van de doorvoer).

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

### Zet de powersave van de driver zelf expliciet uit

```bash
echo "options mt7925e power_save=0" | sudo tee /etc/modprobe.d/mt7925e.conf
```

Riem-en-bretels: maakt de instelling expliciet in plaats van te vertrouwen op de driver-default die zo blijft na kernelupdates.

### Check op een driver-eigen ASPM-schakelaar voordat je iets systeembreeds aanraakt

```bash
modinfo mt7925e | grep -i aspm
```

Staat hier een parameter (bijv. `disable_aspm`)? Voeg die toe aan hetzelfde bestand uit de vorige stap, bijvoorbeeld:

```bash
echo "options mt7925e disable_aspm=1" | sudo tee -a /etc/modprobe.d/mt7925e.conf
```

Komt er niets uit? Dan is de enige overgebleven optie de systeembrede kernel-bootparameter `pcie_aspm=off`. Die zet ASPM uit voor **alle** PCIe-apparaten, niet alleen wifi, en kost dus wat accuduur in ruil voor doorvoersnelheid — pas de moeite waard als de twee stappen hierboven niets oplossen.

### Herstart

```bash
sudo reboot
```

{{% /steps %}}

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

**Doorvoersnelheid:** dezelfde speedtest (bv. `fast.com`, `speedtest-cli`), zelfde plek, zelfde moment van de dag, voor en na elke stap.

## Meer lezen

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/) — de patch uit december 2023 die de driver-default omzette
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches) — een ingrijpendere driverpatch van derden voor dezelfde chip (disconnects, doorvoer, instabiliteit); nuttige achtergrond, geen aanbeveling van deze pagina om zomaar te installeren
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html) — upstream-werk aan hetzelfde ASPM-doorvoerprobleem voor de nieuwere MT7927
