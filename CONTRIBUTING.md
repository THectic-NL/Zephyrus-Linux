# Contributing

Also own a ROG Zephyrus device and are running Linux? And want to contribute or give opinions and/or tips? Issues and Pull Requests are welcome!

---

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).

**Format:**
```
<type>: <short description>
```

**Types:**

| Type | When to use |
|------|-------------|
| `feat` | New page or new feature |
| `fix` | Bug fix — broken link, wrong command, layout issue |
| `content` | Update or improve existing page content |
| `docs` | Changes to README, CONTRIBUTING, or other meta files |
| `chore` | Maintenance — dependencies, config, CI/CD, Hugo theme |
| `refactor` | Restructure without changing content (e.g. rename files, move sections) |
| `style` | Formatting, whitespace, typo fixes |
| `revert` | Reverting a previous commit |

**Examples:**
```
feat: add YubiKey NFC setup guide
fix: correct nmcli command in eduroam guide
content: update kernel version to 6.18.10
content: simplify eduroam page, remove technical comparison
chore: upgrade Hextra theme to v0.9.0
style: fix Dutch translation typos
```

**Rules:**
- Use lowercase for the type and description
- Keep the subject line under 72 characters
- No period at the end
- Use the imperative mood ("add", "fix", "update" — not "added", "fixed", "updated")

---

## Pull requests

- PR titles must follow the same commit convention above
- One logical change per PR
- Update both EN (`*.md`) and NL (`*.nl.md`) versions where applicable
- All images must be in **AVIF format** — no PNG or JPG in `src/static/images/`
- Test locally with `cd src && hugo server` before opening a PR
- Target the `development` branch, not `main`

---

## Images

All images must be in AVIF format. Install `avifenc` from the `libavif` package:

```bash
sudo pacman -S libavif
```

Batch convert all PNGs in `src/static/images/` (converts and removes originals):

```bash
cd src/static/images
for f in *.png; do avifenc -q 80 -s 6 "$f" "${f%.png}.avif" && rm "$f"; done
```

- `-q 80` — 80% quality (0–100 scale, 100 = lossless)
- `-s 6` — encoder speed (0 = best compression, 10 = fastest)

Place converted images in `src/static/images/` and reference them as `/images/filename.avif` in markdown.

---

## Language

This site is bilingual (EN + NL). When updating content:

- Edit both `src/content/docs/page.md` and `src/content/docs/page.nl.md`
- Keep the structure and headings in sync between the two files

---

## CachyOS and Bazzite

The guides cover two distributions.

**Pages that work fundamentally differently per distribution** live in
`content/docs/cachyos/` and `content/docs/bazzite/`. The file names mirror each
other (`cachyos/nvidia.md` has a `bazzite/nvidia.md`), because the navbar
distribution switcher moves between them by swapping the path segment. Set
`distro: cachyos` or `distro: bazzite` in the front matter of every page in
those two trees, and add a matching page on the other side.

**Everything that doesn't depend on the distribution** stays in the shared
sections (`hardware/`, `security/`, `networking/`, `virtualization/`,
`desktop/`, `gaming/`, plus `applications.md` and `known-issues.md`). Where a
shared page has a step that differs only by package manager, use a tab:

```markdown
{{< tabs >}}
{{< tab name="CachyOS" >}}
...
{{< /tab >}}
{{< tab name="Bazzite" >}}
...
{{< /tab >}}
{{< /tabs >}}
```

The tab names must be exactly `CachyOS` and `Bazzite`, in that order, on every
page. Hextra syncs same-named tab groups through the browser, and the switcher
writes that same key, so picking a distribution once follows through every
shared page. A third name, a typo or a swapped order breaks the sync.

For a one-line install command each side, `{{< install cachyos="sudo pacman -S
foo" bazzite="flatpak install flathub org.example.Foo" >}}` is shorter than a
tab and highlights the reader's distribution.

If a shared page only applies to one distribution, put `{{< distro-note >}}` at
the top of the body (with `distro:` in the front matter) so readers on the
other one see why.
