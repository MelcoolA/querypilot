// Turn raw result values into readable text for tables, charts, and tooltips.
import type { Cell } from "./api";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const compactFormat = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const monthFormat = new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric", timeZone: "UTC" });

// The API sends dates as ISO strings, e.g. "2017-11-01T00:00:00".
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?)?$/;

export function formatNumber(value: number): string {
  return numberFormat.format(value);
}

// For axis ticks and bar-end labels: 1,258,681 becomes 1.3M.
export function formatCompact(value: number): string {
  return Math.abs(value) >= 10_000 ? compactFormat.format(value) : numberFormat.format(value);
}

export function formatCell(value: Cell): string {
  if (value === null) return "";
  if (typeof value === "number") return formatNumber(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return formatDate(value) ?? value;
}

// "2017-11-01T00:00:00" -> "2017-11-01"; keeps a time only when there is one.
function formatDate(text: string): string | null {
  const m = ISO_DATE.exec(text);
  if (!m) return null;
  const [, y, mo, d, h, mi] = m;
  const hasTime = h !== undefined && !(h === "00" && mi === "00");
  return hasTime ? `${y}-${mo}-${d} ${h}:${mi}` : `${y}-${mo}-${d}`;
}

// Chart axis label for a date: first-of-month dates (DATE_TRUNC('month')) read as "Nov 2017".
export function formatAxisLabel(value: Cell): string {
  if (typeof value === "string") {
    const m = ISO_DATE.exec(value);
    if (m && m[3] === "01") return monthFormat.format(new Date(`${m[1]}-${m[2]}-01T00:00:00Z`));
  }
  return formatCell(value);
}

// "avg_review_score" -> "Avg review score"
export function humanize(column: string): string {
  const words = column.replace(/_/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}
