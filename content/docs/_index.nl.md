---
title: ""
weight: 1
toc: false
---

# Mijn setup-notities

Alles wat ik heb opgeschreven tijdens het draaien van CachyOS op de ROG Zephyrus G16. Begin bij Aan de slag als je vanaf nul instelt, of ga direct naar de handleiding die je nodig hebt.

## Aan de slag

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Aan de slag"
    subtitle="Van schone CachyOS-installatie tot volledig geconfigureerd systeem"
    icon="play"
    link="getting-started"
  >}}
{{< /hextra/feature-grid >}}

## Hardware & Drivers

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="NVIDIA Driver Installatie"
    subtitle="Proprietary NVIDIA drivers met Secure Boot op CachyOS"
    icon="chip"
    link="hardware/nvidia-driver-installation"
  >}}
  {{< hextra/feature-card
    title="Secure Boot"
    subtitle="Aangepaste ondertekeningssleutels met sbctl, UEFI Secure Boot ingeschakeld"
    icon="shield-check"
    link="hardware/secure-boot"
  >}}
  {{< hextra/feature-card
    title="asusctl & ROG Control Center"
    subtitle="Fan curves, performance profielen, GPU switching, Slash LED"
    icon="adjustments"
    link="hardware/asusctl-rog-control"
  >}}
{{< /hextra/feature-grid >}}

## Beveiliging & Privacy

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="YubiKey 5C NFC"
    subtitle="FIDO2 LUKS poging en wat vandaag werkt"
    icon="key"
    link="security/yubikey"
  >}}
  {{< hextra/feature-card
    title="GDM Autologin"
    subtitle="GDM inlogscherm overslaan na LUKS ontgrendeling"
    icon="lock-open"
    link="security/autologin"
  >}}
{{< /hextra/feature-grid >}}

## Applicaties

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Applicaties"
    subtitle="Browser, communicatie, ontwikkeltools en systeemconfiguratie"
    icon="collection"
    link="applications"
  >}}
{{< /hextra/feature-grid >}}

## Netwerk

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="eduroam Setup"
    subtitle="PEAP/MSCHAPv2 configuratie die daadwerkelijk werkt op Linux"
    icon="wifi"
    link="networking/eduroam-network-installation"
  >}}
{{< /hextra/feature-grid >}}

## Virtualisatie

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Windows 11 VM Setup"
    subtitle="KVM/QEMU VM met VirtIO en SPICE GL"
    icon="desktop-computer"
    link="virtualization/vm-setup"
  >}}
  {{< hextra/feature-card
    title="Looking Glass B7"
    subtitle="GPU passthrough via Looking Glass, werkt niet op deze hardware"
    icon="eye"
    link="virtualization/looking-glass-attempt"
  >}}
  {{< hextra/feature-card
    title="Podman & Podman Desktop"
    subtitle="Docker-vervanging met rootless containers en een desktop GUI"
    icon="server"
    link="virtualization/podman"
  >}}
{{< /hextra/feature-grid >}}

## Bekende Problemen

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Bekende Problemen"
    subtitle="Problemen waarvoor nog geen oplossing is"
    icon="exclamation-circle"
    link="known-issues"
  >}}
{{< /hextra/feature-grid >}}
