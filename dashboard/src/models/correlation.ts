export interface TelemetryPoint {
  timestamp: string
  tag: string
  value: number
}

export interface CorrelationDetail {
  pattern: string
  base_severity: string
  final_severity: string
  network_summary: string | null
  process_summary: string | null
  link_summary: string | null
}

export interface CorrelationContext {
  alert_id: number
  alert_timestamp: string
  rule_id: string | null
  severity: string
  source: string
  destination: string
  correlated: boolean
  window_start: string
  window_end: string
  telemetry: TelemetryPoint[]
  correlation: CorrelationDetail | null
}