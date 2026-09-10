import { apiGet, apiPost, apiPut, apiDelete } from "./client"
import type { BaselineDevice } from "../models/baseline"

export function getBaseline(): Promise<BaselineDevice[]> {
  return apiGet<BaselineDevice[]>("/baseline")
}

export function createBaseline(device: BaselineDevice): Promise<BaselineDevice> {
  return apiPost<BaselineDevice>("/baseline", device)
}

export function updateBaseline(ip: string, device: BaselineDevice): Promise<BaselineDevice> {
  return apiPut<BaselineDevice>(`/baseline/${ip}`, device)
}

export function deleteBaseline(ip: string): Promise<{ deleted: string }> {
  return apiDelete<{ deleted: string }>(`/baseline/${ip}`)
}