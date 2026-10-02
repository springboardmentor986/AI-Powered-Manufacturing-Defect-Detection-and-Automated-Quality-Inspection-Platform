import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });

  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes("/auth/login") ||
      originalRequest.url?.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("role");

      window.location.href = "/login";

      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        null,
        {
          params: {
            refresh_token: refreshToken,
          },
        }
      );

      const newAccessToken = response.data.access_token;

      localStorage.setItem("token", newAccessToken);

      processQueue(null, newAccessToken);

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return api(originalRequest);

    } catch (refreshError) {

      processQueue(refreshError, null);

      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("role");

      window.location.href = "/login";

      return Promise.reject(refreshError);

    } finally {
      isRefreshing = false;
    }
  }
);

export default api;