const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const token = localStorage.getItem('career_twin_token');
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    if (response.status === 401) {
      localStorage.removeItem('career_twin_token');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    throw new Error(detail.detail || 'Request failed');
  }
  return response.json();
}

async function upload(path, file) {
  const token = localStorage.getItem('career_twin_token');
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: file,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || 'Upload failed');
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
