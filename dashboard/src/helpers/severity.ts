export function severityColor(severity: string): string {
  switch (severity) {
    case "CRITICAL":
      return "bg-red-600 text-white"
    case "HIGH":
      return "bg-orange-500 text-white"
    case "MEDIUM":
      return "bg-yellow-500 text-black"
    case "LOW":
      return "bg-blue-500 text-white"
    case "INFO":
      return "bg-slate-500 text-white"
    default:
      return "bg-slate-400 text-white"
  }
}