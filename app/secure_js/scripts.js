function showTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab-active'));
  document.getElementById(tabId).classList.add('tab-active');
}

async function pushSingle() {
  const dataInput = document.getElementById("singleData").value;
  const statusEl = document.getElementById("status");
  let data;
  try {
    data = JSON.parse(dataInput);
  } catch (e) {
    statusEl.textContent = "❌ Invalid JSON format.";
    return;
  }

  const res = await fetch("/encrypt-transaction/", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  if (res.ok) {
    statusEl.textContent = "✅ 1 transaction pushed successfully!";
  } else {
    const result = await res.text();
    statusEl.textContent = "❌ Push failed: " + result;
  }
}

async function pushBulk() {
  const file = document.getElementById("bulkFile").files[0];
  const statusEl = document.getElementById("status");
  const logEl = document.getElementById("bulkLog");

  logEl.innerHTML = "";

  if (!file) {
    statusEl.textContent = "Please select a file.";
    return;
  }

  const extension = file.name.split('.').pop().toLowerCase();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/pushBulk", {
    method: "POST",
    body: formData
  });

  if (res.ok) {
    const result = await res.json();
    statusEl.textContent = `✅ Bulk load complete. Processed: ${result.total_records}.`;
  } else {
    const err = await res.text();
    statusEl.textContent = `❌ Bulk load failed: ${err}`;
  }
}



async function fetchSessionBenchmarks() {
  const res = await fetch("/benchmarks/sessions");
  const data = await res.json();

  const table = document.getElementById("sessionBenchmarkTable");
  table.innerHTML = "<tr><th>ID</th><th>Algorithm</th><th>Avg Latency</th><th>Std Dev</th><th>Min</th><th>Max</th><th>Throughput</th><th>Error Rate</th><th>Encryption Time</th><th>Timestamp</th></tr>";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.id}</td>
      <td>${row.algorithm}</td>
      <td>${row.latency.toFixed(2)}</td>
      <td>${row.stddev.toFixed(2)}</td>
      <td>${row.min_latency.toFixed(2)}</td>
      <td>${row.max_latency.toFixed(2)}</td>
      <td>${row.throughput.toFixed(2)}</td>
      <td>${row.error_rate.toFixed(2)}</td>
      <td>${row.encryption_time.toFixed(2)}</td>
      <td>${row.timestamp}</td>
    `;
    table.appendChild(tr);
  });
}

async function fetchLiveBenchmarks() {
  const res = await fetch("/benchmarks/live");
  const data = await res.json();

  const table = document.getElementById("liveBenchmarkTable");
  table.innerHTML = "<tr><th>Algorithm</th><th>Avg Latency</th><th>Std Dev</th><th>Min</th><th>Max</th><th>Throughput</th><th>Error Rate</th></tr>";

  Object.entries(data).forEach(([algo, metrics]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${algo}</td>
      <td>${metrics.average_latency.toFixed(2)}</td>
      <td>${metrics.stddev_latency.toFixed(2)}</td>
      <td>${metrics.min_latency.toFixed(2)}</td>
      <td>${metrics.max_latency.toFixed(2)}</td>
      <td>${metrics.throughput.toFixed(2)}</td>
      <td>${metrics.error_rate.toFixed(2)}</td>
    `;
    table.appendChild(tr);
  });
}

function logout() {
  document.cookie = "user=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  window.location.href = "/logout";
}
