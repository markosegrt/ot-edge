import { apiGet } from "./client"
import type { Device } from "../models/device"

export function getDevices(): Promise<Device[]> {
  return apiGet<Device[]>("/devices")
}