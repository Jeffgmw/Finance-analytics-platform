async function apiGet(path, params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, v);
  });
  const r = await fetch(
    `${window.API_BASE_URL}${path}${qs.toString() ? `?${qs}` : ""}`,
  );
  if (!r.ok) throw new Error(`API error ${r.status}`);
  return r.json();
}
async function apiPost(path, body) {
  const r = await fetch(`${window.API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`API error ${r.status}`);
  return r.json();
}
function filterParams() {
  return {
    start_date: document.querySelector("#startDate")?.value,
    end_date: document.querySelector("#endDate")?.value,
    transaction_type: document.querySelector("#txnType")?.value,
    channel: document.querySelector("#channel")?.value,
    merchant_category: document.querySelector("#merchant")?.value,
    account_type: document.querySelector("#accountType")?.value,
  };
}
