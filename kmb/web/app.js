(function () {
  "use strict";

  const CAPABILITIES = [
    ["retention", "长期保持"],
    ["memory_recall", "记忆调用"],
    ["dynamic_update", "动态更新"],
    ["similar_distinction", "相近区分"],
    ["boundary", "边界识别"],
    ["task_reuse", "任务复用"]
  ];
  const state = {
    view: "overview",
    configs: [],
    agents: [],
    suites: [],
    runs: [],
    system: null,
    selectedRun: null,
    selectedRunPath: null,
    job: null,
    health: {},
    params: { seed: "42", retries: "1", timeout: "180", scorer_version: "deterministic-v2" },
    baselineParams: null,
    filters: { agent: "all", capability: "all", failure: "all", history: "" },
    loading: false,
    lastRefreshAt: null,
    configSaving: false,
    profiles: [], formTrack: "control", formApiPrimary: "", formApiComparison: "", editingProfileId: null,
    configNotice: null,
    railCollapsed: false,
    resultTab: "result",
    selectedCase: null,
    caseDetail: null,
    agentDetailPath: null,
    providerDetail: null,
    savedAt: null,
    moreOpen: false,
    quickSelected: [],
    quickNotice: null,
    configDraft: {
      profile_id: "",
      provider: "",
      name: "",
      base_url: "",
      endpoint: "/chat/completions",
      model: "",
      api_key_env: "",
      timeout_seconds: "60",
      temperature: "0",
      description: ""
    }
  };

  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value == null ? "" : value)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  const fmt = (value, fallback = "未观测") => value == null || value === "" ? fallback : String(value);
  const pct = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "0.00";
  const scoreValid = (agent) => Boolean(agent) && agent.score_valid !== false;
  const scoreText = (agent) => scoreValid(agent) ? pct(agent.overall) : "不可评分";
  const safeJson = (value) => escapeHtml(JSON.stringify(value, null, 2));
  const api = async (path, options) => {
    const response = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, options || {}));
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || ("请求失败: " + response.status));
    return data;
  };
  const queryPath = (path) => "/api/artifact?path=" + encodeURIComponent(path || "");
  const displayMode = (mode) => ({
    wrapper_assisted: "包装层辅助",
    no_memory: "无记忆基线",
    no_memory_baseline: "无记忆基线",
    simulated: "模拟基线",
    simulated_baseline: "模拟基线",
    memory_state_unobservable: "状态未观测",
    system_level_wrapper_assisted: "包装层辅助",
    mixed: "混合配置"
  }[mode] || mode || "未知");
  // User-facing labels stay Chinese; raw keys remain available in titles and JSON views.
  const displayProfileMode = (mode) => ({
    memory_controller: "记忆开启",
    memory_disabled: "无记忆基线",
    http: "标准 API",
    command: "命令适配器",
    deterministic: "本地基线",
    replay: "证据回放",
    wrapper_assisted: "包装层辅助",
    no_memory: "无记忆基线",
    simulated: "模拟基线",
    simulated_baseline: "模拟基线"
  }[mode] || mode || "未分类");
  const displaySource = (source) => ({ model: "模型", wrapper: "包装层", simulated: "模拟", runner: "运行器", unknown: "未知" }[source] || source || "未知");
  const displayEventKind = (kind) => ({
    action: "实际动作",
    assistant_message: "助手消息",
    user_message: "用户消息",
    memory_write: "记忆写入",
    memory_recall: "记忆检索",
    memory_update: "记忆更新",
    memory_suppress: "记忆抑制",
    model_request: "模型请求",
    model_response: "模型响应",
    error: "错误",
    evidence: "证据事件"
  }[kind] || kind || "事件");
  const displaySuiteName = (suite) => {
    const value = typeof suite === "string" ? suite : (suite && (suite.name || suite.path));
    if (!value) return "未选择";
    const key = String(value).split(/[\\/]/).pop().replace(/\.ya?ml$/i, "");
    return ({
      "core-zh": "核心套件（中文）",
      "core-en": "核心套件（英文）",
      core: "对抗套件",
      innovation: "创新套件"
    }[key] || key);
  };
  const displayTab = (tab) => ({ result: "概览", compare: "对比", cases: "案例", evidence: "证据", trace: "记忆轨迹", logs: "日志" }[tab] || tab);
  const displayAgentName = (value) => {
    const raw = String(value || "");
    const exact = {
      reference: "参考基线",
      flawed: "缺陷基线",
      "grok-memory-controller": "Grok · 记忆控制器",
      "grok-no-memory-baseline": "Grok · 无记忆基线",
      "grok-api": "Grok · 标准 API",
      "deepseek-memory-controller": "DeepSeek · 记忆控制器",
      "deepseek-no-memory-baseline": "DeepSeek · 无记忆基线",
      "deepseek-api": "DeepSeek · 标准 API",
      "doubao-api": "Doubao · 标准 API",
      "real-agent-a": "回放示例（模板）",
      "external-replay": "外部证据回放",
      kylinbot: "小K KylinBot",
      hermes: "Hermes",
      openclaw: "OpenClaw",
      kylinagent: "KylinAgent"
    };
    return exact[raw.toLowerCase()] || raw
      .replace(/\breference\b/gi, "参考基线")
      .replace(/\bflawed\b/gi, "缺陷基线");
  };
  const displayDisclaimer = (value) => {
    const raw = String(value || "");
    if (/deterministic demonstration baseline/i.test(raw) && /native model memory measurement/i.test(raw)) {
      return "这是确定性演示基线，不是真实参评智能体，也不能用于测量模型原生记忆能力。";
    }
    return raw;
  };
  const displayRunName = (value) => {
    const raw = String(value || "");
    const exact = { "offline-compare": "离线对比", "innovation-compare-offline": "创新套件离线对比" };
    if (exact[raw]) return exact[raw];
    if (/innovation-compare-offline/i.test(raw)) return "创新套件离线对比";
    if (/innovation-dual-compare/i.test(raw)) return "创新套件双智能体对比";
    if (/cli-compare-reference-flawed/i.test(raw)) return "CLI 参考与缺陷基线对比";
    if (/^wb-/i.test(raw)) return "工作台运行";
    return displayAgentName(raw) || "未命名运行";
  };
  const runDisplayName = (run) => (run && run.title) ? String(run.title) : displayRunName((run && (run.id || run.run_id)) || "未命名运行");
  const UI_TEXT_MAP = {
    "Result": "概览", "Compare": "对比", "Cases": "案例", "Evidence": "证据", "Memory Trace": "记忆轨迹", "Logs": "日志",
    "Agent": "智能体", "Agents": "智能体", "Agent A": "主智能体", "Agent B": "对比智能体", "Agent A / Agent B": "主智能体 / 对比智能体", "全部 Agent": "全部智能体", "参与 Agent": "参与智能体", "未命名 Agent": "未命名智能体",
    "Provider": "服务商", "Model": "模型", "Memory Mode": "记忆模式", "Credential Status": "凭据状态", "Used Evaluations": "参与评测", "Recent Performance": "最近表现",
    "Endpoint": "接口", "Base URL": "基础 URL（Base URL）", "Environment": "环境变量", "Platform": "平台", "Storage": "存储", "Status": "状态", "Score": "得分", "Duration": "耗时", "Cases": "案例数", "Score Delta": "分数差值", "Current Case": "当前案例", "Current Agent": "当前智能体", "API Key": "API 密钥（API Key）",
    "CAPABILITY SNAPSHOT": "能力概览", "DIMENSIONS": "能力维度", "SHAPE OVERVIEW": "形状概览", "STABILITY": "稳定性", "EVIDENCE INDEX": "证据索引", "RUN LOGS": "运行日志", "CASE COMPARISON": "案例对比", "CASE DETAIL": "案例详情", "MEMORY TRACE": "记忆轨迹",
    "RESULT WORKSPACE": "结果工作区", "LOCAL RUN ARCHIVE": "本地运行存档", "PROVIDER CONFIGURATION": "服务商配置", "PROVIDER DETAILS": "服务商详情", "READ-ONLY ENVIRONMENT": "只读环境", "AGENT REGISTRY": "智能体列表", "CONFIGURATION": "配置", "PRE-FLIGHT": "运行前检查", "LIVE EVENTS": "实时事件", "BOUNDARY": "边界", "TRACE": "追踪", "RUN": "运行", "TASK": "任务", "AGENTS": "智能体", "ADD PROVIDER PROFILE": "新增服务商配置", "Temperature": "温度", "OpenAI-compatible": "OpenAI 兼容", "agent_process_restart": "智能体进程重启（agent_process_restart）", "system_restart": "系统重启（system_restart）", "user_switch": "用户切换（user_switch）", "offline": "离线状态（offline）", "permission_change": "文件权限变化（permission_change）",
    "Idle": "空闲", "Preparing": "准备中", "Running": "运行中", "Completed": "已完成", "Failed": "失败", "Stopped": "已停止", "Stopping": "停止中",
    "Agent is working…": "智能体正在工作…", "Agent is working...": "智能体正在工作…", "step": "步骤", "event id 未记录": "事件 ID 未记录",
    "model": "模型", "wrapper": "包装层", "simulated": "模拟", "runner": "运行器", "reference": "参考基线", "flawed": "缺陷基线", "offline-compare": "离线对比", "innovation-compare-offline": "创新套件离线对比",
    "retention": "长期保持", "memory_recall": "记忆调用", "dynamic_update": "动态更新", "similar_distinction": "相近区分", "boundary": "边界识别", "task_reuse": "任务复用",
    "No data": "暂无数据", "unknown": "未知", "pass": "通过", "failed": "失败", "error": "错误", "pending": "等待中", "retry": "重试", "stability": "稳定性", "reproduce": "复现", "INSPECTOR": "检查器", "This is a deterministic demonstration baseline, not a real participating agent or native model memory measurement.": "这是确定性演示基线，不是真实参评智能体，也不能用于测量模型原生记忆能力。"
  };
  const normalizeUiSpacing = (value) => String(value || "")
    .replace(/双\s+智能体/g, "双智能体")
    .replace(/两个\s+智能体/g, "两个智能体")
    .replace(/开始双智能体\s+评测/g, "开始双智能体评测")
    .replace(/主\s+智能体/g, "主智能体")
    .replace(/对比\s+智能体/g, "对比智能体")
    .replace(/智能体\s+管理/g, "智能体管理")
    .replace(/智能体\s+对比/g, "智能体对比")
    .replace(/OpenAI 兼容\s+的/g, "OpenAI 兼容的")
    .replace(/基础 URL（基础 URL（Base URL））/g, "基础 URL（Base URL）");
  function localizeUi() {
    const root = document.body;
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent || /^(SCRIPT|STYLE|PRE|CODE|TEXTAREA|INPUT|OPTION)$/.test(parent.tagName)) continue;
      nodes.push(node);
    }
    nodes.forEach((textNode) => {
      let value = textNode.nodeValue;
      const trimmed = value.trim();
      if (/^[A-Za-z0-9_.-]+$/.test(trimmed)) {
        const agentDisplay = displayAgentName(trimmed);
        if (agentDisplay !== trimmed) value = value.replace(trimmed, agentDisplay);
      }
      Object.keys(UI_TEXT_MAP).forEach((key) => {
        const replacement = UI_TEXT_MAP[key];
        if (value.trim() === key) value = value.replace(key, replacement);
        else if (["Agent A", "Agent B", "Agent is working…", "Agent is working...", "step"].includes(key)) value = value.replace(new RegExp("\\b" + key.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + "\\b", "g"), replacement);
      });
      [
        ["Provider", "服务商"], ["Endpoint", "接口"], ["Model", "模型"], ["Temperature", "温度"],
        ["OpenAI-compatible", "OpenAI 兼容"], ["Chat Completions", "Chat Completions"], ["Memory Trace", "记忆轨迹"],
        ["Environment", "环境变量"], ["EvidenceEvent", "证据事件（EvidenceEvent）"],
        ["主 Agent", "主智能体"], ["对比 Agent", "对比智能体"], ["Agent", "智能体"], ["Agents", "智能体"]
      ].forEach(([from, to]) => { value = value.replace(new RegExp("\\b" + from.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + "\\b", "g"), to); });
      textNode.nodeValue = normalizeUiSpacing(value);
    });
    root.querySelectorAll("[title],[aria-label],[placeholder]").forEach((element) => {
      ["title", "aria-label", "placeholder"].forEach((attr) => {
        const value = element.getAttribute(attr);
        if (!value || /^(https?:|[A-Za-z]:[\\\\/]|runs[\\\\/]|configs[\\\\/]|suites[\\\\/])/.test(value)) return;
        let localized = UI_TEXT_MAP[value] || value;
        [["主 Agent", "主智能体"], ["对比 Agent", "对比智能体"], ["Agent", "智能体"], ["Agents", "智能体"], ["Provider", "服务商"], ["Endpoint", "接口"], ["Model", "模型"], ["Temperature", "温度"], ["OpenAI-compatible", "OpenAI 兼容"], ["Base URL", "基础 URL（Base URL）"], ["Environment", "环境变量"]]
          .forEach(([from, to]) => { localized = localized.split(from).join(to); });
        localized = normalizeUiSpacing(localized);
        if (localized !== value) element.setAttribute(attr, localized);
      });
    });
  }
  const statusLabel = (status) => ({ queued: "排队中", running: "运行中", completed: "已完成", failed: "失败", partial: "部分完成", pass: "通过", error: "错误", unknown: "未确认" }[status] || status || "未确认");
  const runState = (job, selected) => {
    if (job && job.status === "stopped") return "Stopped";
    if (job && job.status === "stopping") return "Stopping";
    if (job && job.status === "error") return "Failed";
    if (job && job.status === "queued") return "Preparing";
    if (job && job.status === "running") return "Running";
    if (job && job.status === "completed") return "Completed";
    if (selected) return "Completed";
    return "Idle";
  };
  const runStateLabel = (value) => ({ Idle: "空闲", Preparing: "准备中", Running: "运行中", Completed: "已完成", Failed: "失败", Stopping: "停止中", Stopped: "已停止" }[value] || value);
  const FAILURE_LABELS = {
    stale_update: "旧值残留",
    omission: "遗漏或未召回",
    confusion: "相近实体混淆",
    erroneous_persistence: "错误持久化",
    erroneous_reuse: "错误复用",
    boundary_violation: "边界越权",
    action_failure: "实际动作失败",
    runtime_error: "运行错误",
    timeout: "超时",
    credential_error: "凭据错误",
    billing_error: "余额或计费错误",
    missing_input: "缺少输入或存储",
    not_observable: "证据不可观测",
    unsupported_action: "动作不受支持",
    invalid_behavior: "行为不符合规则",
    verified: "证据已记录",
  };
  const SCENARIO_STATUS_LABELS = {
    controlled_boundary_only: "仅包装层边界",
    requires_openkylin_controller: "需 openKylin 控制器",
    requires_dedicated_users: "需专用测试账户",
    requires_network_namespace: "需测试网络命名空间",
    sandbox_only: "仅沙箱目录",
  };
  const failureLabel = (type) => FAILURE_LABELS[type] || type || "未分类失败";
  const scenarioStatusLabel = (status) => SCENARIO_STATUS_LABELS[status] || status || "未确认";
  const capabilityLabel = (key) => (CAPABILITIES.find((item) => item[0] === key) || [key, key])[1];
  const displayScenarioName = (key) => ({
    agent_process_restart: "智能体进程重启",
    system_restart: "系统重启",
    user_switch: "用户切换",
    offline: "离线状态",
    permission_change: "文件权限变化"
  }[key] || key || "未确认");
  const activeAgent = (summary) => String((summary && summary.agent) || "");

  async function loadData() {
    state.loading = true;
    updateRefreshState();
    if (!state.savedAt) {
      try {
        const draft = JSON.parse(localStorage.getItem("kmb-workbench-draft") || "null");
        if (draft) { state.formPrimary = draft.primary || state.formPrimary; state.formComparison = draft.comparison || state.formComparison; state.formSuite = draft.suite || state.formSuite; state.params = Object.assign({}, state.params, draft.params || {}); }
      } catch (error) { /* ignore malformed local-only draft */ }
    }
    const failures = [];
    const results = await Promise.allSettled([api("/api/configs"), api("/api/agents"), api("/api/suites"), api("/api/runs?limit=120"), api("/api/system"), api("/api/profiles")]);
    ["configs", "agents", "suites", "runs", "system", "profiles"].forEach((key, index) => {
      const result = results[index];
      if (result.status === "fulfilled") state[key] = key === "system" ? result.value : (result.value[key] || result.value);
      else failures.push(result.reason.message);
    });
    const runnable = (state.agents || []).filter((agent) => agent && agent.installed && agent.runnable).map((agent) => agent.id);
    state.quickSelected = state.quickSelected.filter((id) => runnable.includes(id));
    if (!state.quickSelected.length) state.quickSelected = runnable.slice(0, 2);
    if (failures.length) showGlobalError(failures.join("；")); else showGlobalError("");
    updateEnvironmentBadge();
    if (state.selectedRunPath && state.view === "results") {
      try { state.selectedRun = await api("/api/runs?path=" + encodeURIComponent(state.selectedRunPath)); } catch (error) { showGlobalError(error.message); }
    }
    state.loading = false;
    state.lastRefreshAt = new Date();
    render();
    updateRefreshState();
  }

  function showGlobalError(message) {
    const target = $("#global-error");
    if (!target) return;
    target.hidden = !message;
    target.textContent = message || "";
  }

  function updateEnvironmentBadge() {
    const chip = $("#status-chip");
    const chipText = $("#status-chip-text");
    if (!chip || !state.system) return;
    const env = state.system.openkylin || {};
    const credentials = state.system.credentials || {};
    const secure = credentials.status === "secure";
    const ready = secure || credentials.status === "absent";
    const envLabel = env.detected ? (env.distribution || "openKylin") : "本地";
    const credLabel = secure ? "凭据已加载" : credentials.status === "absent" ? "无云凭据" : "凭据需检查";
    chip.className = "status-chip " + (secure ? "ok" : ready ? "limited" : "blocked") + (env.detected ? " openkylin" : "");
    if (chipText) chipText.textContent = envLabel;
    chip.title = envLabel + " · " + credLabel + (env.detected ? "" : " · 非 openKylin 环境，不能替代 VM 验证") + " · 页面不显示密钥";
  }

  function updateRefreshState() {
    const button = $("#refresh-button");
    if (!button) return;
    button.disabled = Boolean(state.loading);
    button.setAttribute("aria-busy", state.loading ? "true" : "false");
    button.title = state.loading ? "正在刷新数据" : "刷新数据";
  }

  const PAGE_META = {
    overview: { title: "总览", subtitle: "本地评测工作区" },
    new: { title: "新建评测", subtitle: "使用相同参数对比两个智能体" },
    tasks: { title: "评测任务", subtitle: "当前队列与运行状态" },
    history: { title: "运行历史", subtitle: "本地结果目录中的真实运行" },
    results: { title: "结果中心", subtitle: "结果、对比、案例与证据" },
    agents: { title: "智能体", subtitle: "可用配置与连接状态" },
    configs: { title: "API / 模型", subtitle: "供应商、接口与凭据状态" },
    settings: { title: "系统设置", subtitle: "环境与复现信息" },
  };
  function applyPageChrome(view) {
    const meta = PAGE_META[view] || { title: "工作台", subtitle: "" };
    const title = document.getElementById("page-title");
    const subtitle = document.getElementById("page-subtitle");
    if (title) title.textContent = meta.title;
    if (subtitle) subtitle.textContent = meta.subtitle;
  }

  function setView(view) {
    if (view === "results" && state.view !== "results") state.resultTab = "result";
    state.view = view;
    applyPageChrome(view);
    document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
    state.moreOpen = false;
    render();
  }

  function render() {
    const root = $("#view-root");
    if (!root) return;
    applyPageChrome(state.view);
    document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === state.view));
    const views = { overview: renderOverview, new: renderNew, tasks: renderTasks, history: renderHistory, results: renderResults, agents: renderAgents, configs: renderConfigs, settings: renderSettings };
    root.innerHTML = (views[state.view] || renderNew)();
    bindViewEvents();
    enhanceConfigView();
    renderInspectorRail();
    renderStatusBar();
    renderToolbar();
    updateEnvironmentBadge();
    localizeUi();
  }

  function currentRunSummary() {
    if (state.selectedRun) return normalizeAgents(state.selectedRun)[0] || null;
    const path = state.selectedRunPath;
    return path ? (state.runs.find((run) => run.path === path) || null) : null;
  }

  function renderInspectorRail() {
    const rail = $("#inspector-rail");
    const root = $("#inspector-root");
    const shell = $("#app-shell");
    if (!rail || !root || !shell) return;
    shell.classList.toggle("rail-collapsed", state.railCollapsed);
    const selected = currentRunSummary();
    const agents = state.selectedRun ? normalizeAgents(state.selectedRun) : [];
    const active = state.job && ["queued", "running", "stopping"].includes(state.job.status);
    const stateName = runState(state.job, selected);
    const activeLabel = active ? ((state.job.progress && state.job.progress.phase) || "智能体正在工作…") : selected ? (selected.agent || "已选择运行") : "尚未开始运行";
    const progress = active && state.job.progress ? Math.round((Number(state.job.progress.completed || 0) / Math.max(1, Number(state.job.progress.total || 2))) * 100) : null;
    const observed = (agents[0] && agents[0].observability) || {};
    const selectedMeta = selected && (selected._workbench || selected.workbench || {});
    const suite = state.job && state.job.suite ? state.job.suite : (selected && (selected.suite || selected.suite_path || selectedMeta.suite || selectedMeta.suite_path));
    const runId = state.job && state.job.id ? state.job.id : (state.selectedRunPath || "未选择运行");
    const eventCount = agents.reduce((sum, agent) => sum + Number(((agent._workbench || {}).metrics || {}).events || 0), 0);
    const boundary = displayDisclaimer(observed.disclaimer) || (state.selectedRun ? "当前结果没有提供额外观测边界声明。" : "运行后将在此显示真实观测边界。没有运行数据时不展示推测状态。");
    const pageContext = inspectorPageContext(state.view, { selected, agents, active, stateName, suite, runId, eventCount, boundary, progress });
    if (pageContext) {
      root.innerHTML = '<div class="rail-header"><div><h2>' + escapeHtml(pageContext.title) + '</h2></div><button class="icon-button" data-rail-toggle type="button" title="' + (state.railCollapsed ? "展开检查器" : "折叠检查器") + '" aria-label="' + (state.railCollapsed ? "展开检查器" : "折叠检查器") + '">' + (state.railCollapsed ? "‹" : "›") + '</button></div><div class="rail-content">' + pageContext.body + '</div>';
      const pageToggle = root.querySelector("[data-rail-toggle]");
      if (pageToggle) pageToggle.addEventListener("click", () => { state.railCollapsed = !state.railCollapsed; renderInspectorRail(); });
      return;
    }
    root.innerHTML = '<div class="rail-header"><div><h2>运行上下文</h2></div><button class="icon-button" data-rail-toggle type="button" title="' + (state.railCollapsed ? "展开检查器" : "折叠检查器") + '" aria-label="' + (state.railCollapsed ? "展开检查器" : "折叠检查器") + '">' + (state.railCollapsed ? "‹" : "›") + '</button></div>'
      + '<div class="rail-content">'
      + '<section class="rail-section"><div class="rail-section-title"><span>当前运行状态</span><span class="status-pill ' + (active ? "partial" : stateName === "Failed" ? "failed" : stateName === "Completed" ? "completed" : "") + '">' + escapeHtml(runStateLabel(stateName)) + '</span></div><div class="rail-task-name">' + escapeHtml(activeLabel) + '</div>' + (progress != null ? '<div class="rail-progress"><div class="progress-track"><div class="progress-value" style="width:' + progress + '%"></div></div><div class="rail-meta"><span>进度</span><strong>' + progress + '%</strong></div></div>' : '') + '<div class="rail-meta"><span>运行 ID</span><strong title="' + escapeHtml(runId) + '">' + escapeHtml(runId.length > 28 ? runId.slice(0, 28) + "…" : runId) + '</strong></div></section>'
      + '<section class="rail-section"><div class="rail-section-title"><span>当前任务</span></div><div class="rail-task-name">' + escapeHtml(active ? ((state.job.progress && state.job.progress.phase) || "智能体正在工作…") : selected ? "已载入结果工作区" : "尚未开始评测") + '</div><div class="rail-meta"><span>当前案例</span><strong>' + escapeHtml(active && state.job.progress ? fmt(state.job.progress.current_case, "准备中") : "未观测") + '</strong></div></section>'
      + '<section class="rail-section"><div class="rail-section-title"><span>参与 Agent</span><span class="rail-count">' + (agents.length || (active ? 2 : 0)) + '</span></div>' + (agents.length ? agents.map((agent, index) => '<div class="rail-agent"><span class="legend-dot ' + (index === 0 ? "blue" : "orange") + '"></span><div><strong>' + escapeHtml(agent.agent || "未命名 Agent") + '</strong><span>' + escapeHtml(displayMode((agent.observability || {}).mode)) + '</span></div></div>').join("") : '<div class="rail-empty">运行后显示真实 Agent 状态</div>') + '</section>'
      + '<section class="rail-section"><div class="rail-section-title"><span>运行参数</span></div><dl class="rail-facts"><div><dt>套件</dt><dd title="' + escapeHtml(suite || "") + '">' + escapeHtml(displaySuiteName(suite)) + '</dd></div><div><dt>Seed</dt><dd>' + escapeHtml(fmt((selected && selected.seed) || state.params.seed, "未记录")) + '</dd></div><div><dt>超时</dt><dd>' + escapeHtml(fmt((selected && selected.timeout) || state.params.timeout, "未记录")) + '</dd></div><div><dt>评分器</dt><dd>' + escapeHtml(fmt((selected && selected.scorer_version) || state.params.scorer_version, "未记录")) + '</dd></div><div><dt>证据事件</dt><dd>' + escapeHtml(eventCount ? eventCount : "未记录") + '</dd></div></dl></section>'
      + '<section class="rail-section"><div class="rail-log">' + (active ? '<div class="rail-log-line"><span class="log-dot live"></span><span>' + escapeHtml((state.job.progress && state.job.progress.phase) || "后端正在执行") + '</span></div>' : state.job && (state.job.error || state.job.status === "stopped") ? '<div class="rail-log-line error"><span class="log-dot"></span><span>' + escapeHtml(state.job.error || "运行已停止") + '</span></div>' : '<div class="rail-empty">暂无实时事件。日志来自实际运行进程和证据文件。</div>') + '</div></section>'
      + '<section class="rail-section rail-boundary"><div class="rail-section-title"><span>观测边界</span></div><p>' + escapeHtml(boundary) + '</p><div class="rail-sources"><span class="source-pill model">model</span><span class="source-pill wrapper">wrapper</span><span class="source-pill simulated">simulated</span></div></section>'
      + '</div>';
    const toggle = root.querySelector("[data-rail-toggle]");
    if (toggle) toggle.addEventListener("click", () => { state.railCollapsed = !state.railCollapsed; renderInspectorRail(); });
  }

  function inspectorPageContext(view, data) {
    const esc = escapeHtml;
    const { selected, agents, active, stateName, suite, runId, eventCount, boundary, progress } = data;
    const facts = (items) => '<dl class="rail-facts">' + items.map((item) => '<div><dt>' + esc(item[0]) + '</dt><dd title="' + esc(item[1]) + '">' + esc(item[1]) + '</dd></div>').join('') + '</dl>';
    const header = (_kicker, title) => '<section class="rail-section"><div class="rail-section-title"><span>' + esc(title) + '</span></div>';
    if (view === 'new') {
      const primary = configByPath(state.formPrimary || defaultConfigPaths()[0]);
      const comparison = configByPath(state.formComparison || defaultConfigPaths()[1]);
      return { title: '评测配置', body: header('CONFIGURATION', '评测配置') + '<div class="rail-task-name">双 Agent 对比工作区</div>' + facts([['主 Agent', primary ? primary.name : '未选择'], ['对比 Agent', comparison ? comparison.name : '未选择'], ['测试套件', suite ? String(suite).split(/[\\/]/).pop() : '未选择'], ['Seed', fmt(state.params.seed, '未记录')], ['重试', fmt(state.params.retries, '未记录')], ['超时', fmt(state.params.timeout, '未记录')], ['评分器', fmt(state.params.scorer_version, '未记录')]]) + '</section>' };
    }
    if (view === 'tasks') {
      return { title: '任务进度', body: header('RUN', '当前任务') + '<div class="rail-section-title"><span>状态</span><span class="status-pill ' + (active ? 'partial' : stateName === 'Completed' ? 'completed' : stateName === 'Failed' ? 'failed' : '') + '">' + esc(runStateLabel(stateName)) + '</span></div><div class="rail-task-name">' + esc(active ? ((state.job.progress && state.job.progress.phase) || '智能体正在工作…') : '没有正在执行的任务') + '</div>' + (progress != null ? '<div class="rail-progress"><div class="progress-track"><div class="progress-value" style="width:' + progress + '%"></div></div><div class="rail-meta"><span>进度</span><strong>' + progress + '%</strong></div></div>' : '') + facts([['当前案例', active && state.job.progress ? fmt(state.job.progress.current_case, '准备中') : '未观测'], ['任务 ID', state.job && state.job.id ? state.job.id : '未开始'], ['开始时间', state.job && state.job.created_at ? formatCheckedAt(state.job.created_at) : '未记录']]) + '</section>' + header('LIVE EVENTS', '事件') + '<div class="rail-log">' + (active ? '<div class="rail-log-line"><span class="log-dot live"></span><span>' + esc((state.job.progress && state.job.progress.phase) || '后端正在执行') + '</span></div>' : '<div class="rail-empty">暂无活动事件。进入任务详情查看已归档日志。</div>') + '</div></section>' };
    }
    if (view === 'results' && !['compare', 'cases', 'evidence', 'trace', 'logs'].includes(state.resultTab)) {
      const first = agents[0], second = agents[1];
      const delta = second ? Number(first?.overall || 0) - Number(second.overall || 0) : null;
      const resultFailures = collectFailures(agents);
      return { title: '结果摘要', body: header('RESULT', '结果摘要') + '<div class="rail-task-name">' + esc(first && second ? displayAgentName(first.agent || '主 Agent') + ' 对比 ' + displayAgentName(second.agent || '对比 Agent') : displayAgentName(first?.agent || '未选择运行')) + '</div>' + facts([['主 Agent', first ? pct(first.overall) + ' / 100' : '未观测'], ['对比 Agent', second ? pct(second.overall) + ' / 100' : '未观测'], ['分数差值', delta == null ? '未观测' : (delta >= 0 ? '+' : '') + pct(delta)], ['失败案例', String(failureCaseCount(resultFailures))], ['证据事件', eventCount ? String(eventCount) : '未记录']]) + '</section>' + header('BOUNDARY', '边界') + '<p>' + esc(displayDisclaimer(boundary) || '模型文本不能替代状态证据。') + '</p><div class="rail-sources"><span class="source-pill model">模型</span><span class="source-pill wrapper">包装层</span><span class="source-pill simulated">模拟</span></div></section>' };
    }
    if (view === 'compare' || (view === 'results' && ['compare', 'cases', 'evidence', 'trace', 'logs'].includes(state.resultTab))) {
      const first = agents[0], second = agents[1];
      return { title: state.resultTab === 'cases' ? '案例详情' : state.resultTab === 'evidence' ? '证据上下文' : state.resultTab === 'trace' ? '记忆轨迹' : state.resultTab === 'logs' ? '运行日志' : '对比上下文', body: header('COMPARE', '调查上下文') + '<div class="rail-task-name">' + esc(first && second ? displayAgentName(first.agent || '主 Agent') + ' 对比 ' + displayAgentName(second.agent || '对比 Agent') : '等待双智能体结果') + '</div>' + facts([['运行 ID', runId], ['套件', displaySuiteName(suite)], ['能力维度', '6'], ['当前案例', state.selectedCase || '未选择'], ['证据事件', eventCount ? String(eventCount) : '未记录']]) + '</section>' };
    }
    if (view === 'agents') {
      const config = configByPath(state.agentDetailPath);
      return { title: '智能体详情', body: header('AGENT REGISTRY', '智能体详情') + '<div class="rail-task-name">' + esc(config ? displayAgentName(config.name) : '选择一个智能体') + '</div>' + facts(config ? [['服务商', providerLabel(config)], ['模型', config.model || config.type || '未记录'], ['记忆模式', profileMode(config)], ['凭据', credentialLabel(config)]] : [['可用智能体', String(state.configs.length)], ['参与评测', '从列表选择']]) + '</section>' };
    }
    if (view === 'configs') {
      const config = configByPath(state.providerDetail);
      return { title: '服务商详情', body: header('PROVIDER', '服务商详情') + '<div class="rail-task-name">' + esc(config ? providerLabel(config) : '选择一个服务商') + '</div>' + facts(config ? [['接口', config.endpoint || '未记录'], ['模型', config.model || '待运行时解析'], ['API Key', '仅安全凭据引用'], ['状态', credentialLabel(config)]] : [['服务商数量', String(new Set(state.configs.map(providerLabel)).size)], ['凭据', '页面不显示密钥']]) + '</section>' };
    }
    if (view === 'overview') {
      const completed = state.runs.filter((run) => run.status === 'completed').length;
      const failed = state.runs.filter((run) => ['failed', 'error'].includes(run.status)).length;
      return { title: '工作区', body: header('WORKSPACE', '工作区摘要') + '<div class="rail-task-name">本地评测工作区</div>' + facts([['运行总数', String(state.runs.length)], ['已完成', String(completed)], ['失败 / 错误', String(failed)], ['双 Agent', String(state.runs.filter((run) => run.kind === 'comparison').length)], ['最近运行', state.runs[0] ? (state.runs[0].id || '未命名') : '暂无']]) + '</section>' };
    }
    if (view === 'history') {
      return { title: '运行历史', body: header('ARCHIVE', '运行存档') + '<div class="rail-task-name">本地结果目录中的真实运行</div>' + facts([['记录数', String(state.runs.length)], ['筛选', state.filters.history || '全部'], ['选中运行', selected ? (selected.id || selected.agent || '已加载') : '未选择']]) + '</section>' };
    }
    if (view === 'settings') {
      const env = (state.system || {}).openkylin || {};
      return { title: '系统环境', body: header('RUNTIME', '环境信息') + '<div class="rail-task-name">只读系统探针</div>' + facts([['平台', fmt((state.system || {}).platform, '未记录')], ['Python', fmt((state.system || {}).python, '未记录')], ['openKylin', env.detected ? '已检测' : '未检测'], ['存储', fmt((state.system || {}).results_directory, '未记录')]]) + '</section>' };
    }
    return null;
  }

  function renderStatusBar() {
    const bar = $("#status-bar");
    if (!bar) return;
    const credentials = (state.system || {}).credentials || {};
    const serviceText = credentials.status === "secure" ? "凭据安全" : credentials.status === "absent" ? "无云凭据" : "凭据需检查";
    const jobState = runState(state.job, currentRunSummary());
    bar.innerHTML = '<span class="status-item"><span class="status-dot"></span>本地</span>'
      + '<span class="status-item">' + escapeHtml(serviceText) + '</span>'
      + '<span class="status-item">状态 <strong>' + escapeHtml(runStateLabel(jobState)) + '</strong></span>'
      + '<span class="status-spacer"></span>'
      + '<span class="status-item">' + escapeHtml(state.job && state.job.id ? state.job.id.slice(0, 24) : "未开始") + '</span>';
  }

  function renderToolbar() {
    const root = $("#toolbar-actions");
    if (!root) return;
    const active = state.job && ["queued", "running", "stopping"].includes(state.job.status);
    const selected = currentRunSummary();
    const canStart = state.view === "new" && !active;
    root.innerHTML = '<button class="toolbar-button icon-only" data-toolbar="refresh" type="button" title="刷新"' + (state.loading ? " disabled" : "") + '><span class="toolbar-icon">↻</span></button>'
      + (active
        ? '<button class="toolbar-button danger" data-toolbar="stop" type="button" title="停止评测"><span>■</span><span>停止</span></button>'
        : '<button class="toolbar-button primary" data-toolbar="start" type="button" title="开始双 Agent 评测"' + (canStart ? "" : " disabled") + '><span>▶</span><span>开始评测</span></button>')
      + '<div class="toolbar-more-wrap"><button class="toolbar-button icon-only" data-toolbar="more" type="button" aria-expanded="' + (state.moreOpen ? "true" : "false") + '" title="更多">•••</button>'
      + (state.moreOpen
        ? '<div class="toolbar-menu">'
          + '<button type="button" data-toolbar="save">保存配置草稿</button>'
          + '<button type="button" data-toolbar="copy">复制配置</button>'
          + '<button type="button" data-toolbar="open-results">打开结果中心</button>'
          + '<button type="button" data-toolbar="open-history">打开运行历史</button>'
          + (selected ? '<button type="button" data-toolbar="copy-id">复制运行 ID</button>' : '')
          + '<button type="button" data-toolbar="reset-view">重置当前视图</button>'
          + '</div>'
        : '')
      + '</div>';
    root.querySelectorAll("[data-toolbar]").forEach((button) => button.addEventListener("click", () => toolbarAction(button.dataset.toolbar)));
  }

  async function toolbarAction(action) {
    if (action === "refresh") return loadData();
    if (action === "start") return startRun();
    if (action === "stop") return stopRun();
    if (action === "more") { state.moreOpen = !state.moreOpen; renderToolbar(); return; }
    if (action === "open-results") return setView("results");
    if (action === "open-history") return setView("history");
    if (action === "reset-view") { state.resultTab = "result"; state.selectedCase = null; state.moreOpen = false; render(); return; }
    if (action === "copy-id") { const run = currentRunSummary(); return copyText(run && (run.id || state.selectedRunPath)); }
    if (action === "save") {
      const payload = { primary: state.formPrimary || "", comparison: state.formComparison || "", suite: state.formSuite || "", params: state.params };
      try { localStorage.setItem("kmb-workbench-draft", JSON.stringify(payload)); state.savedAt = new Date(); renderToolbar(); } catch (error) { showGlobalError("保存本地工作区草稿失败：" + error.message); }
      return;
    }
    if (action === "copy") {
      const config = { primary_agent: state.formPrimary || "", comparison_agent: state.formComparison || "", suite: state.formSuite || "", seed: state.params.seed, retries: state.params.retries, timeout: state.params.timeout, scorer_version: state.params.scorer_version };
      return copyText(JSON.stringify(config, null, 2));
    }
  }

  async function copyText(value) {
    if (!value) return;
    try { await navigator.clipboard.writeText(String(value)); } catch (error) { showGlobalError("复制失败：" + error.message); }
  }

  function configByPath(path) { return state.configs.find((config) => config.path === path); }
  const providerOrder = ["Grok", "DeepSeek"];
  const profileMode = (config) => displayProfileMode((config && config.profile_mode) || (config && config.type) || "未分类");
  const providerLabel = (config) => (config && config.provider) || "其他";
  const TRACK_LABELS = { A: "A 轨", B: "B 轨", control: "对照基线" };
  function trackForConfig(config) {
    const type = String((config && config.type) || "");
    if (type === "memory_tool") return "B";
    if (["deterministic", "replay", "memory_disabled", "http"].includes(type)) return "control";
    return "A";
  }
  function needsLlm(config) { return Boolean(config && ["memory_tool", "http"].includes(String(config.type))); }
  const credentialLabel = (config) => !config ? "未检测到凭据" : config.credential === "configured" ? "凭据已加载" : config.credential === "not_required" ? "无需凭据" : "未检测到凭据";
  function defaultConfigPaths(track) {
    const wanted = track || state.formTrack || "control";
    const usable = state.configs.filter((config) => config.status !== "error" && trackForConfig(config) === wanted);
    const byPattern = (pattern) => usable.find((config) => pattern.test(config.name) || pattern.test(config.path || ""));
    let primary, comparison;
    if (wanted === "control") {
      primary = byPattern(/agent-reference/) || byPattern(/reference/i) || usable[0];
      comparison = byPattern(/agent-flawed/) || byPattern(/flawed/i) || usable.find((config) => primary && config.path !== primary.path);
    } else if (wanted === "B") {
      primary = byPattern(/b-memory-kv-real/) || usable[0];
      comparison = byPattern(/b-memory-similar-real/) || usable.find((config) => primary && config.path !== primary.path);
    } else {
      primary = byPattern(/kylinbot/) || usable[0];
      comparison = byPattern(/openclaw|hermes/) || usable.find((config) => primary && config.path !== primary.path);
    }
    return [primary ? primary.path : "", comparison ? comparison.path : ""];
  }
  function suiteOptions(selected) {
    return state.suites.map((suite) => '<option value="' + escapeHtml(suite.path) + '"' + (suite.path === selected ? " selected" : "") + ' title="' + escapeHtml(suite.name || suite.path) + '">' + escapeHtml(displaySuiteName(suite)) + " · " + suite.cases + " 个案例" + (suite.status !== "valid" ? " · 无效" : "") + "</option>").join("");
  }
  function configOptions(selected, track) {
    const usable = state.configs.filter((config) => trackForConfig(config) === (track || state.formTrack || "control"));
    return usable.map((config) => '<option value="' + escapeHtml(config.path) + '"' + (config.path === selected ? " selected" : "") + '>' + escapeHtml(config.name) + '</option>').join("");
  }
  function apiSelectHtml(pane, config, selected) {
    if (!needsLlm(config)) return '<div class="field"><label>API 模型</label><span class="muted-line">不适用（该智能体无 LLM 后端）</span></div>';
    const profiles = state.profiles || [];
    const current = selected || (config && config.api_profile) || "";
    if (!profiles.length) return '<div class="field"><label>API 模型</label><span class="muted-line">尚无 API 档案——请先在 API / 模型页新增</span></div>';
    const options = profiles.map((profile) => '<option value="' + escapeHtml(profile.id) + '"' + (profile.id === current ? " selected" : "") + '>' + escapeHtml(profile.name + " · " + profile.model) + '</option>').join("");
    return '<div class="field"><label for="api-' + pane + '">API 模型（本次评测）</label><select id="api-' + pane + '" data-api-pane="' + pane + '">' + options + '</select><span class="field-help">默认预选该智能体的默认档案；本次评测可临时改选，不回写智能体配置。</span></div>';
  }
  function agentMetaHtml(config) {
    if (!config) return '<div class="agent-meta"><span>尚未选择配置</span></div>';
    const credential = config.credential === "configured" || config.credential === "not_required";
    return '<div class="agent-meta"><span>' + escapeHtml(providerLabel(config)) + ' · ' + escapeHtml(config.model || "本地适配器") + ' · ' + escapeHtml(profileMode(config)) + '</span><span class="' + (credential ? "credential-safe" : "credential-missing") + '">' + escapeHtml(credentialLabel(config)) + '</span></div>';
  }

  function suiteByPath(path) { return state.suites.find((suite) => suite.path === path); }
  function suiteInsightHtml(path) {
    const suite = suiteByPath(path);
    if (!suite) return '<div class="suite-insight muted">套件信息未观测</div>';
    const capabilities = (suite.capabilities || []).map(capabilityLabel).join(" · ") || "未记录能力覆盖";
    const hash = suite.sha256 ? String(suite.sha256) : "未记录";
    return '<div class="suite-insight"><span><strong>' + escapeHtml(suite.cases) + '</strong> 个案例</span><span>覆盖 <strong>' + escapeHtml(capabilities) + '</strong></span><span class="suite-hash" title="完整哈希来自本地套件元数据">SHA-256 <strong>' + escapeHtml(hash.length > 16 ? hash.slice(0, 16) + "…" : hash) + '</strong></span><span title="原始套件标识">标识 <code>' + escapeHtml(suite.name || suite.path) + '</code></span></div>';
  }
  function credentialMissing(result) { return Boolean(result && /required environment variable .* is not set/i.test(String(result.error || ""))); }
  function healthStateMarkup(configPath, fallback) {
    const result = state.health[configPath];
    if (!result) return '<span class="health-state">' + escapeHtml(fallback || "尚未检查连接") + '</span>';
    const healthy = result.status === "healthy";
    const missing = credentialMissing(result);
    const detail = healthy ? "连接成功 · " + fmt(result.latency_ms, "-") + " ms" : missing ? "未配置安全凭据" : "连接失败 · " + (result.error || "未知错误");
    const checked = result.checked_at ? " · " + formatCheckedAt(result.checked_at) : "";
    const title = missing ? (result.error || "当前服务未加载安全凭据") : (result.checked_at || "");
    return '<span class="health-state ' + (healthy ? "ok" : missing ? "warn" : "bad") + '" title="' + escapeHtml(title) + '">' + escapeHtml(detail + checked) + '</span>';
  }
  function formatCheckedAt(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "已检查" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  function fairnessSummaryHtml() {
    return '<div class="fairness-strip" role="status"><span class="fairness-lock"><span aria-hidden="true">▣</span> 比较条件锁定</span><span>Seed <strong>' + escapeHtml(fmt(state.params.seed, "未记录")) + '</strong></span><span>重试 <strong>' + escapeHtml(fmt(state.params.retries, "未记录")) + '</strong></span><span>超时 <strong>' + escapeHtml(fmt(state.params.timeout, "未记录")) + ' 秒</strong></span><span>评分器 <strong>' + escapeHtml(fmt(state.params.scorer_version, "未记录")) + '</strong></span></div>';
  }

  function renderOverview() {
    const latest = state.runs[0];
    const selected = currentRunSummary();
    const headline = latest ? (latest.title || displayRunName(latest.id || latest.run_id || "最近运行")) : "尚无运行记录";
    const agents = latest && latest.agents && latest.agents.length ? latest.agents.map(displayAgentName).join(" · ") : displayAgentName((latest && latest.agent) || "本地运行");
    const latestStatus = latest ? '<span class="status-pill ' + escapeHtml(latest.status || "unknown") + '">' + escapeHtml(statusLabel(latest.status)) + '</span>' : '';
    const recentAgents = recentAgentUsage();
    return '<div class="workspace-intro compact-intro"><div></div><div class="section-actions"><button class="button" data-view="new" type="button">新建评测</button>' + (latest ? '<button class="button" data-open-run="' + escapeHtml(latest.path) + '" type="button">打开最近运行</button>' : '') + '</div></div>'
      + '<section class="overview-current"><div><h3>' + escapeHtml(headline) + '</h3><p>' + escapeHtml(agents) + '</p></div><div class="overview-current-meta">' + latestStatus + '<span>' + escapeHtml(latest ? fmt(latest.started_at, "时间未记录") : "等待第一次运行") + '</span></div></section>'
      + quickCompareMarkup()
      + (recentAgents.length ? '<section class="overview-section"><div class="section-title-row"><h3>最近使用 Agent</h3></div><div class="overview-run-list">' + recentAgents.map((item) => '<div class="overview-run-row static"><span class="run-status-dot completed"></span><span class="overview-run-main"><strong>' + escapeHtml(item.name) + '</strong><small>' + escapeHtml(item.meta) + '</small></span><span class="overview-run-score">' + escapeHtml(item.score) + '</span><span class="overview-run-time">' + escapeHtml(item.runs + " 次") + '</span></div>').join("") + '</div></section>' : '')
      + '<div class="overview-columns">'
      + '<section class="overview-section"><div class="section-title-row"><h3>评测趋势</h3></div>' + trendMarkup() + '</section>'
      + '<section class="overview-section"><div class="section-title-row"><h3>最近运行</h3><button class="link-button" data-view="history" type="button">全部 →</button></div>'
      + (state.runs.length ? '<div class="overview-run-list">' + state.runs.slice(0, 8).map((run) => '<button class="overview-run-row" data-open-run="' + escapeHtml(run.path) + '" type="button"><span class="run-status-dot ' + escapeHtml(run.status || "unknown") + '"></span><span class="overview-run-main"><strong title="' + escapeHtml(run.id || run.run_id || "") + '">' + escapeHtml(runDisplayName(run)) + '</strong><small>' + escapeHtml((run.agents || []).map(displayAgentName).join(" · ") || displayAgentName(run.agent) || "本地运行") + '</small></span><span class="overview-run-score">' + escapeHtml(Array.isArray(run.overall) ? run.overall.map(pct).join(" / ") : (run.overall != null ? pct(run.overall) : "—")) + '</span><span class="overview-run-time">' + escapeHtml(fmt(run.started_at, "未记录")) + '</span></button>').join('') + '</div>' : '<div class="empty-inline"><span>暂无本地运行记录</span></div>')
      + '</section></div>'
      + (selected ? '<div class="overview-selection"><span>已载入</span><strong>' + escapeHtml(selected.agent || selected.id || "运行结果") + '</strong><button class="link-button" data-view="results" type="button">继续分析 →</button></div>' : '');
  }

  function recentAgentUsage() {
    const grouped = {};
    state.runs.forEach((run) => {
      const names = (run.agents && run.agents.length) ? run.agents : (run.agent ? [run.agent] : []);
      names.forEach((name) => {
        const key = displayAgentName(name);
        if (!grouped[key]) grouped[key] = { name: key, runs: 0, scores: [], invalid: 0 };
        grouped[key].runs += 1;
        const score = Array.isArray(run.overall) ? run.overall[0] : run.overall;
        if (score != null && Number.isFinite(Number(score))) grouped[key].scores.push(Number(score)); else grouped[key].invalid += 1;
      });
    });
    return Object.values(grouped).map((item) => {
      const avg = item.scores.length ? item.scores.reduce((a, b) => a + b, 0) / item.scores.length : null;
      const meta = item.runs + " 次运行" + (item.invalid ? "（" + (item.runs - item.invalid) + " 次有效）" : "");
      return { name: item.name, meta, score: avg == null ? "—" : pct(avg), runs: item.runs };
    }).sort((a, b) => b.runs - a.runs).slice(0, 4);
  }

  function overviewAgentRankingMarkup() {
    const grouped = {};
    state.runs.filter((run) => run.agent && run.overall != null && Number.isFinite(Number(run.overall))).forEach((run) => { const key = run.agent; if (!grouped[key]) grouped[key] = []; grouped[key].push(Number(run.overall)); });
    const ranking = Object.entries(grouped).map(([agent, values]) => ({ agent, score: values.reduce((a, b) => a + b, 0) / values.length, runs: values.length })).sort((a, b) => b.score - a.score).slice(0, 5);
    if (!ranking.length) return '<div class="empty-inline">暂无带有 Agent 总分的历史记录。</div>';
    return '<div class="overview-ranking">' + ranking.map((row, index) => '<div class="overview-ranking-row"><span class="ranking-position">' + (index + 1) + '</span><div><strong>' + escapeHtml(row.agent) + '</strong><small>' + row.runs + ' 次可用运行</small></div><span class="ranking-score">' + pct(row.score) + '</span></div>').join('') + '</div>';
  }
  function overviewFailureMarkup() {
    const items = [];
    state.runs.filter((run) => run.failure_counts && Object.keys(run.failure_counts).length).slice(0, 8).forEach((run) => Object.entries(run.failure_counts).forEach(([type, count]) => items.push({ run, type, count })));
    if (!items.length) return '<div class="empty-inline">暂无可从运行摘要确认的失败类型。</div>';
    return '<div class="overview-failure-list">' + items.slice(0, 8).map((item) => '<div class="overview-failure-row"><span class="failure-preview-id">' + escapeHtml(item.run.id || item.run.agent || '运行') + '</span><span>' + escapeHtml(item.run.agent || 'Agent') + '</span><span class="status-pill failed">' + escapeHtml(failureLabel(item.type)) + '</span><strong>' + escapeHtml(String(item.count)) + ' 次</strong></div>').join('') + '</div>';
  }

  function quickCompareMarkup() {
    const agents = Array.isArray(state.agents) ? state.agents : [];
    const selected = state.quickSelected || [];
    const active = state.job && ["queued", "running", "stopping"].includes(state.job.status) && state.job.kind === "quick_compare";
    const ready = selected.length === 2 && !active;
    const jobError = state.job && state.job.kind === "quick_compare" && state.job.status === "error" ? { kind: "error", message: state.job.error || "快速对比失败，请查看任务日志。" } : null;
    const currentNotice = state.quickNotice || jobError;
    const notice = currentNotice ? '<div class="quick-compare-notice ' + (currentNotice.kind === "error" ? "error" : "success") + '" role="status">' + escapeHtml(currentNotice.message) + '</div>' : '';
    const runnableCount = agents.filter((agent) => Boolean(agent.installed && agent.runnable)).length;
    const rows = agents.length ? agents.map((agent) => {
      const runnable = Boolean(agent.installed && agent.runnable);
      const checked = selected.includes(agent.id);
      const status = !agent.installed ? "未安装" : runnable ? "可自动运行" : "需手动观测";
      const fixHint = !runnable && agent.fix_hint ? (agent.reason ? "；" + agent.fix_hint : agent.fix_hint) : "";
      const detail = runnable ? (agent.evidence_mode === "agent_memory_observed" ? "可读取结构化记忆证据" : "已发现运行入口") : (agent.reason || "当前适配器不能自动驱动") + fixHint;
      return '<label class="quick-agent-row ' + (!runnable ? "unavailable" : "") + '"><input type="checkbox" data-quick-agent value="' + escapeHtml(agent.id) + '"' + (checked ? " checked" : "") + (!runnable || active ? " disabled" : "") + '><span class="quick-agent-copy"><strong>' + escapeHtml(displayAgentName(agent.id || agent.display_name)) + '</strong><small>' + escapeHtml(detail) + '</small></span><span class="status-pill ' + (runnable ? "completed" : "partial") + '">' + escapeHtml(status) + '</span></label>';
    }).join("") : '<div class="empty-inline">尚未发现已安装的支持 Agent。请在 openKylin 环境刷新。</div>';
    return '<section class="workspace-surface quick-compare-panel"><div class="surface-toolbar"><div><div class="eyebrow">QUICK COMPARE</div><h3>快速对比</h3><p>选择两个系统中已有的 Agent，使用固定六维套件直接生成可追溯结果。</p></div><span class="quick-compare-count">已选 ' + selected.length + ' / 2</span></div><div class="quick-compare-body"><div class="quick-agent-list">' + rows + '</div><div class="quick-compare-actions"><span class="field-help">默认参数：Seed 42 · 重试 1 次 · 单案例 180 秒</span><button class="button" data-quick-auto type="button"' + (runnableCount >= 2 && !active ? "" : " disabled") + ' title="自动选择两个可运行 Agent 并立即开始">一键对比可用 Agent</button><button class="button primary" data-quick-start type="button"' + (ready ? "" : " disabled") + '>' + (active ? "对比运行中…" : "开始快速对比") + '</button></div>' + notice + (active ? '<div class="quick-job-progress" role="status"><span>' + escapeHtml((state.job.progress && state.job.progress.phase) || "正在准备") + '</span><div class="progress-track"><div class="progress-value" style="width:' + Math.round((Number(state.job.progress?.completed || 0) / Math.max(1, Number(state.job.progress?.total || 2))) * 100) + '%"></div></div></div>' : '') + '</div></section>';
  }

  function renderTasks() {
    const active = state.job && ["queued", "running", "stopping"].includes(state.job.status);
    const jobs = state.runs.filter((run) => run.kind === "comparison").slice(0, 8);
    return '<div class="workspace-intro compact-intro"><div><p>当前运行与最近任务</p></div><div class="section-actions"><button class="button primary" data-view="new" type="button">＋ 新建任务</button></div></div>'
      + '<section class="workspace-surface task-console"><div class="console-header"><div><h3>' + escapeHtml(active ? ((state.job.progress && state.job.progress.phase) || state.job.id) : "没有正在执行的任务") + '</h3></div><span class="status-pill ' + (active ? "partial" : state.job && state.job.status === "stopped" ? "failed" : "") + '">' + escapeHtml(runStateLabel(runState(state.job, null))) + '</span></div>'
      + (active ? '<div class="task-progress"><div class="progress-track"><div class="progress-value" style="width:' + Math.round((Number(state.job.progress?.completed || 0) / Math.max(1, Number(state.job.progress?.total || 2))) * 100) + '%"></div></div><div class="job-meta"><span>当前智能体 ' + escapeHtml(fmt(state.job.progress?.current_agent, "准备中")) + '</span><span>' + escapeHtml(state.job.id) + '</span></div></div><div class="task-actions"><button class="button danger" data-toolbar="stop" type="button">■ 停止评测</button><button class="button" data-view="results" type="button">打开结果中心</button></div>' : '<div class="empty-inline"><span>空闲 · 后端没有活动进程</span><button class="button" data-view="new" type="button">开始评测</button></div>') + '</section>'
      + '<div class="workspace-section-head"><div><h3>最近任务</h3></div><button class="link-button" data-view="history" type="button">运行历史 →</button></div>'
      + (jobs.length ? '<div class="task-list">' + jobs.map((run) => '<button class="task-list-row" data-open-run="' + escapeHtml(run.path) + '" type="button"><span class="task-list-icon">' + (run.status === "completed" ? "✓" : "•") + '</span><span class="task-list-copy"><strong>' + escapeHtml(run.id || run.path) + '</strong><small>' + escapeHtml((run.agents || []).map(displayAgentName).join("  对比  ")) + '</small></span><span class="status-pill ' + escapeHtml(run.status || "unknown") + '">' + escapeHtml(statusLabel(run.status)) + '</span><span class="task-arrow">→</span></button>').join("") + '</div>' : '<section class="workspace-surface empty-inline"><span>还没有可显示的任务</span></section>');
  }

  function renderAgents() {
    const usable = state.configs.filter((config) => config.status !== "error");
    const detail = configByPath(state.agentDetailPath);
    return '<div class="workspace-intro"><div><p>密钥由本地安全配置加载，页面只显示状态。</p></div><div class="section-actions"><button class="button" data-view="configs" type="button">管理 API 配置</button><button class="button primary" data-view="new" type="button">选择并开始</button></div></div>'
      + '<div class="agent-registry">' + (usable.length ? usable.map((config) => { const used = state.runs.filter((run) => (run.agents || []).some((agent) => agent === config.name || agent === config.agent || String(config.name).toLowerCase().includes(String(agent).toLowerCase()))); const perf = used.find((run) => run.overall != null && Number.isFinite(Number(run.overall))); return '<article class="agent-registry-row"><span class="legend-dot ' + (/deepseek/i.test(config.name) ? "orange" : "blue") + '"></span><div class="agent-registry-main"><strong>' + escapeHtml(config.name) + '</strong><span>' + escapeHtml(providerLabel(config)) + ' · ' + escapeHtml(config.model || config.type || "本地适配器") + '</span></div><span class="mode-pill">' + escapeHtml(profileMode(config)) + '</span><span class="agent-usage">' + used.length + ' 次评测</span><span class="agent-performance">' + (perf ? pct(perf.overall) : '未观测') + '</span><span class="' + (config.credential === "configured" || config.credential === "not_required" ? "credential-safe" : "credential-missing") + '">' + escapeHtml(credentialLabel(config)) + '</span><button class="button small" data-agent-detail="' + escapeHtml(config.path) + '" type="button">查看详情</button><button class="button small" data-select-agent="' + escapeHtml(config.path) + '" type="button">用于评测</button></article>'; }).join("") : '<section class="workspace-surface empty-state"><strong>没有可用智能体配置</strong><p>先在 API / 模型配置中添加配置档案。</p></section>') + '</div>'
      + (detail ? '<section class="workspace-surface agent-detail-panel"><div class="surface-toolbar"><div><h3>' + escapeHtml(detail.name) + '</h3></div><button class="button small" data-select-agent="' + escapeHtml(detail.path) + '" type="button">用于评测</button></div><div class="agent-detail-grid"><div><span>服务商</span><strong>' + escapeHtml(providerLabel(detail)) + '</strong></div><div><span>模型</span><strong>' + escapeHtml(detail.model || detail.type || '未记录') + '</strong></div><div><span>记忆模式</span><strong>' + escapeHtml(profileMode(detail)) + '</strong></div><div><span>凭据状态</span><strong>' + escapeHtml(credentialLabel(detail)) + '</strong></div><div><span>参与评测</span><strong>' + state.runs.filter((run) => (run.agents || []).includes(detail.name)).length + ' 次</strong></div><div><span>最近表现</span><strong>来自本地运行结果</strong></div></div></section>' : '');
  }

  function renderNew() {
    const defaults = defaultConfigPaths(state.formTrack);
    const primary = state.formPrimary || defaults[0] || "";
    const comparison = state.formComparison || defaults[1] || "";
    const suite = state.formSuite || (state.suites.find((item) => /innovation/i.test(item.path) && item.status === "valid") || state.suites.find((item) => item.status === "valid") || {}).path || "";
    const primaryConfig = configByPath(primary);
    const comparisonConfig = configByPath(comparison);
    if (!state.baselineParams) state.baselineParams = Object.assign({}, state.params);
    const changed = JSON.stringify(state.params) !== JSON.stringify(state.baselineParams);
    const job = state.job;
    const progress = job && job.progress ? Math.round((Number(job.progress.completed || 0) / Math.max(1, Number(job.progress.total || 2))) * 100) : 0;
    const trackOptions = [["A", "A 轨 · 生态智能体"], ["B", "B 轨 · 记忆层智能体"], ["control", "对照基线 · 离线/回放"]];
    const trackSelector = '<section class="workspace-surface track-workspace"><div class="surface-toolbar"><div><h3>评测轨道</h3></div><span class="track-note">轨道只做归类与过滤，不改变证据语义：A 轨 = 系统级行为，B 轨 = 记忆层行为，对照 = 模拟/回放。</span></div><div class="track-selector">' + trackOptions.map((item) => '<button class="track-option' + (state.formTrack === item[0] ? " active" : "") + '" data-track="' + item[0] + '" type="button">' + item[1] + '</button>').join("") + '</div></section>';
    return '<div class="workspace-intro compact-intro"><div><p>使用相同参数运行两个 Agent。</p></div><div class="section-actions"><button class="button" data-action="reload" type="button">刷新配置</button><button class="button" data-toolbar="copy" type="button">复制配置</button></div></div>'
      + trackSelector
      + '<section class="workspace-surface compare-workspace"><div class="surface-toolbar"><div><h3>Agent 对比</h3></div><span class="compare-lock">参数锁定</span></div><div class="agent-compare-grid">'
      + '<div class="agent-pane blue"><div class="agent-pane-head"><div><h3>主智能体</h3></div></div><div class="field"><label for="primary-agent">配置档案</label><select id="primary-agent">' + configOptions(primary, state.formTrack) + '</select></div>' + agentMetaHtml(primaryConfig) + apiSelectHtml("primary", primaryConfig, state.formApiPrimary) + '<div class="agent-pane-footer"><span id="health-primary">' + healthStateMarkup(primary, "尚未检查连接") + '</span><button class="button small" data-health="primary" type="button">连接检查</button></div></div>'
      + '<div class="compare-divider" aria-hidden="true">对比</div>'
      + '<div class="agent-pane orange"><div class="agent-pane-head"><div><h3>对比智能体</h3></div></div><div class="field"><label for="comparison-agent">配置档案</label><select id="comparison-agent">' + configOptions(comparison, state.formTrack) + '</select></div>' + agentMetaHtml(comparisonConfig) + apiSelectHtml("comparison", comparisonConfig, state.formApiComparison) + '<div class="agent-pane-footer"><span id="health-comparison">' + healthStateMarkup(comparison, "尚未检查连接") + '</span><button class="button small" data-health="comparison" type="button">连接检查</button></div></div>'
      + '</div></section>'
      + '<section class="workspace-surface run-config"><div class="surface-toolbar"><div><h3>评测参数</h3></div>' + (changed ? '<span class="change-badge">参数已变化</span>' : '<span class="lock-badge">▣ 已锁定</span>') + '</div><div class="run-config-grid"><div class="field suite-field"><label for="suite">测试套件</label><select id="suite">' + suiteOptions(suite) + '</select>' + suiteInsightHtml(suite) + '</div><div class="field"><label for="seed">Seed</label><input id="seed" type="number" value="' + escapeHtml(state.params.seed) + '"></div><div class="field"><label for="retries">重试次数</label><input id="retries" min="0" max="5" type="number" value="' + escapeHtml(state.params.retries) + '"></div><div class="field"><label for="timeout">单案例超时（秒）</label><input id="timeout" min="1" max="900" type="number" value="' + escapeHtml(state.params.timeout) + '"></div><div class="field"><label for="scorer-version">评分器版本</label><input id="scorer-version" type="text" value="' + escapeHtml(state.params.scorer_version) + '"></div></div>' + (changed ? '<div class="change-warning"><strong>比较参数已变化。</strong> 本次运行将使用新的条件，不能与旧运行直接当作同一实验。</div>' : '') + '</section>'
      + '<section class="workspace-surface validation-workspace"><div class="surface-toolbar"><div><h3>运行前校验</h3></div><button id="start-run" class="button primary" type="button"' + ((!primary || !comparison || !suite || primary === comparison) ? " disabled" : "") + '>▶ 开始评测</button></div><div class="validation-inline"><ul class="validation-list">'
      + validationItem(Boolean(primary), primary ? "主 Agent 配置已选择" : "请选择主 Agent")
      + validationItem(Boolean(comparison), comparison ? "对比 Agent 配置已选择" : "请选择对比 Agent")
      + validationItem(Boolean(primary && comparison && primary !== comparison), primary === comparison ? "两个 Agent 必须使用不同配置" : "两个 Agent 配置不同")
      + validationItem(Boolean(state.suites.find((item) => item.path === suite && item.status === "valid")), "套件通过结构校验")
      + validationItem(Boolean(state.formTrack), "评测轨道已选择（" + (TRACK_LABELS[state.formTrack] || state.formTrack) + "）")
      + validationItem(primaryConfig && needsLlm(primaryConfig) ? Boolean(state.formApiPrimary || (primaryConfig.api_profile)) : true, "主智能体 API 模型已确定")
      + validationItem(comparisonConfig && needsLlm(comparisonConfig) ? Boolean(state.formApiComparison || (comparisonConfig.api_profile)) : true, "对比智能体 API 模型已确定")
      + validationItem(!changed, changed ? "比较参数已变化，结果将被标记为新条件" : "比较参数保持一致")
      + '</ul>' + fairnessSummaryHtml() + (job ? '<div class="job-status" role="status" aria-live="polite"><div class="job-meta"><strong>' + escapeHtml(job.status === "error" ? "运行失败" : runStateLabel(runState(job, null))) + '</strong><span>' + progress + '%</span></div><div class="progress-track"><div class="progress-value" style="width:' + progress + '%"></div></div><div class="job-meta"><span>运行 ID ' + escapeHtml(job.id) + '</span><span>结果目录 ' + escapeHtml(job.output || job.result_path || "待生成") + '</span></div>' + (job.error ? '<div class="job-error">' + escapeHtml(job.error) + '</div>' : '') + (job.result_path ? '<div style="margin-top:10px"><button class="link-button" data-open-run="' + escapeHtml(job.result_path) + '" type="button">打开这次结果</button></div>' : '') + '</div>' : '') + '</div></section>';
  }
  function validationItem(pass, text) { return '<li class="validation-item ' + (pass ? "pass" : "fail") + '"><span class="validation-mark">' + (pass ? "✓" : "!") + '</span><span>' + escapeHtml(text) + '</span></li>'; }

  function normalizeAgents(detail) {
    if (!detail) return [];
    if (detail.kind === "comparison") return detail.agents || [];
    return detail.result ? [detail.result] : [];
  }
  function renderResults() {
    if (!state.selectedRun) {
      const first = state.runs.find((run) => run.kind === "comparison") || state.runs[0];
      if (!first) return emptyState("还没有可查看的运行", "完成一次本地评测后，结果、证据和报告会出现在这里。", "new");
      state.selectedRunPath = first.path;
      loadSelectedRun(first.path);
      return '<div class="empty-state"><div class="empty-mark">…</div><strong>正在读取真实结果</strong><p>结果中心正在从本地结果目录载入 JSON 和证据索引。</p></div>';
    }
    if (state.resultTab === "result") return renderResultDashboard();
    return renderInvestigationWorkspace(state.resultTab);
  }
  function resultTabs(active) { return '<div class="result-tabs" role="tablist"><button class="result-tab ' + (active === "result" ? "active" : "") + '" data-result-tab="result" type="button">概览</button><button class="result-tab ' + (active === "compare" ? "active" : "") + '" data-result-tab="compare" type="button">对比</button><button class="result-tab ' + (active === "cases" ? "active" : "") + '" data-result-tab="cases" type="button">案例</button><button class="result-tab ' + (active === "evidence" ? "active" : "") + '" data-result-tab="evidence" type="button">证据</button><button class="result-tab ' + (active === "trace" ? "active" : "") + '" data-result-tab="trace" type="button">记忆轨迹</button><button class="result-tab ' + (active === "logs" ? "active" : "") + '" data-result-tab="logs" type="button">日志</button></div>'; }
  function resultDetails() {
    const agents = normalizeAgents(state.selectedRun);
    const primary = agents[0] || {};
    const comparison = agents[1] || null;
    const failures = collectFailures(agents);
    return { agents, primary, comparison, failures, path: state.selectedRun && (state.selectedRun.path || state.selectedRunPath) || state.selectedRunPath || "" };
  }
  function successRate(agent) {
    const results = Array.isArray(agent && agent.results) ? agent.results : [];
    if (!results.length) return null;
    return results.filter((result) => result.status === "pass").length / results.length * 100;
  }
  function failureCaseCount(rows) { return new Set((rows || []).map((row) => row.result && row.result.case_id).filter(Boolean)).size; }
  function averageLatency(agent) {
    const latency = agent && agent.metrics && agent.metrics.latency_ms;
    if (!latency) return null;
    return latency.mean != null ? Number(latency.mean) : latency.average != null ? Number(latency.average) : null;
  }
  function scoreDelta(primary, comparison) { return comparison && scoreValid(primary) && scoreValid(comparison) ? Number(primary.overall || 0) - Number(comparison.overall || 0) : null; }
  function winnerText(primary, comparison) {
    if (!comparison) return "单 Agent";
    if (!scoreValid(primary) || !scoreValid(comparison)) return "不可比较";
    const delta = scoreDelta(primary, comparison);
    if (delta === 0) return "平局";
    return delta > 0 ? displayAgentName(primary.agent || "主 Agent") : displayAgentName(comparison.agent || "对比 Agent");
  }
  function resultDashboardHeader(primary, comparison, path) {
    const record = state.runs.find((run) => run.path === path) || {};
    return '<div class="workspace-intro compact-intro result-dashboard-intro"><div><div class="run-summary"><span>运行 <strong>' + escapeHtml(record.id || state.selectedRunPath || path) + '</strong></span><span>状态 <strong>' + escapeHtml(statusLabel(record.status || "completed")) + '</strong></span><span>案例 <strong>' + fmt(primary.cases, "未记录") + '</strong></span><span>随机种子 <strong>' + fmt(primary.seed, "未记录") + '</strong></span></div></div><div class="section-actions"><button class="button" data-view="history" type="button">切换运行</button><button class="button primary" data-view="new" type="button">开始新的评测</button></div></div>' + resultTabs("result");
  }
  function dashboardDimensionSnapshot(primary, comparison) {
    if (!scoreValid(primary) || (comparison && !scoreValid(comparison))) {
      return '<section class="workspace-surface empty-inline"><strong>本次运行不可评分</strong><span>至少一个 Agent 出现运行错误；请先处理余额、凭据、超时或运行环境问题，再比较六维能力。</span></section>';
    }
    const rows = CAPABILITIES.map((item) => ({ item, delta: comparison == null ? null : Number((primary.dimensions || {})[item[0]] || 0) - Number((comparison.dimensions || {})[item[0]] || 0) })).filter((row) => row.delta != null).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
    const differenceList = comparison && rows.length ? '<section class="workspace-surface dashboard-differences"><div class="surface-toolbar"><div><h3>差异最大的项目</h3></div><button class="link-button" data-result-tab="compare" type="button">查看完整对比 →</button></div><div class="difference-list">' + rows.slice(0, 4).map((row) => '<button class="difference-row" data-result-tab="cases" type="button"><span class="difference-rank">' + (rows.indexOf(row) + 1) + '</span><span><strong>' + row.item[1] + '</strong><small>' + row.item[0] + '</small></span><span class="difference-value ' + (row.delta < 0 ? 'negative' : '') + '">' + (row.delta > 0 ? '+' : '') + pct(row.delta) + '</span><span class="difference-note">点击查看案例</span></button>').join('') + '</div></section>' : '';
    return '<div class="dashboard-analysis-grid"><section class="workspace-surface"><div class="surface-toolbar"><div><h3>六维能力得分</h3></div><button class="link-button" data-result-tab="compare" type="button">查看完整对比 →</button></div><div class="dashboard-dimensions"><div class="dashboard-dimension-head"><span>能力维度</span><span>' + escapeHtml(displayAgentName(primary.agent || "主 Agent")) + '</span><span>' + escapeHtml(displayAgentName(comparison?.agent || "对比 Agent")) + '</span><span>差值</span></div>' + CAPABILITIES.map((item) => { const a = Number((primary.dimensions || {})[item[0]] || 0), b = comparison ? Number((comparison.dimensions || {})[item[0]] || 0) : null; const d = b == null ? null : a - b; return '<div class="dashboard-dimension-row"><div><strong>' + item[1] + '</strong><span>' + item[0] + '</span></div><span class="dashboard-score blue">' + pct(a) + '</span><span class="dashboard-score orange">' + (b == null ? '未观测' : pct(b)) + '</span><span class="dashboard-delta ' + (d != null && d < 0 ? 'negative' : '') + '">' + (d == null ? '—' : (d > 0 ? '+' : '') + pct(d)) + '</span></div>'; }).join('') + '</div><div class="dashboard-legend"><span><i class="legend-dot blue"></i>' + escapeHtml(displayAgentName(primary.agent || "主 Agent")) + '</span>' + (comparison ? '<span><i class="legend-dot orange"></i>' + escapeHtml(displayAgentName(comparison.agent || "对比 Agent")) + '</span>' : '') + '</div></section><section class="workspace-surface radar-surface"><div class="surface-toolbar"><div><h3>能力雷达</h3></div></div><div class="radar-wrap compact">' + radarChart(primary.dimensions || {}, comparison && comparison.dimensions) + '</div></section></div>' + differenceList;
  }
  function trendMarkup() {
    const rows = state.runs.filter((run) => run.kind === "comparison" && Array.isArray(run.overall)).slice(0, 6).reverse();
    if (!rows.length) return '<div class="empty-inline">暂无足够的历史双 Agent 运行用于趋势展示。</div>';
    return '<div class="trend-list">' + rows.map((run) => { const values = run.overall || []; const top = Math.max(Number(values[0] || 0), Number(values[1] || 0), 1); return '<div class="trend-row"><span class="trend-label" title="' + escapeHtml(run.id || run.run_id || '') + '">' + escapeHtml(runDisplayName(run)) + '</span><div class="trend-bars"><i class="trend-bar blue" style="height:' + Math.max(8, Number(values[0] || 0) / top * 34) + 'px" title="主 Agent ' + pct(values[0]) + '"></i><i class="trend-bar orange" style="height:' + Math.max(8, Number(values[1] || 0) / top * 34) + 'px" title="对比 Agent ' + pct(values[1]) + '"></i></div><span class="trend-score">' + pct(values[0]) + ' / ' + pct(values[1]) + '</span></div>'; }).join('') + '</div>';
  }
  function recentEvaluationMarkup() {
    const rows = state.runs.filter((run) => run.kind === "comparison").slice(0, 5);
    if (!rows.length) return '<div class="empty-inline">暂无最近评测。</div>';
    return '<div class="recent-evaluations">' + rows.map((run) => '<button class="recent-evaluation" data-open-run="' + escapeHtml(run.path) + '" type="button"><span class="recent-evaluation-main"><strong title="' + escapeHtml(run.id || run.run_id || '') + '">' + escapeHtml(runDisplayName(run)) + '</strong><small>' + escapeHtml((run.agents || []).map(displayAgentName).join('  对比  ') || '双智能体') + '</small></span><span class="recent-evaluation-score">' + (Array.isArray(run.overall) ? run.overall.map((value) => pct(value)).join(' / ') : pct(run.overall)) + '</span><span class="status-pill ' + escapeHtml(run.status || 'unknown') + '">' + escapeHtml(statusLabel(run.status)) + '</span></button>').join('') + '</div>';
  }
  function renderResultDashboard() {
    const { primary, comparison, failures, path } = resultDetails();
    if (!primary || !Object.keys(primary).length) return emptyState("结果结构不完整", "本地结果没有包含可展示的 Agent 摘要。", "history");
    const delta = scoreDelta(primary, comparison);
    const winner = winnerText(primary, comparison);
    const aRate = successRate(primary), bRate = successRate(comparison);
    const aLatency = averageLatency(primary);
    const cases = Number(primary.cases || (primary.results || []).length || 0);
    return resultDashboardHeader(primary, comparison, path)
      + '<div class="boundary-notice"><strong>观测边界</strong> ' + escapeHtml((primary.observability || {}).disclaimer || "模型文本不能替代状态证据。") + '<span class="source-key" title="原始来源字段：model / wrapper / simulated / runner">模型 / 包装层 / 模拟 / 运行器</span></div>'
      + '<section class="result-conclusion"><div class="result-score-line"><div><span>主 Agent</span><strong class="score-blue">' + scoreText(primary) + '</strong></div><div><span>对比 Agent</span><strong class="score-orange">' + (comparison ? scoreText(comparison) : '未观测') + '</strong></div><div><span>胜出</span><strong>' + escapeHtml(winner) + '</strong></div><div><span>差值</span><strong>' + (delta == null ? '不可比较' : (delta > 0 ? '+' : '') + pct(delta)) + '</strong></div></div><div class="result-fact-line"><span>成功率 ' + (aRate == null ? '未观测' : pct(aRate) + '%') + (comparison ? ' / ' + (bRate == null ? '未观测' : pct(bRate) + '%') : '') + '</span><span>案例 ' + cases + '</span><span>平均耗时 ' + (aLatency == null ? '未记录' : pct(aLatency) + ' ms') + '</span><span>失败案例 ' + failureCaseCount(failures) + '</span></div></section>'
      + dashboardDimensionSnapshot(primary, comparison);
  }
  function investigationDifferenceList(primary, comparison) {
    if (!comparison) return '<div class="empty-inline">没有第二个 Agent，无法生成差异分析。</div>';
    const rows = CAPABILITIES.map((item) => ({ item, delta: Number((primary.dimensions || {})[item[0]] || 0) - Number((comparison.dimensions || {})[item[0]] || 0) })).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
    return '<div class="difference-list">' + rows.map((row) => '<div class="difference-row"><span class="difference-rank">' + (rows.indexOf(row) + 1) + '</span><div><strong>' + row.item[1] + '</strong><small>' + row.item[0] + '</small></div><span class="difference-value ' + (row.delta < 0 ? 'negative' : '') + '">' + (row.delta > 0 ? '+' : '') + pct(row.delta) + '</span><span class="difference-note">' + (row.delta > 0 ? escapeHtml(displayAgentName(primary.agent || '主 Agent')) + ' 领先' : row.delta < 0 ? escapeHtml(displayAgentName(comparison.agent || '对比 Agent')) + ' 领先' : '无差异') + '</span></div>').join('') + '</div>';
  }
  function renderMemoryTrace(agents) {
    const rows = caseRows(agents);
    const selected = (state.selectedCase && rows.find((row) => row.caseId === state.selectedCase)) || rows[0];
    if (!selected) return '<section class="workspace-surface empty-inline">没有可读取的案例证据链。</section>';
    const traces = [];
    [selected.first, selected.second].forEach((result, index) => {
      if (!result) return;
      (result.checks || []).forEach((check) => (check.evidence_refs || []).forEach((ref) => traces.push({ agent: agents[index]?.agent || ('Agent ' + (index ? 'B' : 'A')), source: ref.source || 'unknown', kind: ref.kind || 'evidence', step: ref.step, event: ref.event_id, passed: check.passed, reason: check.reason })));
    });
    return '<section class="workspace-surface"><div class="surface-toolbar"><div><h3>' + escapeHtml(selected.caseId) + '</h3><span>从原始检查项回溯检索、状态转换和评分依据；未提供的内部状态不会被推断。</span></div><button class="button small" data-go-compare-tab="evidence" type="button">打开证据</button></div><div class="trace-summary"><span>主 Agent / 对比 Agent</span><strong>' + traces.length + ' 条可观测引用</strong><span>来源仅展示实际证据事件元数据</span></div><div class="trace-list">' + (traces.length ? traces.map((trace) => '<div class="trace-row"><span class="legend-dot ' + (trace.agent === agents[0]?.agent ? 'blue' : 'orange') + '"></span><div><strong>' + escapeHtml(trace.agent) + ' · ' + escapeHtml(displayEventKind(trace.kind)) + '</strong><small>步骤 ' + escapeHtml(fmt(trace.step, '未记录')) + ' · ' + escapeHtml(displaySource(trace.source)) + '</small></div><span class="source-pill ' + escapeHtml(trace.source) + '">' + escapeHtml(displaySource(trace.source)) + '</span><span class="trace-status ' + (trace.passed ? 'pass' : 'fail') + '">' + (trace.passed ? '通过' : '失败') + '</span><code title="' + escapeHtml(trace.event || '') + '">' + escapeHtml(trace.event || '事件 ID 未记录') + '</code></div>').join('') : '<div class="empty-inline">当前案例没有结构化证据引用。</div>') + '</div></section>';
  }
  function renderInvestigationWorkspace(tab) {
    const { agents, primary, comparison, failures, path } = resultDetails();
    if (!agents.length) return emptyState("结果结构不完整", "本地结果没有包含可比较的 Agent 摘要。", "history");
    const delta = scoreDelta(primary, comparison);
    const header = '<div class="workspace-intro compact-intro investigation-intro"><div><div class="run-summary"><span>' + escapeHtml(displayAgentName(primary.agent || '主 Agent')) + (comparison ? ' 对比 ' + escapeHtml(displayAgentName(comparison.agent || '对比 Agent')) : '') + '</span><span>差值 <strong>' + (delta == null ? '未观测' : (delta > 0 ? '+' : '') + pct(delta)) + '</strong></span><span>当前案例 <strong>' + escapeHtml(state.selectedCase || '未选择') + '</strong></span></div></div><div class="section-actions"><button class="button" data-view="history" type="button">切换运行</button><button class="button primary" data-view="new" type="button">开始新的评测</button></div></div>' + resultTabs(tab);
    let body = '<div class="boundary-notice"><strong>观测边界</strong> ' + escapeHtml(displayDisclaimer((primary.observability || {}).disclaimer) || '模型文本不能替代状态证据。') + '<span class="source-key" title="原始来源字段：model / wrapper / simulated / runner">模型 / 包装层 / 模拟 / 运行器</span></div>';
    if (tab === 'cases') body += renderCasesWorkspace(agents, failures);
    else if (tab === 'evidence') body += '<section class="workspace-surface"><div class="surface-toolbar"><div><h3>证据链调查</h3><span>从失败类型进入完整证据事件时间线、动作结果和评分理由。</span></div></div>' + failureFilters(agents, failures) + '<div class="table-wrap">' + failureTable(filterFailures(failures)) + '</div></section>';
    else if (tab === 'trace') body += renderMemoryTrace(agents);
    else if (tab === 'logs') body += '<section class="workspace-surface"><div class="surface-toolbar"><div><h3>运行日志与工件</h3><span>仅列出结果元数据中实际存在的本地文件。</span></div></div><div class="artifact-list">' + artifactButtons(primary, '主 Agent') + (comparison ? artifactButtons(comparison, '对比 Agent') : '') + '<div class="log-note">日志来源：本地运行目录、workbench-job.json 和证据事件 JSONL。</div></div></section>';
    else if (!scoreValid(primary) || (comparison && !scoreValid(comparison))) body += '<div class="compare-summary"><span>主 Agent <strong class="score-blue">' + scoreText(primary) + '</strong></span><span>对比 Agent <strong class="score-orange">' + (comparison ? scoreText(comparison) : '未观测') + '</strong></span><span>差值 <strong>不可比较</strong></span></div><section class="workspace-surface empty-inline"><strong>运行错误阻止了能力对比</strong><span>错误证据已保留在“证据”和“日志”页。</span></section>';
    else body += '<div class="compare-summary"><span>主 Agent <strong class="score-blue">' + scoreText(primary) + '</strong></span><span>对比 Agent <strong class="score-orange">' + (comparison ? scoreText(comparison) : '未观测') + '</strong></span><span>差值 <strong>' + (delta == null ? '未观测' : (delta > 0 ? '+' : '') + pct(delta)) + '</strong></span></div><div class="compare-workspace-result"><section class="workspace-surface"><div class="surface-toolbar"><div><h3>六维能力对比</h3></div><div class="agent-legend"><i class="legend-dot blue"></i>' + escapeHtml(displayAgentName(primary.agent || '主 Agent')) + ' <i class="legend-dot orange"></i>' + escapeHtml(displayAgentName(comparison?.agent || '对比 Agent')) + '</div></div><div class="compare-table"><div class="compare-head"><span>能力维度</span><span>主 Agent</span><span>对比 Agent</span></div>' + CAPABILITIES.map((item) => dimensionRow(item, primary, comparison)).join('') + '</div></section><section class="workspace-surface radar-surface"><div class="surface-toolbar"><div><h3>雷达概览</h3></div></div><div class="radar-wrap">' + radarChart(primary.dimensions || {}, comparison && comparison.dimensions) + '</div></section></div>';
    return header + body;
  }
  function caseRows(agents) { const ids = [...new Set(agents.flatMap((agent) => (agent.results || []).map((result) => result.case_id)))]; return ids.map((caseId) => ({ caseId, first: (agents[0].results || []).find((result) => result.case_id === caseId), second: agents[1] && (agents[1].results || []).find((result) => result.case_id === caseId) })); }
  function caseScore(result) { return result && result.status === "error" ? "运行错误" : pct(Number((result || {}).score || 0) * 100); }
  function renderCasesWorkspace(agents, failures) { const rows = caseRows(agents); const selected = state.selectedCase && rows.find((row) => row.caseId === state.selectedCase); return '<section class="workspace-surface"><div class="surface-toolbar"><div><h3>逐案例对比</h3><span>选择案例后，左右展示两个智能体的结果、差异和评分。</span></div><span class="rail-count">' + rows.length + ' 个案例</span></div><div class="case-list">' + rows.map((row) => '<button class="case-list-row ' + (row.caseId === state.selectedCase ? "active" : "") + '" data-select-case="' + escapeHtml(row.caseId) + '" type="button"><span class="case-list-id">' + escapeHtml(row.caseId) + '</span><span>' + escapeHtml(capabilityLabel((row.first || row.second || {}).capability)) + '</span><strong>' + caseScore(row.first) + ' / ' + (row.second ? caseScore(row.second) : "-") + '</strong><span class="case-arrow">→</span></button>').join("") + '</div></section>' + (selected ? caseDetailWorkspace(selected, agents) : '<section class="workspace-surface empty-inline"><span>选择一个案例查看主 Agent / 对比 Agent 的详细差异。</span></section>'); }
  function caseDetailWorkspace(row, agents) { const first = row.first || {}, second = row.second || {}; return '<section class="workspace-surface case-detail-workspace"><div class="surface-toolbar"><div><h3>' + escapeHtml(row.caseId) + '</h3><span>' + escapeHtml(capabilityLabel(first.capability || second.capability)) + '</span></div><button class="button small" data-open-case-evidence="' + escapeHtml(row.caseId) + '" type="button">打开证据</button></div><div class="case-agent-grid"><div class="case-agent-card blue"><span class="agent-tag">主 Agent</span><strong>' + escapeHtml(agents[0].agent || "主 Agent") + '</strong><span>分数 ' + caseScore(first) + '</span><p>' + escapeHtml((first.failures || []).map((failure) => failure.reason).join("；") || "案例通过或未记录失败理由") + '</p></div><div class="case-agent-card orange"><span class="agent-tag">对比 Agent</span><strong>' + escapeHtml(agents[1]?.agent || "对比 Agent") + '</strong><span>分数 ' + (row.second ? caseScore(second) : "未观测") + '</span><p>' + escapeHtml((second.failures || []).map((failure) => failure.reason).join("；") || "案例通过或未记录失败理由") + '</p></div></div><div class="case-detail-footer"><span>评分理由</span><strong>' + escapeHtml((first.failures || second.failures || []).map((failure) => failure.reason).join("；") || "由确定性评分器根据证据和动作结果判定") + '</strong></div></section>'; }
  function summaryMetric(label, value, note) { return '<div class="metric"><div class="metric-label">' + escapeHtml(label) + '</div><div class="metric-value">' + escapeHtml(value) + '</div><div class="metric-note">' + escapeHtml(note || "") + '</div></div>'; }
  function dimensionRow(item, primary, comparison) { const p = Number((primary.dimensions || {})[item[0]] || 0), c = comparison ? Number((comparison.dimensions || {})[item[0]] || 0) : null; return '<div class="compare-row"><div><div class="dimension-name">' + item[1] + '</div><div class="dimension-key">' + item[0] + '</div></div><div class="bar-cell"><span class="bar-number">' + pct(p) + '</span><div class="bar-track"><div class="bar-fill blue" style="width:' + Math.max(0, Math.min(100, p)) + '%"></div></div></div><div class="bar-cell"><span class="bar-number">' + (c == null ? "-" : pct(c)) + '</span>' + (c == null ? '<div class="bar-track"></div>' : '<div class="bar-track"><div class="bar-fill orange" style="width:' + Math.max(0, Math.min(100, c)) + '%"></div></div>') + '</div></div>'; }
  function radarChart(first, second) {
    const cx = 150, cy = 140, r = 90, n = CAPABILITIES.length;
    const point = (index, value, radius = r) => { const angle = -Math.PI / 2 + index * 2 * Math.PI / n; const distance = radius * Math.max(0, Math.min(100, Number(value || 0))) / 100; return (cx + Math.cos(angle) * distance).toFixed(1) + "," + (cy + Math.sin(angle) * distance).toFixed(1); };
    const ring = (scale) => CAPABILITIES.map((_, index) => point(index, scale)).join(" ");
    const axes = CAPABILITIES.map((_, index) => '<line class="radar-axis" x1="' + cx + '" y1="' + cy + '" x2="' + point(index, 100) .split(",")[0] + '" y2="' + point(index, 100).split(",")[1] + '"></line>').join("");
    const labels = CAPABILITIES.map((item, index) => { const p = point(index, 116); return '<text class="radar-label" x="' + p.split(",")[0] + '" y="' + p.split(",")[1] + '">' + item[1] + '</text>'; }).join("");
    const p1 = CAPABILITIES.map((item) => point(CAPABILITIES.indexOf(item), first[item[0]])).join(" ");
    const p2 = second ? CAPABILITIES.map((item) => point(CAPABILITIES.indexOf(item), second[item[0]])).join(" ") : "";
    return '<svg class="radar-svg" viewBox="0 0 300 285" role="img" aria-label="六维能力雷达图"><polygon class="radar-grid" points="' + ring(100) + '"></polygon><polygon class="radar-grid" points="' + ring(66) + '"></polygon><polygon class="radar-grid" points="' + ring(33) + '"></polygon>' + axes + '<polygon class="radar-polygon blue" points="' + p1 + '"></polygon>' + (p2 ? '<polygon class="radar-polygon orange" points="' + p2 + '"></polygon>' : '') + labels + '</svg>';
  }
  function stabilityHtml(agents) { return '<div class="grid ' + (agents.length > 1 ? "two" : "") + '">' + agents.map((agent) => { const metrics = (agent._workbench || {}).metrics || {}; const obs = agent.observability || {}; const failures = agent.failure_counts || {}; const totalFailures = Object.values(failures).reduce((sum, value) => sum + Number(value || 0), 0); return '<div class="quiet-panel" style="padding:14px"><div class="run-summary"><span><strong>' + escapeHtml(agent.agent || "Agent") + '</strong></span><span>模式 <strong>' + escapeHtml(displayMode(obs.mode)) + '</strong></span><span>重试 <strong>' + fmt(agent.retries, "未记录") + '</strong></span></div><div class="run-summary" style="margin-top:10px"><span>证据 <strong>' + fmt(metrics.events || agent.evidence_chain?.events, "未记录") + '</strong></span><span>模型响应 <strong>' + fmt(metrics.model_responses, "未记录") + '</strong></span><span>失败计数 <strong>' + totalFailures + '</strong></span><span>原生记忆事件 <strong>' + fmt(obs.native_memory_events, "0") + '</strong></span></div><div style="margin-top:9px;color:var(--faint);font-size:11px">' + escapeHtml(obs.disclaimer || "未提供声明") + '</div></div>'; }).join("") + '</div>'; }
  function collectFailures(agents) { const output = []; agents.forEach((agent) => (agent.results || []).forEach((result) => { if (result.status !== "pass" || (result.failures || []).length) (result.failures || [{ type: result.status === "error" ? "runtime_error" : "invalid_behavior", reason: "案例未通过" }]).forEach((failure) => output.push({ agent: agent.agent, result, failure, agentSummary: agent })); })); return output; }
  function filterFailures(rows) { return rows.filter((row) => state.filters.agent === "all" || row.agent === state.filters.agent).filter((row) => state.filters.capability === "all" || row.result.capability === state.filters.capability).filter((row) => state.filters.failure === "all" || row.failure.type === state.filters.failure).sort((a, b) => Number(a.result.score || 0) - Number(b.result.score || 0)); }
  function failureFilters(agents, rows) { const failures = [...new Set(rows.map((row) => row.failure.type))]; return '<div class="filter-row"><select id="failure-agent"><option value="all">全部 Agent</option>' + agents.map((agent) => '<option value="' + escapeHtml(agent.agent) + '"' + (state.filters.agent === agent.agent ? " selected" : "") + '>' + escapeHtml(agent.agent) + '</option>').join("") + '</select><select id="failure-capability"><option value="all">全部能力</option>' + CAPABILITIES.map((item) => '<option value="' + item[0] + '"' + (state.filters.capability === item[0] ? " selected" : "") + '>' + item[1] + '</option>').join("") + '</select><select id="failure-type"><option value="all">全部失败类型</option>' + failures.map((type) => '<option value="' + escapeHtml(type) + '"' + (state.filters.failure === type ? " selected" : "") + '>' + escapeHtml(failureLabel(type)) + '</option>').join("") + '</select></div>'; }
  function failureTable(rows) { if (!rows.length) return '<div class="empty-state"><div class="empty-mark">✓</div><strong>当前筛选下没有失败案例</strong><p>这表示没有可从当前结果证据中确认的失败项，不代表未观测状态等同于通过。</p></div>'; return '<table><thead><tr><th>Agent</th><th>案例</th><th>能力</th><th>分数</th><th>失败类型</th><th>原因</th><th></th></tr></thead><tbody>' + rows.map((row, index) => '<tr><td><strong>' + escapeHtml(row.agent) + '</strong></td><td>' + escapeHtml(row.result.case_id) + '</td><td>' + capabilityLabel(row.result.capability) + '</td><td class="' + (Number(row.result.score || 0) < 1 ? "score-low" : "score-high") + '">' + pct(Number(row.result.score || 0) * 100) + '</td><td><span class="status-pill failed" title="' + escapeHtml(row.failure.type || "invalid_behavior") + '">' + escapeHtml(failureLabel(row.failure.type)) + '</span></td><td style="max-width:310px;white-space:normal">' + escapeHtml(row.failure.reason || "未提供理由") + '</td><td><button class="link-button" data-failure-index="' + index + '" type="button">查看证据</button></td></tr>').join("") + '</tbody></table>'; }
  function artifactButtons(agent, label) { const paths = (agent._workbench || {}).report_paths || {}; return '<span style="display:inline-flex;align-items:center;gap:7px;margin-right:16px;font-size:11px;color:var(--muted)"><strong>' + escapeHtml(label) + '</strong>' + Object.keys(paths).map((key) => '<button class="link-button" data-artifact="' + escapeHtml(paths[key]) + '" type="button">' + escapeHtml(key) + '</button>').join("") + '</span>'; }

  function renderHistory() { const query = state.filters.history.toLowerCase(); const rows = state.runs.filter((run) => !query || JSON.stringify(run).toLowerCase().includes(query)); if (!rows.length) return emptyState("没有匹配的历史运行", "工作台只读取本地 runs/ 目录中的实际结果文件。", "new"); return '<div class="section-head"><div><p>按运行摘要浏览本地结果；详细路径保留在结果元数据和复现入口中。</p></div><div class="section-actions"><input id="history-filter" class="history-search" value="' + escapeHtml(state.filters.history) + '" placeholder="搜索运行 ID / 智能体 / 套件" aria-label="搜索历史运行" style="height:34px;border:1px solid var(--line-strong);padding:0 10px;font-size:12px"></div></div><section class="panel"><div class="table-wrap"><table><thead><tr><th>时间</th><th>任务</th><th>主 Agent</th><th>对比 Agent</th><th>案例数</th><th>得分</th><th>状态</th><th>耗时</th><th></th></tr></thead><tbody>' + rows.map((run) => { const agents = run.agents || []; const score = Array.isArray(run.overall) ? run.overall.map((value) => pct(value)).join(' / ') : pct(run.overall); const rawId = run.id || run.run_id || '未命名运行'; return '<tr><td>' + escapeHtml(fmt(run.started_at, '未记录')) + '</td><td><button class="link-button" data-open-run="' + escapeHtml(run.path) + '" title="' + escapeHtml(rawId) + '" type="button">' + escapeHtml(run.title || displayRunName(rawId)) + '</button><div class="history-mode">' + escapeHtml(displayMode(run.mode)) + '</div></td><td>' + escapeHtml(displayAgentName(agents[0] || run.agent || '未观测')) + '</td><td>' + escapeHtml(displayAgentName(agents[1] || '未观测')) + '</td><td>' + escapeHtml(fmt(run.cases, '—')) + '</td><td>' + escapeHtml(score) + '</td><td><span class="status-pill ' + escapeHtml(run.status || 'unknown') + '">' + escapeHtml(statusLabel(run.status)) + '</span></td><td>' + escapeHtml(fmt(run.duration_ms != null ? run.duration_ms + ' ms' : run.duration, '未记录')) + '</td><td><button class="button small" data-open-run="' + escapeHtml(run.path) + '" type="button">打开</button></td></tr>'; }).join('') + '</tbody></table></div></section>'; }
  function configCard(config) {
    const credential = config.credential === "configured" || config.credential === "not_required";
    return '<article class="config-card">'
      + '<div class="config-title"><button class="provider-card-main" data-provider-detail="' + escapeHtml(config.path) + '" type="button"><h3>' + escapeHtml(config.name) + '</h3><div class="config-type">' + escapeHtml(profileMode(config)) + ' · ' + escapeHtml(config.path) + '</div></button>'
      + '<span class="status-pill ' + (credential ? "completed" : "partial") + '">' + escapeHtml(credentialLabel(config)) + '</span></div>'
      + '<div class="config-lines">'
      + '<div class="config-line"><span>服务商</span><span>' + escapeHtml(providerLabel(config)) + '</span></div>'
      + '<div class="config-line"><span>模型</span><span>' + escapeHtml(config.model || "本地") + '</span></div>'
      + '<div class="config-line"><span>接口</span><span>' + escapeHtml(config.endpoint || "本地适配器") + '</span></div>'
      + '</div>'
      + '<div class="health-row"><span id="config-health-' + escapeHtml(config.path.replace(/[^A-Za-z0-9]/g, "-")) + '" class="health-state">未检查</span><button class="button small" data-health-config="' + escapeHtml(config.path) + '" type="button">连接检查</button></div>'
      + '</article>';
  }
  function providerCard(provider, configs) {
    const primary = configs.find((config) => profileMode(config) === "标准 API") || configs[0];
    const ready = configs.some((config) => config.credential === "configured" || config.credential === "not_required");
    return '<article class="config-card provider-card">'
      + '<div class="provider-heading">'
      + '<button class="provider-card-main" data-provider-detail="' + escapeHtml(primary.path) + '" type="button">'
      + '<h3>' + escapeHtml(provider) + '</h3>'
      + '<div class="provider-summary">'
      + '<span>模型 <strong>' + escapeHtml(primary.model || "待运行时解析") + '</strong></span>'
      + '<span>Endpoint <strong>' + escapeHtml(primary.endpoint || "未配置") + '</strong></span>'
      + '</div>'
      + '</button>'
      + '<span class="status-pill ' + (ready ? "completed" : "partial") + '">' + escapeHtml(ready ? "凭据已加载" : "未检测到凭据") + '</span>'
      + '</div>'
      + '<div class="profile-list">' + configs.map((config) => '<div class="profile-row">'
        + '<div><strong>' + escapeHtml(profileMode(config)) + '</strong><span>' + escapeHtml(config.name) + ' · ' + escapeHtml(config.path) + '</span></div>'
        + '<button class="button small" data-health-config="' + escapeHtml(config.path) + '" type="button">连接检查</button>'
        + '<span id="config-health-' + escapeHtml(config.path.replace(/[^A-Za-z0-9]/g, "-")) + '">' + healthStateMarkup(config.path, credentialLabel(config)) + '</span>'
        + '</div>').join("") + '</div>'
      + '</article>';
  }
    function renderConfigs() {
    const credentials = (state.system || {}).credentials || {};
    const notice = credentials.status === "secure"
      ? '<div class="credential-notice ok"><strong>安全配置已加载</strong><span>当前服务已从同一运行环境的 <code>~/.config/kmb/credentials.env</code> 读取连接信息；页面只展示状态，不显示密钥。</span></div>'
      : '<div class="credential-notice warn"><strong>' + (credentials.status === "insecure" ? "凭据文件权限不安全" : "云端连接未就绪") + '</strong><span>' + escapeHtml(credentials.status === "insecure" ? "凭据文件权限不安全，服务拒绝加载。请将 ~/.config/kmb/credentials.env 权限设为 600。" : "本机未检测到凭据文件（~/.config/kmb/credentials.env）。配置 API Key 环境变量并刷新后即可连接云端；不填写凭据也能运行离线基线评测。") + '</span></div>';
    const profiles = state.profiles || [];
    const groups = [];
    profiles.forEach((profile) => {
      const provider = profile.provider || "其他";
      let group = groups.find((item) => item.provider === provider);
      if (!group) { group = { provider, items: [] }; groups.push(group); }
      group.items.push(profile);
    });
    const editing = state.editingProfileId;
    const poolCards = groups.length
      ? groups.map((group) => '<div class="provider-group"><div class="provider-name">' + escapeHtml(group.provider) + '</div>' + group.items.map(profileCard).join("") + '</div>').join("")
      : '<div class="empty-state"><strong>尚无 API 档案</strong><p>使用下方表单新增；新增后所有需要 LLM 的智能体立即可选用。</p></div>';
        if (editing) {
      const profile = (state.profiles || []).find((item) => item.id === editing) || {};
      state.configDraft = {
        profile_id: profile.id || "", provider: profile.provider || "", name: profile.name || "",
        base_url: profile.base_url || "", endpoint: profile.endpoint || "", model: profile.model || "",
        api_key_env: profile.api_key_env || "", timeout_seconds: profile.timeout_seconds || 60,
        temperature: profile.temperature || 0, description: profile.description || "",
      };
    }
    return '<section class="panel"><div class="panel-header"><div><h3>API 档案池（全局）</h3><p>' + profiles.length + ' 个 API 档案；一处定义，所有需要 LLM 的智能体共用。修改后对所有引用它的评测立即生效。</p></div></div><div class="panel-body">' + notice + poolCards + '</div></section>' + configWizardMarkup() + (editing ? '<div class="edit-banner"><button class="link-button" data-cancel-edit type="button">取消编辑，返回新增</button></div>' : '');
  }
  function profileCard(profile) {
    return '<article class="agent-registry-row profile-row"><span class="legend-dot blue"></span><div class="agent-registry-main"><strong>' + escapeHtml(profile.name) + '</strong><span>' + escapeHtml(profile.provider || "未分组") + ' · ' + escapeHtml(profile.model) + ' · ' + escapeHtml((profile.base_url || "") + (profile.endpoint || "")) + '</span></div><span class="mode-pill">API 档案</span><span class="' + (profile.credential === "configured" ? "credential-safe" : "credential-missing") + '">' + escapeHtml(profile.credential === "configured" ? "凭据已配置" : "未检测到凭据") + '</span><button class="button small" data-edit-profile="' + escapeHtml(profile.id) + '" type="button">编辑</button></article>';
  }
  function renderSettings() { const system = state.system || {}; const env = system.openkylin || {}; const capabilities = system.system_scenarios || {}; return '<div class="section-head"><div><p>环境和复现信息只读展示，敏感凭据不会从后端返回。</p></div></div><div class="grid two"><section class="panel"><div class="panel-header"><div><h3>运行环境</h3><p>来源：本地服务环境探针。</p></div></div><div class="panel-body"><div class="setting-list">' + settingLine("openKylin", env.detected ? "已检测：" + (env.distribution || "openKylin") : "未检测到 openKylin") + settingLine("平台", system.platform) + settingLine("机器架构", system.machine) + settingLine("Python", system.python) + settingLine("PyYAML", system.pyyaml) + settingLine("CLI 版本", system.cli_version) + settingLine("结果目录", system.results_directory) + settingLine("套件目录", system.suite_directory) + '</div></div></section><section class="panel"><div class="panel-header"><div><h3>系统级场景能力</h3><p>未执行的系统边界不会被 UI 显示为通过。</p></div></div><div class="panel-body"><div class="capability-list">' + Object.keys(capabilities).map((key) => '<div class="capability-line"><span>' + escapeHtml(key) + '</span><span class="mode-pill">' + escapeHtml(scenarioStatusLabel(capabilities[key].status)) + '</span></div>').join("") + '</div></div></section></div>'; }
  function settingLine(label, value) { return '<div class="setting-line"><span class="setting-label">' + escapeHtml(label) + '</span><span class="setting-value">' + escapeHtml(fmt(value)) + '</span></div>'; }
  function emptyState(title, description, view) { return '<section class="panel"><div class="empty-state"><div class="empty-mark">□</div><strong>' + escapeHtml(title) + '</strong><p>' + escapeHtml(description) + '</p>' + (view ? '<div style="margin-top:16px"><button class="button" data-view="' + escapeHtml(view) + '" type="button">前往新建评测</button></div>' : '') + '</div></section>'; }

  async function loadSelectedRun(path) { try { state.selectedRunPath = path; state.selectedRun = await api("/api/runs?path=" + encodeURIComponent(path)); render(); } catch (error) { showGlobalError(error.message); } }
  function selectedFailure(index) { const agents = normalizeAgents(state.selectedRun); return filterFailures(collectFailures(agents))[Number(index)]; }
  async function openFailure(row) {
    if (!row) return;
    const summary = row.agentSummary;
    const evidencePath = (summary._workbench || {}).evidence_path || summary.evidence;
    let events = [];
    if (evidencePath) {
      try { events = (await api("/api/evidence?path=" + encodeURIComponent(evidencePath) + "&case=" + encodeURIComponent(row.result.case_id) + "&limit=500")).events || []; } catch (error) { events = [{ kind: "error", data: { message: error.message }, step: 0 }]; }
    }
    const result = row.result;
    $("#drawer-title").textContent = result.case_id || "案例详情";
    $("#drawer-content").innerHTML = '<div class="detail-block"><h3>判定</h3><div class="reason-box"><strong title="' + escapeHtml(row.failure.type || "invalid_behavior") + '">' + escapeHtml(failureLabel(row.failure.type)) + '</strong><span class="failure-category">' + escapeHtml(row.failure.category || "behavior_failure") + '</span><br>' + escapeHtml(row.failure.reason || "未提供失败理由") + '</div></div><div class="detail-block"><h3>案例与状态</h3><div class="detail-code">' + safeJson({ agent: row.agent, capability: capabilityLabel(result.capability), score: result.score, status: result.status, attempts: result.attempts, observability: result.observability }) + '</div></div><div class="detail-block"><h3>检查项</h3><div class="detail-code">' + safeJson(result.checks || []) + '</div></div><div class="detail-block"><h3>EvidenceEvent 时间线（' + events.length + '）</h3><div class="timeline">' + (events.length ? events.map(timelineItem).join("") : '<div class="empty-state"><strong>没有可读取的证据事件</strong><p>结果可能缺少 evidence.jsonl，或路径不在当前工作区白名单中。</p></div>') + '</div></div><div class="detail-block"><h3>复现入口</h3><div class="detail-code">' + safeJson({ evidence: evidencePath || "未记录", result: (summary._workbench || {}).result_path || "未记录", command: "python -m kmb.cli run/compare ...（以运行记录中的实际命令为准）" }) + '</div></div>';
    localizeUi();
    $("#drawer-backdrop").hidden = false; $("#case-drawer").classList.add("open"); $("#case-drawer").setAttribute("aria-hidden", "false");
  }
  function timelineItem(event) { const kind = event.kind || "event"; const source = event.source || (event.data || {}).source || "unknown"; const details = Object.assign({}, event.data || {}); ["messages", "content"].forEach((key) => { if (details[key] && String(details[key]).length > 260) details[key] = String(details[key]).slice(0, 260) + "…"; }); return '<div class="timeline-item"><span class="timeline-dot"></span><div class="timeline-main"><div class="timeline-title"><span>' + escapeHtml(displayEventKind(kind)) + '</span><span class="source-pill ' + escapeHtml(source) + '">' + escapeHtml(displaySource(source)) + '</span></div><div class="timeline-meta">步骤 ' + escapeHtml(event.step) + ' · ' + escapeHtml(fmt(event.timestamp, "时间未记录")) + (event.fact_version ? ' · v' + escapeHtml(event.fact_version) : "") + '</div><div class="timeline-data">' + escapeHtml(JSON.stringify(details)) + '</div></div></div>'; }
  function closeDrawer() { $("#case-drawer").classList.remove("open"); $("#case-drawer").setAttribute("aria-hidden", "true"); $("#drawer-backdrop").hidden = true; }

  function updateParamsFromForm() { ["seed", "retries", "timeout", "scorer-version"].forEach((id) => { const input = $("#" + id); if (input) state.params[id === "scorer-version" ? "scorer_version" : id] = input.value; }); }

  function selectTriggerLabel(select) {
    const opt = select.options[select.selectedIndex];
    return opt ? opt.text : "选择…";
  }

  function getSelectPopupLayer() {
    let layer = document.getElementById("select-popup-layer");
    if (!layer) {
      layer = document.createElement("div");
      layer.id = "select-popup-layer";
      layer.className = "select-popup-layer";
      document.body.appendChild(layer);
    }
    return layer;
  }

  function scrollOptionIntoPopup(popup, el) {
    if (!popup || !el) return;
    const pRect = popup.getBoundingClientRect();
    const eRect = el.getBoundingClientRect();
    if (eRect.top < pRect.top) {
      popup.scrollTop += eRect.top - pRect.top;
    } else if (eRect.bottom > pRect.bottom) {
      popup.scrollTop += eRect.bottom - pRect.bottom;
    }
  }

  function positionSelectPopup(trigger, popup) {
    const layer = getSelectPopupLayer();
    if (popup.parentElement !== layer) layer.appendChild(popup);
    popup.style.visibility = "hidden";
    popup.style.display = "block";
    popup.style.left = "0px";
    popup.style.top = "0px";
    popup.style.width = "auto";
    popup.style.maxHeight = "";

    const tRect = trigger.getBoundingClientRect();
    const gap = 6;
    const viewportPad = 8;
    const desiredWidth = Math.max(tRect.width, 220);
    const maxHDown = Math.max(120, window.innerHeight - tRect.bottom - gap - viewportPad);
    const maxHUp = Math.max(120, tRect.top - gap - viewportPad);
    const natural = popup.scrollHeight;
    const wantDown = natural <= maxHDown || maxHDown >= maxHUp;
    const maxHeight = Math.min(320, wantDown ? maxHDown : maxHUp);

    let top = wantDown ? tRect.bottom + gap : Math.max(viewportPad, tRect.top - gap - Math.min(natural, maxHeight));
    let left = tRect.left;
    let width = desiredWidth;
    if (left + width > window.innerWidth - viewportPad) {
      left = Math.max(viewportPad, window.innerWidth - viewportPad - width);
    }
    if (width > window.innerWidth - viewportPad * 2) {
      width = window.innerWidth - viewportPad * 2;
      left = viewportPad;
    }

    popup.style.left = Math.round(left) + "px";
    popup.style.top = Math.round(top) + "px";
    popup.style.width = Math.round(width) + "px";
    popup.style.maxHeight = Math.round(maxHeight) + "px";
    popup.dataset.side = wantDown ? "down" : "up";
    popup.style.visibility = "";
  }

  function ensureSelectMenu(select) {
    let wrap = select.closest(".select-menu");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "select-menu";
      select.parentNode.insertBefore(wrap, select);
      wrap.appendChild(select);
    }
    select.classList.add("native-select");
    select.setAttribute("tabindex", "-1");
    select.setAttribute("aria-hidden", "true");

    let trigger = wrap.querySelector(":scope > .select-trigger");
    if (!trigger) {
      trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "select-trigger";
      trigger.setAttribute("aria-haspopup", "listbox");
      trigger.setAttribute("aria-expanded", "false");
      trigger.innerHTML = '<span class="select-trigger-text"></span><span class="select-chevron" aria-hidden="true">▾</span>';
      wrap.appendChild(trigger);
    }

    // Popup lives in a body layer when open so overflow:hidden cannot clip it.
    let popup = wrap.querySelector(":scope > .select-popup");
    if (!popup) {
      popup = document.createElement("div");
      popup.className = "select-popup";
      popup.setAttribute("role", "listbox");
      popup.tabIndex = -1;
      wrap.appendChild(popup);
    }
    if (!wrap.dataset.menuId) {
      wrap.dataset.menuId = "m" + Math.random().toString(36).slice(2, 10);
    }
    popup.dataset.menuId = wrap.dataset.menuId;

    const syncLabel = () => {
      trigger.querySelector(".select-trigger-text").textContent = selectTriggerLabel(select);
    };
    syncLabel();

    const rebuildOptions = () => {
      popup.innerHTML = "";
      const items = [];
      let lastGroup = null;
      Array.from(select.options).forEach((opt) => {
        const groupLabel = opt.parentElement && opt.parentElement.tagName === "OPTGROUP" ? opt.parentElement.label : null;
        if (groupLabel && groupLabel !== lastGroup) {
          lastGroup = groupLabel;
          const gl = document.createElement("div");
          gl.className = "select-group-label";
          gl.textContent = groupLabel;
          popup.appendChild(gl);
        }
        if (!groupLabel) lastGroup = null;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "select-option" + (opt.selected ? " selected" : "");
        btn.setAttribute("role", "option");
        btn.dataset.value = opt.value;
        btn.innerHTML = '<span class="select-option-label"></span><span class="select-option-check">✓</span>';
        btn.querySelector(".select-option-label").textContent = opt.text;
        btn.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          select.value = opt.value;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          syncLabel();
          rebuildOptions();
          closeSelectMenus();
          trigger.focus({ preventScroll: true });
        });
        popup.appendChild(btn);
        items.push(btn);
      });
      let active = Math.max(0, items.findIndex((el) => el.classList.contains("selected")));
      const setActive = (index) => {
        items.forEach((el) => el.classList.remove("active"));
        if (items[index]) items[index].classList.add("active");
      };
      setActive(active);
      popup.onkeydown = (event) => {
        if (event.key === "ArrowDown") {
          event.preventDefault();
          active = Math.min(items.length - 1, active + 1);
          setActive(active);
          scrollOptionIntoPopup(popup, items[active]);
        }
        if (event.key === "ArrowUp") {
          event.preventDefault();
          active = Math.max(0, active - 1);
          setActive(active);
          scrollOptionIntoPopup(popup, items[active]);
        }
        if (event.key === "Home") {
          event.preventDefault();
          active = 0;
          setActive(active);
          scrollOptionIntoPopup(popup, items[0]);
        }
        if (event.key === "End") {
          event.preventDefault();
          active = items.length - 1;
          setActive(active);
          scrollOptionIntoPopup(popup, items[active]);
        }
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          items[active]?.click();
        }
        if (event.key === "Escape") {
          closeSelectMenus();
          trigger.focus({ preventScroll: true });
        }
      };
    };
    rebuildOptions();

    const openMenu = () => {
      closeSelectMenus();
      wrap.classList.add("open");
      wrap.setAttribute("data-last-open", "1");
      trigger.setAttribute("aria-expanded", "true");
      popup.dataset.menuId = wrap.dataset.menuId;
      positionSelectPopup(trigger, popup);
      // Only scroll inside popup; never page/outer containers.
      const selected = popup.querySelector(".select-option.selected") || popup.querySelector(".select-option");
      if (selected) {
        popup.scrollTop = 0;
        scrollOptionIntoPopup(popup, selected);
      }
      popup.focus({ preventScroll: true });
    };

    if (!trigger.dataset.bound) {
      trigger.dataset.bound = "1";
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (wrap.classList.contains("open")) {
          closeSelectMenus();
          return;
        }
        openMenu();
      });
    }

    select.addEventListener("change", () => {
      syncLabel();
      rebuildOptions();
    });

    return wrap;
  }

  let selectScrollBound = false;
  function bindSelectOverlayListeners() {
    if (selectScrollBound) return;
    selectScrollBound = true;
    document.addEventListener("click", (event) => {
      if (event.target && event.target.closest && (event.target.closest(".select-menu") || event.target.closest(".select-popup"))) return;
      closeSelectMenus();
    }, true);
    window.addEventListener("resize", () => closeSelectMenus());
    window.addEventListener(
      "scroll",
      (event) => {
        if (!document.querySelector(".select-menu.open")) return;
        const popup = document.getElementById("select-popup-layer");
        if (popup && event.target && popup.contains(event.target)) return;
        closeSelectMenus();
      },
      true
    );
  }
  bindSelectOverlayListeners();

  function enhanceSelectMenus() {
    document.querySelectorAll("#view-root select").forEach(ensureSelectMenu);
  }

  function closeSelectMenus() {
    document.querySelectorAll(".select-menu.open").forEach((el) => {
      el.classList.remove("open");
      const t = el.querySelector(".select-trigger");
      if (t) t.setAttribute("aria-expanded", "false");
    });
    const layer = document.getElementById("select-popup-layer");
    if (!layer) return;
    Array.from(layer.querySelectorAll(":scope > .select-popup")).forEach((popup) => {
      const menu = popup.closest(".select-menu") || document.querySelector(".select-menu.open") || null;
      // Prefer returning popup to its original menu wrapper when we can find it via data
      const wrapId = popup.dataset.menuId;
      let target = wrapId ? document.querySelector('.select-menu[data-menu-id="' + wrapId + '"]') : null;
      if (!target) {
        // last open menu
        target = document.querySelector('.select-menu[data-last-open="1"]');
      }
      if (target) {
        popup.removeAttribute("style");
        popup.dataset.side = "";
        target.appendChild(popup);
      } else {
        popup.remove();
      }
    });
    document.querySelectorAll(".select-menu[data-last-open]").forEach((el) => el.removeAttribute("data-last-open"));
  }


  function bindViewEvents() {
    document.querySelectorAll("#view-root [data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
    const primary = $("#primary-agent"), comparison = $("#comparison-agent"), suite = $("#suite");
    if (primary) primary.addEventListener("change", (event) => { state.formPrimary = event.target.value; render(); });
    if (comparison) comparison.addEventListener("change", (event) => { state.formComparison = event.target.value; render(); });
    if (suite) suite.addEventListener("change", (event) => { state.formSuite = event.target.value; });
    ["seed", "retries", "timeout", "scorer-version"].forEach((id) => { const input = $("#" + id); if (input) input.addEventListener("change", () => { updateParamsFromForm(); render(); }); });
    document.querySelectorAll("[data-health]").forEach((button) => button.addEventListener("click", () => healthCheck(button.dataset.health)));
    document.querySelectorAll("[data-health-config]").forEach((button) => button.addEventListener("click", () => healthConfig(button.dataset.healthConfig)));
    const start = $("#start-run"); if (start) start.addEventListener("click", startRun);
    document.querySelectorAll("[data-toolbar]").forEach((button) => button.addEventListener("click", () => toolbarAction(button.dataset.toolbar)));
    document.querySelectorAll('[data-action="reload"]').forEach((button) => button.addEventListener("click", loadData));
    document.querySelectorAll("[data-open-run]").forEach((button) => button.addEventListener("click", () => { state.selectedRun = null; state.selectedRunPath = button.dataset.openRun; setView("results"); loadSelectedRun(button.dataset.openRun); }));
    document.querySelectorAll("[data-artifact]").forEach((button) => button.addEventListener("click", () => { if (button.dataset.artifact) window.open(queryPath(button.dataset.artifact), "_blank", "noopener"); }));
    ["failure-agent", "failure-capability", "failure-type"].forEach((id) => { const input = $("#" + id); if (input) input.addEventListener("change", (event) => { const key = id === "failure-agent" ? "agent" : id === "failure-capability" ? "capability" : "failure"; state.filters[key] = event.target.value; render(); }); });
    const history = $("#history-filter"); if (history) history.addEventListener("input", (event) => { state.filters.history = event.target.value; render(); const field = $("#history-filter"); if (field) { field.focus(); field.setSelectionRange(field.value.length, field.value.length); } });
    document.querySelectorAll("[data-failure-index]").forEach((button) => button.addEventListener("click", () => openFailure(selectedFailure(button.dataset.failureIndex))));
     document.querySelectorAll("[data-result-tab]").forEach((button) => button.addEventListener("click", () => { const tab = button.dataset.resultTab; state.resultTab = tab; state.view = "results"; render(); }));
    document.querySelectorAll("[data-select-case]").forEach((button) => button.addEventListener("click", () => { state.selectedCase = button.dataset.selectCase; state.resultTab = "cases"; render(); }));
    document.querySelectorAll("[data-open-case-evidence]").forEach((button) => button.addEventListener("click", () => { const caseId = button.dataset.openCaseEvidence; const agents = normalizeAgents(state.selectedRun); const failed = filterFailures(collectFailures(agents)).find((item) => item.result.case_id === caseId); if (failed) return openFailure(failed); const summary = agents.find((agent) => (agent.results || []).some((result) => result.case_id === caseId)); const result = summary && (summary.results || []).find((item) => item.case_id === caseId); if (summary && result) return openFailure({ agent: summary.agent, result, failure: { type: result.status === "pass" ? "verified" : "invalid_behavior", reason: result.status === "pass" ? "该 Case 已通过确定性规则检查，继续查看 EvidenceEvent 记录。" : "该 Case 未通过，但未提供结构化失败原因。" }, agentSummary: summary }); showGlobalError("该 Case 没有可读取的证据事件"); }));
    document.querySelectorAll("[data-select-agent]").forEach((button) => button.addEventListener("click", () => { const path = button.dataset.selectAgent; if (!state.formPrimary) { state.formPrimary = path; state.formApiPrimary = (configByPath(path) || {}).api_profile || ""; } else { state.formComparison = path; state.formApiComparison = (configByPath(path) || {}).api_profile || ""; } setView("new"); }));
    document.querySelectorAll("[data-track]").forEach((button) => button.addEventListener("click", () => { state.formTrack = button.dataset.track; state.formPrimary = ""; state.formComparison = ""; state.formApiPrimary = ""; state.formApiComparison = ""; const defaults = defaultConfigPaths(state.formTrack); state.formPrimary = defaults[0] || ""; state.formComparison = defaults[1] || ""; state.formApiPrimary = (configByPath(state.formPrimary) || {}).api_profile || ""; state.formApiComparison = (configByPath(state.formComparison) || {}).api_profile || ""; setView("new"); render(); }));
    document.addEventListener("change", (event) => {
      const pane = event.target && event.target.getAttribute && event.target.getAttribute("data-api-pane");
      if (pane === "primary") state.formApiPrimary = event.target.value;
      if (pane === "comparison") state.formApiComparison = event.target.value;
    });
    document.querySelectorAll("[data-edit-profile]").forEach((button) => button.addEventListener("click", () => { state.editingProfileId = button.dataset.editProfile; setView("configs"); render(); }));
    document.querySelectorAll("[data-cancel-edit]").forEach((button) => button.addEventListener("click", () => { state.editingProfileId = null; setView("configs"); render(); }));
    document.querySelectorAll("[data-quick-agent]").forEach((input) => input.addEventListener("change", (event) => {
      const checked = Array.from(document.querySelectorAll("[data-quick-agent]:checked")).map((item) => item.value);
      if (checked.length > 2) {
        event.target.checked = false;
        state.quickNotice = { kind: "error", message: "快速对比一次只能选择两个 Agent。" };
        render();
        return;
      }
      state.quickSelected = checked;
      state.quickNotice = null;
      render();
    }));
    const quickStart = document.querySelector("[data-quick-start]");
    if (quickStart) quickStart.addEventListener("click", startQuickCompare);
    const quickAuto = document.querySelector("[data-quick-auto]");
    if (quickAuto) quickAuto.addEventListener("click", startQuickCompareAuto);
    document.querySelectorAll("[data-agent-detail]").forEach((button) => button.addEventListener("click", () => { state.agentDetailPath = button.dataset.agentDetail; render(); }));
    document.querySelectorAll("[data-provider-detail]").forEach((button) => button.addEventListener("click", () => { state.providerDetail = button.dataset.providerDetail; render(); }));
     document.querySelectorAll("[data-go-compare-tab]").forEach((button) => button.addEventListener("click", () => { state.resultTab = button.dataset.goCompareTab || "cases"; state.view = "results"; render(); }));
     document.querySelectorAll("[data-go-compare-case]").forEach((button) => button.addEventListener("click", () => { state.selectedCase = button.dataset.goCompareCase; state.resultTab = "cases"; state.view = "results"; render(); }));
    enhanceSelectMenus();
  }

  async function healthCheck(which) { const config = which === "primary" ? $("#primary-agent")?.value : $("#comparison-agent")?.value; if (!config) return; const target = $("#health-" + which); if (target) { target.textContent = "检查中…"; target.className = "health-state"; } try { const result = await api("/api/health", { method: "POST", body: JSON.stringify({ config }) }); state.health[config] = result; if (target) { target.innerHTML = healthStateMarkup(config, "尚未检查连接"); } } catch (error) { state.health[config] = { status: "error", error: error.message, checked_at: new Date().toISOString() }; if (target) { target.innerHTML = healthStateMarkup(config, "尚未检查连接"); } } }
  async function healthConfig(config) { const id = "#config-health-" + config.replace(/[^A-Za-z0-9]/g, "-"); const targets = [$(id), $("#provider-detail-health")].filter(Boolean); targets.forEach((target) => { target.textContent = "检查中…"; }); try { const result = await api("/api/health", { method: "POST", body: JSON.stringify({ config }) }); state.health[config] = result; targets.forEach((target) => { target.innerHTML = healthStateMarkup(config, credentialLabel(configByPath(config))); }); } catch (error) { state.health[config] = { status: "error", error: error.message, checked_at: new Date().toISOString() }; targets.forEach((target) => { target.innerHTML = healthStateMarkup(config, credentialLabel(configByPath(config))); }); } }
  async function startRun() {
    updateParamsFromForm();
    let primary = $("#primary-agent")?.value, comparison = $("#comparison-agent")?.value, suite = $("#suite")?.value;
    // 标签页可能是在服务重启期间启动的（数据未加载）——启动前自动重取一次
    if (!primary || !comparison || !suite || !(state.configs || []).length) {
      await loadData();
      primary = $("#primary-agent")?.value || primary;
      comparison = $("#comparison-agent")?.value || comparison;
      suite = $("#suite")?.value || suite;
    }
    if (!primary || !comparison || !suite) {
      showGlobalError("评测数据尚未加载（配置/套件为空）。请点击刷新配置或重新打开工作台后重试。");
      return;
    }
    const primaryConfig = configByPath(primary), comparisonConfig = configByPath(comparison);
    const apiProfiles = {};
    if (needsLlm(primaryConfig) && state.formApiPrimary) apiProfiles[primary] = state.formApiPrimary;
    if (needsLlm(comparisonConfig) && state.formApiComparison) apiProfiles[comparison] = state.formApiComparison;
    const payload = { primary_agent: primary, comparison_agent: comparison, suite, track: state.formTrack || "control", api_profiles: apiProfiles, seed: state.params.seed === "" ? null : Number(state.params.seed), retries: Number(state.params.retries), timeout: Number(state.params.timeout), scorer_version: state.params.scorer_version }; const button = $("#start-run"); if (button) button.disabled = true; try { state.job = await api("/api/runs", { method: "POST", body: JSON.stringify(payload) }); pollJob(state.job.id); render(); } catch (error) { showGlobalError(error.message); if (button) button.disabled = false; } }
  async function startQuickCompare() {
    const selected = (state.quickSelected || []).slice(0, 2);
    if (selected.length !== 2) {
      state.quickNotice = { kind: "error", message: "请选择两个已安装且可自动运行的 Agent。" };
      render();
      return;
    }
    await postQuickCompare({ agents: selected });
  }
  async function startQuickCompareAuto() {
    await postQuickCompare({ agents: [] });
  }
  async function postQuickCompare(payload) {
    const button = document.querySelector("[data-quick-start]");
    if (button) button.disabled = true;
    state.quickNotice = null;
    try {
      state.job = await api("/api/quick-compare", { method: "POST", body: JSON.stringify(payload) });
      render();
      pollJob(state.job.id);
    } catch (error) {
      state.quickNotice = { kind: "error", message: error.message };
      render();
    }
  }
  async function stopRun() { if (!state.job || !state.job.id || !["queued", "running", "stopping"].includes(state.job.status)) return; try { state.job = await api("/api/jobs/" + encodeURIComponent(state.job.id) + "/stop", { method: "POST", body: JSON.stringify({}) }); render(); } catch (error) { showGlobalError("停止评测失败：" + error.message); } }
  async function pollJob(id) { try { const job = await api("/api/jobs/" + encodeURIComponent(id)); state.job = job; if (["queued", "running", "stopping"].includes(job.status)) { render(); window.setTimeout(() => pollJob(id), 900); } else if (job.status === "completed") { state.selectedRun = null; state.selectedRunPath = job.result_path; if (job.kind === "quick_compare" && job.result_path) { setView("results"); await loadSelectedRun(job.result_path); } else render(); } else render(); } catch (error) { showGlobalError(error.message); } }

  function configCredentialCommand(envName) {
    const env = String(envName || "MY_API_KEY");
    return [
      "umask 077",
      "mkdir -p ~/.config/kmb && chmod 700 ~/.config/kmb",
      'read -rsp "' + env + ': " KMB_NEW_KEY; printf "\\n"',
      'tmp="$(mktemp ~/.config/kmb/credentials.XXXXXX)"',
      "grep -v '^" + env + "=' ~/.config/kmb/credentials.env 2>/dev/null > \"$tmp\" || true",
      "printf '" + env + "=%s\\n' \"$KMB_NEW_KEY\" >> \"$tmp\"",
      'chmod 600 "$tmp" && mv "$tmp" ~/.config/kmb/credentials.env',
      "unset KMB_NEW_KEY"
    ].join("\n");
  }
  function configWizardNotice() {
    const notice = state.configNotice;
    if (!notice) return "";
    if (notice.kind === "error") return '<div class="config-wizard-notice error" role="alert">' + escapeHtml(notice.message) + "</div>";
    const env = notice.env || state.configDraft.api_key_env || "MY_API_KEY";
    const command = configCredentialCommand(env);
    return '<div class="config-wizard-notice success" role="status"><strong>配置档案已保存</strong><span>' + escapeHtml(notice.message || "请在运行工作台的同一环境配置凭据，然后刷新页面。") + '</span><div class="credential-command"><pre>' + escapeHtml(command) + '</pre><button class="button small" data-copy-credential="' + escapeHtml(command) + '" type="button">复制安全命令</button></div><small>命令只读取隐藏输入并写入权限为 600 的用户级凭据文件；网页不会接收或保存 API Key。</small></div>';
  }
  function configWizardMarkup() {
    const draft = state.configDraft;
    const disabled = state.configSaving ? " disabled" : "";
    const editingId = state.editingProfileId;
    const wizardTitle = editingId ? "编辑 API 档案（" + editingId + "）" : "新增 API 配置档案";
    const wizardHelp = editingId
      ? "修改会立即对所有引用此档案的智能体与评测生效（单一事实来源）。"
      : "支持 OpenAI-compatible 的 Chat Completions 接口。只保存非敏感元数据，API Key 由运行环境安全加载；新增后所有需要 LLM 的智能体立即可选用。";
    return '<section id="config-create-panel" class="panel config-wizard"><div class="panel-header"><div><div class="eyebrow">ADD PROVIDER PROFILE</div><h3>' + escapeHtml(wizardTitle) + '</h3><p>' + escapeHtml(wizardHelp) + '</p></div></div><div class="panel-body"><form id="config-create-form" class="form-grid" autocomplete="off"><div class="field"><label for="config-profile-id">配置标识</label><input id="config-profile-id" name="profile_id" value="' + escapeHtml(draft.profile_id) + '" placeholder="例如 openrouter" pattern="[A-Za-z0-9][A-Za-z0-9_.-]{0,63}" required><span class="field-help">API 档案 id：智能体通过它引用此档案；只能使用英文、数字、点、下划线和连字符。</span></div><div class="field"><label for="config-provider">提供商（可选）</label><input id="config-provider" name="provider" value="' + escapeHtml(draft.provider) + '" placeholder="例如 OpenRouter" maxlength="120"><span class="field-help">用于配置列表分组，不会改变协议或请求方式。</span></div><div class="field"><label for="config-name">显示名称</label><input id="config-name" name="name" value="' + escapeHtml(draft.name) + '" placeholder="例如 OpenRouter · GPT-4.1 mini" maxlength="120" required></div><div class="field"><label for="config-base-url">Base URL</label><input id="config-base-url" name="base_url" type="url" value="' + escapeHtml(draft.base_url) + '" placeholder="https://api.example.com/v1" required><span class="field-help">不得在 URL 中写用户名、密码或 API Key。</span></div><div class="field"><label for="config-endpoint">接口路径</label><input id="config-endpoint" name="endpoint" value="' + escapeHtml(draft.endpoint) + '" placeholder="/chat/completions" required></div><div class="field"><label for="config-model">模型 ID</label><input id="config-model" name="model" value="' + escapeHtml(draft.model) + '" placeholder="provider-model-id" required></div><div class="field"><label for="config-api-key-env">API Key 环境变量名</label><input id="config-api-key-env" name="api_key_env" value="' + escapeHtml(draft.api_key_env) + '" placeholder="OPENROUTER_API_KEY" pattern="[A-Z][A-Z0-9_]{1,62}" required><span class="field-help">只填变量名，不填密钥值；建议以 API_KEY、TOKEN 或 SECRET 结尾。</span></div><div class="field"><label for="config-timeout">请求超时（秒）</label><input id="config-timeout" name="timeout_seconds" type="number" min="1" max="900" step="1" value="' + escapeHtml(draft.timeout_seconds) + '" required></div><div class="field"><label for="config-temperature">Temperature</label><input id="config-temperature" name="temperature" type="number" min="0" max="2" step="0.1" value="' + escapeHtml(draft.temperature) + '" required></div><div class="field full"><label for="config-description">说明（可选）</label><input id="config-description" name="description" maxlength="500" value="' + escapeHtml(draft.description) + '" placeholder="例如公司内部 OpenAI-compatible 网关"></div><div class="full wizard-actions"><button class="button primary" id="config-create-submit" type="submit"' + disabled + '>' + (state.configSaving ? "保存中…" : "保存配置档案") + '</button><span class="field-help">保存后可在新建评测中选择该档案，并从配置卡片发起连接检查。</span></div></form>' + configWizardNotice() + '</div></section>';
  }
  function bindConfigWizard() {
    const form = $("#config-create-form");
    if (!form) return;
    form.addEventListener("input", (event) => {
      if (event.target && event.target.name && Object.prototype.hasOwnProperty.call(state.configDraft, event.target.name)) state.configDraft[event.target.name] = event.target.value;
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      state.configDraft = Object.assign({}, state.configDraft, payload);
      state.configSaving = true;
      state.configNotice = null;
      const button = $("#config-create-submit");
      if (button) { button.disabled = true; button.textContent = "保存中…"; }
      try {
        const editingId = state.editingProfileId;
        const target = editingId ? "/api/profiles/" + encodeURIComponent(editingId) + "/update" : "/api/profiles";
        const result = await api(target, { method: "POST", body: JSON.stringify(payload) });
        state.configNotice = {
          kind: "success",
          message: editingId
            ? "API 档案已更新：所有引用它的智能体与评测立即按新配置解析（智能体文件不受影响）。"
            : "API 档案已保存：所有需要 LLM 的智能体立即可选用此档案（不再生成或改写智能体文件）。",
        };
        state.configDraft = Object.assign({}, state.configDraft, { profile_id: "", provider: "", name: "", model: "", api_key_env: "", description: "" });
        state.editingProfileId = null;
        state.configSaving = false;
        await loadData();
      } catch (error) {
        state.configNotice = { kind: "error", message: error.message };
        state.configSaving = false;
        render();
      }
    });
    document.querySelectorAll("[data-copy-credential]").forEach((button) => button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copyCredential || "");
        button.textContent = "已复制";
      } catch (error) {
        button.textContent = "复制失败";
      }
    }));
  }
  function enhanceConfigView() {
    if (state.view !== "configs") return;
    const root = $("#view-root");
    if (!root || root.querySelector("#config-create-panel")) return;
    const sectionDescription = root.querySelector(".section-head p");
    // keep generated copy
    const secondarySummary = root.querySelector(".secondary-profiles summary");
    if (secondarySummary && !secondarySummary.textContent.startsWith("其他 API、")) secondarySummary.textContent = secondarySummary.textContent.replace("本地基线与接入模板", "其他 API、本地基线与接入模板");
    root.insertAdjacentHTML("beforeend", configWizardMarkup());
    bindConfigWizard();
  }

  const legacyRefreshButton = $("#refresh-button");
  if (legacyRefreshButton) legacyRefreshButton.addEventListener("click", loadData);
  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#drawer-backdrop").addEventListener("click", closeDrawer);
  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  loadData();
}());

