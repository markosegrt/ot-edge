import { apiGet } from "./client"
import type { Alert } from "../models/alert"

export function getAlarms(): Promise<Alert[]> {
  return apiGet<Alert[]>("/alarms")
}