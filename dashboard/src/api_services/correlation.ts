import { apiGet } from "./client"
import type { CorrelationContext } from "../models/correlation"

export function getCorrelationContext(alertId: number): Promise<CorrelationContext> {
  return apiGet<CorrelationContext>(`/alarms/${alertId}/context`)
}