import { useEffect, useState } from "react"
import {
  getBaseline,
  createBaseline,
  updateBaseline,
  deleteBaseline,
} from "../api_services/baseline"
import type { BaselineDevice } from "../models/baseline"
import { Table, type Column } from "../components/Table"
import { Button } from "../components/Button"
import { BoolBadge } from "../components/BoolBadge"
import { Modal } from "../components/Modal"
import { ConfirmDialog } from "../components/ConfirmDialog"

const DEVICE_TYPES = ["PLC", "HMI", "SCADA", "UNKNOWN"]
const CRITICAL_TYPES = ["PLC", "SCADA"]

const EMPTY: BaselineDevice = {
  ip: "",
  device_type: "UNKNOWN",
  name: "",
  trusted: true,
  can_write: false,
}

export function BaselinePage() {
  const [devices, setDevices] = useState<BaselineDevice[]>([])
  const [error, setError] = useState<string | null>(null)

  // Forma (modal): null = zatvorena.
  const [form, setForm] = useState<BaselineDevice | null>(null)
  const [editingIp, setEditingIp] = useState<string | null>(null)

  // Potvrda brisanja (modal): null = zatvorena.
  const [toDelete, setToDelete] = useState<BaselineDevice | null>(null)

  function reload() {
    getBaseline()
      .then(setDevices)
      .catch((e) => setError(e.message))
  }

  useEffect(reload, [])

  function openAdd() {
    setForm({ ...EMPTY })
    setEditingIp(null)
  }

  function openEdit(d: BaselineDevice) {
    setForm({ ...d })
    setEditingIp(d.ip)
  }

  function closeForm() {
    setForm(null)
    setEditingIp(null)
  }

  async function submit() {
    if (!form) return
    try {
      if (editingIp) {
        await updateBaseline(editingIp, form)
      } else {
        await createBaseline(form)
      }
      closeForm()
      reload()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function confirmDelete() {
    if (!toDelete) return
    try {
      await deleteBaseline(toDelete.ip)
      setToDelete(null)
      reload()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const columns: Column<BaselineDevice>[] = [
    { header: "IP Address", cell: (d) => <span className="font-mono">{d.ip}</span> },
    { header: "Type", cell: (d) => d.device_type },
    { header: "Name", cell: (d) => d.name },
    { header: "Trusted", cell: (d) => <BoolBadge value={d.trusted} /> },
    { header: "Can Write", cell: (d) => <BoolBadge value={d.can_write} /> },
    {
      header: "Actions",
      cell: (d) => (
        <div className="flex gap-2">
          <Button variant="subtle" onClick={() => openEdit(d)}>Edit</Button>
          <Button variant="danger" onClick={() => setToDelete(d)}>Delete</Button>
        </div>
      ),
    },
  ]

  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  const isCritical = toDelete ? CRITICAL_TYPES.includes(toDelete.device_type) : false

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Baseline (Known Devices)</h2>
        <Button onClick={openAdd}>+ Add device</Button>
      </div>

      <Table
        columns={columns}
        rows={devices}
        rowKey={(d) => d.ip}
        emptyText="No baseline devices"
      />

      {form && (
        <Modal
          title={editingIp ? `Edit ${editingIp}` : "New device"}
          onClose={closeForm}
        >
          <div className="grid grid-cols-2 gap-4">
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-slate-400">IP Address</span>
              <input
                className="bg-slate-900 border border-slate-600 rounded px-3 py-2 font-mono disabled:opacity-60"
                value={form.ip}
                disabled={editingIp !== null}
                onChange={(e) => setForm({ ...form, ip: e.target.value })}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-slate-400">Name</span>
              <input
                className="bg-slate-900 border border-slate-600 rounded px-3 py-2"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-slate-400">Type</span>
              <select
                className="bg-slate-900 border border-slate-600 rounded px-3 py-2"
                value={form.device_type}
                onChange={(e) => setForm({ ...form, device_type: e.target.value })}
              >
                {DEVICE_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <div className="flex items-end gap-6">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.trusted}
                  onChange={(e) => setForm({ ...form, trusted: e.target.checked })}
                />
                <span>Trusted</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.can_write}
                  onChange={(e) => setForm({ ...form, can_write: e.target.checked })}
                />
                <span>Can write to PLC</span>
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="subtle" onClick={closeForm}>Cancel</Button>
            <Button variant="primary" onClick={submit}>
              {editingIp ? "Save" : "Create"}
            </Button>
          </div>
        </Modal>
      )}

      {toDelete && (
        <ConfirmDialog
          title={isCritical ? "Delete critical device?" : "Delete device?"}
          danger={isCritical}
          confirmLabel="Delete"
          message={
            isCritical
              ? `${toDelete.name} (${toDelete.ip}) is a ${toDelete.device_type}. ` +
                `Removing it means the system will no longer treat it as a known device, ` +
                `which can weaken detection (e.g. RULE-007 for unauthorized writes). ` +
                `Are you sure you want to delete it?`
              : `Delete ${toDelete.name} (${toDelete.ip}) from the baseline?`
          }
          onConfirm={confirmDelete}
          onCancel={() => setToDelete(null)}
        />
      )}
    </div>
  )
}