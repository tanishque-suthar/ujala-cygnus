const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function fetchWithTimeout(url, options = {}, timeoutMs = 60000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (options.signal) {
    options.signal.addEventListener('abort', () => controller.abort());
  }
  return fetch(url, { ...options, signal: controller.signal })
    .finally(() => clearTimeout(timer));
}

async function request(path, options = {}) {
  const res = await fetchWithTimeout(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function screenXray(file, patientName, patientId = null, signal = null) {
  const form = new FormData();
  form.append("file", file);
  form.append("patient_name", patientName);
  if (patientId) form.append("patient_id", patientId);

  const res = await fetchWithTimeout(`${BASE}/screen`, { method: "POST", body: form, signal }, 120000);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const fetchPatients = () => request("/patients");

export const fetchPatientStats = () => request("/patients/stats");

export const fetchPatient = (patientId) => request(`/patients/${patientId}`);

export const fetchPatientDocuments = (patientId) =>
  request(`/patients/${patientId}/documents`);

export const fetchDocument = (documentId) =>
  request(`/documents/${documentId}`);

export const heatmapUrl = (scanResultId) =>
  `${BASE}/heatmap/${scanResultId}`;

export const imageUrl = (documentId) =>
  `${BASE}/image/${documentId}`;

export async function uploadReport(file, signal = null) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetchWithTimeout(`${BASE}/reports/upload`, { method: "POST", body: form, signal }, 120000);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function confirmReport(data, signal = null) {
  const res = await fetchWithTimeout(`${BASE}/reports/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    signal,
  }, 60000);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const reportFileUrl = (documentId) =>
  `${BASE}/reports/${documentId}/file`;
