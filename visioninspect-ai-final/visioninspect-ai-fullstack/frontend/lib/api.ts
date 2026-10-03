/**
 * Milestone 1 - Thin fetch wrapper for the FastAPI backend.
 * Reads the JWT from localStorage (set on login) and attaches it to every request.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("vi_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  async signup(username: string, password: string, role = "quality_engineer") {
    const res = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role }),
    });
    return handle(res);
  },

  async login(username: string, password: string) {
    const form = new URLSearchParams({ username, password });
    const res = await fetch(`${API_URL}/auth/login`, { method: "POST", body: form });
    const data = await handle(res);
    localStorage.setItem("vi_token", data.access_token);
    return data;
  },

  logout() {
    localStorage.removeItem("vi_token");
  },

  async me() {
    const res = await fetch(`${API_URL}/auth/me`, { headers: authHeaders() });
    return handle(res);
  },

  async uploadInspection(file: File, productLine?: string, batchId?: string) {
    const form = new FormData();
    form.append("file", file);
    if (productLine) form.append("product_line", productLine);
    if (batchId) form.append("batch_id", batchId);
    const res = await fetch(`${API_URL}/inspections`, { method: "POST", headers: authHeaders(), body: form });
    return handle(res);
  },

  async listInspections() {
    const res = await fetch(`${API_URL}/inspections`, { headers: authHeaders() });
    return handle(res);
  },

  async getInspection(id: number) {
    const res = await fetch(`${API_URL}/inspections/${id}`, { headers: authHeaders() });
    return handle(res);
  },

  async getFixes(id: number) {
    const res = await fetch(`${API_URL}/inspections/${id}/fixes`, { headers: authHeaders() });
    return handle(res);
  },

  async analyticsSummary() {
    const res = await fetch(`${API_URL}/analytics/summary`, { headers: authHeaders() });
    return handle(res);
  },

  async runValidation(nImages = 25) {
    const res = await fetch(`${API_URL}/validation/run?n_images=${nImages}`, {
      method: "POST", headers: authHeaders(),
    });
    return handle(res);
  },

  async listUsers() {
    const res = await fetch(`${API_URL}/users`, { headers: authHeaders() });
    return handle(res);
  },
};
