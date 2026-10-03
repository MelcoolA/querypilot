"use client";

// The whole question-and-answer flow: input, example chips, the agent's steps
// as they stream in, and the answer. A Client Component because it needs
// state, event handlers, and browser fetch streaming.

import { useEffect, useRef, useState } from "react";
import { type AskResult, type Health, type Step, getExamples, getHealth, streamAsk } from "@/lib/api";
import styles from "./ask.module.css";
import ResultTabs from "./result-tabs";

// Plain-English labels for the graph steps in backend/agent/graph.py.
const STEP_LABELS: Record<string, string> = {
  get_schema: "Read the schema",
  write_sql: "Wrote SQL",
  validate: "Checked the SQL",
  execute: "Ran the query",
  repair_sql: "Repaired the SQL",
  pick_chart: "Chose a chart",
  summarize: "Wrote the answer",
};

export default function Ask() {
  const [question, setQuestion] = useState("");
  const [examples, setExamples] = useState<string[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // Check the API, and keep checking while the local model warms up.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const check = async () => {
      try {
        const h = await getHealth();
        setHealth(h);
        setOffline(false);
        if (!h.ready) timer = setTimeout(check, 2000);
      } catch {
        setOffline(true);
        timer = setTimeout(check, 3000);
      }
    };
    check();
    getExamples().then(setExamples).catch(() => setExamples([]));
    return () => clearTimeout(timer);
  }, []);

  async function ask(text: string) {
    const q = text.trim();
    if (!q || running) return;
    setQuestion(q);
    setSteps([]);
    setResult(null);
    setError("");
    setRunning(true);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamAsk(
        q,
        {
          onStep: (step) => setSteps((prev) => [...prev, step]),
          onResult: setResult,
          onError: setError,
        },
        controller.signal,
      );
    } catch (e) {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  function stop() {
    abortRef.current?.abort();
    setError("Stopped.");
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>QueryPilot</h1>
          <p className={styles.subtitle}>Ask a question about the Olist e-commerce data in plain English.</p>
        </div>
        <StatusPill health={health} offline={offline} />
      </header>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
      >
        <input
          className={styles.input}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Which 5 customer states generated the most revenue?"
          aria-label="Your question"
          maxLength={500}
          disabled={running}
        />
        {running ? (
          <button type="button" className={styles.secondaryButton} onClick={stop}>
            Stop
          </button>
        ) : (
          <button type="submit" className={styles.button} disabled={!question.trim() || offline}>
            Ask
          </button>
        )}
      </form>

      {examples.length > 0 && (
        <div className={styles.chips} aria-label="Example questions">
          {examples.map((ex) => (
            <button key={ex} className={styles.chip} onClick={() => ask(ex)} disabled={running || offline}>
              {ex}
            </button>
          ))}
        </div>
      )}

      {(steps.length > 0 || running) && (
        <section className={styles.panel} aria-live="polite">
          <h2 className={styles.panelTitle}>Agent steps</h2>
          <ol className={styles.steps}>
            {steps.map((s, i) => (
              <li key={i} className={s.error ? styles.stepError : styles.step}>
                <span className={styles.stepMark}>{s.error ? "!" : "✓"}</span>
                <span className={styles.stepLabel}>{STEP_LABELS[s.node] ?? s.node}</span>
                <span className={styles.stepDetail}>{s.detail}</span>
                <span className={styles.stepTime}>{s.elapsed_s.toFixed(1)}s</span>
              </li>
            ))}
            {running && (
              <li className={styles.stepPending}>
                <span className={styles.spinner} aria-hidden />
                <span className={styles.stepLabel}>Working...</span>
              </li>
            )}
          </ol>
        </section>
      )}

      {error && <p className={styles.error}>{error}</p>}

      {result && <ResultTabs result={result} />}
    </main>
  );
}

function StatusPill({ health, offline }: { health: Health | null; offline: boolean }) {
  if (offline) return <span className={`${styles.pill} ${styles.pillBad}`}>API offline: run make api</span>;
  if (!health) return <span className={styles.pill}>Connecting...</span>;
  const state = health.ready ? "ready" : "warming up";
  return (
    <span className={`${styles.pill} ${health.ready ? styles.pillOk : styles.pillWarn}`}>
      {health.model} · {health.dataset} on {health.warehouse} · {state}
    </span>
  );
}
