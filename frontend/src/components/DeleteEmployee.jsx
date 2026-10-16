import { useState } from 'react';
import { employeesApi } from '../api';
import Modal from './Modal';
import Icon from './Icon';

export default function DeleteEmployee({ employee, onClose, onDeleted }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function remove() {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await employeesApi.remove(employee.id);
      onDeleted(employee);
    } catch (failure) {
      setError(failure.message);
      setBusy(false);
    }
  }

  return (
    <Modal
      compact
      title="Remove employee?"
      subtitle="This action can’t be undone."
      onClose={onClose}
      busy={busy}
    >
      <div className="delete-content">
        <div className="delete-symbol">
          <Icon name="trash" size={24} />
        </div>
        <p>
          <strong>{employee.name}</strong> will be removed from your directory.
        </p>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
      <footer className="modal-footer">
        <button className="button button-secondary" onClick={onClose} disabled={busy}>
          Keep employee
        </button>
        <button className="button button-danger" onClick={remove} disabled={busy}>
          {busy ? 'Removing…' : 'Remove employee'}
        </button>
      </footer>
    </Modal>
  );
}
