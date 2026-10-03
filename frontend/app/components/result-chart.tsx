"use client";

// Draws the chart the backend's pick_chart step chose. Mark specs follow the
// dataviz guidelines: bars at most 24px thick with a 4px rounded end, 2px
// lines, hairline gridlines, a legend only for 2+ series, text in text colors
// (never series colors), and a hover tooltip on every chart.

import { useMemo, useSyncExternalStore } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import type { Cell, ChartSpec } from "@/lib/api";
import { formatAxisLabel, formatCompact, formatNumber, humanize } from "@/lib/format";
import styles from "./result.module.css";

type Props = { chart: ChartSpec; columns: string[]; rows: Cell[][] };

const MAX_LABELED_BARS = 10; // label bar ends only when there are few bars

export default function ResultChart({ chart, columns, rows }: Props) {
  const colors = useChartColors();

  if (chart.type === "table" || rows.length === 0) {
    return <p className={styles.note}>This result reads best as a table ({chart.reason}). See the Table tab.</p>;
  }
  if (chart.type === "single_number") return <SingleNumber chart={chart} columns={columns} row={rows[0]} />;
  if (!colors || chart.x === null) return null;

  // Recharts wants one object per row. Series use index keys (s0, s1) so
  // duplicate column names can't collide.
  const xIndex = columns.indexOf(chart.x);
  const yIndexes = chart.y.map((c) => columns.indexOf(c));
  const data = rows.map((row) => {
    // A true/false label alone ("Yes") doesn't say what is true, so name it: "Is late: Yes".
    const raw = row[xIndex];
    const label = typeof raw === "boolean" ? `${humanize(chart.x!)}: ${formatAxisLabel(raw)}` : formatAxisLabel(raw);
    const point: Record<string, string | number | null> = { label };
    yIndexes.forEach((i) => (point[`s${i}`] = typeof row[i] === "number" ? row[i] : null));
    return point;
  });
  const series = yIndexes.map((i, k) => ({ key: `s${i}`, name: humanize(columns[i]), color: colors.series[k] }));
  const axisTick = { fill: colors.ink, fontSize: 12 };
  const legend =
    series.length > 1 ? (
      <Legend
        verticalAlign="top"
        align="left"
        iconType="circle"
        iconSize={8}
        formatter={(value) => <span style={{ color: colors.text }}>{value}</span>}
      />
    ) : null;

  if (chart.type === "bar") {
    const showValues = data.length <= MAX_LABELED_BARS;
    // Many bars: thinner (14px) so the chart stays a reasonable height.
    const barSize = showValues ? 24 : 14;
    const longestLabel = Math.max(...data.map((d) => String(d.label).length));
    const height = Math.max(160, data.length * (series.length * barSize + 12) + 60);
    return (
      // Horizontal bars: long category names read better on the side.
      <BarChart
        responsive
        style={{ width: "100%", height }}
        data={data}
        layout="vertical"
        barGap={2}
        margin={{ top: 8, right: showValues ? 56 : 16, bottom: 4, left: 4 }}
        accessibilityLayer
      >
        {legend}
        <CartesianGrid horizontal={false} stroke={colors.grid} />
        <XAxis type="number" tickFormatter={formatCompact} tick={axisTick} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={Math.min(200, Math.max(48, longestLabel * 7 + 12))}
          tick={{ ...axisTick, fill: colors.text }}
          tickLine={false}
          axisLine={{ stroke: colors.baseline }}
          interval={0}
        />
        <Tooltip cursor={{ fill: colors.grid, fillOpacity: 0.5 }} content={(p) => <ChartTooltip {...p} />} />
        {series.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.name}
            fill={s.color}
            maxBarSize={barSize}
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          >
            {showValues && (
              <LabelList
                dataKey={s.key}
                position="right"
                fill={colors.ink}
                fontSize={12}
                formatter={(v) => (typeof v === "number" ? formatCompact(v) : "")}
              />
            )}
          </Bar>
        ))}
      </BarChart>
    );
  }

  // Line: values over time. The value is labeled only at the end of each line.
  const last = data.length - 1;
  return (
    <LineChart
      responsive
      style={{ width: "100%", height: 300 }}
      data={data}
      margin={{ top: 16, right: 56, bottom: 4, left: 4 }}
      accessibilityLayer
    >
      {legend}
      <CartesianGrid vertical={false} stroke={colors.grid} />
      <XAxis dataKey="label" tick={axisTick} tickLine={false} axisLine={{ stroke: colors.baseline }} minTickGap={24} />
      <YAxis tickFormatter={formatCompact} tick={axisTick} tickLine={false} axisLine={false} width={56} />
      <Tooltip cursor={{ stroke: colors.baseline, strokeWidth: 1 }} content={(p) => <ChartTooltip {...p} />} />
      {series.map((s) => (
        <Line
          key={s.key}
          type="linear"
          dataKey={s.key}
          name={s.name}
          stroke={s.color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 5, fill: s.color, stroke: colors.surface, strokeWidth: 2 }}
          isAnimationActive={false}
        >
          <LabelList
            dataKey={s.key}
            content={(props) =>
              props.index === last && typeof props.value === "number" ? (
                <text x={Number(props.x) + 8} y={Number(props.y)} dy={4} fill={colors.ink} fontSize={12}>
                  {formatCompact(props.value)}
                </text>
              ) : null
            }
          />
        </Line>
      ))}
    </LineChart>
  );
}

// One number, shown big: "96,478 / Delivered orders".
function SingleNumber({ chart, columns, row }: { chart: ChartSpec; columns: string[]; row: Cell[] }) {
  const value = row[columns.indexOf(chart.y[0])];
  const context = chart.x ? formatAxisLabel(row[columns.indexOf(chart.x)]) : "";
  return (
    <div className={styles.hero}>
      <div className={styles.heroValue}>{typeof value === "number" ? formatNumber(value) : String(value)}</div>
      <div className={styles.heroLabel}>
        {humanize(chart.y[0])}
        {context && ` · ${context}`}
      </div>
    </div>
  );
}

function ChartTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipLabel}>{label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className={styles.tooltipRow}>
          <span className={styles.swatch} style={{ background: p.color }} />
          <span>{p.name}</span>
          <span className={styles.tooltipValue}>{typeof p.value === "number" ? formatNumber(p.value) : ""}</span>
        </div>
      ))}
    </div>
  );
}

type ChartColors = {
  series: string[];
  grid: string;
  baseline: string;
  ink: string;
  text: string;
  surface: string;
};

// Recharts writes colors as SVG attributes, which can't use CSS variables, so
// read the tokens from globals.css and re-read when light/dark mode changes.
function subscribeToTheme(onChange: () => void) {
  const query = window.matchMedia("(prefers-color-scheme: dark)");
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

function useChartColors(): ChartColors | null {
  const theme = useSyncExternalStore(
    subscribeToTheme,
    () => (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
    () => null, // on the server there is no theme yet
  );
  return useMemo(() => {
    if (!theme) return null;
    const css = getComputedStyle(document.documentElement);
    const token = (name: string) => css.getPropertyValue(name).trim();
    return {
      series: [token("--series-1"), token("--series-2"), token("--series-3")],
      grid: token("--chart-grid"),
      baseline: token("--chart-baseline"),
      ink: token("--chart-ink"),
      text: token("--text"),
      surface: token("--surface"),
    };
  }, [theme]);
}
