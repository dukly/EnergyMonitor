const powerAcEl = document.getElementById('powerAc');
const energyDayEl = document.getElementById('energyDay');
const statusEl = document.getElementById('status');
const errorEl = document.getElementById('error');
const chartCanvas = document.getElementById('chart');

function drawChart(values) {
  const ctx = chartCanvas.getContext('2d');
  const width = chartCanvas.width;
  const height = chartCanvas.height;
  ctx.clearRect(0, 0, width, height);

  if (!values.length) {
    ctx.fillStyle = '#6b7280';
    ctx.fillText('Нет данных', 20, height / 2);
    return;
  }

  const max = Math.max(...values, 1);
  const step = width / Math.max(values.length - 1, 1);

  ctx.strokeStyle = '#f5a623';
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = index * step;
    const y = height - (value / max) * (height - 20) - 10;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

async function refresh() {
  const apiUrl = document.getElementById('apiUrl').value.replace(/\/$/, '');
  const siteId = document.getElementById('siteId').value;

  const response = await fetch(`${apiUrl}/v1/sites/${siteId}/metrics`);
  const data = await response.json();

  const latest = data.latest;
  if (latest) {
    powerAcEl.textContent = latest.power_ac != null ? `${latest.power_ac} W` : '—';
    energyDayEl.textContent = latest.energy_day != null ? `${latest.energy_day} kWh` : '—';
    statusEl.textContent = latest.status_text || latest.status || '—';
    errorEl.textContent = latest.error_text || latest.error || '—';
  }

  const series = (data.measurements || [])
    .map((row) => row.power_ac)
    .filter((value) => value != null);
  drawChart(series);
}

document.getElementById('refreshBtn').addEventListener('click', refresh);
refresh();
