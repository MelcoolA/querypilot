// Talks to the FastAPI backend (backend/api/main.py).

// Inlined at build time (NEXT_PUBLIC_ prefix), so the browser can read it.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Step = {
  node: string;
  detail: string;
  error: boolean;
  elapsed_s: number;
};

export type ChartSpec = {
  type: "single_number" | "bar" | "line" | "table";
  x: string | null;
  y: string[];
  reason: string;
};

export type Cell = string | number | boolean | null;

export type AskResult = {
  question: string;
  answer: string;
  sql: string;
  columns: string[];
  rows: Cell[][];
  chart: ChartSpec | null;
  error: string;
  repairs: number;
  input_tokens: number;
  output_tokens: number;
  elapsed_s: number;
  model: string;
};

export type Health = { status: string; ready: boolean; model: string; dataset: string; warehouse: string };

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

export async function getExamples(): Promise<string[]> {
  const res = await fetch(`${API_URL}/examples`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return (await res.json()).questions;
}

type Handlers = {
  onStep: (step: Step) => void;
  onResult: (result: AskResult) => void;
  onError: (message: string) => void;
};

// POST /ask and read the Server-Sent Events as they arrive. We use fetch
// rather than the browser's EventSource because EventSource only does GET and
// reconnects on its own, which would silently ask the question again.
export async function streamAsk(question: string, handlers: Handlers, signal: AbortSignal): Promise<void> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`API returned ${res.status}`);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    // Events are separated by a blank line; a chunk may hold several or half of one.
    let end;
    while ((end = buffer.indexOf("\n\n")) !== -1) {
      handleEvent(buffer.slice(0, end), handlers);
      buffer = buffer.slice(end + 2);
    }
  }
}

function handleEvent(block: string, handlers: Handlers) {
  let name = "";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) name = line.slice(7);
    else if (line.startsWith("data: ")) data = line.slice(6);
  }
  if (!data) return;
  const payload = JSON.parse(data);
  if (name === "step") handlers.onStep(payload);
  else if (name === "result") handlers.onResult(payload);
  else if (name === "error") handlers.onError(payload.message);
}
