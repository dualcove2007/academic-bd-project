const API_BASE = '/api';

function getToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
}

function setAuth(token, user) {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user_data', JSON.stringify(user));
}

function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
}

function isAuthenticated() {
    return !!getToken();
}

function logout() {
    clearAuth();
    window.location.href = '/';
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

    if (res.status === 401) {
        if (token) {
            clearAuth();
            window.location.href = '/';
            throw new Error('Sesión expirada');
        }
    }

    if (res.status === 204) return null;

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error en la solicitud');
    return data;
}

function apiGet(endpoint) {
    return apiRequest(endpoint);
}

function apiPost(endpoint, body) {
    return apiRequest(endpoint, { method: 'POST', body: JSON.stringify(body) });
}

function apiPut(endpoint, body) {
    return apiRequest(endpoint, { method: 'PUT', body: JSON.stringify(body) });
}

function apiPatch(endpoint, body) {
    return apiRequest(endpoint, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined });
}

function escapeHtml(str) {
    if (!str) return str;
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}
