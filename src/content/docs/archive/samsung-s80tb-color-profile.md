---
title: "Samsung ViewFinity S8 color profile"
weight: 1
---

{{< callout type="info" >}}
**Archived.** I don't use this monitor any more, so this page is no longer maintained or tested. It stays here for anyone who still has one.
{{< /callout >}}

The Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN, S80TB) ships with a factory color profile (`SxxB80xT.icm`) in its Windows INF driver package. On Linux this profile has to be installed by hand.

The profile is in the [`/icc-profiles/archive/LS27B800TGUXEN - S80TB/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles/archive/LS27B800TGUXEN%20-%20S80TB) directory of this repository. Where a profile may live, system-wide or per user, is explained on the [Display Color Profiles]({{< relref "/docs/hardware/color-profiles" >}}) page.

**Install the color profile:**

```bash
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

**Activate in GNOME:**

1. Open **Settings** → **Color Management**
2. Select the **Samsung display** (e.g. "LS27B800TGUXEN")
3. Click **Add Profile**
4. Select `SxxB80xT`
5. Click **Add**
