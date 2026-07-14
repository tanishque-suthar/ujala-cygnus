const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function screenXray(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE}/screen`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}
