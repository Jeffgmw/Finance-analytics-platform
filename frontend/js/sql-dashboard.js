const money = (n) =>
  new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(
    Number(n || 0),
  );
const base = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, Segoe UI, sans-serif", color: "#334155" },
  margin: { t: 18, r: 18, b: 48, l: 55 },
};
const plotConfig = {
  responsive: true,
  displaylogo: false,
  modeBarButtons: [["zoomIn2d", "zoomOut2d", "autoScale2d", "toImage"]],
};
function sqlPlot(id, data, layout = {}) {
  return Plotly.react(id, data, { ...base, ...layout }, plotConfig);
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
  sqlPlot(
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
  sqlPlot(
    "threatLevels",
    [
      {
        x: fr.threat_levels.map((x) => x.threat_level),
        y: fr.threat_levels.map((x) => x.transaction_count),
        type: "bar",
        text: fr.threat_levels.map((x) => money(x.transaction_value)),
        textposition: "auto",
        hovertemplate: "%{x}<br>Volume: %{y}<br>Value: %{text}<extra></extra>",
      },
    ],
    {
      xaxis: {
        categoryorder: "array",
        categoryarray: ["Low", "Medium", "High"],
      },
      yaxis: { title: "Transactions" },
    },
  );
  sqlPlot(
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
  sqlPlot(
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
    { xaxis: { title: "Date" }, yaxis: { title: "High-risk volume" } },
  );
}
async function loadCore() {
  const data = await apiGet("/api/analytics/dashboard", filterParams());
  const s = data.summary;
  const m = data.monthly;
  const fr = data.fraud;
  customers.textContent = money(s.customers);
  accounts.textContent = money(s.accounts);
  txnValue.textContent = money(s.transaction_value);
  channelsKpi.textContent = money(s.channels);
  drawCore(m, fr);
}
async function loadSecondary() {
  const [a, c] = await Promise.all([
    apiGet("/api/analytics/sql/account-summary"),
    apiGet("/api/analytics/sql/customer-360", filterParams()),
  ]);
  sqlPlot(
    "accountsChart",
    [
      {
        x: a.map((x) => `${x.account_type} / ${x.status}`),
        y: a.map((x) => x.total_balance),
        type: "bar",
      },
    ],
    { xaxis: { tickangle: -30 }, yaxis: { title: "Balance" } },
  );
  const rows = c.slice(0, 30);
  customerTable.innerHTML = `<div style="overflow:auto"><table><thead><tr><th>Customer</th><th>Income</th><th>Credit score</th><th>Accounts</th><th>Balance</th><th>Transactions</th><th>Transaction value</th><th>Rank</th></tr></thead><tbody>${rows.map((x) => `<tr><td>Customer #${x.customer_id}</td><td>${money(x.annual_income)}</td><td>${x.credit_score ?? "—"}</td><td>${x.account_count}</td><td>${money(x.total_balance)}</td><td>${x.transaction_count}</td><td>${money(x.total_transaction_value)}</td><td>${x.transaction_value_rank}</td></tr>`).join("")}</tbody></table></div>`;
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
