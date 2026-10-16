async function request(path = '', options = {}) {
  let response;
  try {
    response = await fetch(`/api/employees${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('We couldn’t reach TeamDesk. Check your connection and try again.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (typeof body.detail === 'string') throw new Error(body.detail);
    if (Array.isArray(body.detail)) {
      throw new Error(
        body.detail
          .map((item) => `${item.loc.at(-1).replaceAll('_', ' ')}: ${item.msg}`)
          .join('. '),
      );
    }
    throw new Error('Something went wrong. Please try again.');
  }
  return response.status === 204 ? null : response.json();
}

export const employeesApi = {
  list: (signal) => request('', { signal }),
  create: (employee) => request('', { method: 'POST', body: JSON.stringify(employee) }),
  update: (id, employee) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(employee) }),
  remove: (id) => request(`/${id}`, { method: 'DELETE' }),
};
