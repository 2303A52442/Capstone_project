const API_BASE = (
  import.meta.env.VITE_API_URL
  || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://ai-career-twin-backend-kis8.onrender.com')
).replace(/\/+$/, '');

function formatApiError(detail, status) {
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (!item || typeof item !== 'object') return '';
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
        return field && item.msg ? `${field}: ${item.msg}` : item.msg || '';
      })
      .filter(Boolean);
    if (messages.length) return messages.join('. ');
  }

  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message;
  }

  return {
    401: 'Invalid username or password.',
    404: 'The requested resource was not found.',
    422: 'Please check the form fields and try again.',
    500: 'The server could not complete the request. Please try again later.',
  }[status] || 'Request failed. Please try again.';
}

async function request(path, options = {}) {
  const token = localStorage.getItem('career_twin_token');
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  } catch {
    console.error('API request could not be completed', { path, status: 'network' });
    throw new Error('Unable to reach the API. Please check your connection and try again.');
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    console.error('API request failed', { path, status: response.status });
    if (response.status === 401) {
      localStorage.removeItem('career_twin_token');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    throw new Error(formatApiError(detail.detail, response.status));
  }
  return response.json();
}

async function upload(path, file) {
  const token = localStorage.getItem('career_twin_token');
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: file,
    });
  } catch {
    console.error('API upload could not be completed', { path, status: 'network' });
    throw new Error('Unable to reach the API. Please check your connection and try again.');
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    console.error('API upload failed', { path, status: response.status });
    throw new Error(formatApiError(detail.detail, response.status));
  }
  return response.json();
}

export function login(username, password) {
  return request('/auth/login-json', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function register(payload) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getDashboard() {
  return request('/dashboard');
}

export function getRecommendations() {
  return request('/recommendations');
}

export function generateRecommendation() {
  return request('/recommendations/generate', { method: 'POST' });
}

export function acceptRecommendation(id) {
  return request(`/recommendations/${id}/accept`, { method: 'POST' });
}

export function completeRecommendation(id) {
  return request(`/recommendations/${id}/complete`, { method: 'POST' });
}

export function recordOutcome(id, payload) {
  return request(`/recommendations/${id}/outcome`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getProfile() {
  return request('/candidate/profile');
}

export function updateProfile(payload) {
  return request('/candidate/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function getRoles() {
  return request('/roles');
}

export function createRole(payload) {
  return request('/roles', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function addRoleSkill(roleId, payload) {
  return request(`/roles/${roleId}/skills`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getSelectedRole() {
  return request('/roles/current/selected');
}

export function getRole(roleId) {
  return request(`/roles/${roleId}`);
}

export function selectRole(roleId) {
  return request(`/roles/${roleId}/select`, { method: 'PUT' });
}

export function getSkills() {
  return request('/skills');
}

export function createSkill(payload) {
  return request('/skills', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getCandidateSkills() {
  return request('/skills/candidate');
}

export function updateCandidateSkill(payload) {
  return request('/skills/candidate', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function getPerformance() {
  return request('/performance');
}

export function addPerformance(payload) {
  return request('/performance', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getCareerTwin() {
  return request('/career-twin');
}

export function compareRoles(roleAId, roleBId) {
  return request(`/comparison?role_a_id=${roleAId}&role_b_id=${roleBId}`);
}

export function simulateSkills(payload) {
  return request('/career-twin/simulate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getEvidence() { return request('/evidence'); }

export function analyzeResume(file) {
  const form = new FormData();
  form.append('file', file);
  return upload('/evidence/resume/analyze', form);
}

export function analyzeGithub(username) {
  return request('/evidence/github/analyze', { method: 'POST', body: JSON.stringify({ username }) });
}

export function confirmEvidence(id) { return request(`/evidence/${id}/confirm`, { method: 'POST' }); }
export function rejectEvidence(id) { return request(`/evidence/${id}/reject`, { method: 'POST' }); }
