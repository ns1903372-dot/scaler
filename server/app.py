from fastapi import Response
from fastapi.responses import HTMLResponse
from openenv.core.env_server import create_app

from retail_ops_env.models import RetailOpsAction, RetailOpsObservation
from retail_ops_env.server.case_resolution_env import RetailOpsEnvironment
from retail_ops_env.tasks import TASKS

app = create_app(
    RetailOpsEnvironment,
    RetailOpsAction,
    RetailOpsObservation,
    env_name="retail_ops_env",
)


UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Retail Ops OpenEnv</title>
  <style>
    :root {
      --bg: #f5efe4;
      --panel: rgba(255,255,255,0.82);
      --line: rgba(34,43,69,0.12);
      --ink: #1f2937;
      --muted: #5f6b7a;
      --accent: #c8672f;
      --accent-dark: #8e4322;
      --ok: #16794b;
      --shadow: 0 20px 60px rgba(80, 56, 35, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(236, 175, 95, 0.28), transparent 28%),
        radial-gradient(circle at bottom right, rgba(122, 162, 109, 0.24), transparent 26%),
        linear-gradient(135deg, #f7f2e8 0%, #efe4d4 52%, #f7f2e8 100%);
      min-height: 100vh;
    }
    .shell {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 20px 40px;
    }
    .hero {
      display: grid;
      gap: 18px;
      margin-bottom: 24px;
    }
    .eyebrow {
      font-size: 12px;
      letter-spacing: 0.24em;
      text-transform: uppercase;
      color: var(--accent-dark);
      font-weight: 700;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 5vw, 4.3rem);
      line-height: 0.94;
      max-width: 10ch;
    }
    .lead {
      max-width: 70ch;
      margin: 0;
      color: var(--muted);
      font-size: 1.02rem;
      line-height: 1.65;
    }
    .grid {
      display: grid;
      grid-template-columns: 380px minmax(0, 1fr);
      gap: 20px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .panel-pad {
      padding: 20px;
    }
    .panel h2, .panel h3 {
      margin: 0 0 10px;
      font-size: 1rem;
    }
    .stack {
      display: grid;
      gap: 14px;
    }
    label {
      display: grid;
      gap: 6px;
      font-size: 0.9rem;
      color: var(--muted);
    }
    input, select, textarea {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      font: inherit;
      color: var(--ink);
      background: rgba(255,255,255,0.92);
    }
    textarea {
      min-height: 130px;
      resize: vertical;
    }
    .buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 11px 16px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease, background 140ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button.primary { background: var(--accent); color: white; }
    button.secondary { background: #243042; color: white; }
    button.ghost { background: rgba(36,48,66,0.08); color: var(--ink); }
    .hint {
      font-size: 0.88rem;
      color: var(--muted);
      line-height: 1.5;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(22,121,75,0.08);
      color: var(--ok);
      font-size: 0.88rem;
      font-weight: 700;
    }
    .output-grid {
      display: grid;
      gap: 18px;
    }
    .output-box {
      padding: 18px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.86);
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.88rem;
      line-height: 1.55;
    }
    .mini {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .metric {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .metric strong {
      font-size: 1.1rem;
    }
    @media (max-width: 980px) {
      .grid { grid-template-columns: 1fr; }
      .mini { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">OpenEnv Retail Operations Simulator</div>
      <h1>Buttons, input, output, and live API actions.</h1>
      <p class="lead">
        This Space lets you drive the environment directly in the browser while keeping the evaluator-friendly API routes live at
        <code>/reset</code>, <code>/step</code>, and <code>/state</code>.
      </p>
      <div class="status" id="health-status">Checking API status...</div>
    </section>

    <section class="grid">
      <div class="panel panel-pad stack">
        <div>
          <h2>Control Panel</h2>
          <p class="hint">Choose a task, reset the environment, then send actions with the typed payload format.</p>
        </div>

        <label>
          Task
          <select id="task-select"></select>
        </label>

        <div class="buttons">
          <button class="primary" id="reset-btn">Reset Task</button>
          <button class="ghost" id="state-btn">Refresh State</button>
        </div>

        <label>
          Command
          <select id="command-select">
            <option value="inspect_case">inspect_case</option>
            <option value="inspect_order">inspect_order</option>
            <option value="inspect_policy">inspect_policy</option>
            <option value="inspect_inventory">inspect_inventory</option>
            <option value="update_shipping_address">update_shipping_address</option>
            <option value="issue_refund">issue_refund</option>
            <option value="create_replacement">create_replacement</option>
            <option value="send_message">send_message</option>
            <option value="add_internal_note">add_internal_note</option>
            <option value="resolve_case">resolve_case</option>
            <option value="escalate_case">escalate_case</option>
          </select>
        </label>

        <label>
          Order ID
          <input id="order-id" placeholder="ORD-1001" />
        </label>

        <label>
          Reference ID
          <input id="reference-id" placeholder="ADDR-01 / GRIND-09 / PAY-02" />
        </label>

        <label>
          Payload JSON
          <textarea id="payload-box">{"message":"We are reviewing your case."}</textarea>
        </label>

        <label>
          Rationale
          <input id="rationale-box" placeholder="Optional explanation for the action" />
        </label>

        <div class="buttons">
          <button class="secondary" id="step-btn">Send Step</button>
        </div>

        <div class="output-box">
          <h3>Quick API Examples</h3>
          <pre>POST /reset
{"task_id":"easy_address_fix"}

POST /step
{"action":{"command":"inspect_case","payload":{}}}

GET /state</pre>
        </div>
      </div>

      <div class="output-grid">
        <div class="mini">
          <div class="metric"><span>Active Task</span><strong id="metric-task">-</strong></div>
          <div class="metric"><span>Score</span><strong id="metric-score">0.0</strong></div>
          <div class="metric"><span>Done</span><strong id="metric-done">false</strong></div>
        </div>

        <div class="panel panel-pad">
          <h2>Latest Response</h2>
          <div class="output-box">
            <pre id="response-box">No response yet.</pre>
          </div>
        </div>

        <div class="panel panel-pad">
          <h2>Current State</h2>
          <div class="output-box">
            <pre id="state-box">No state loaded yet.</pre>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const taskSelect = document.getElementById("task-select");
    const commandSelect = document.getElementById("command-select");
    const orderId = document.getElementById("order-id");
    const referenceId = document.getElementById("reference-id");
    const payloadBox = document.getElementById("payload-box");
    const rationaleBox = document.getElementById("rationale-box");
    const responseBox = document.getElementById("response-box");
    const stateBox = document.getElementById("state-box");
    const healthStatus = document.getElementById("health-status");

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    function setMetrics(data) {
      const visibleCase = data?.visible_case || {};
      const taskId = visibleCase.task_id || data?.task_id || data?.metadata?.task_id || "-";
      const score = data?.score ?? data?.reward ?? 0.0;
      const done = data?.done ?? (data?.resolution_status ? data.resolution_status !== "active" : false);
      document.getElementById("metric-task").textContent = String(taskId);
      document.getElementById("metric-score").textContent = String(score);
      document.getElementById("metric-done").textContent = String(done);
    }

    async function loadTasks() {
      const res = await fetch("/tasks");
      const tasks = await res.json();
      taskSelect.innerHTML = "";
      tasks.forEach((task) => {
        const option = document.createElement("option");
        option.value = task.id;
        option.textContent = `${task.difficulty.toUpperCase()} - ${task.title}`;
        taskSelect.appendChild(option);
      });
    }

    async function checkHealth() {
      const res = await fetch("/health");
      const data = await res.json();
      healthStatus.textContent = data.status === "ok" ? "API healthy and ready" : "API status unknown";
    }

    async function refreshState() {
      const res = await fetch("/state");
      const data = await res.json();
      stateBox.textContent = pretty(data);
      setMetrics(data);
    }

    async function resetTask() {
      const res = await fetch("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskSelect.value })
      });
      const data = await res.json();
      responseBox.textContent = pretty(data);
      setMetrics(data);
      await refreshState();
    }

    async function sendStep() {
      let payload = {};
      try {
        payload = payloadBox.value.trim() ? JSON.parse(payloadBox.value) : {};
      } catch (error) {
        responseBox.textContent = "Payload JSON is invalid. Please fix it before sending.";
        return;
      }

      const action = {
        command: commandSelect.value,
        payload: payload,
      };

      if (orderId.value.trim()) action.order_id = orderId.value.trim();
      if (referenceId.value.trim()) action.reference_id = referenceId.value.trim();
      if (rationaleBox.value.trim()) action.rationale = rationaleBox.value.trim();

      const res = await fetch("/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
      });
      const data = await res.json();
      responseBox.textContent = pretty(data);
      setMetrics(data.observation || data);
      await refreshState();
    }

    document.getElementById("reset-btn").addEventListener("click", resetTask);
    document.getElementById("step-btn").addEventListener("click", sendStep);
    document.getElementById("state-btn").addEventListener("click", refreshState);

    Promise.all([loadTasks(), checkHealth(), refreshState()]);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(UI_HTML)


@app.get("/tasks")
def tasks() -> list[dict[str, str]]:
    return [
        {
            "id": task["id"],
            "difficulty": task["difficulty"],
            "title": task["title"],
        }
        for task in TASKS
    ]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    return Response(status_code=200)
