---
title: "MT7925 Wifi-prestaties"
weight: 2
prev: docs/networking/eduroam-network-installation
next: docs/virtualization/vm-setup
---

De G16 GA605WV heeft een MediaTek Wi-Fi 7 MT7925-kaart. Wegvallende verbindingen, traag roamen tussen mesh-nodes, of downloadsnelheden ruim onder wat de verbinding zou moeten geven: deze pagina behandelt alle drie.

Dit is een script dat drie fixes tegelijk toepast (NetworkManager-powersave, PCIe ASPM en een wireless-stack-queuelimiet), elk met een echt effect gemeten op deze hardware, plus een optionele extra (Bluetooth uit) die je zelf kunt aanzetten. Het heeft Python 3.14+ nodig (alleen standaardbibliotheek) en `pkexec` voor de bevoegde stappen -- één wachtwoordprompt per commando, die alle bevoegde stappen in dat commando dekt, niet één prompt per stap.

{{< callout type="info" >}}
**Geverifieerd op deze hardware.** Getest met `iperf3` tegen een lokale server op een 2,5GbE-netwerk met UniFi. Stock: ~300 Mbit/s. Getuned: 500-608 Mbit/s, meestal 560+. Jouw cijfers variëren met AP, signaalsterkte en kernelversie, maar de fixes zelf zijn bevestigd, niet theoretisch.

Testomstandigheden, want die beïnvloeden de cijfers: een UniFi U7 Pro access point, in een houten kast, ongeveer 10 meter van de laptop met een muur ertussen. 6GHz-band, 160MHz-kanaal (het maximum van deze kaart), signaal variërend van -62 tot -71 dBm over de runs, meestal -63 tot -66 dBm. Dat is een realistische alledaagse afstand, geen beste-geval-test in dezelfde kamer, dus zie de cijfers hierboven als een redelijke baseline en niet als plafond.
{{< /callout >}}

{{< callout type="warning" >}}
**Is dit nog steeds de moeite waard?** Voorlopig wel -- elke fix hieronder heeft een gemeten, reproduceerbaar effect en kost niets behalve een herstart. Maar zie het niet aan voor "de kaart gefixt": dit zijn workarounds voor driver-defaults die nooit getuned hadden hoeven worden, geen herschrijving van wat de silicon kan. Afgezet tegen de wifi-chip van een telefoon van twee jaar oud (zie [Resultaten](#resultaten) hieronder) is de eerlijke conclusie dat de MT7925 zelf gewoon een middelmatige Wi-Fi 7-kaart is, en geen enkele tuning verandert dat. Het goede nieuws: dit is geen doodlopende weg. MediaTek's Wi-Fi 7-stack wordt nog steeds actief upstream ontwikkeld, met patches die nog deze testweek van deze pagina landden -- zie [Meer lezen](#meer-lezen) hieronder. Liever wachten tot de driver volwassener is dan zelf tunen? Ook een prima keuze.
{{< /callout >}}

## Installatie

{{% steps %}}

### Downloaden en verifiëren

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/mt7925-tune.py
echo "cf5aa114d872c6480525b55f637fab346337f9cbbdce9657e0688fd48cac1247  mt7925-tune.py" | sha256sum -c
```

### Toepassen

```bash
python3 mt7925-tune.py enable
```

Herstart daarna. Eén van de drie fixes (PCIe ASPM) is een kernel-moduleparameter, alleen gelezen bij het laden van de module.

Wil je ook de optionele Bluetooth-uit-extra (zie tabel hieronder)?

```bash
python3 mt7925-tune.py enable --bluetooth-off
```

{{% /steps %}}

Bron: [mt7925-tune.py](/scripts/mt7925-tune.py). SHA-256 `cf5aa114d872c6480525b55f637fab346337f9cbbdce9657e0688fd48cac1247`.

| Fix (toegepast door `enable`) | Wat het doet |
|---|---|
| NetworkManager's wifi-powersave uitzetten | De meest voorkomende oorzaak van drops en traag roamen op mesh-netwerken |
| PCIe ASPM voor de kaart uitzetten | De energiestatus van de PCIe-link zelf, niet de radio. De belangrijkste doorvoerfix |
| AQL Best Effort-limiet verhogen | `mac80211` begrenst hoeveel data per verkeersklasse in de wachtrij mag staan om latency laag te houden onder congestie. De standaardlimiet kiest voor eerlijkheid boven het verzadigen van één stream. Trade-off: minder marge voor latency-gevoelig verkeer (calls, gaming) dat de radio deelt onder belasting |

| Optionele extra (`--bluetooth-off`, niet standaard toegepast) | Wat het doet |
|---|---|
| Bluetooth uit | De MT7925 is een combo Wi-Fi+Bluetooth-chip die dezelfde silicon en antennepaden deelt. Haalt een bron van variatie weg, ten koste van Bluetooth. Geen van de gemeten fixes hierboven, dus jouw keuze, niet die van het script |

`python3 mt7925-tune.py status` laat precies zien wat nu actief is, wat nog een herstart nodig heeft, en welke hardware en driver/firmwareversie gedetecteerd zijn. `python3 mt7925-tune.py disable` maakt alles ongedaan, Bluetooth inbegrepen.

{{< callout type="info" >}}
**Bewust weggelaten:** `disable_eht=1` duikt op in sommige externe gidsen, maar bestaat alleen in out-of-tree patchsets, niet in de mainline-driver die deze G16 draait. CPU-governor- en power-profile-wijzigingen hielpen ook in tests, maar dat is een systeembrede afweging, geen wifi-specifieke, dus het script raakt ze niet aan. Oudere gidsen noemen ook het vastzetten van de `power_save`-moduleparameter van de driver zelf; op de kernel van deze G16 (7.2.4) bestaat die parameter niet meer (`dmesg` toont `mt7925e: unknown parameter 'power_save' ignored`), dus het script slaat die ook over.
{{< /callout >}}

## Resultaten

| Configuratie | Doorvoer |
|---|---|
| Stock | ~300 Mbit/s |
| Alleen ASPM uit + NM-powersave uit | 410-450 Mbit/s |
| Alles, inclusief de optionele Bluetooth-uit-extra (`enable --bluetooth-off`) | 500-608 Mbit/s, meestal 560+ |

Ter referentie: een telefoon (Samsung Galaxy S24 Ultra) op dezelfde AP mat 439-811 Mbit/s over meerdere runs, gemiddeld rond de 545 Mbit/s, dus de getunede G16 zit nu in hetzelfde bereik als de wifi-radio van een moderne telefoon hier. Op een sterkere/dichterbije AP haalde diezelfde telefoon 1,24 Gbit/s, ruim boven wat het 160MHz-plafond van de MT7925 ooit kan bereiken, ongeacht signaalkwaliteit (zie [hardware-plafond](#het-hardware-plafond) hieronder).

Om even bij stil te staan: die telefoon kwam uit in januari 2024. Een speciaal gebouwde M.2 2230 Wi-Fi 7-kaart in een 2024/2025-gaminglaptop, getuned tot zijn eigen plafond, verliest nog steeds van de wifi-chip van een telefoon van twee jaar oud. Dat is geen configuratieprobleem dat dit script kan wegtunen -- de MT7925 is, op basis van dit bewijs, gewoon een middelmatige kaart. De fixes hierboven brengen 'm waar hij uit de doos had moeten zitten, niet waar hij eigenlijk zou moeten zitten.

{{< callout type="warning" >}}
Verwacht variatie tussen runs, ook in een stabiele, getunede staat (herhaalde runs van 20s liepen uiteen van 509-598 Mbit/s zonder dat er iets veranderde). Direct na een herstart of reconnect is het erger: retries kunnen fors pieken voordat de verbinding settelt (gezien: 3000+ retries in één run). Beoordeel de fix op een paar runs, niet op één, en nooit op de allereerste test na een herstart.
{{< /callout >}}

**Op UniFi:** heb je meerdere AP's, dan is de standaard 6GHz roaming RSSI-drempel (-88 dBm) permissief genoeg dat een client op een zwak signaal blijft hangen ruim voorbij het punt waar retries beginnen op te lopen (merkbaar onder ongeveer -62 dBm in tests). Aanscherpen naar ongeveer -70 dBm (jouw SSID → Advanced → Roaming Assistance → Handoff Suggestions) hielp.

## Het hardware-plafond

De MT7925 is hardware-gelimiteerd tot 160MHz-kanaalbreedte en 2×2 MIMO, bevestigd via `iw phy phy0 info`: `Supported Channel Width: 160 MHz`, `Rx/Tx Max NSS: 2`, helemaal geen `EHT-MCS Map (BW = 320)`-vermelding. Een Wi-Fi 7 access point kan 320MHz 6GHz-kanalen aanbieden; deze kaart kan daar altijd maar de helft van gebruiken. Geen driver, firmware of instelling verandert dat. Verwacht met de fixes hierboven ruwweg een verdubbeling van de doorvoer uit de doos, geen multi-gigabit wifi.

## Als jouw cijfers niet overeenkomen met die van deze pagina

De cijfers hierboven gaan uit van een redelijk sterk 6GHz-signaal. 6GHz heeft minder bereik en muurpenetratie dan 5GHz, en de MT7925 valt stilletjes terug van 2 spatial streams naar 1 ruim voordat de verbinding daadwerkelijk wegvalt -- wat het plafond ruwweg halveert, bovenop wat het zwakkere signaal al kost.

Echt voorbeeld, dezelfde laptop en access point, alleen de afstand veranderde:

| | Verder van de AP | Dichter bij de AP |
|---|---|---|
| Signaal | -70 tot -73 dBm | -63 dBm |
| Onderhandelde rate (ook in `status`'s "Current link") | `EHT-NSS 1`, 432-576 Mbit/s | `EHT-NSS 2`, 1152,8 Mbit/s |
| `iperf3 -P 4`-doorvoer | ~170-260 Mbit/s | 583-594 Mbit/s |

Zelfde script, zelfde tuning, verder alles gelijk -- de enige variabele was afstand. `python3 mt7925-tune.py status` toont signaal en `EHT-NSS` in het "Current link"-onderdeel precies om deze reden: check eerst of je niet gewoon naar een signaalprobleem kijkt voordat je aanneemt dat een fix niet werkt. Springt `EHT-NSS` terug naar 2 en stijgt de doorvoer als je dichterbij gaat staan? Dan is het bereik, geen kapotte kaart.

## Drops en roaming-problemen diagnosticeren

```bash
journalctl -k -f | grep -iE "mt7925|deauth|disassoc|beacon loss"
```

Laat dit open staan tijdens normaal gebruik, voor en na, om te vergelijken hoe vaak er iets verschijnt.

Voor roaming specifiek: ping continu naar het LAN-IP van een mesh-node terwijl je tussen nodes loopt (geen internet-host, om WAN-problemen buiten beeld te houden):

```bash
ping -D -i 0.2 <ip-mesh-node>
```

`iw dev <iface> link` laat zien met welke node je op dat moment verbonden bent, handig om een echte roam te onderscheiden van een "sticky" client die een zwakke node niet loslaat.

Voor doorvoersnelheid: `iperf3` tegen iets op je eigen LAN is beter dan een speedtest tegen het internet, want het haalt je ISP en WAN-pad als variabelen weg:

```bash
iperf3 -s                              # op een andere machine op het netwerk
iperf3 -c <die-machine> -P 4           # vanaf de laptop
```

## Moet je de kaart vervangen?

Waarschijnlijk nog niet. De kaart zit in een socket (M.2 2230, key E) en ROG-laptops hanteren geen BIOS-whitelist, dus een swap is fysiek mogelijk.

{{% details title="Waarom niet, in meer detail" closed="true" %}}

De voor de hand liggende kandidaat, MT7927, voegt 320MHz-support toe en heeft mainline Linux-support sinds kernel 7.2, maar praktijkmeldingen tonen *hogere* TX-retransmissiepercentages dan MT7925 op verder identieke hardware, omschreven als firmware-niveau en niet op te lossen met een driverpatch. De driver is ook jong, gemerged in mainline in 2026. Deze zelfde MT7925-driver was in januari 2026 aanzienlijk slechter dan hij nu is; MT7927 staat er nu ongeveer voor zoals MT7925 er ongeveer een jaar geleden voor stond.

Qualcomm's huidige Wi-Fi 7-kaart (QCNCM865/FastConnect 7800) is ook niet beter: meldingen dat de 6GHz-band niet verschijnt in scans, niet-functionerende MLO, en ~33% lagere doorvoer dan Windows op dezelfde hardware. Qualcomm's interessantere aankondiging, de FastConnect 8800 (Wi-Fi 8, 4×4-radio, tot 11,6 Gbit/s), zit ten vroegste eind 2026 in producten.

{{% /details %}}

{{% details title="Je driver- en firmwareversie checken" closed="true" %}}

`python3 mt7925-tune.py status` laat dit allemaal automatisch zien (kernel/driverversie, de firmwareversie en bouwdatum uit `dmesg`, en de `linux-firmware-mediatek`-packageversie op Arch-gebaseerde distro's). Handmatig checken kan ook:

```bash
uname -r                                                          # kernel = driverversie, zit in-tree
sudo dmesg | grep -i "mt7925e.*Firmware\|mt7925e.*HW/SW"          # firmwareversie
pacman -Qi linux-firmware-mediatek | grep Version                  # firmware-packageversie
```

{{% /details %}}

{{% details title="Waar je actieve ontwikkeling volgt" closed="true" %}}

Er wordt nog steeds actief aan deze chip gewerkt; er landden patches nog deze week tijdens het testen voor deze pagina. `python3 mt7925-tune.py status` toont dezelfde links, zodat je ze niet hoeft te onthouden.

- [lore.kernel.org/linux-wireless](https://lore.kernel.org/linux-wireless/): de officiële patch-mailinglist. Zoek op "mt7925".
- [ratatoskr.run](https://ratatoskr.run/): een beter leesbaar webarchief van dezelfde mailinglists.
- [github.com/openwrt/mt76](https://github.com/openwrt/mt76): spiegel van de driverbroncode, makkelijker te doorbladeren dan de kernel.org-tree.

Recent bewijs dat dit beweegt, niet stilstaat: een [patch die scans tijdens suspend overslaat](https://ratatoskr.run/linux-mediatek/2026/04/3520789) landde in april 2026 om command-timeouts bij resume te stoppen, en een [mt7925-firmware-update](https://ratatoskr.run/linux-wireless/2026/08/17426467/t) ging uit in augustus 2026. Geen van beide is op zichzelf spectaculair, maar het tempo is het punt: deze driver wordt de meeste maanden aangeraakt, niet één keer per jaar.

{{% /details %}}

## Meer lezen

- [wifi: mt76: mt7921/mt7925: Disable powersaving by default](https://patchwork.kernel.org/project/linux-wireless/patch/20231212090852.162787-1-mario.limonciello@amd.com/): de patch uit december 2023 die de driver-default omzette.
- [burakgon/mt7925-wifi-patches](https://github.com/burakgon/mt7925-wifi-patches): een ingrijpendere driverpatch van derden voor dezelfde chip. Achtergrondinformatie, geen aanbeveling van deze pagina om zomaar te installeren.
- [wifi: mt76: mt7925: disable ASPM for MT7927 to fix throughput collapse](https://lkml.iu.edu/hypermail/linux/kernel/2603.0/12526.html): upstream-werk aan hetzelfde ASPM-probleem voor de nieuwere MT7927.
- [MT7927 WiFi on Linux: Making It Work](https://jetm.github.io/blog/posts/mt7927-wifi-making-it-work/): de community reverse-engineering-inspanning achter MT7927-support.
- [Known Issues, Linux MT7921/MT7925 WiFi Driver Fixes](https://zbowling.github.io/mt7925/issues/known-issues/): een lopende lijst van chip-niveau issues en hun status.
- [From "Replace It with Intel" to Upstream: Bringing MediaTek Bluetooth/WiFi 7 to Linux](https://www.linaro.org/blog/from-replace-it-with-intel-to-upstream-bringing-mediatek-bluetooth-wifi-7-to-linux/): Linaro's verhaal over hoe MediaTek's Wi-Fi 7-support van "niet te ondersteunen, vervang de kaart" naar actief geüpstreamd ging -- nuttige context voor waarom de situatie van deze chip er over een jaar beter uitziet dan vandaag.
- [MT7925 WiFi Driver Fixes, nu als DKMS-package](https://community.frame.work/t/mt7925-wifi-driver-fixes-now-available-as-dkms-package/79777): de community-fixset uit de lijst "Waar je actieve ontwikkeling volgt" hierboven, nu installeerbaar zonder handmatig patchen -- een teken dat de fixes stabiel genoeg worden om te packagen.
