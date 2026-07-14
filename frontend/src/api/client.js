const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function screenXray(file, patientName, patientId = null) {
  const form = new FormData();
  form.append("file", file);
  form.append("patient_name", patientName);
  if (patientId) form.append("patient_id", patientId);

  const res = await fetch(`${BASE}/screen`, { method: "POST", body: form });
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

