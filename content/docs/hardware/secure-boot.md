---
title: "Secure Boot"
weight: 12
---

To install CachyOS, Secure Boot has to be off first. Unlike Ubuntu or Fedora, CachyOS doesn't use shim — a Microsoft-signed bootloader that lets third-party systems boot under Secure Boot. Without it, Secure Boot blocks the CachyOS bootloader before it even starts, so it has to be disabled for installation ([CachyOS installation docs](https://wiki.cachyos.org/installation/installation_on_root/)).

After installation, it's possible to re-enable it with your own signing keys. This is how I did that using `sbctl`.

> **Result:** UEFI Secure Boot goes from **Fail** to **Pass** after completing this guide. The overall HSI score remains **HSI:3!** — the Encrypted RAM check at HSI-4 is not supported on this hardware, which prevents reaching HSI:4.


## Security Report Context

Running `fwupdmgr security` shows what passes and what doesn't. After enabling Secure Boot, the remaining failures on this hardware are:

| Test | After this guide | Reason |
|---|---|---|
| UEFI Secure Boot | ✓ Pass | Fixed by this guide |
| Encrypted RAM (HSI-4) | ✗ Not Supported | Hardware limitation — Ryzen AI 9 HX 370 does not implement AMD SME/TME |
| Linux Kernel Verification | ✗ Tainted | Proprietary NVIDIA driver permanently taints the kernel — expected |
| Linux Kernel Lockdown | ✗ Not Enabled | Requires kernel lockdown mode — not covered here, conflicts with proprietary modules |

![fwupdmgr security output showing HSI:3 with UEFI Secure Boot disabled](/images/secure-boot-hsi-report.png)


## How It Works

Instead of the shim → MOK → kernel chain that many distributions use, `sbctl` enrolls custom Secure Boot keys directly into the UEFI firmware. The bootloader and kernel EFI images are then signed with those keys. No shim or MOK Manager needed.

`sbctl` also ships with a pacman hook that automatically re-signs all registered EFI binaries after kernel or bootloader updates — so it's not something you have to think about after the initial setup.


## Installation

```bash
sudo pacman -S sbctl
```


## Step 1 — Enter UEFI Setup Mode

Setup Mode is a UEFI state where no Secure Boot keys are enrolled yet, which allows new ones to be added. You need to get into this state before creating keys.

Reboot into the ASUS UEFI:

```bash
systemctl reboot --firmware-setup
```

In the ASUS UEFI (press **F7** for Advanced Mode if needed):

1. Go to the **Security** tab
2. Select **Secure Boot**
3. Set **Secure Boot Control** to **Enabled**
4. Open **Key Management**
5. Select **Clear Secure Boot Keys** (or **Reset to Setup Mode** if available)
6. Confirm and **Save & Exit** (F10)

After rebooting into CachyOS, verify Setup Mode is active:

```bash
sudo sbctl status
```

Expected output:

```
Installed:    ✗ sbctl is not installed
Owner GUID:   <your-guid>
Setup Mode:   ✗ Enabled
Secure Boot:  ✗ Disabled
Vendor Keys:  none
```

`Setup Mode` showing `Enabled` confirms the UEFI is ready for key enrollment. The `✗` symbols aren't errors here — they just mean the keys haven't been set up yet, which is exactly where we want to be at this point.


## Step 2 — Create Keys

```bash
sudo sbctl create-keys
```


## Step 3 — Enroll Keys

This enrolls the custom keys into the firmware, including Microsoft's UEFI CA certificates. The `--microsoft` flag is required on ASUS hardware — without it, option ROMs (GPU firmware) and other UEFI drivers signed by Microsoft refuse to load. I was a bit hesitant about including Microsoft's certificates here, but without them the system won't boot properly.

```bash
sudo sbctl enroll-keys --microsoft
```


## Step 4 — Sign EFI Binaries

The signing process differs slightly depending on your bootloader.

### systemd-boot

Sign all EFI binaries and register them in sbctl's database. The `-s` flag is important — it ensures files are automatically re-signed after future updates:

```bash
sudo sbctl verify
sudo sbctl-batch-sign
sudo sbctl verify
```

All entries should show `✓`. If any show `✗`, sign them individually:

```bash
sudo sbctl sign -s /path/to/unsigned.efi
```

CachyOS uses `systemd-boot-update.service` to update the systemd-boot binary. This runs outside the standard sbctl hook, so the source binary needs to be signed explicitly to ensure it's re-signed on every bootloader update:

```bash
sudo sbctl sign -s -o /usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed \
  /usr/lib/systemd/boot/efi/systemd-bootx64.efi
```

### Limine

Limine handles its own signing process and doesn't require kernel image signatures:

```bash
sudo limine-enroll-config
sudo limine-update
```


## Step 5 — Enable Secure Boot

Reboot into the ASUS UEFI again:

```bash
systemctl reboot --firmware-setup
```

1. Go to **Security** → **Secure Boot**
2. Set **Secure Boot Control** to **Enabled**
3. Confirm the keys are present under **Key Management** (DB, KEK, PK should all be populated)
4. Save & Exit (F10)


## Verification

After rebooting, this is what things look like:

```bash
sudo sbctl status
```

```
Installed:    ✓ sbctl is installed
Owner GUID:   <your-guid>
Setup Mode:   ✓ Disabled
Secure Boot:  ✓ Enabled
Vendor Keys:  microsoft
```

![sbctl status confirming Secure Boot is enabled and Setup Mode is disabled](/images/secure-boot-sbctl-status.png)

```bash
fwupdmgr security
```

The **UEFI Secure Boot** line under HSI-1 should now show **Enabled**. The overall score remains **HSI:3!** — Encrypted RAM at HSI-4 is not supported on this hardware, which is a hardware limitation unrelated to this guide.

![fwupdmgr security output after enabling Secure Boot — HSI:3! with UEFI Secure Boot now passing under HSI-1](/images/secure-boot-fwupdmgr-after.png)

GNOME Settings → Privacy & Security → Device Security also confirms it:

![GNOME Device Security showing Protected and Secure Boot is Active](/images/secure-boot-gnome-after.png)


## NVIDIA and Kernel Updates

UEFI Secure Boot only verifies the bootloader and kernel EFI image. The NVIDIA driver is loaded as a DKMS module by the kernel. In this configuration, the kernel does not enforce module signatures, so the NVIDIA module continues to work but the kernel is marked as tainted. Signing NVIDIA modules is therefore outside the scope of this guide.

> Those who want to cryptographically enforce kernel modules must sign NVIDIA modules with the same key or avoid the proprietary driver.

After a kernel update, pacman triggers both:
1. sbctl's hook → re-signs the new kernel EFI image
2. DKMS → rebuilds NVIDIA modules for the new kernel

No manual intervention needed after updates.

> **Kernel taint:** The proprietary NVIDIA driver will continue to taint the kernel. This shows as `Linux Kernel Verification: Tainted` in the HSI report. This is expected — it means non-open-source code is loaded, not that the system is compromised.


## Remaining HSI Failures Explained

### Encrypted RAM (HSI-4)

**Not fixable on this hardware.** The Ryzen AI 9 HX 370 does not support AMD Secure Memory Encryption (SME) in the mode fwupd checks for. This is a hardware capability limitation, not a configuration issue.

### Linux Kernel Lockdown

Kernel lockdown can be enabled by adding `lockdown=integrity` to kernel parameters. However, lockdown restricts unsigned kernel modules and certain privileged operations — the proprietary NVIDIA driver would break under lockdown mode. Not something I'd recommend for day-to-day use on this hardware.

### Linux Kernel Verification (Tainted)

Caused by the proprietary NVIDIA driver. Can't be resolved while using proprietary NVIDIA drivers. Not a security vulnerability.


## Troubleshooting

{{% details title="sbctl status still shows 'Setup Mode: Disabled' after clearing keys" closed="true" %}}

Some ASUS UEFI versions require the platform key (PK) to be explicitly deleted before Setup Mode activates.

In the ASUS UEFI:
1. Go to **Security** → **Secure Boot** → **Key Management**
2. Select **Platform Key (PK)** → **Delete**
3. Save & Exit and reboot

After rebooting, `sudo sbctl status` should show Setup Mode: Enabled.

{{% /details %}}

{{% details title="System does not boot after enabling Secure Boot" closed="true" %}}

If the system doesn't boot after enabling Secure Boot, one or more EFI files weren't signed.

1. Reboot into the ASUS UEFI and temporarily disable Secure Boot
2. Boot into CachyOS
3. Check which files are unsigned:
```bash
sudo sbctl verify
```
4. Sign any missing files:
```bash
sudo sbctl sign -s /path/to/file.efi
```
5. Or re-run the batch sign:
```bash
sudo sbctl-batch-sign
```
6. Reboot and re-enable Secure Boot

{{% /details %}}

{{% details title="fwupdmgr shows HSI:3 instead of HSI:4 after enabling Secure Boot" closed="true" %}}

The fwupd daemon caches results. Refresh the report:

```bash
fwupdmgr refresh
fwupdmgr security --force
```

If Secure Boot shows Pass but the score is still HSI:3, check whether any other HSI-4 tests are failing. Encrypted RAM is a hardware limitation on this platform and does not count towards the score here.

{{% /details %}}


## References

- [CachyOS Wiki: Secure Boot Setup](https://wiki.cachyos.org/configuration/secure_boot_setup/)
- [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot)
- [sbctl GitHub](https://github.com/Foxboron/sbctl)
- [fwupd HSI Documentation](https://fwupd.github.io/hsi.html)
