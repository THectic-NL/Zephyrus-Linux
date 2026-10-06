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
  Zo vind ik Linux fijn, opgeschreven en gescript. Gebouwd op de ROG Zephyrus G16, bruikbaar op elke laptop.
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-6">
{{< hextra/hero-badge link="/nl/docs/setup-script/" >}}
  <span>Richt een machine in zoals de mijne</span>
  {{< icon name="arrow-circle-right" attributes="height=20" >}}
{{< /hextra/hero-badge >}}
</div>

<div class="hx-mt-6"></div>

{{< callout type="info" >}}
**Mijn setup, opgeschreven.** Zo vind ik Linux fijn, en zo stel ik het in op de ene laptop die ik heb, een ROG Zephyrus G16 GA605WV (2024). Ik heb alles opgeschreven zodat ik de machine in een middag opnieuw kan opbouwen, en daarna heb ik het grootste deel in een setup-venster gezet. Je hebt niet precies deze laptop nodig: alleen de pagina's die met de hardware praten zijn specifiek voor de G16, de rest werkt op elke machine. Het is eigenzinnig, getest op mijn eigen machine en op eigen risico. Kom je ergens niet uit, laat het gerust weten; ik denk graag mee.
{{< /callout >}}

## Twee manieren om dit te gebruiken

{{< cards >}}
  {{< card link="/docs/setup-script" title="Richt een machine in zoals de mijne" subtitle="Een checklist die laat zien wat er klaar is en wat openstaat, en mijn aanbevolen standaarden instelt, met bij elke stap een link naar de handleiding." >}}
  {{< card link="/docs/" title="Lees de handleidingen" subtitle="Hoe en waarom ik dingen zo heb ingesteld, voor CachyOS en Bazzite." >}}
{{< /cards >}}

## Huidige Systeemconfiguratie (op het moment van schrijven)

| Onderdeel | Specificatie |
|-----------|--------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **RAM** | 32 GB LPDDR5 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | [CachyOS]({{< relref "/docs/cachyos/getting-started" >}}) (Arch); de handleidingen dekken ook [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) (Fedora Atomic) |
| **Kernel** | 7.2.9-1-cachyos |
| **Bootloader** | Limine |
| **Bureaublad** | GNOME 50 en 51 op Wayland (KDE niet behandeld) |
| **CPU Scheduler** | scx_lavd (sched_ext) |
| **Secure Boot** | Uitgeschakeld |

![Systeeminformatie-overzicht](/images/system-info.avif)

<small style="opacity: 0.45;">Een deel van de documentatie op deze site is geschreven of verbeterd met hulp van GitHub Copilot.</small>
