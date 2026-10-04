// Render every docs/diagrams/*.mmd to docs/images/<name>-light.png and -dark.png.
//
//   node docs/diagrams/render.mjs
//
// Why images instead of Mermaid blocks in the README: the GitHub mobile app
// shows Mermaid as raw code, and on the website GitHub's zoom buttons cover
// part of wide diagrams. PNGs look the same everywhere.
// Uses headless Chrome (set CHROME to its path if it is not in the default
// macOS location) and Mermaid from a CDN; Node 22+ (built-in fetch/WebSocket).
import { spawn } from "node:child_process";
import { readdirSync, readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "..", "images");
const chromePath = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const themes = {
  light: { mermaid: "default", background: "#ffffff" },
  dark: { mermaid: "dark", background: "#0d1117" }, // GitHub's dark page color
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const port = 9400 + Math.floor(Math.random() * 400);
const chrome = spawn(chromePath, ["--headless=new", "--disable-gpu", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "mmd-"))}`, "about:blank"], { stdio: "ignore" });

try {
  let targets;
  for (let i = 0; i < 60 && !targets; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await sleep(250); }
  }
  const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
  const js = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result.value;
  await send("Emulation.setDeviceMetricsOverride", { width: 1000, height: 2000, deviceScaleFactor: 2, mobile: false });

  for (const file of readdirSync(here).filter((f) => f.endsWith(".mmd"))) {
    const source = readFileSync(join(here, file), "utf8");
    for (const [name, theme] of Object.entries(themes)) {
      const html = `<!doctype html><html><body style="margin:0;padding:24px;background:${theme.background};display:inline-block">
        <pre class="mermaid">${source.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</pre>
        <script type="module">
          import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
          mermaid.initialize({ startOnLoad: false, theme: "${theme.mermaid}", flowchart: { useMaxWidth: false } });
          try { await mermaid.run(); document.title = "OK"; } catch (e) { document.title = "ERROR " + e; }
        </script></body></html>`;
      await send("Page.navigate", { url: "data:text/html;base64," + Buffer.from(html).toString("base64") });
      let status = "";
      for (let i = 0; i < 60 && !status.startsWith("OK") && !status.startsWith("ERROR"); i++) { await sleep(250); status = await js("document.title"); }
      if (!status.startsWith("OK")) throw new Error(`${file} (${name}): ${status || "timed out"}`);
      const box = await js(`(() => { const r = document.querySelector("pre.mermaid svg").getBoundingClientRect();
        return { x: Math.max(0, r.x - 16), y: Math.max(0, r.y - 16), width: r.width + 32, height: r.height + 32 }; })()`);
      const { data } = await send("Page.captureScreenshot", { format: "png", clip: { ...box, scale: 1 }, captureBeyondViewport: true });
      const out = join(outDir, file.replace(/\.mmd$/, `-${name}.png`));
      writeFileSync(out, Buffer.from(data, "base64"));
      console.log(`rendered ${out} (${Math.round(box.width)} x ${Math.round(box.height)} px at 2x)`);
    }
  }
} finally {
  chrome.kill("SIGKILL");
}
