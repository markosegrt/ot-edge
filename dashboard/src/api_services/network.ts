import { apiGet } from "./client"
import type { NetworkData } from "../models/network"

export function getNetwork(): Promise<NetworkData> {
  return apiGet<NetworkData>("/network")
}