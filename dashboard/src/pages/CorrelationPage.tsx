import { useEffect, useState } from "react"
import { getAlarms } from "../api_services/alarms"
import { getCorrelationContext } from "../api_services/correlation"
import type { Alert } from "../models/alert"
import type { CorrelationContext } from "../models/correlation"
import { SeverityBadge } from "../components/SeverityBadge"
import { CorrelationChart } from "../components/CorrelationChart"
import { Button } from "../components/Button"
import { Modal } from "../components/Modal"

const PATTERN_LABELS: Record<string, string> = {
  WRITE_TO_DANGER: "Sabotaža procesa (upis → opasno stanje)",
  CHANGE_WITHOUT_COMMAND: "Promena procesa bez komande",
  COMMAND_WITHOUT_CHANGE: "Komanda bez očekivane promene",
  UNKNOWN_ACCESS_WITH_CHANGE: "Nepoznat pristup uz promenu procesa",
  UNKNOWN_ACCESS_NO_CHANGE: "Nepoznat pristup bez promene procesa",
}

export function CorrelationPage() {
  const [alarms, setAlarms] = useState<Alert[]>([])
  const [selected, setSelected] = useState<CorrelationContext | null>(null)
  const [showChart, setShowChart] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAlarms()
      .then((all) => setAlarms(all.filter((a) => a.correlated)))
      .catch((e) => setError(e.message))
  }, [])

  function selectAlarm(id: number) {
    getCorrelationContext(id)
      .then((ctx) => {
        setSelected(ctx)
        setShowChart(false)
      })
      .catch((e) => setError(e.message))
  }

  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  return (
    <div className="flex gap-6">
      {/* Leva lista — samo korelirani, skroluje nezavisno */}
      <div className="w-72 shrink-0">
        <h3 className="text-base font-semibold text-slate-300 mb-3">
          Correlated events
        </h3>
        {alarms.length === 0 ? (
          <p className="text-sm text-slate-500">No correlated events.</p>
        ) : (
          <ul className="space-y-2 max-h-[75vh] overflow-auto pr-1">
            {alarms.map((a) => (
              <li key={a.id}>
                <button
                  onClick={() => selectAlarm(a.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-base transition-colors ${
                    selected?.alert_id === a.id
                      ? "bg-slate-700"
                      : "bg-slate-800 hover:bg-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{a.rule_id}</span>
                    <SeverityBadge severity={a.severity} />
                  </div>
                  <div className="text-sm text-slate-500 mt-1 font-mono">
                    {a.source} → {a.destination}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Desno — kartica sa 4 dela */}
      <div className="flex-1">
        {selected === null ? (
          <p className="text-slate-400 text-base">
            Select a correlated event on the left to see how the network and
            process signals were combined.
          </p>
        ) : (
          <>
            <CorrelationCard
              ctx={selected}
              patternLabels={PATTERN_LABELS}
              onShowChart={() => setShowChart(true)}
            />

            {showChart && (
              <Modal
                title={`Process context · ${selected.rule_id}`}
                onClose={() => setShowChart(false)}
              >
                <CorrelationChart
                  telemetry={selected.telemetry}
                  alertTimestamp={selected.alert_timestamp}
                />
                <p className="text-xs text-slate-500 mt-3">
                  Crvena linija označava trenutak mrežnog događaja. Grafik
                  prikazuje procesne vrednosti u prozoru oko njega.
                </p>
              </Modal>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function CorrelationCard({
  ctx,
  patternLabels,
  onShowChart,
}: {
  ctx: CorrelationContext
  patternLabels: Record<string, string>
  onShowChart: () => void
}) {
  const c = ctx.correlation
  // Da li je korelacija PODIGLA ozbiljnost (npr. HIGH -> CRITICAL) ili je
  // ostala ista (HIGH -> HIGH). Od toga zavisi tekst i boja zakljucka.
  const escalated = c ? c.base_severity !== c.final_severity : false

  return (
    <div>
      {/* Zaglavlje */}
      <div className="flex items-center gap-3 mb-1">
        <SeverityBadge severity={ctx.severity} />
        <span className="text-xl font-semibold">{ctx.rule_id}</span>
        {c && (
          <span className="text-sm text-slate-400">
            · {patternLabels[c.pattern] ?? c.pattern}
          </span>
        )}
      </div>
      <p className="text-base text-slate-400 mb-5 font-mono">
        {ctx.source} → {ctx.destination} ·{" "}
        {new Date(ctx.alert_timestamp).toLocaleTimeString("en-GB")}
      </p>

      {/* Kartica sa 4 dela */}
      {c ? (
        <div className="rounded-lg border border-slate-700 overflow-hidden mb-5">
          <CardSection index="1" title="Na mreži" text={c.network_summary} />
          <CardSection index="2" title="U procesu" text={c.process_summary} />
          <CardSection index="3" title="Veza" text={c.link_summary} />
          {escalated ? (
            <div className="p-4 bg-red-500/10 border-t border-red-500/30">
              <div className="text-sm font-semibold text-red-300 mb-1">
                4 · Zaključak
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">
                Bez procesnog konteksta ozbiljnost bi bila{" "}
                <span className="font-semibold">{c.base_severity}</span>. Sa
                procesnim kontekstom sistem je podigao na{" "}
                <span className="font-semibold text-red-300">
                  {c.final_severity}
                </span>
                . Mreža sama ovo ne bi videla kao kritično.
              </p>
            </div>
          ) : (
            <div className="p-4 bg-slate-800/40 border-t border-slate-600">
              <div className="text-sm font-semibold text-slate-300 mb-1">
                4 · Zaključak
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Ozbiljnost ostaje{" "}
                <span className="font-semibold">{c.final_severity}</span>.
                Procesni kontekst nije potvrdio fizičku posledicu, pa se događaj
                ne eskalira — sumnjiv je, ali nije kritičan.
              </p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-slate-400 text-sm mb-5">
          This event was correlated, but no detailed pattern description is
          stored.
        </p>
      )}

      <Button variant="primary" onClick={onShowChart}>
        Prikaži grafik
      </Button>
    </div>
  )
}

function CardSection({
  index,
  title,
  text,
}: {
  index: string
  title: string
  text: string | null
}) {
  return (
    <div className="p-4 border-b border-slate-700 last:border-b-0">
      <div className="text-sm font-semibold text-slate-300 mb-1">
        {index} · {title}
      </div>
      <p className="text-sm text-slate-300 leading-relaxed">{text ?? "—"}</p>
    </div>
  )
}