(function () {
  "use strict";

  const API_BASE_URL =
    window.KAIROS_API_URL ||
    localStorage.getItem("kairos_api_url") ||
    "https://kairos-backend.onrender.com";

  const API = {
    auth: {
      register: "/api/v1/auth/register",
      login: "/api/v1/auth/login",
      refresh: "/api/v1/auth/refresh",
      google: "/api/v1/auth/google/login",
    },
    users: {
      me: "/api/v1/users/me",
      profile: "/api/v1/users/me/profile",
      interests: "/api/v1/users/me/interests",
      assessment: "/api/v1/users/me/skill-assessment",
    },
    roadmaps: {
      generate: "/api/v1/roadmaps/generate",
      detail: (id) => `/api/v1/roadmaps/${encodeURIComponent(id)}`,
    },
    learning: {
      badges: "/api/v1/learning/skills/my-badges",
      quiz: (id) => `/api/v1/learning/quizzes/${encodeURIComponent(id)}/questions`,
      submitQuiz: (id) => `/api/v1/learning/quizzes/${encodeURIComponent(id)}/submit`,
      submitProject: "/api/v1/learning/projects/submit",
    },
    mentors: {
      list: "/api/v1/mentors/",
      detail: (id) => `/api/v1/mentors/${encodeURIComponent(id)}`,
      book: (id) => `/api/v1/mentors/${encodeURIComponent(id)}/book`,
    },
    companies: {
      jobs: "/api/v1/companies/jobs",
      apply: (id) => `/api/v1/companies/jobs/${encodeURIComponent(id)}/apply`,
      analytics: "/api/v1/companies/dashboard/analytics",
      profile: "/api/v1/companies/me/profile",
      portfolio: "/api/v1/companies/portfolio/me",
      resume: "/api/v1/companies/resume/generate",
      improve: "/api/v1/companies/resume/ai-improve",
    },
    gigs: {
      list: "/api/v1/gigs/",
      detail: (id) => `/api/v1/gigs/${encodeURIComponent(id)}`,
      apply: (id) => `/api/v1/gigs/${encodeURIComponent(id)}/apply`,
      mine: "/api/v1/gigs/applications/mine",
    },
    notifications: {
      list: "/api/v1/notifications/",
      read: (id) => `/api/v1/notifications/${encodeURIComponent(id)}/read`,
    },
    payments: {
      wallet: "/api/v1/payments/wallet/me",
      withdraw: "/api/v1/payments/wallet/withdraw",
      history: "/api/v1/payments/history",
    },
    admin: {
      usage: "/api/v1/admin/ai-usage",
    },
  };

  function token(key) {
    return localStorage.getItem(key);
  }

  function saveTokens(data) {
    if (data && data.access_token) {
      localStorage.setItem("access_token", data.access_token);
    }
    if (data && data.refresh_token) {
      localStorage.setItem("refresh_token", data.refresh_token);
    }
  }

  function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("kairos_user");
  }

  async function parseResponse(response) {
    const raw = await response.text();
    let data = null;
    try {
      data = raw ? JSON.parse(raw) : null;
    } catch {
      data = raw;
    }

    if (!response.ok) {
      const error = new Error(data && data.detail ? data.detail : `Request failed (${response.status})`);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    // Handle 204 No Content explicitly
    if (response.status === 204) {
      return null;
    }

    return data;
  }

  async function apiFetch(endpoint, options = {}, retried = false) {
    const headers = new Headers(options.headers || {});

    // Only set Content-Type if not already present and body is not FormData
    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const accessToken = token("access_token");
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    let response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
    } catch (error) {
      const unavailable = new Error(
        "Backend unavailable. Check that the FastAPI server is running and that the API URL is configured correctly."
      );
      unavailable.cause = error;
      throw unavailable;
    }

    // Handle 401 with token refresh (only once per request)
    if (response.status === 401 && !retried && token("refresh_token") && !endpoint.endsWith("/refresh")) {
      try {
        const refreshed = await apiFetch(
          API.auth.refresh,
          {
            method: "POST",
            body: JSON.stringify({ refresh_token: token("refresh_token") }),
          },
          true
        );
        saveTokens(refreshed);
        return apiFetch(endpoint, options, true);
      } catch {
        clearTokens();
        if (!location.pathname.endsWith("/login.html")) {
          location.href = "/pages/login.html";
        }
        throw new Error("Your session has expired. Please log in again.");
      }
    }

    return parseResponse(response);
  }

  window.KairosAPI = {
    API,
    API_BASE_URL,
    apiFetch,
    saveTokens,
    clearTokens,
    getAccessToken: () => token("access_token"),
    getRefreshToken: () => token("refresh_token"),
  };
})();