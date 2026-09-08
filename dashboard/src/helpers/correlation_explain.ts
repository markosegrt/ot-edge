import type { CorrelationContext } from "../models/correlation"

const PUMP_TAGS = ["Pumpa1.Radi", "Pumpa2.Radi"]

export interface CorrelationExplanation {
  processChanged: boolean
  changedPumps: string[]
  text: string
}

export function explainCorrelation(ctx: CorrelationContext): CorrelationExplanation {
  const valuesByTag = new Map<string, Set<number>>()
  for (const point of ctx.telemetry) {
    if (!PUMP_TAGS.includes(point.tag)) continue
    if (!valuesByTag.has(point.tag)) valuesByTag.set(point.tag, new Set())
    valuesByTag.get(point.tag)!.add(point.value)
  }

  const changedPumps: string[] = []
  for (const [tag, values] of valuesByTag) {
    if (values.size > 1) changedPumps.push(tag)
  }

  const processChanged = changedPumps.length > 0

  let text: string
  if (processChanged) {
    const pumpList = changedPumps
      .map((t) => t.replace(".Radi", ""))
      .join(", ")
    text =
      `The unauthorized write from ${ctx.source} coincided with a change in ` +
      `process state (${pumpList}) within the ±5s window. Because the write ` +
      `actually affected the physical process, correlation raised the severity ` +
      `to ${ctx.severity}.`
  } else {
    text =
      `The unauthorized write from ${ctx.source} did not coincide with any ` +
      `process change in the ±5s window. The severity therefore remains ` +
      `${ctx.severity} — a network-only event without confirmed physical impact.`
  }

  return { processChanged, changedPumps, text }
}