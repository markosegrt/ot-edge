import { Modal } from "./Modal"
import { Button } from "./Button"

interface Props {
  title: string
  message: string
  confirmLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  danger = false,
  onConfirm,
  onCancel,
}: Props) {
  return (
    <Modal title={title} onClose={onCancel}>
      <div className="flex gap-4">
        <div
          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-xl font-bold ${
            danger ? "bg-red-600/20 text-red-400" : "bg-blue-600/20 text-blue-400"
          }`}
        >
          !
        </div>
        <p className="text-slate-300 text-sm leading-relaxed">{message}</p>
      </div>
      <div className="flex justify-end gap-2 mt-6">
        <Button variant="subtle" onClick={onCancel}>Cancel</Button>
        <Button variant={danger ? "danger" : "primary"} onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}