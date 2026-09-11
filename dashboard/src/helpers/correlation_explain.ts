import type { CorrelationContext } from "../models/correlation"

// Prekidacki tagovi (pali/gasi, otvori/zatvori) — gledamo promenu stanja.
const STATE_TAGS = ["Pumpa1.Radi", "Pumpa2.Radi", "Ventil.Otvoren"]

// Opasne vrednosti — gledamo da li su presle prag (isto kao RULE-008 / korelator).
const DANGER_THRESHOLDS: Record<string, number> = {
  "Cev.Pritisak": 85.0,
  "Rezervoar.Nivo": 95.0,
}

// Ljudska imena za prikaz.
const TAG_LABELS: Record<string, string> = {
  "Pumpa1.Radi": "Pumpa1",
  "Pumpa2.Radi": "Pumpa2",
  "Ventil.Otvoren": "Ventil",
  "Cev.Pritisak": "pritisak",
  "Rezervoar.Nivo": "nivo",
}

export interface CorrelationExplanation {
  processChanged: boolean
  changedItems: string[]
  dangerItems: { tag: string; value: number; threshold: number }[]
  text: string
}

export function explainCorrelation(ctx: CorrelationContext): CorrelationExplanation {
  // 1) Prekidacke promene: skup razlicitih vrednosti po tagu.
  const valuesByTag = new Map<string, Set<number>>()
  for (const point of ctx.telemetry) {
    if (!STATE_TAGS.includes(point.tag)) continue
    if (!valuesByTag.has(point.tag)) valuesByTag.set(point.tag, new Set())
    valuesByTag.get(point.tag)!.add(point.value)
  }

  const changedItems: string[] = []
  for (const [tag, values] of valuesByTag) {
    if (values.size > 1) changedItems.push(TAG_LABELS[tag] ?? tag)
  }

  // 2) Opasne vrednosti: da li je neka presla prag.
  const dangerItems: { tag: string; value: number; threshold: number }[] = []
  const seenDangerTags = new Set<string>()
  for (const point of ctx.telemetry) {
    const threshold = DANGER_THRESHOLDS[point.tag]
    if (threshold === undefined) continue
    if (point.value >= threshold && !seenDangerTags.has(point.tag)) {
      dangerItems.push({ tag: point.tag, value: point.value, threshold })
      seenDangerTags.add(point.tag)
    }
  }

  const processChanged = changedItems.length > 0 || dangerItems.length > 0

  let text: string
  if (dangerItems.length > 0) {
    // Najjaci slucaj: opasna vrednost (sabotaza).
    const d = dangerItems[0]
    const label = TAG_LABELS[d.tag] ?? d.tag
    text =
      `The unauthorized write from ${ctx.source} was followed by a dangerous ` +
      `process value: ${label} reached ${d.value.toFixed(0)} ` +
      `(threshold ${d.threshold.toFixed(0)}). The write drove the physical ` +
      `process into an unsafe state, so correlation raised the severity to ` +
      `${ctx.severity}. The network layer alone could not see this — only ` +
      `combining the write with the process reveals the sabotage.`
  } else if (changedItems.length > 0) {
    text =
      `The unauthorized write from ${ctx.source} coincided with a change in ` +
      `process state (${changedItems.join(", ")}) within the correlation ` +
      `window. Because the write affected the physical process, correlation ` +
      `raised the severity to ${ctx.severity}.`
  } else {
    text =
      `The unauthorized write from ${ctx.source} did not coincide with any ` +
      `process change in the correlation window. The severity remains ` +
      `${ctx.severity} — a network-only event without confirmed physical impact.`
  }

  return { processChanged, changedItems, dangerItems, text }
}