const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      data?.detail ?? "The request could not be completed.",
      response.status,
    );
  }

  return data;
}

export function getCurrentUser() {
  return request("/auth/me");
}

export function login(credentials) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function logout() {
  return request("/auth/logout", { method: "POST" });
}

export function getEvents({ page = 1, pageSize = 20, filters = {} } = {}) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  const filterParameters = {
    application_id: filters.applicationId,
    actor_id: filters.actorId,
    action: filters.action,
    resource_type: filters.resourceType,
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
  };

  Object.entries(filterParameters).forEach(([name, value]) => {
    if (value) {
      query.set(name, value);
    }
  });

  return request(`/events?${query.toString()}`);
}

export { ApiError };
