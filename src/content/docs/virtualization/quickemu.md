---
title: "Quickemu"
weight: 2
prev: docs/virtualization/vm-setup
next: docs/virtualization/winboat
---

[Quickemu](https://github.com/quickemu-project/quickemu) is the shortest path from "I need a VM to try this in" to a running desktop. It wraps QEMU with sensible defaults, and its companion `quickget` downloads the ISO for you.

Two commands and you have a Windows 11 VM:

```bash
quickget windows 11
quickemu --vm windows-11.conf
```

No virt-manager, no XML, no walking a wizard. The trade is control: it picks the hardware layout for you.

## Where it fits

There are four ways to run something that isn't Linux on this laptop, and they're for different things:

| | Best for | Not for |
|---|---|---|
| **Quickemu** | Throwaway VMs, trying a distribution, a Windows install you'll delete next week | A VM you tune and keep for years |
| [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}) | The VM you keep — passthrough, snapshots, exact device control | A quick look at something |
| [WinBoat]({{< relref "/docs/virtualization/winboat" >}}) | Individual Windows applications in your Linux session | A full Windows desktop |
| [VMware Workstation]({{< relref "/docs/virtualization/vmware-workstation" >}}) | Best performance, easiest UI (CachyOS only) | Bazzite — no supported path |

Same hypervisor underneath as virt-manager, so a Quickemu VM isn't slower. It's a different front end, not a different technology.

## Install

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S quickemu
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Quickemu drives QEMU on the host and wants `/dev/kvm`, so this is one to layer rather than to put in a container:

```bash
rpm-ostree install quickemu
systemctl reboot
```

If you haven't set up virtualization yet, do that first — it brings in QEMU and libvirt and puts you in the right group:

```bash
ujust setup-virtualization
systemctl reboot
```

Running both from one reboot is fine; layer them in the same `rpm-ostree install` if you like.

{{< callout type="info" >}}
A distrobox container can run Quickemu too — `/dev/kvm` is available inside one — but the VM window then belongs to the container, and file paths get confusing fast. Layering is the less annoying answer here.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Using it

{{% steps %}}

### Find what's available

```bash
quickget --list
```

That's a long list: most Linux distributions, Windows, macOS, and the BSDs.

### Download and generate a config

```bash
quickget ubuntu 24.04
```

This downloads the ISO into a directory next to your current one and writes a small `.conf` file describing the VM. On this hardware the ISO is usually the slow part.

### Boot it

```bash
quickemu --vm ubuntu-24.04.conf
```

A window opens and the VM boots. That's the whole workflow.

### Delete it when you're done

The VM is a directory and a config file. Remove both and it's gone — no libvirt definition left behind, nothing registered anywhere:

```bash
rm -rf ubuntu-24.04 ubuntu-24.04.conf
```

This is the actual reason to use Quickemu. A throwaway VM should be genuinely throwaway.

{{% /steps %}}

## Windows 11

`quickget windows 11` handles the ISO, the VirtIO driver disc and the TPM requirement, which is most of what makes a manual Windows 11 setup tedious.

```bash
quickget windows 11
quickemu --vm windows-11.conf
```

Everything on the [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}) page about Windows licensing and ISO choices applies here too — the evaluation ISO, the Media Creation Tool, and AtlasOS are all just ISOs, and Quickemu will boot any of them.

{{< callout type="warning" >}}
`swtpm` has to be present for the TPM 2.0 device Windows 11 checks for. It comes with the CachyOS package list on the virt-manager page, and with `ujust setup-virtualization` on Bazzite. If Windows setup complains the PC doesn't meet requirements, that's the thing to check.
{{< /callout >}}

## Configuration worth knowing

The generated `.conf` is a handful of shell variables. The ones that matter on this laptop:

```bash
cpu_cores="8"
ram="8G"
disk_size="64G"
gpu_accel="on"
```

- **`cpu_cores` and `ram`.** Quickemu guesses from the host. The HX 370 has cores to spare, but leaving the guess alone is usually right.
- **`gpu_accel`.** Uses the AMD iGPU for the VM's display. That's what you want — the same reasoning as the SPICE GL section on the virt-manager page. The RTX 4060 is not what should be drawing a VM window.
- **`disk_size`.** Grows as needed rather than being allocated up front, so being generous costs nothing until it's used.

## On the G16 specifically

- **Hybrid graphics.** Let the VM render on the iGPU. Forcing it onto the discrete card with `prime-run` gains nothing for a desktop VM and costs battery.
- **Display scaling.** VM windows come up at the config's resolution, which on a 2560x1600 panel means small. Set the resolution inside the guest rather than fighting the host window.
- **Battery.** A running VM keeps cores busy and defeats the point of the Silent [`asusctl` profile]({{< relref "/docs/hardware/asusctl-rog-control" >}}). Fine on AC, noticeable on battery.

## References

- [Quickemu on GitHub](https://github.com/quickemu-project/quickemu)
- [Quickgui](https://github.com/quickemu-project/quickgui) — a graphical front end for Quickemu
- [QEMU documentation](https://www.qemu.org/docs/master/)
