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
  Personal Linux setup and configuration notes for the ROG Zephyrus G16
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-6">
{{< hextra/hero-badge link="/docs/" >}}
  <span>See how I did it</span>
  {{< icon name="arrow-circle-right" attributes="height=20" >}}
{{< /hextra/hero-badge >}}
</div>

<div class="hx-mt-6"></div>

{{< callout type="info" >}}
**Personal documentation.** I'm not a developer and my low-level Linux knowledge is limited, but I'm learning more with every step. Some things I figured out through guides, others by just trying and seeing what happens. I share what worked for me so others don't have to start from scratch. Everything here is at your own risk. Feel free to reach out if something doesn't work; I'm happy to think along.
{{< /callout >}}

## Current System Configuration

| Component | Specification |
|-----------|---------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **RAM** | 32 GB LPDDR5 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS (Arch) |
| **Kernel** | 6.19.8-1-cachyos |
| **Display Server** | Wayland (GNOME 49) |
| **CPU Scheduler** | scx_lavd (sched_ext) |
| **Secure Boot** | Enabled |

![System information overview](/images/system-info.avif)

<small style="opacity: 0.45;">Some documentation on this site has been written or improved with assistance from GitHub Copilot.</small>
