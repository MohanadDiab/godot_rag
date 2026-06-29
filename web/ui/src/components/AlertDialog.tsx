interface AlertDialogProps {
  message: string;
  onClose: () => void;
}

export function AlertDialog({ message, onClose }: AlertDialogProps) {
  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <div
        className="modal-dialog"
        role="alertdialog"
        aria-labelledby="alert-title"
        aria-describedby="alert-desc"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="alert-title">OpenAI API key required</h3>
        <p id="alert-desc">{message}</p>
        <button type="button" className="btn primary" onClick={onClose} autoFocus>
          OK
        </button>
      </div>
    </div>
  );
}
