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
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).filter(Boolean).join("; ")
          : "The request could not be completed.";
    throw new ApiError(
      message || "The request could not be completed.",
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

export function getEvent(eventId) {
  return request(`/events/${eventId}`);
}

export function getApplications() {
  return request("/admin/applications");
}

export function createApplication(application) {
  return request("/admin/applications", {
    method: "POST",
    body: JSON.stringify(application),
  });
}

export function updateApplicationStatus(applicationId, isActive) {
  return request(`/admin/applications/${applicationId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export function getApiKeys(applicationId) {
  return request(`/admin/applications/${applicationId}/api-keys`);
}

export function createApiKey(applicationId, apiKey) {
  return request(`/admin/applications/${applicationId}/api-keys`, {
    method: "POST",
    body: JSON.stringify(apiKey),
  });
}

export function revokeApiKey(applicationId, apiKeyId) {
  return request(
    `/admin/applications/${applicationId}/api-keys/${apiKeyId}/revoke`,
    { method: "POST" },
  );
}

export function getUsers() {
  return request("/admin/users");
}

export function createUser(user) {
  return request("/admin/users", {
    method: "POST",
    body: JSON.stringify(user),
  });
}

export function updateUserStatus(userId, isActive) {
  return request(`/admin/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export { ApiError };
