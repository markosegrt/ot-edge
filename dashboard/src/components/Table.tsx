import type { ReactNode } from "react"

export interface Column<T> {
  header: string
  cell: (row: T) => ReactNode
}

interface Props<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  emptyText?: string
}

export function Table<T>({ columns, rows, rowKey, emptyText = "No data" }: Props<T>) {
  if (rows.length === 0) {
    return <p className="text-slate-400 text-base">{emptyText}</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700">
      <table className="w-full text-base">
        <thead>
          <tr className="text-left text-slate-300 bg-slate-800/60">
            {columns.map((col, i) => (
              <th key={i} className="py-3 px-4 font-semibold whitespace-nowrap">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              className="border-t border-slate-800 hover:bg-slate-800/40 transition-colors"
            >
              {columns.map((col, i) => (
                <td key={i} className="py-3 px-4">
                  {col.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}