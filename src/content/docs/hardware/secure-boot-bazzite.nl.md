---
title: "Secure Boot op Bazzite"
weight: 4
prev: docs/hardware/secure-boot-cachyos
next: docs/hardware/asusctl-rog-control
---

Bazzite start op met Secure Boot aan. Het gebruikt shim, de door Microsoft ondertekende bootloader waarmee distributies van derden onder Secure Boot kunnen opstarten, dus anders dan bij CachyOS hoef je Secure Boot niet uit te zetten om te installeren en hoef je achteraf geen eigen sleutels in te schrijven.

Wat je wél moet doen is de sleutel van Universal Blue één keer inschrijven. Zonder die sleutel weigeren de kernelmodules die niet in standaard-Fedora zitten te laden, en de NVIDIA-modules voorop.

> **Resultaat:** UEFI Secure Boot slaagt met de standaardconfiguratie. De HSI-score blijft **HSI:3!**, om dezelfde hardware-reden als op CachyOS: de Encrypted RAM-controle op HSI-4 wordt door deze CPU niet ondersteund.

## De sleutel inschrijven

```bash
ujust enroll-secure-boot-key
```

Het wachtwoord dat je gebruikt is `universalblue`.

Bij de volgende start verschijnt het blauwe **MOK Management**-scherm:

1. Kies **Enroll MOK**
2. Kies **Continue**
3. Kies **Yes**
4. Voer `universalblue` in
5. Herstart

{{< callout type="warning" >}}
MokManager laat tijdens het typen van het wachtwoord helemaal niets zien — geen puntjes, geen sterretjes. Het lijkt alsof het toetsenbord niet werkt. Dat werkt wel; typ het in en druk op enter.
{{< /callout >}}

## Als Bazzite niet wil installeren met Secure Boot aan

Sommige firmware weigert de installer voordat je überhaupt iets kunt inschrijven. De ASUS UEFI op de G16 is werkbaar, maar loop je ertegenaan:

{{% steps %}}

### Zet Secure Boot uit

```bash
systemctl reboot --firmware-setup
```

In de ASUS UEFI (druk zo nodig op **F7** voor Advanced Mode): **Security** → **Secure Boot** → zet **Secure Boot Control** op **Disabled** en daarna **Save & Exit** (F10).

### Installeer Bazzite

Start daarna gewoon op.

### Schrijf de sleutel in

```bash
ujust enroll-secure-boot-key
```

Doorloop MokManager zoals hierboven.

### Zet Secure Boot weer aan

```bash
systemctl reboot --firmware-setup
```

**Security** → **Secure Boot** → **Secure Boot Control** → **Enabled** → Save & Exit.

{{% /steps %}}

## Verificatie

```bash
mokutil --sb-state
```

Verwacht: `SecureBoot enabled`.

Of de sleutel echt aangekomen is, controleer je het beste met datgene wat hem nodig had:

```bash
lsmod | grep nvidia
```

Laden de NVIDIA-modules met Secure Boot aan, dan is de sleutel ingeschreven. Laden ze niet, dan is dat niet zo — en dat is verreweg de meest voorkomende oorzaak van een Bazzite-installatie zonder GPU-versnelling.

```bash
fwupdmgr security
```

De regel **UEFI Secure Boot** onder HSI-1 hoort nu **Enabled** te tonen. GNOME Instellingen → Privacy & Security → Device Security laat hetzelfde zien, wat rustiger.

## Waarom hier geen eigen sleutels

Op CachyOS is `sbctl` het interessante deel: de firmwaresleutels wissen, je eigen sleutels maken en de bootloader en kernel zelf ondertekenen. Dat kan hier niet op een manier die blijft werken, want de images zijn niet van jou — elke update vervangt de kernel en de bootloader door ondertekende artefacten van Universal Blue.

De route naar een volledig eigen vertrouwensketen op een atomic systeem is je eigen image bouwen en ondertekenen, en dat is een ander project dan deze laptop inrichten. [secureblue](https://github.com/secureblue/secureblue) is waar je dan moet kijken.

Voor alle anderen geldt dezelfde eerlijke samenvatting als op de CachyOS-pagina: Secure Boot dekt de bootketen en houdt daar op.

## Resterende HSI-fouten verklaard

### Encrypted RAM (HSI-4)

**Niet op te lossen op deze hardware.** De Ryzen AI 9 HX 370 ondersteunt AMD Secure Memory Encryption (SME) niet in de vorm waar fwupd op controleert. Dat is een beperking van de hardware, geen configuratiekwestie, en het geldt op allebei de distributies.

### Linux Kernel Verification (Tainted)

Hier ook tainted, maar om een andere reden dan op CachyOS. De `-nvidia-open`-images gebruiken NVIDIA's open kernelmodules, die GPL-compatibel zijn en dus niet de taint-vlag voor *proprietary modules* zetten. Het blijven wel out-of-tree modules, en dat zet op zichzelf al de `O`-vlag:

```bash
cat /proc/sys/kernel/tainted
```

Geen beveiligingslek, en niets dat je wegconfigureert zolang je de NVIDIA-driver überhaupt gebruikt.

### Linux Kernel Lockdown

Kernel lockdown beperkt niet-ondertekende kernelmodules en bepaalde geprivilegieerde operaties. De NVIDIA-driver zou eronder breken. Niets dat ik voor dagelijks gebruik op deze hardware zou aanraden.

{{< callout type="info" >}}
Troubleshooting voor het instellen van Secure Boot staat op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}

## Referenties

- [Bazzite: Secure Boot Guide](https://docs.bazzite.gg/General/Installation_Guide/secure_boot/)
- [Universal Blue](https://universal-blue.org/)
- [secureblue](https://github.com/secureblue/secureblue)
- [fwupd HSI-documentatie](https://fwupd.github.io/hsi.html)
