---
title: "Secure Boot on Bazzite"
weight: 4
prev: docs/hardware/secure-boot-cachyos
next: docs/hardware/asusctl-rog-control
---

Bazzite boots with Secure Boot enabled. It uses shim, the Microsoft-signed bootloader that lets third-party systems boot under Secure Boot, so unlike CachyOS you don't have to turn Secure Boot off to install it and you don't have to enroll your own keys afterwards.

What you do have to do is enroll Universal Blue's key once. Without it, the kernel modules that aren't part of stock Fedora — the NVIDIA modules first among them — refuse to load.

> **Result:** UEFI Secure Boot passes with the stock configuration. The overall HSI score stays at **HSI:3!**, for the same hardware reason as on CachyOS: the Encrypted RAM check at HSI-4 isn't supported by this CPU.

## Enroll the key

```bash
ujust enroll-secure-boot-key
```

The password to use is `universalblue`.

On the next boot the blue **MOK Management** screen appears:

1. Select **Enroll MOK**
2. Select **Continue**
3. Select **Yes**
4. Enter `universalblue`
5. Reboot

{{< callout type="warning" >}}
MokManager shows nothing at all while you type the password — no dots, no asterisks. It looks like the keyboard isn't working. It is; type it and press enter.
{{< /callout >}}

## If Bazzite won't install with Secure Boot on

Some firmware refuses the installer before you ever get to enroll anything. The ASUS UEFI on the G16 is workable, but if you hit it:

{{% steps %}}

### Turn Secure Boot off

```bash
systemctl reboot --firmware-setup
```

In the ASUS UEFI (press **F7** for Advanced Mode if needed): **Security** → **Secure Boot** → set **Secure Boot Control** to **Disabled**, then **Save & Exit** (F10).

### Install Bazzite

Then boot into it as normal.

### Enroll the key

```bash
ujust enroll-secure-boot-key
```

Go through MokManager as above.

### Turn Secure Boot back on

```bash
systemctl reboot --firmware-setup
```

**Security** → **Secure Boot** → **Secure Boot Control** → **Enabled** → Save & Exit.

{{% /steps %}}

## Verification

```bash
mokutil --sb-state
```

Expected: `SecureBoot enabled`.

That the key actually took is best confirmed by the thing that needed it:

```bash
lsmod | grep nvidia
```

If the NVIDIA modules are loaded with Secure Boot on, the key is enrolled. If they aren't, it isn't — that is the single most common cause of a Bazzite install with no GPU acceleration.

```bash
fwupdmgr security
```

The **UEFI Secure Boot** line under HSI-1 should show **Enabled**. GNOME Settings → Privacy & Security → Device Security shows the same thing with less shouting.

## Why not your own keys

On CachyOS the interesting part is `sbctl`: clear the firmware keys, generate your own, sign the bootloader and kernel yourself. You can't do that here in any way that survives, because you don't own the images — every update replaces the kernel and the bootloader with signed artifacts built by Universal Blue.

The way to a fully self-owned chain of trust on an atomic system is to build and sign your own image, which is a different project from configuring this laptop. [secureblue](https://github.com/secureblue/secureblue) is where to look if that's what you want.

For everyone else, the honest summary is the one from the CachyOS page: Secure Boot covers the boot chain and stops there.

## Remaining HSI Failures Explained

### Encrypted RAM (HSI-4)

**Not fixable on this hardware.** The Ryzen AI 9 HX 370 does not support AMD Secure Memory Encryption (SME) in the mode fwupd checks for. This is a hardware capability limitation, not a configuration issue, and it applies on both distributions.

### Linux Kernel Verification (Tainted)

Still tainted here, but for a different reason than on CachyOS. The `-nvidia-open` images use NVIDIA's open kernel modules, which are GPL-compatible and therefore do not set the *proprietary module* taint flag. They are still out-of-tree modules, which sets the `O` flag on its own:

```bash
cat /proc/sys/kernel/tainted
```

Not a security vulnerability, and not something you can configure away while using the NVIDIA driver at all.

### Linux Kernel Lockdown

Kernel lockdown restricts unsigned kernel modules and certain privileged operations. The NVIDIA driver would break under it. Not something I'd recommend for day-to-day use on this hardware.

{{< callout type="info" >}}
Troubleshooting for Secure Boot setup is documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}

## References

- [Bazzite: Secure Boot Guide](https://docs.bazzite.gg/General/Installation_Guide/secure_boot/)
- [Universal Blue](https://universal-blue.org/)
- [secureblue](https://github.com/secureblue/secureblue)
- [fwupd HSI Documentation](https://fwupd.github.io/hsi.html)
