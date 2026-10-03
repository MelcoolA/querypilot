"use client";

// The result panel: Answer, Chart, Table, and SQL tabs.

import { useState } from "react";
import type { AskResult } from "@/lib/api";
import { formatCell, humanize } from "@/lib/format";
import ResultChart from "./result-chart";
import styles from "./result.module.css";

const TABS = ["Answer", "Chart", "Table", "SQL"] as const;
type Tab = (typeof TABS)[number];
const ROW_LIMIT = 1000; // matches the backend guardrail that adds LIMIT 1000

export default function ResultTabs({ result }: { result: AskResult }) {
  const [tab, setTab] = useState<Tab>("Answer");
  const failed = Boolean(result.error);

  return (
    <section className={styles.panel}>
      <div className={styles.tabs} role="tablist" aria-label="Result views">
        {TABS.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            className={tab === t ? styles.tabActive : styles.tab}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      <div className={styles.tabBody} role="tabpanel">
        {tab === "Answer" && (
          <>
            <p className={failed ? styles.answerFailed : styles.answer}>{result.answer}</p>
            {!failed && (
              <p className={styles.note}>
                Check the numbers in the Table tab: the answer is written by the model and can misread the data.
              </p>
            )}
          </>
        )}

        {tab === "Chart" &&
          (failed || !result.chart ? (
            <p className={styles.note}>No chart: the query did not return a result.</p>
          ) : (
            <ResultChart chart={result.chart} columns={result.columns} rows={result.rows} />
          ))}

        {tab === "Table" && (failed ? <p className={styles.note}>No result to show.</p> : <ResultTable result={result} />)}

        {tab === "SQL" && <SqlView sql={result.sql} failed={failed} />}
      </div>

      <p className={styles.meta}>
        {result.model} · {result.elapsed_s.toFixed(1)}s · {result.repairs} repair{result.repairs === 1 ? "" : "s"}
      </p>
    </section>
  );
}

function ResultTable({ result }: { result: AskResult }) {
  const { columns, rows } = result;
  // Right-align columns that hold numbers, so digits line up.
  const numeric = columns.map((_, i) => rows.length > 0 && rows.every((r) => r[i] === null || typeof r[i] === "number"));
  if (rows.length === 0) return <p className={styles.note}>The query returned no rows.</p>;
  return (
    <>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((c, i) => (
                <th key={i} className={numeric[i] ? styles.num : undefined}>
                  {humanize(c)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr key={r}>
                {row.map((value, i) => (
                  <td key={i} className={numeric[i] ? styles.num : undefined}>
                    {formatCell(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={styles.note}>
        {rows.length.toLocaleString("en-US")} row{rows.length === 1 ? "" : "s"}
        {rows.length >= ROW_LIMIT && ". Cut off at the 1,000-row limit, so this is not all of the data."}
      </p>
    </>
  );
}

function SqlView({ sql, failed }: { sql: string; failed: boolean }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <>
      <div className={styles.sqlWrap}>
        <button className={styles.copy} onClick={copy}>
          {copied ? "Copied" : "Copy"}
        </button>
        <pre className={styles.sql}>
          <code>{sql}</code>
        </pre>
      </div>
      <p className={styles.note}>
        {failed ? "The last SQL the agent tried. It did not run successfully." : "The exact SQL that ran, so you can check it."}
      </p>
    </>
  );
}
