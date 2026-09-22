const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("vi_token");
}

export function setToken(token) {
  localStorage.setItem("vi_token", token);
} 

export async function getAnalyticsSummary() {
  return request("/analytics/summary");
}


export function clearToken() {
  localStorage.removeItem("vi_token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = "Something went wrong";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (e) {
      /* ignore parse error */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export async function signup({ name, email, password, role }) {
  return request("/users/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role }),
  });
}

export async function login({ email, password }) {
  const data = await request("/users/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function getCurrentUser() {
  return request("/users/me");
}

export async function getImages() {
  return request("/images/");
}

export const listImages = getImages;

export async function getImageDetail(imageId) {
  return request(`/images/${imageId}`);
}

export async function runInspection(imageId) {
  return request(`/inspections/run/${imageId}`, { method: "POST" });
}

export function getImageFileUrl(imageId) {
  return `${API_URL}/images/${imageId}/file`;
}

export async function uploadImage({ categoryId, file }) {
  const token = getToken();
  const formData = new FormData();
  formData.append("category_id", categoryId);
  formData.append("file", file);

  const res = await fetch(`${API_URL}/images/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    let detail = "Upload failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (e) {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}
