# Diagrams

Source files for the README diagrams. GitHub's mobile app shows Mermaid
blocks as raw code, so the README uses rendered images instead.

After editing a `.mmd` file, re-render the light and dark PNGs into
`docs/images/`:

```bash
node docs/diagrams/render.mjs
```

Needs Node 22+ and Google Chrome (set `CHROME` to its path if it is not in the
default macOS location).
