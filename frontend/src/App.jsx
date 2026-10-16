import { useEffect, useMemo, useState } from 'react';
import { employeesApi } from './api';
import EmployeeForm from './components/EmployeeForm';
import DeleteEmployee from './components/DeleteEmployee';
import Icon from './components/Icon';

const pageSize = 8;
const dateFormat = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});
const initials = (name) =>
  name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
const formatDate = (date) => dateFormat.format(new Date(`${date}T12:00:00`));

export default function App() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [sort, setSort] = useState('name');
  const [page, setPage] = useState(1);
  const [dialog, setDialog] = useState(null);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    employeesApi
      .list(controller.signal)
      .then(setEmployees)
      .catch((failure) => {
        if (failure.name !== 'AbortError') setError(failure.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reload]);

  useEffect(() => {
    if (!notice) return;
    const timeout = setTimeout(() => setNotice(''), 5000);
    return () => clearTimeout(timeout);
  }, [notice]);

  const departments = useMemo(
    () =>
      [...new Set(employees.map((employee) => employee.department))].sort((a, b) =>
        a.localeCompare(b),
      ),
    [employees],
  );
  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return employees
      .filter(
        (employee) =>
          (!department || employee.department === department) &&
          [employee.name, employee.email, employee.job_title, employee.department].some((value) =>
            value.toLocaleLowerCase().includes(query),
          ),
      )
      .sort((a, b) =>
        sort === 'newest'
          ? b.joining_date.localeCompare(a.joining_date) || b.id - a.id
          : a.name.localeCompare(b.name),
      );
  }, [employees, search, department, sort]);
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pages);
  const visible = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const now = new Date();
  const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const joinedThisMonth = employees.filter((employee) =>
    employee.joining_date.startsWith(month),
  ).length;

  function saved(employee, editing) {
    setEmployees((current) =>
      editing
        ? current.map((item) => (item.id === employee.id ? employee : item))
        : [employee, ...current],
    );
    setDialog(null);
    setSearch('');
    setDepartment('');
    setPage(1);
    setNotice(`${employee.name} ${editing ? 'updated' : 'added to the team'}.`);
  }

  function deleted(employee) {
    setEmployees((current) => current.filter((item) => item.id !== employee.id));
    if (
      department === employee.department &&
      !employees.some((item) => item.id !== employee.id && item.department === department)
    )
      setDepartment('');
    setDialog(null);
    setNotice(`${employee.name} removed from the directory.`);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a href="/" className="brand" aria-label="TeamDesk home">
          <span className="brand-mark">
            t<span>.</span>
          </span>
          <span>
            teamdesk<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">
            <Icon name="grid" size={17} />
          </span>
          <div>
            <strong>Your workspace</strong>
            <span>People & connections</span>
          </div>
        </div>
        <nav aria-label="Main navigation">
          <span className="nav-label">WORKSPACE</span>
          <a href="/" className="nav-link" aria-current="page">
            <Icon name="people" />
            <span>People directory</span>
            <span className="nav-count">{loading || error ? '—' : employees.length}</span>
          </a>
        </nav>
        <div className="sidebar-note">
          <span className="small-mark">✳</span>
          <p>
            Good teams start
            <br />
            with good connections.
          </p>
          <span>ONE DIRECTORY. EVERYONE.</span>
        </div>
        <div className="sidebar-bottom">
          <span className="workspace-avatar">T</span>
          <div>
            <strong>TeamDesk workspace</strong>
            <span>A place for your people</span>
          </div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <Icon name="arrow" size={12} />
            <span>People</span>
          </div>
          <span className="topbar-note">A little more connected.</span>
          <span className="mobile-brand">teamdesk.</span>
        </header>
        <main id="main-content">
          <section className="page-heading">
            <div>
              <p className="eyebrow">
                <span />
                THE TEAM, TOGETHER
              </p>
              <h1>
                People directory<span>.</span>
              </h1>
              <p className="subtitle">The people behind the work. All in one place.</p>
            </div>
            <button
              className="button button-primary add-main"
              onClick={() => setDialog({ type: 'add' })}
            >
              <Icon name="plus" size={19} />
              Add employee
            </button>
          </section>

          <section className="stats" aria-label="Directory overview">
            <div className="stat">
              <span>Total employees</span>
              <div>
                <strong>
                  {loading || error ? '—' : String(employees.length).padStart(2, '0')}
                </strong>
                <span>People on your team</span>
              </div>
            </div>
            <div className="stat">
              <span>Departments</span>
              <div>
                <strong>
                  {loading || error ? '—' : String(departments.length).padStart(2, '0')}
                </strong>
                <span>Different strengths, one team</span>
              </div>
            </div>
            <div className="stat">
              <span>Joined this month</span>
              <div>
                <strong>{loading || error ? '—' : String(joinedThisMonth).padStart(2, '0')}</strong>
                <span>{now.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}</span>
              </div>
            </div>
          </section>

          <section className="directory" aria-labelledby="directory-title" aria-busy={loading}>
            <div className="directory-heading">
              <h2 id="directory-title">
                Everyone{' '}
                <span className="count-badge">{loading || error ? '—' : employees.length}</span>
              </h2>
              <button
                className="icon-button refresh"
                aria-label="Refresh directory"
                title="Refresh directory"
                onClick={() => setReload((value) => value + 1)}
                disabled={loading}
              >
                <Icon name="refresh" />
              </button>
            </div>
            <div className="toolbar">
              <div className="search-field">
                <Icon name="search" />
                <input
                  type="search"
                  aria-label="Search employees"
                  placeholder="Search by name, email or role…"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
              </div>
              <div className="filters">
                <select
                  aria-label="Filter by department"
                  value={department}
                  onChange={(event) => {
                    setDepartment(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All departments</option>
                  {departments.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
                <select
                  aria-label="Sort employees"
                  value={sort}
                  onChange={(event) => {
                    setSort(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="name">Name: A–Z</option>
                  <option value="newest">Newest joining date</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="state-panel" role="status">
                <span className="spinner" />
                <h3>Getting everyone together…</h3>
                <p>Loading your directory.</p>
              </div>
            ) : error ? (
              <div className="state-panel">
                <span className="state-icon error-icon">
                  <Icon name="alert" size={27} />
                </span>
                <h3>Couldn’t load the directory</h3>
                <p role="alert">{error}</p>
                <button
                  className="button button-secondary"
                  onClick={() => setReload((value) => value + 1)}
                >
                  Try again
                </button>
              </div>
            ) : filtered.length === 0 ? (
              <div className="state-panel">
                <span className="state-icon">
                  <Icon name={employees.length ? 'search' : 'people'} size={30} />
                </span>
                <h3>{employees.length ? 'No matching people' : 'Your team starts here.'}</h3>
                <p>
                  {employees.length
                    ? 'Try a different search or department.'
                    : 'Add your first employee and make this space your own.'}
                </p>
                <button
                  className="button button-secondary"
                  onClick={() => {
                    if (employees.length) {
                      setSearch('');
                      setDepartment('');
                    } else setDialog({ type: 'add' });
                  }}
                >
                  {employees.length ? 'Clear filters' : 'Add your first employee'}
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Employee</th>
                      <th scope="col">Department</th>
                      <th scope="col">Job title</th>
                      <th scope="col">Joining date</th>
                      <th scope="col">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((employee) => (
                      <tr key={employee.id}>
                        <td className="employee-cell">
                          <div className="person">
                            <span className={`avatar tone-${employee.id % 5}`}>
                              {initials(employee.name)}
                            </span>
                            <div>
                              <span className="person-name">{employee.name}</span>
                              <a className="person-email" href={`mailto:${employee.email}`}>
                                {employee.email}
                              </a>
                            </div>
                          </div>
                        </td>
                        <td data-label="Department">
                          <span
                            className={`department-tag tag-${[...employee.department].reduce((sum, char) => sum + char.charCodeAt(0), 0) % 4}`}
                          >
                            <span />
                            {employee.department}
                          </span>
                        </td>
                        <td data-label="Job title" className="job-cell">
                          {employee.job_title}
                        </td>
                        <td data-label="Joined" className="date-cell">
                          {formatDate(employee.joining_date)}
                        </td>
                        <td className="actions-cell">
                          <div className="row-actions">
                            <button
                              className="icon-button"
                              aria-label={`Edit ${employee.name}`}
                              title="Edit employee"
                              onClick={() => setDialog({ type: 'edit', employee })}
                            >
                              <Icon name="edit" size={17} />
                            </button>
                            <button
                              className="icon-button delete-button"
                              aria-label={`Remove ${employee.name}`}
                              title="Remove employee"
                              onClick={() => setDialog({ type: 'delete', employee })}
                            >
                              <Icon name="trash" size={17} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!loading && !error && (
              <div className="table-footer">
                <span>
                  {filtered.length
                    ? `Showing ${(currentPage - 1) * pageSize + 1}–${Math.min(currentPage * pageSize, filtered.length)} of ${filtered.length}`
                    : '0 employees'}
                  {filtered.length > 0 && ' employees'}
                </span>
                <div className="pagination">
                  <button
                    className="icon-button previous"
                    aria-label="Previous page"
                    disabled={currentPage === 1}
                    onClick={() => setPage(currentPage - 1)}
                  >
                    <Icon name="arrow" size={15} />
                  </button>
                  <span>
                    Page {currentPage} of {pages}
                  </span>
                  <button
                    className="icon-button"
                    aria-label="Next page"
                    disabled={currentPage === pages}
                    onClick={() => setPage(currentPage + 1)}
                  >
                    <Icon name="arrow" size={15} />
                  </button>
                </div>
              </div>
            )}
          </section>
          <footer className="page-footer">
            <span>Small details. Stronger connections.</span>
            <span>MADE FOR YOUR TEAM</span>
          </footer>
        </main>
      </div>
      {dialog && dialog.type !== 'delete' && (
        <EmployeeForm
          employee={dialog.employee}
          departments={departments}
          onClose={() => setDialog(null)}
          onSaved={saved}
        />
      )}
      {dialog?.type === 'delete' && (
        <DeleteEmployee
          employee={dialog.employee}
          onClose={() => setDialog(null)}
          onDeleted={deleted}
        />
      )}
      <div className="toast-region" aria-live="polite" aria-atomic="true">
        {notice && (
          <div className="toast">
            <span>
              <Icon name="check" size={17} />
            </span>
            {notice}
            <button
              className="icon-button"
              aria-label="Dismiss notification"
              onClick={() => setNotice('')}
            >
              <Icon name="close" size={15} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
