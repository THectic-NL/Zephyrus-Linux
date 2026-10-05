---
title: ""
toc: false
---

<div class="hx-mt-6 hx-mb-6">
{{< hextra/hero-headline >}}
  Zephyrus Linux
{{< /hextra/hero-headline >}}
</div>

<div class="hx-mb-12">
{{< hextra/hero-subtitle >}}
  How I like Linux, written down and scripted. Built on the ROG Zephyrus G16, usable on any laptop.
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-6">
{{< hextra/hero-badge link="/docs/setup-script/" >}}
  <span>Set up a machine like mine</span>
  {{< icon name="arrow-circle-right" attributes="height=20" >}}
{{< /hextra/hero-badge >}}
</div>

<div class="hx-mt-6"></div>

{{< callout type="info" >}}
**My setup, written down.** This is how I like Linux, and how I set it up on the one laptop I own, a ROG Zephyrus G16 GA605WV (2024). I wrote it all down so I can rebuild the machine in an afternoon, and then turned most of it into a script. You don't need this exact laptop: only the pages that talk to its hardware are specific to the G16, the rest works on any machine. It is opinionated, tested on my own machine and at your own risk. Feel free to reach out if something doesn't work; I'm happy to think along.
{{< /callout >}}

## Two ways to use this

{{< cards >}}
  {{< card link="/docs/setup-script" title="Set up a machine like mine" subtitle="A menu that shows what is done and what is open, and applies my recommended defaults, with a guide link for every step." >}}
  {{< card link="/docs/" title="Read the guides" subtitle="How and why I set things up the way I did, for CachyOS and Bazzite." >}}
{{< /cards >}}

## Current System Configuration (at the time of writing)

| Component | Specification |
|-----------|---------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **RAM** | 32 GB LPDDR5 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | [CachyOS]({{< relref "/docs/cachyos/getting-started" >}}) (Arch); the guides also cover [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) (Fedora Atomic) |
| **Kernel** | 7.2.9-1-cachyos |
| **Bootloader** | Limine |
| **Desktop** | GNOME 49 and 50 on Wayland (KDE not covered) |
| **CPU Scheduler** | scx_lavd (sched_ext) |
| **Secure Boot** | Disabled |

![System information overview](/images/system-info.avif)

<small style="opacity: 0.45;">Some documentation on this site has been written or improved with assistance from GitHub Copilot.</small>
