const BASE_URL = "http://localhost:8000/api"

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`API greska ${response.status}: ${path}`)
  }
  return response.json() as Promise<T>
}