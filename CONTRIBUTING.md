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
