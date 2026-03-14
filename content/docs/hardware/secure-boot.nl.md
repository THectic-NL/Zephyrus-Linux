---
title: "Secure Boot"
weight: 2
---

Om CachyOS te installeren moet Secure Boot eerst uit. Anders dan Ubuntu of Fedora gebruikt CachyOS geen shim, een door Microsoft ondertekende bootloader waarmee distributies van derden kunnen opstarten onder Secure Boot. Zonder shim blokkeert Secure Boot de CachyOS-bootloader bij het opstarten, waardoor het voor de installatie uitgeschakeld moet worden ([CachyOS installatiedocumentatie](https://wiki.cachyos.org/installation/installation_on_root/)).

Na de installatie kan Secure Boot opnieuw worden ingeschakeld met je eigen ondertekeningssleutels. Dit is hoe ik dat heb gedaan met `sbctl`.

> **Resultaat:** UEFI Secure Boot gaat van **Fail** naar **Pass** na het voltooien van deze handleiding. De algehele HSI-score blijft **HSI:3!** (de Encrypted RAM-check op HSI-4 wordt niet ondersteund op deze hardware, waardoor HSI:4 niet haalbaar is).


## Even een kanttekening

Secure Boot klinkt als een stevige beveiligingsfunctie, en technisch gezien doet het wat het belooft: het verifieert dat de bootloader en kernel zijn ondertekend door een vertrouwde sleutel. Maar het is de moeite waard om even stil te staan bij wat "vertrouwd" hier eigenlijk betekent.

Het Secure Boot-ecosysteem wordt beheerd door Microsoft. Zij beheren de signing-servers, geven de certificaten uit en bepalen welke bootloaders en shims toegang krijgen tot de vertrouwensketen. De meeste hardware wordt geleverd met de sleutels van Microsoft al ingeschreven, wat betekent dat hun sleutels standaard bepalen wat "secure" is op jouw apparaat. Dat is geen onafhankelijke standaard; het is een door een leverancier beheerde lijst.

De `--microsoft` vlag in stap 3 maakt dit direct zichtbaar: zelfs met je eigen sleutels moet je de UEFI CA-certificaten van Microsoft meenemen, anders laadt je GPU-firmware niet. Hun sleutels zitten structureel ingebakken in hoe de hardware werkt.

Maakt dat Secure Boot nutteloos? Nee. Je eigen bootloader en kernel ondertekenen met sleutels die jij beheert verhoogt de lat echt voor bepaalde aanvallen (evil maid, gemanipuleerde bootloader, etc.). Maar als Linux-gebruiker moet je dit in perspectief blijven zien: dit is geen neutrale, onafhankelijke beveiligingsstandaard. Het is een door Microsoft beheerde poort, met alle voorbehouden van dien. Stel het in als het zinvol is voor jouw situatie, maak je er geen zorgen over als dat niet zo is, en laat de HSI-score geen doel op zich worden.


## Context van het beveiligingsrapport

Het uitvoeren van `fwupdmgr security` toont wat slaagt en wat niet. Na het inschakelen van Secure Boot zijn de overgebleven fouten op deze hardware:

| Test | Na deze handleiding | Reden |
|---|---|---|
| UEFI Secure Boot | ✓ Pass | Opgelost door deze handleiding |
| Encrypted RAM (HSI-4) | ✗ Not Supported | Hardwarebeperking: Ryzen AI 9 HX 370 implementeert AMD SME/TME niet |
| Linux Kernel Verification | ✗ Tainted | Proprietary NVIDIA-driver vervuilt de kernel permanent (verwacht gedrag) |
| Linux Kernel Lockdown | ✗ Not Enabled | Vereist kernel lockdown-modus, niet behandeld hier; conflicteert met proprietary modules |

![fwupdmgr security uitvoer met HSI:3 en UEFI Secure Boot uitgeschakeld](/images/secure-boot-hsi-report.avif)


## Hoe het werkt

In plaats van de shim → MOK → kernel-keten die veel distributies gebruiken, schrijft `sbctl` aangepaste Secure Boot-sleutels rechtstreeks in de UEFI-firmware in. De bootloader en het kernel EFI-image worden daarna ondertekend met die sleutels. Geen shim of MOK Manager nodig.

`sbctl` wordt ook geleverd met een pacman-hook die alle geregistreerde EFI-binaries automatisch opnieuw ondertekent na kernel- of bootloader-updates, iets wat je na de initiële setup niet meer handmatig hoeft te doen.


## Installatie

```bash
sudo pacman -S sbctl
```


## Stap 1: UEFI Setup Mode activeren

Setup Mode is een UEFI-toestand waarbij er nog geen Secure Boot-sleutels zijn ingeschreven, waardoor nieuwe sleutels kunnen worden toegevoegd. Je moet eerst in deze toestand komen voordat je sleutels aanmaakt.

Herstart naar de ASUS UEFI:

```bash
systemctl reboot --firmware-setup
```

In de ASUS UEFI (druk op **F7** voor Geavanceerde Modus indien nodig):

1. Ga naar het tabblad **Security**
2. Selecteer **Secure Boot**
3. Zet **Secure Boot Control** op **Enabled**
4. Open **Key Management**
5. Selecteer **Clear Secure Boot Keys** (of **Reset to Setup Mode** indien beschikbaar)
6. Bevestig en **Save & Exit** (F10)

Controleer na het herstarten in CachyOS of Setup Mode actief is:

```bash
sudo sbctl status
```

Verwachte uitvoer:

```
Installed:    ✗ sbctl is not installed
Owner GUID:   <jouw-guid>
Setup Mode:   ✗ Enabled
Secure Boot:  ✗ Disabled
Vendor Keys:  none
```

`Setup Mode` met de waarde `Enabled` bevestigt dat de UEFI klaar is voor sleutelinschrijving. De `✗`-symbolen zijn hier geen fouten; ze geven alleen aan dat de sleutels nog niet zijn aangemaakt, wat precies de bedoeling is op dit punt.


## Stap 2: Sleutels aanmaken

```bash
sudo sbctl create-keys
```


## Stap 3: Sleutels inschrijven

Dit schrijft de aangepaste sleutels in de firmware in, inclusief de UEFI CA-certificaten van Microsoft. De `--microsoft`-vlag is vereist op ASUS-hardware; zonder die certificaten weigeren option ROMs (GPU-firmware) en andere UEFI-drivers van Microsoft te laden. Ik aarzelde een beetje om de sleutels van Microsoft mee te nemen, maar zonder die vlag start het systeem niet goed op.

```bash
sudo sbctl enroll-keys --microsoft
```


## Stap 4: EFI-binaries ondertekenen

Het ondertekeningsproces verschilt iets per bootloader.

### systemd-boot

Onderteken alle EFI-binaries en registreer ze in de sbctl-database. De `-s`-vlag is belangrijk; die zorgt ervoor dat bestanden automatisch opnieuw worden ondertekend na toekomstige updates:

```bash
sudo sbctl verify
sudo sbctl-batch-sign
sudo sbctl verify
```

Alle vermeldingen moeten `✓` tonen. Als er `✗` staan, onderteken ze dan handmatig:

```bash
sudo sbctl sign -s /pad/naar/niet-ondertekend.efi
```

CachyOS gebruikt `systemd-boot-update.service` om de systemd-boot binary bij te werken. Dit werkt buiten de standaard sbctl-hook om, dus de bronbinary moet expliciet worden ondertekend zodat die bij elke bootloader-update opnieuw wordt meegenomen:

```bash
sudo sbctl sign -s -o /usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed \
  /usr/lib/systemd/boot/efi/systemd-bootx64.efi
```

### Limine

Limine beheert zijn eigen ondertekeningsproces en vereist geen handtekeningen op kernel-images:

```bash
sudo limine-enroll-config
sudo limine-update
```


## Stap 5: Secure Boot inschakelen

Herstart opnieuw naar de ASUS UEFI:

```bash
systemctl reboot --firmware-setup
```

1. Ga naar **Security** → **Secure Boot**
2. Zet **Secure Boot Control** op **Enabled**
3. Bevestig dat de sleutels aanwezig zijn onder **Key Management** (DB, KEK, PK moeten allemaal gevuld zijn)
4. Save & Exit (F10)


## Verificatie

Na het herstarten ziet het er zo uit:

```bash
sudo sbctl status
```

```
Installed:    ✓ sbctl is installed
Owner GUID:   <jouw-guid>
Setup Mode:   ✓ Disabled
Secure Boot:  ✓ Enabled
Vendor Keys:  microsoft
```

![sbctl status bevestigt dat Secure Boot ingeschakeld is en Setup Mode uitgeschakeld is](/images/secure-boot-sbctl-status.avif)

```bash
fwupdmgr security
```

De regel **UEFI Secure Boot** onder HSI-1 moet nu **Enabled** tonen. De algehele score blijft **HSI:3!** (Encrypted RAM op HSI-4 wordt niet ondersteund op deze hardware, wat los staat van deze handleiding).

![fwupdmgr security uitvoer na het inschakelen van Secure Boot - HSI:3 met UEFI Secure Boot nu geslaagd onder HSI-1](/images/secure-boot-fwupdmgr-after.avif)

GNOME Instellingen → Privacy & Beveiliging → Apparaatbeveiliging bevestigt ook het resultaat:

![GNOME Apparaatbeveiliging met Protected en Secure Boot is Active](/images/secure-boot-gnome-after.avif)


## NVIDIA en kernelupdates

UEFI Secure Boot verifieert alleen de bootloader en het kernel-EFI-image. De NVIDIA-driver wordt als DKMS-module door de kernel geladen. In deze configuratie staat de kernel module-signatures niet af te dwingen, waardoor de NVIDIA-module blijft werken, maar de kernel als tainted wordt gemarkeerd. Extra module-signing voor NVIDIA valt daarom buiten de scope van deze handleiding.

> Wie ook kernelmodules cryptografisch wil afdwingen, moet NVIDIA-modules met dezelfde sleutel signen of de proprietary driver vermijden.

Na een kernelupdate activeert pacman beide:
1. sbctl-hook → ondertekent het nieuwe kernel EFI-image opnieuw
2. DKMS → bouwt NVIDIA-modules voor de nieuwe kernel opnieuw

Na updates is geen handmatige actie nodig.

> **Kernelvervuiling:** De proprietary NVIDIA-driver zal de kernel blijven vervuilen. Dit verschijnt als `Linux Kernel Verification: Tainted` in het HSI-rapport. Dit is verwacht; het betekent dat niet-open-source code is geladen, niet dat het systeem is aangetast.


## Overgebleven HSI-fouten uitgelegd

### Encrypted RAM (HSI-4)

**Niet oplosbaar op deze hardware.** De Ryzen AI 9 HX 370 ondersteunt AMD Secure Memory Encryption (SME) niet op de manier waarop fwupd dit controleert. Dit is een hardwarebeperking, geen configuratieprobleem.

### Linux Kernel Lockdown

Kernel lockdown kan worden ingeschakeld door `lockdown=integrity` toe te voegen aan de kernelparameters. Lockdown beperkt echter niet-ondertekende kernelmodules en bepaalde bevoorrechte bewerkingen, en de proprietary NVIDIA-driver zou niet werken onder lockdown-modus. Niet iets wat ik zou aanraden voor dagelijks gebruik op deze hardware.

### Linux Kernel Verification (Tainted)

Veroorzaakt door de proprietary NVIDIA-driver. Kan niet worden opgelost zolang proprietary NVIDIA-drivers worden gebruikt. Dit is geen beveiligingslek.


{{< callout type="info" >}}
Probleemoplossing voor Secure Boot staat op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}


## Referenties

- [CachyOS Wiki: Secure Boot Setup](https://wiki.cachyos.org/configuration/secure_boot_setup/)
- [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot)
- [sbctl GitHub](https://github.com/Foxboron/sbctl)
- [fwupd HSI-documentatie](https://fwupd.github.io/hsi.html)
