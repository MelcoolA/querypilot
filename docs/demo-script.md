# Recording the demo GIF

A 45 to 60 second screen recording of the web UI, converted to a GIF for the
top of the README.

## 1. Set up (5 minutes)

1. Start the API with Claude, so answers take about 4 seconds instead of
   about 18 (the whole recording costs well under $0.50):

   ```bash
   LLM_PROVIDER=anthropic make api
   ```

   Or use the local model (free) and speed up the waiting parts when
   converting (see step 3).
2. Start the UI with `make ui` and open http://localhost:3000.
3. Clean up the browser: close other tabs, hide the bookmarks bar
   (Cmd+Shift+B), and make the window about 1,200 px wide.
4. Pick light or dark mode (the README already shows both).
5. Ask one throwaway question first, so nothing is slow on camera.
6. Refresh the page so it starts empty.

## 2. Shot list

| Time | Action | What the viewer sees |
|---|---|---|
| 0 to 3s | Pause on the empty page | The title, the examples, the green "ready" badge |
| 3 to 12s | Click the chip *Which 5 customer states generated the most revenue?* | Agent steps appearing one by one, then the answer |
| 12 to 18s | Click **Chart**, hover over the SP bar | Bar chart with a tooltip (SP 5,202,955.05) |
| 18 to 24s | Click **Table**, then **SQL**, then **Copy** | Formatted numbers, then the exact SQL that ran |
| 24 to 36s | Type *How many orders were placed each month in 2017?* and press Enter | Steps streaming again |
| 36 to 45s | Click **Chart**, hover over November | Line chart with the November 2017 peak (7,544) |
| 45 to 52s | Optional: ask *Delete all canceled orders*, then open **SQL** | The answer says QueryPilot only reads data; the SQL tab shows the `DELETE` the guardrail blocked |

Move the mouse slowly and pause about a second after each click, so viewers
can follow.

## 3. Record and convert

1. Press **Cmd+Shift+5**, choose **Record Selected Portion**, drag the box
   over the browser's page area (not the tabs or address bar), and click
   **Record**. Stop with the stop button in the menu bar. macOS saves a
   `.mov` file to the Desktop.
2. Install a converter once: `brew install ffmpeg`
3. Convert to a GIF about 1,000 px wide at 12 frames per second:

   ```bash
   ffmpeg -i ~/Desktop/demo.mov \
     -vf "fps=12,scale=1000:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer" \
     -loop 0 docs/images/demo.gif
   ```

   To cut waiting time with the local model, speed the whole clip up 2x by
   adding `setpts=0.5*PTS,` at the start of the `-vf` string.
4. Keep the file under about 8 MB so GitHub shows it inline. If it is
   bigger, lower `fps` to 10, `scale` to 900, or trim the clip in QuickTime
   (Edit, Trim) before converting.

## 4. Put it in the README

Replace the screenshot line near the top of `README.md` with:

```markdown
![QueryPilot demo](docs/images/demo.gif)
```

The bar-chart screenshot (`docs/images/ui-bar-chart.png`) is then unused;
delete it or keep it for slides.

**Alternative:** GitHub plays `.mp4` videos in a README. Drag the `.mov` or
`.mp4` into a GitHub issue comment box, copy the link it generates, and paste
that link on its own line in the README. Sharper and smaller than a GIF, but
it does not autoplay.
