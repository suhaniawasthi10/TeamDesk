import { useState } from 'react';
import { employeesApi } from '../api';
import Modal from './Modal';
import Icon from './Icon';

const blank = { name: '', email: '', department: '', job_title: '', joining_date: '' };
const fields = [
  {
    key: 'name',
    label: 'Full name',
    placeholder: 'e.g. Aanya Mehta',
    maxLength: 120,
    wide: true,
    autoComplete: 'name',
  },
  {
    key: 'email',
    label: 'Email address',
    placeholder: 'aanya@example.com',
    maxLength: 254,
    type: 'email',
    wide: true,
    autoComplete: 'email',
  },
  { key: 'department', label: 'Department', placeholder: 'e.g. Engineering', maxLength: 80 },
  { key: 'job_title', label: 'Job title', placeholder: 'e.g. Product Designer', maxLength: 120 },
  { key: 'joining_date', label: 'Joining date', type: 'date', wide: true },
];

export default function EmployeeForm({ employee, departments, onClose, onSaved }) {
  const [values, setValues] = useState(() =>
    employee ? Object.fromEntries(Object.keys(blank).map((key) => [key, employee[key]])) : blank,
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (saving) return;
    const payload = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, value.trim()]),
    );
    if (Object.values(payload).some((value) => !value)) {
      setError('Please fill in every field.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const saved = employee
        ? await employeesApi.update(employee.id, payload)
        : await employeesApi.create(payload);
      onSaved(saved, Boolean(employee));
    } catch (failure) {
      setError(failure.message);
      setSaving(false);
    }
  }

  return (
    <Modal
      title={employee ? 'Edit employee' : 'A new face on the team.'}
      subtitle={employee ? 'Keep their details up to date.' : 'Add their details to the directory.'}
      onClose={onClose}
      busy={saving}
    >
      <form onSubmit={submit}>
        <div className="form-fields">
          {fields.map(({ key, label, wide, ...input }) => (
            <label className={wide ? 'field field-wide' : 'field'} key={key} htmlFor={key}>
              <span>{label}</span>
              <input
                id={key}
                name={key}
                {...input}
                type={input.type || 'text'}
                required
                value={values[key]}
                disabled={saving}
                list={key === 'department' ? 'departments' : undefined}
                onChange={(event) => setValues({ ...values, [key]: event.target.value })}
              />
            </label>
          ))}
          <datalist id="departments">
            {departments.map((department) => (
              <option value={department} key={department} />
            ))}
          </datalist>
        </div>
        {error && (
          <p role="alert" className="form-error">
            <Icon name="alert" />
            {error}
          </p>
        )}
        <footer className="modal-footer">
          <span className="form-note">All fields are required.</span>
          <div className="button-group">
            <button
              type="button"
              className="button button-secondary"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="button button-primary" disabled={saving}>
              {saving ? 'Saving…' : employee ? 'Save changes' : 'Add employee'}
            </button>
          </div>
        </footer>
      </form>
    </Modal>
  );
}
