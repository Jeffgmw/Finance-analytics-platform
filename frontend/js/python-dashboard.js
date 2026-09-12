const fmt = (n) =>
  new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(
    Number(n || 0),
  );
const plotBase = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, Segoe UI, sans-serif", color: "#334155" },
  margin: { t: 18, r: 18, b: 48, l: 55 },
};
const config = {
  responsive: true,
  displaylogo: false,
  modeBarButtons: [["zoomIn2d", "zoomOut2d", "autoScale2d", "toImage"]],
};
function plot(id, data, layout = {}) {
  return Plotly.react(id, data, { ...plotBase, ...layout }, config);
}
function fillSelect(id, values) {
  const el = document.getElementById(id);
  for (const v of values || [])
    el.insertAdjacentHTML(
      "beforeend",
      `<option value="${String(v).replaceAll('"', "&quot;")}">${v}</option>`,
    );
}
async function populate() {
  const o = await apiGet("/api/analytics/python/filter-options");
  fillSelect("txnType", o.transaction_types);
  fillSelect("channel", o.channels);
  fillSelect("merchant", o.merchant_categories);
  fillSelect("accountType", o.account_types);
}
function drawCore(m, fr) {
  plot(
    "trend",
    [
      {
        x: m.map((x) => x.month),
        y: m.map((x) => x.total_value),
        name: "Value",
        type: "bar",
        opacity: 0.32,
      },
      {
        x: m.map((x) => x.month),
        y: m.map((x) => x.transaction_count),
        name: "Volume",
        type: "scatter",
        mode: "lines+markers",
        yaxis: "y2",
      },
    ],
    {
      barmode: "overlay",
      yaxis: { title: "Value" },
      yaxis2: {
        title: "Volume",
        overlaying: "y",
        side: "right",
        showgrid: false,
      },
    },
  );
  plot(
    "threatLevels",
    [
      {
        x: fr.threat_levels.map((x) => x.threat_level),
        y: fr.threat_levels.map((x) => x.transaction_count),
        type: "bar",
        text: fr.threat_levels.map((x) => fmt(x.transaction_value)),
        textposition: "auto",
        hovertemplate: "%{x}<br>Volume: %{y}<br>Value: %{text}<extra></extra>",
      },
    ],
    {
      yaxis: { title: "Transactions" },
      xaxis: {
        categoryorder: "array",
        categoryarray: ["Low", "Medium", "High"],
      },
    },
  );
  plot(
    "channels",
    [
      {
        x: fr.channels.map((x) => x.channel),
        y: fr.channels.map((x) => x.transaction_value),
        type: "bar",
        text: fr.channels.map((x) => x.high_count),
        textposition: "outside",
        hovertemplate:
          "%{x}<br>Value: %{y}<br>High-risk signals: %{text}<extra></extra>",
      },
    ],
    { xaxis: { tickangle: -25 }, yaxis: { title: "Transaction value" } },
  );
  plot(
    "riskPeak",
    [
      {
        x: fr.daily.map((x) => x.txn_date),
        y: fr.daily.map((x) => x.high_count),
        type: "scatter",
        mode: "lines+markers",
        fill: "tozeroy",
        customdata: fr.daily.map((x) => [x.transaction_count, x.high_value]),
        hovertemplate:
          "%{x}<br>High-risk signals: %{y}<br>Total volume: %{customdata[0]}<br>High-risk value: %{customdata[1]}<extra></extra>",
      },
    ],
    { yaxis: { title: "High-risk volume" }, xaxis: { title: "Date" } },
  );
}
async function loadCore() {
  const data = await apiGet("/api/analytics/dashboard", filterParams());
  const s = data.summary;
  const m = data.monthly;
  const fr = data.fraud;
  customers.textContent = fmt(s.customers);
  accounts.textContent = fmt(s.accounts);
  value.textContent = fmt(s.transaction_value);
  channelsKpi.textContent = fmt(s.channels);
  drawCore(m, fr);
}
async function loadSecondary() {
  const f = filterParams();
  const [t, mc, i] = await Promise.all([
    apiGet("/api/analytics/python/transaction-types", f),
    apiGet("/api/analytics/python/merchant-categories", f),
    apiGet("/api/analytics/python/income-activity", f),
  ]);
  plot(
    "types",
    [
      {
        labels: t.map((x) => x.category || "Unknown"),
        values: t.map((x) => x.total_value),
        type: "pie",
        hole: 0.48,
        textinfo: "label+percent",
      },
    ],
    { margin: { t: 15, b: 15, l: 15, r: 15 } },
  );
  plot(
    "merchantChart",
    [
      {
        x: mc.slice(0, 12).map((x) => x.category || "Unknown"),
        y: mc.slice(0, 12).map((x) => x.total_value),
        type: "bar",
      },
    ],
    { xaxis: { tickangle: -35 }, yaxis: { title: "Value" } },
  );
  plot(
    "income",
    [
      {
        x: i.map((x) => x.annual_income),
        y: i.map((x) => x.transaction_value),
        mode: "markers",
        type: "scatter",
        marker: { size: 7, opacity: 0.65 },
        text: i.map((x) => `Customer #${x.customer_id}`),
        hovertemplate:
          "%{text}<br>Income: %{x}<br>Txn value: %{y}<extra></extra>",
      },
    ],
    {
      xaxis: { title: "Annual income" },
      yaxis: { title: "Transaction value" },
    },
  );
}
function idle(fn) {
  if ("requestIdleCallback" in window)
    requestIdleCallback(fn, { timeout: 1200 });
  else setTimeout(fn, 250);
}
document.addEventListener("DOMContentLoaded", async () => {
  try {
    await populate();
    await loadCore();
    idle(() => loadSecondary());
    apply.addEventListener("click", async () => {
      await loadCore();
      idle(() => loadSecondary());
    });
  } catch (e) {
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div class="error">${e.message}. Start the FastAPI backend and load PostgreSQL.</div>`,
    );
  }
});
