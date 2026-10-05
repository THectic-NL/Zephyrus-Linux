---
title: "Samsung ViewFinity S8 kleurprofiel"
weight: 1
---

{{< callout type="info" >}}
**Gearchiveerd.** Ik gebruik deze monitor niet meer, dus deze pagina wordt niet meer onderhouden of getest. Hij blijft hier staan voor wie er nog een heeft.
{{< /callout >}}

De Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN, S80TB) wordt geleverd met een fabriekskleurprofiel (`SxxB80xT.icm`) in het Windows INF driver package. Op Linux moet dit profiel handmatig worden geïnstalleerd.

Het profiel staat in de [`/icc-profiles/archive/LS27B800TGUXEN - S80TB/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles/archive/LS27B800TGUXEN%20-%20S80TB) map van deze repository. Waar een profiel mag staan, systeembreed of per gebruiker, staat uitgelegd op de pagina [Kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}}).

**Installeer het kleurprofiel:**

```bash
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

**Activeer in GNOME:**

1. Open **Instellingen** → **Color Management**
2. Selecteer het **Samsung display** (bijv. "LS27B800TGUXEN")
3. Klik **Add Profile**
4. Selecteer `SxxB80xT`
5. Klik **Add**
