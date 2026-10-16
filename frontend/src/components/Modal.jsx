import { useEffect, useRef } from 'react';
import Icon from './Icon';

export default function Modal({ title, subtitle, onClose, busy, children, compact = false }) {
  const dialog = useRef(null);

  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    document.body.style.overflow = 'hidden';
    return () => {
      element.close();
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      className={`modal ${compact ? 'modal-compact' : ''}`}
      aria-labelledby="modal-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      onClick={(event) => {
        if (event.target !== dialog.current || busy) return;
        const bounds = dialog.current.getBoundingClientRect();
        if (
          event.clientX < bounds.left ||
          event.clientX > bounds.right ||
          event.clientY < bounds.top ||
          event.clientY > bounds.bottom
        )
          onClose();
      }}
    >
      <header className="modal-header">
        <div>
          <h2 id="modal-title">{title}</h2>
          <p>{subtitle}</p>
        </div>
        <button
          className="icon-button"
          type="button"
          onClick={onClose}
          disabled={busy}
          aria-label="Close dialog"
        >
          <Icon name="close" />
        </button>
      </header>
      {children}
    </dialog>
  );
}
