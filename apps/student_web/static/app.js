const state = {
  users: [],
  authenticated: false,
  activeUser: null,
  activeUserId: 0,
  selectedExam: localStorage.getItem("aieyu.practiceExam") || localStorage.getItem("aieyu.selectedExam") || "TEM8_RU",
  selectedWordExam: localStorage.getItem("aieyu.wordExam") || "TEM8_RU",
  activeView: localStorage.getItem("aieyu.activeView") || "study",
  quiz: null,
  result: null,
  explanation: null,
  profile: null,
  studyCenter: null,
  wrongbook: null,
  wrongbookSelected: new Set(),
  wrongbookFilters: { status: "all", type: "all", knowledge: "all", search: "" },
  wordStatus: null,
  wordReviewPool: null,
  wordSession: null,
  currentWordIndex: 0,
  wordSessionStats: null,
  latestThreadId: 1,
  selectionTranslation: { requestId: 0, text: "", context: "", interacting: false },
};

const $ = (selector) => document.querySelector(selector);

const DIAGNOSTIC_TYPES = ["grammar_choice", "literature_choice", "culture_choice", "reading_choice"];
const TYPE_ORDER = [
  ["grammar_choice", "语法"],
  ["literature_choice", "文学"],
  ["culture_choice", "国情"],
  ["reading_choice", "阅读"],
];

const WORD_RESULT_LABELS = {
  unknown: "不认识",
  fuzzy: "模糊",
  known: "认识",
};

function optionLabel(item) {
  return `${item.key}. ${item.text}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function queryForActiveUser(scope = "practice") {
  const exam = scope === "words" ? currentWordExam() : currentExam();
  return new URLSearchParams({ exam_system: exam.system, level: exam.level }).toString();
}

function currentExam() {
  return state.selectedExam === "TEM4_RU"
    ? { system: "TEM4_RU", level: "TEM4", label: "俄语专四" }
    : { system: "TEM8_RU", level: "TEM8", label: "俄语专八" };
}

function currentWordExam() {
  return state.selectedWordExam === "TEM4_RU"
    ? { system: "TEM4_RU", level: "TEM4", label: "俄语专四" }
    : { system: "TEM8_RU", level: "TEM8", label: "俄语专八" };
}

function selectionContext(element, selectedText) {
  const container = element.closest(
    ".passage-body, .question, .wrongbook-item, .question-explanation, .word-card, .thread, .results, .page",
  );
  const text = String(container?.innerText || selectedText).replace(/\s+/g, " ").trim();
  const position = text.toLocaleLowerCase("ru").indexOf(selectedText.toLocaleLowerCase("ru"));
  if (position < 0 || text.length <= 500) return text.slice(0, 500);
  const start = Math.max(position - 220, 0);
  const end = Math.min(position + selectedText.length + 220, text.length);
  return text.slice(start, end);
}

function hideSelectionTranslator() {
  $("#selectionTranslator").classList.add("hidden");
}

function placeSelectionTranslator(rect) {
  const panel = $("#selectionTranslator");
  const width = 340;
  const left = Math.max(12, Math.min(rect.left, window.innerWidth - width - 12));
  const top = Math.min(rect.bottom + 10, window.innerHeight - 180);
  panel.style.left = `${left}px`;
  panel.style.top = `${Math.max(top, 12)}px`;
}

function renderSelectionTranslation(payload) {
  const body = $("#translatorBody");
  if (payload.requires_ai_confirmation) {
    body.innerHTML = `
      <p class="translator-empty">本地词库暂未收录这个词或短语。</p>
      <p class="translator-notice">${escapeHtml(payload.ai_notice || "将选中内容和所在句子发送给 DeepSeek 进行语境翻译。")}</p>
      <button type="button" class="primary translator-ai-btn" data-translate-with-ai>使用 AI 语境翻译</button>
    `;
    return;
  }
  const details = [payload.lemma, payload.part_of_speech].filter(Boolean).join(" · ");
  body.innerHTML = `
    ${details ? `<p class="translator-meta">${escapeHtml(details)}</p>` : ""}
    ${payload.context_meaning_zh ? `<div class="translator-context"><span>本句含义</span><strong>${escapeHtml(payload.context_meaning_zh)}</strong></div>` : ""}
    ${payload.meaning_zh ? `<p class="translator-meaning">${escapeHtml(payload.meaning_zh)}</p>` : ""}
    ${payload.note_zh ? `<p class="translator-note">${escapeHtml(payload.note_zh)}</p>` : ""}
    <div class="translator-source">${escapeHtml(payload.source_label || "翻译结果")}${payload.matched_by_morphology ? " · 已还原词形" : ""}${payload.cached ? " · 已缓存" : ""}</div>
  `;
}

async function translateCurrentSelection(allowAi = false) {
  const current = state.selectionTranslation;
  if (!current.text || !state.authenticated) return;
  const requestId = ++current.requestId;
  $("#translatorBody").innerHTML = `<div class="translator-loading"><span class="loader"></span><span>${allowAi ? "正在进行语境翻译..." : "正在查询词库..."}</span></div>`;
  try {
    const exam = currentExam();
    const payload = await requestJson("/api/translate-selection", {
      method: "POST",
      body: JSON.stringify({
        selected_text: current.text,
        context: current.context,
        exam_system: exam.system,
        level: exam.level,
        allow_ai: allowAi,
      }),
    });
    if (requestId !== current.requestId) return;
    renderSelectionTranslation(payload);
  } catch (error) {
    if (requestId !== current.requestId) return;
    $("#translatorBody").innerHTML = `<p class="translator-error">${escapeHtml(error.message)}</p>`;
  }
}

function inspectTextSelection() {
  if (state.selectionTranslation.interacting || !state.authenticated) return;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    hideSelectionTranslator();
    return;
  }
  const rawText = selection.toString().replace(/\s+/g, " ").trim();
  const selectedText = rawText.replace(/^[.,!?;:()\[\]{}<>"'«»„“”`—–…]+|[.,!?;:()\[\]{}<>"'«»„“”`—–…]+$/g, "");
  if (!selectedText || selectedText.length > 80 || selectedText.split(/\s+/).length > 6 || !/[А-Яа-яЁё]/.test(selectedText)) {
    hideSelectionTranslator();
    return;
  }
  const anchor = selection.anchorNode?.nodeType === Node.ELEMENT_NODE
    ? selection.anchorNode
    : selection.anchorNode?.parentElement;
  if (!anchor?.closest(".pagearea") || anchor.closest("input, textarea, select, button, .selection-translator")) {
    hideSelectionTranslator();
    return;
  }
  const rect = selection.getRangeAt(0).getBoundingClientRect();
  if (!rect.width && !rect.height) return;
  state.selectionTranslation.text = selectedText;
  state.selectionTranslation.context = selectionContext(anchor, selectedText);
  $("#translatorWord").textContent = selectedText;
  placeSelectionTranslator(rect);
  $("#selectionTranslator").classList.remove("hidden");
  translateCurrentSelection(false);
}

let selectionTimer = 0;
function scheduleSelectionInspection() {
  window.clearTimeout(selectionTimer);
  selectionTimer = window.setTimeout(inspectTextSelection, 280);
}

function examDescription(exam, status) {
  const typeNames = (status.question_types || []).map((item) => item.name).join("、");
  if (exam.system === "TEM4_RU") {
    return `${typeNames || "语法、国情、阅读"} · 阅读题按文章整组展示`;
  }
  return `${typeNames || "语法、文学、国情、阅读"} · 已审核题库`;
}

function renderExamOverview(status) {
  const exam = currentExam();
  $("#examOverviewTitle").textContent = exam.label;
  $("#examOverviewDescription").textContent = examDescription(exam, status);
  $("#examPoolCount").textContent = status.question_count;
  $("#examYearCount").textContent = (status.years || []).length;
  $("#examTypeCount").textContent = (status.question_types || []).length;
}

function renderExamContext() {
  const practiceExam = currentExam();
  const wordExamSelection = currentWordExam();
  document.querySelectorAll("[data-exam-system]").forEach((button) => {
    const exam = button.dataset.examScope === "words" ? wordExamSelection : practiceExam;
    const active = button.dataset.examSystem === exam.system;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  const brand = document.querySelector("#brandExamLabel");
  if (brand) brand.textContent = `${practiceExam.label}练习`;
  const wordExamLabel = document.querySelector("#wordExamLabel");
  if (wordExamLabel) wordExamLabel.textContent = wordExamSelection.label;
  const title = document.querySelector("#practiceTitle");
  if (title) title.textContent = `今日${practiceExam.label}训练`;
  const diagnosticDescription = document.querySelector("#diagnosticDescription");
  if (diagnosticDescription) {
    diagnosticDescription.textContent = practiceExam.system === "TEM4_RU"
      ? "覆盖语法、国情和阅读，用于建立第一版能力画像。"
      : "覆盖语法、文学、国情和阅读，用于建立第一版能力画像。";
  }
}
function showView(view) {
  const nextView = ["study", "practice", "words", "wrongbook"].includes(view) ? view : "study";
  state.activeView = nextView;
  localStorage.setItem("aieyu.activeView", nextView);
  for (const page of document.querySelectorAll(".page")) {
    page.classList.toggle("active", page.id === `${nextView}Page`);
  }
  for (const button of document.querySelectorAll(".navbtn")) {
    button.classList.toggle("active", button.dataset.view === nextView);
  }
  if (nextView === "wrongbook") {
    loadWrongbook();
  }
  if (nextView === "words") {
    loadWordStatus();
  }
  if (nextView === "study") {
    loadStudyCenter();
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "请求失败");
  }
  return payload;
}

function renderStatus(status) {
  state.latestThreadId = status.latest_thread?.id || 1;
  renderExamOverview(status);
  $("#statusSummary").innerHTML = `
    <p><strong>${status.question_count}</strong> 道已审核题</p>
    <p>${status.years.map((item) => `${item.year} 年 ${item.count} 题`).join(" · ")}</p>
    <p>解析服务：${status.deepseek_configured ? "已连接" : "未连接"}</p>
  `;

  const typeControls = $("#typeControls");
  typeControls.innerHTML = status.question_types
    .map((item) => {
      const checked = item.code === "reading_choice" ? "" : "checked";
      return `
        <label class="chip">
          <input type="checkbox" name="questionType" value="${item.code}" ${checked} />
          <span>${item.name} ${item.count}</span>
        </label>
      `;
    })
    .join("");

  const yearControls = $("#yearControls");
  yearControls.innerHTML = status.years
    .map(
      (item) => `
        <label class="chip">
          <input type="checkbox" name="year" value="${item.year}" checked />
          <span>${item.year}</span>
        </label>
      `
    )
    .join("");
}

function clearStudentState() {
  state.quiz = null;
  state.result = null;
  state.explanation = null;
  state.studyCenter = null;
  state.wrongbook = null;
  state.wrongbookSelected.clear();
  state.wordStatus = null;
  state.wordReviewPool = null;
  state.wordSession = null;
  state.currentWordIndex = 0;
  state.wordSessionStats = null;
  state.latestThreadId = null;
  $("#emptyState").classList.remove("hidden");
  $("#quizForm").classList.add("hidden");
  $("#quizMeta").textContent = "尚未生成练习";
  $("#quizProgressWrap").classList.add("hidden");
  $("#quizProgressBar").style.width = "0%";
  $("#quizProgressText").textContent = "0/0 已作答";
  $("#resultBox").classList.add("muted");
  $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "批改后自动生成薄弱点、复习方案和可追问问题。";
  $("#wordCard").classList.add("hidden");
  $("#wordEmpty").classList.remove("hidden");
  resetWordEmpty();
  $("#wordSessionMeta").textContent = "尚未开始";
  $("#reviewPoolBox").classList.add("muted");
  $("#reviewPoolBox").textContent = "请先登录后查看复习词库。";
  $("#reviewPoolMeta").textContent = "未登录";
  $("#startReviewWordsBtn").disabled = true;
  $("#todayTasks").classList.add("muted");
  $("#todayTasks").textContent = "请先登录后查看今日学习安排。";
  $("#todayPlanMeta").textContent = "未登录";
  $("#periodSummary").classList.add("muted");
  $("#periodSummary").textContent = "登录后显示学习记录。";
  $("#dailyTrend").innerHTML = "";
  $("#studyTypeMastery").classList.add("muted");
  $("#studyTypeMastery").textContent = "登录后显示能力概览。";
  $("#knowledgeMap").classList.add("muted");
  $("#knowledgeMap").textContent = "登录后查看可练知识点。";
  $("#wrongbookStats").classList.add("muted");
  $("#wrongbookStats").textContent = "登录后显示错题概况。";
  updateWrongbookSelection();
}

function renderAuthStatus(payload) {
  state.authenticated = Boolean(payload.authenticated);
  state.activeUser = payload.user || null;
  state.activeUserId = state.activeUser ? Number(state.activeUser.id) : 0;
  $("#accountButtonName").textContent = state.activeUser
    ? `用户：${state.activeUser.display_name}`
    : "用户：未登录";
  $("#activeUserHint").textContent = state.activeUser
    ? `当前记录写入：${state.activeUser.display_name}`
    : "请先登录或注册。";
  $("#logoutBtn").classList.toggle("hidden", !state.authenticated);
  $("#loginBtn").classList.toggle("hidden", state.authenticated);
  $("#registerBtn").classList.toggle("hidden", state.authenticated);
  $("#authName").disabled = state.authenticated;
  $("#authPassword").disabled = state.authenticated;
  if (state.activeUser) {
    $("#authName").value = state.activeUser.display_name;
    $("#authPassword").value = "";
  }
}

async function loadAuthStatus() {
  const payload = await requestJson("/api/auth/status");
  renderAuthStatus(payload);
  if (!payload.authenticated) {
    clearStudentState();
  }
  return payload;
}

function authPayload() {
  return {
    display_name: $("#authName").value.trim(),
    password: $("#authPassword").value.trim(),
  };
}

async function submitAuth(mode) {
  const button = mode === "login" ? $("#loginBtn") : $("#registerBtn");
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = mode === "login" ? "登录中..." : "注册中...";
  try {
    const payload = await requestJson(`/api/auth/${mode}`, {
      method: "POST",
      body: JSON.stringify(authPayload()),
    });
    renderAuthStatus(payload);
    await refreshStudentData();
    closeAccountMenu();
  } catch (error) {
    $("#activeUserHint").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function logoutUser() {
  $("#logoutBtn").disabled = true;
  $("#logoutBtn").textContent = "退出中...";
  try {
    const payload = await requestJson("/api/auth/logout", { method: "POST", body: "{}" });
    renderAuthStatus(payload);
    clearStudentState();
    closeAccountMenu();
  } catch (error) {
    $("#activeUserHint").textContent = error.message;
  } finally {
    $("#logoutBtn").disabled = false;
    $("#logoutBtn").textContent = "退出登录";
  }
}

function openAccountMenu() {
  $("#accountDropdown").classList.remove("hidden");
}

function closeAccountMenu() {
  $("#accountDropdown").classList.add("hidden");
}

function toggleAccountMenu() {
  $("#accountDropdown").classList.toggle("hidden");
}

function masteryClass(status) {
  if (status === "strong" || status === "stable") return "good";
  if (status === "unstable" || status === "insufficient_data") return "mid";
  return "low";
}

function profileTypeOrder() {
  return state.selectedExam === "TEM4_RU"
    ? [["listening_choice", "听力"], ["grammar_choice", "语法"], ["culture_choice", "国情"], ["reading_choice", "阅读"]]
    : TYPE_ORDER;
}
function renderProfile(profile) {
  state.profile = profile;
  const byType = new Map((profile.question_type_mastery || []).map((item) => [item.target_code, item]));
  const items = profileTypeOrder().map(([code, name]) => {
    const item = byType.get(code);
    const score = item ? Number(item.mastery_score || 0) : 0;
    const status = item?.mastery_status || "insufficient_data";
    const statusZh = item?.mastery_status_zh || "数据不足";
    const attempts = item?.attempt_count || 0;
    return `
      <div class="mastery ${masteryClass(status)}">
        <div class="mastery-head">
          <strong>${name}</strong>
          <span>${attempts} 次</span>
        </div>
        <div class="meter" aria-label="${name}掌握度 ${score}">
          <span style="width: ${Math.max(score, 4)}%"></span>
        </div>
        <div class="mastery-foot">
          <span>${statusZh} · ${score} 分</span>
          <button type="button" class="textbtn" data-practice-type="${code}">只练此类</button>
        </div>
      </div>
    `;
  }).join("");

  const next = profile.next_training
    ? `
      <div class="profile-recommendation">
        <span>下一步训练</span>
        <strong>${escapeHtml(profile.next_training.target_name_zh)}</strong>
        <p>${profile.next_training.target_code.startsWith("grammar") ? "优先巩固语法、词汇与实际运用。" : "根据近期作答表现安排。"}</p>
        <button type="button" class="secondary" data-start-weakness>开始专项训练</button>
      </div>
    `
    : `<p class="profile-next">数据还不够，建议先完成入门诊断。</p>`;

  $("#profileSummary").classList.remove("muted");
  $("#profileSummary").innerHTML = `${items}${next}`;
}

async function loadProfile() {
  const profile = await requestJson(`/api/profile?${queryForActiveUser()}`);
  renderProfile(profile);
}

function wrongbookVisibleItems() {
  const items = state.wrongbook?.items || [];
  const filters = state.wrongbookFilters;
  const search = filters.search.trim().toLocaleLowerCase();
  return items.filter((item) => {
    if (filters.status === "favorite" && !item.is_favorite) return false;
    if (["pending", "corrected"].includes(filters.status) && item.status !== filters.status) return false;
    if (filters.type !== "all" && item.question_type !== filters.type) return false;
    if (filters.knowledge !== "all" && !(item.knowledge_points || []).some((point) => point.code === filters.knowledge)) return false;
    if (search && !`${item.stem} ${item.note_text || ""}`.toLocaleLowerCase().includes(search)) return false;
    return true;
  });
}

function updateWrongbookSelection() {
  const availableIds = new Set((state.wrongbook?.items || []).map((item) => Number(item.question_id)));
  for (const id of state.wrongbookSelected) {
    if (!availableIds.has(id)) state.wrongbookSelected.delete(id);
  }
  const count = state.wrongbookSelected.size;
  $("#reviewSelectedBtn").textContent = `重练已选 · ${count}`;
  $("#reviewSelectedBtn").disabled = count === 0;
  const pendingCount = state.wrongbook?.pending_count || 0;
  $("#reviewPendingBtn").disabled = pendingCount === 0;
  for (const checkbox of document.querySelectorAll("[data-wrongbook-select]")) {
    checkbox.checked = state.wrongbookSelected.has(Number(checkbox.dataset.wrongbookSelect));
  }
}

function renderWrongbookFilters(payload) {
  const typeSelect = $("#wrongbookTypeFilter");
  const knowledgeSelect = $("#wrongbookKnowledgeFilter");
  typeSelect.innerHTML = `<option value="all">全部题型</option>${(payload.filters?.question_types || [])
    .map((item) => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.name_zh)} · ${item.count}</option>`)
    .join("")}`;
  knowledgeSelect.innerHTML = `<option value="all">全部知识点</option>${(payload.filters?.knowledge_points || [])
    .filter((item) => item.category !== "reading")
    .map((item) => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.name_zh)} · ${item.count}</option>`)
    .join("")}`;
  typeSelect.value = [...typeSelect.options].some((option) => option.value === state.wrongbookFilters.type)
    ? state.wrongbookFilters.type
    : "all";
  knowledgeSelect.value = [...knowledgeSelect.options].some((option) => option.value === state.wrongbookFilters.knowledge)
    ? state.wrongbookFilters.knowledge
    : "all";
}

function renderWrongbookList() {
  const box = $("#wrongbookBox");
  const items = wrongbookVisibleItems();
  for (const button of document.querySelectorAll("[data-wrong-status]")) {
    const active = button.dataset.wrongStatus === state.wrongbookFilters.status;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  }
  if (!items.length) {
    box.classList.remove("muted");
    box.innerHTML = `<div class="wrongbook-empty"><strong>当前筛选下没有错题</strong><p class="mini">可以切换状态、题型或知识点继续查看。</p></div>`;
    updateWrongbookSelection();
    return;
  }

  box.classList.remove("muted");
  box.innerHTML = `
    <div class="wrongbook-list">
      ${items.map((item) => {
        const source = item.source?.label || `${item.source?.year || ""} 年真题`;
        const knowledgePoints = (item.knowledge_points || []).filter((point) => point.category !== "reading");
        const tags = item.question_type === "reading_choice"
          ? [{ code: "reading", name_zh: "阅读理解" }]
          : knowledgePoints;
        const passage = item.passage?.body
          ? `<div class="passage"><div class="passage-head"><strong>${escapeHtml(item.passage.title || "阅读文章")}</strong><span>原文</span></div><div class="passage-body">${escapeHtml(item.passage.body)}</div></div>`
          : "";
        return `
          <article class="wrongbook-item ${item.status}" data-wrongbook-id="${item.question_id}">
            <div class="wrongbook-head">
              <div class="wrongbook-heading">
                <label class="wrongbook-select">
                  <input type="checkbox" data-wrongbook-select="${item.question_id}" />
                  <span>选择</span>
                </label>
                <strong>${escapeHtml(item.status_zh)}</strong>
                <span>${escapeHtml(item.question_type_name)} · ${escapeHtml(source)}</span>
                ${item.is_repeat_wrong ? `<span class="wrongbook-alert">反复错 ${item.wrong_count} 次</span>` : ""}
              </div>
              <button class="favorite-btn ${item.is_favorite ? "active" : ""}" type="button" data-wrongbook-favorite="${item.question_id}" aria-label="${item.is_favorite ? "取消收藏" : "收藏错题"}" title="${item.is_favorite ? "取消收藏" : "收藏错题"}">${item.is_favorite ? "★" : "☆"}</button>
            </div>
            <div class="wrongbook-tags">
              ${tags.map((point) => `<span class="wrongbook-tag">${escapeHtml(point.name_zh)}</span>`).join("")}
            </div>
            <p class="wrongbook-stem">${escapeHtml(item.stem)}</p>
            <p class="wrongbook-history">最近作答 ${escapeHtml(item.selected_answer || "未作答")} · 累计作答 ${item.seen_count} 次 · 答错 ${item.wrong_count} 次</p>
            <details class="wrongbook-detail">
              <summary>查看选项与复盘笔记</summary>
              ${passage}
              <div class="wrongbook-options">
                ${(item.options || []).map((option) => {
                  const optionClass = option.key === item.correct_answer
                    ? "correct"
                    : option.key === item.selected_answer && item.selected_answer !== item.correct_answer
                      ? "selected-wrong"
                      : "";
                  return `<p class="wrongbook-option ${optionClass}"><strong>${escapeHtml(option.key)}.</strong> ${escapeHtml(option.text)}</p>`;
                }).join("")}
              </div>
              <p class="mini">你的最近答案：${escapeHtml(item.selected_answer || "未作答")} · 正确答案：${escapeHtml(item.correct_answer)}</p>
              <div class="wrongbook-note">
                <label for="wrongbookNote${item.question_id}">我的复盘笔记</label>
                <textarea id="wrongbookNote${item.question_id}" rows="3" maxlength="1000" placeholder="记录错因、规则或仍不理解的地方">${escapeHtml(item.note_text || "")}</textarea>
                <div class="wrongbook-note-actions">
                  <span class="mini" data-wrongbook-save-status="${item.question_id}"></span>
                  <button type="button" class="secondary" data-wrongbook-save="${item.question_id}">保存笔记</button>
                </div>
              </div>
            </details>
          </article>
        `;
      }).join("")}
    </div>
  `;
  updateWrongbookSelection();
}

function renderWrongbook(payload) {
  state.wrongbook = payload;
  state.wrongbookSelected.clear();
  if (!payload.items || !payload.items.length) {
    $("#wrongbookBox").classList.remove("muted");
    $("#wrongbookBox").innerHTML = `<div class="wrongbook-empty"><strong>还没有错题</strong><p class="mini">完成练习后，答错的题会自动进入这里。</p></div>`;
    $("#wrongbookMeta").textContent = "0 道";
    $("#wrongbookStats").classList.add("muted");
    $("#wrongbookStats").textContent = "完成一次练习后显示错题概况。";
    renderWrongbookFilters(payload);
    updateWrongbookSelection();
    return;
  }

  $("#wrongbookMeta").textContent = `${payload.pending_count} 道待巩固 · ${payload.corrected_count} 道已订正`;
  $("#wrongbookStats").classList.remove("muted");
  $("#wrongbookStats").innerHTML = `
    <div class="wrongbook-stat"><strong>${payload.count}</strong><span>累计错题</span></div>
    <div class="wrongbook-stat"><strong>${payload.pending_count}</strong><span>待巩固</span></div>
    <div class="wrongbook-stat"><strong>${payload.repeat_wrong_count}</strong><span>反复出错</span></div>
    <div class="wrongbook-stat"><strong>${payload.favorite_count}</strong><span>已收藏</span></div>
  `;
  renderWrongbookFilters(payload);
  renderWrongbookList();
}

async function loadWrongbook() {
  if (!state.authenticated) {
    $("#wrongbookBox").classList.add("muted");
    $("#wrongbookBox").textContent = "请先登录后查看错题本。";
    $("#wrongbookMeta").textContent = "未登录";
    return;
  }
  const payload = await requestJson(`/api/wrongbook?${queryForActiveUser()}`);
  renderWrongbook(payload);
}

async function saveWrongbookPreference(questionId, favoriteOverride = null) {
  const item = (state.wrongbook?.items || []).find((entry) => Number(entry.question_id) === Number(questionId));
  if (!item) return;
  const note = $(`#wrongbookNote${questionId}`)?.value ?? item.note_text ?? "";
  const isFavorite = favoriteOverride === null ? Boolean(item.is_favorite) : Boolean(favoriteOverride);
  const statusBox = document.querySelector(`[data-wrongbook-save-status="${questionId}"]`);
  if (statusBox) statusBox.textContent = "保存中...";
  try {
    const result = await requestJson("/api/wrongbook/item", {
      method: "POST",
      body: JSON.stringify({ question_id: Number(questionId), note_text: note, is_favorite: isFavorite }),
    });
    item.note_text = result.note_text;
    item.is_favorite = result.is_favorite;
    await loadWrongbook();
  } catch (error) {
    if (statusBox) statusBox.textContent = error.message;
  }
}

async function startWrongbookReview(questionIds = []) {
  if (!state.authenticated) return;
  const pendingIds = (state.wrongbook?.items || [])
    .filter((item) => item.status === "pending")
    .map((item) => Number(item.question_id));
  const selectedIds = questionIds.length ? questionIds : pendingIds.slice(0, 50);
  if (!selectedIds.length) return;
  const button = questionIds.length ? $("#reviewSelectedBtn") : $("#reviewPendingBtn");
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "正在准备...";
  try {
    state.quiz = await requestJson("/api/quiz", {
      method: "POST",
      body: JSON.stringify({
        mode: "wrongbook_review",
        question_ids: selectedIds,
        count: selectedIds.length,
        exam_system: currentExam().system,
        level: currentExam().level,
        seed: Date.now(),
      }),
    });
    state.result = null;
    state.explanation = null;
    state.latestThreadId = null;
    showView("practice");
    renderQuiz(state.quiz);
    $("#resultBox").classList.add("muted");
    $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = "批改后自动生成错题讲解。";
  } catch (error) {
    $("#wrongbookBox").classList.remove("muted");
    $("#wrongbookBox").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = original;
    updateWrongbookSelection();
  }
}

function renderWordStatus(payload) {
  state.wordStatus = payload;
  $("#wordMeta").textContent = `${payload.reviewed_today} 个今日已打卡 · ${payload.review_pool_count || 0} 个复习词`;

  const statusRows = payload.by_status || [];
  $("#wordStats").classList.remove("muted");
  $("#wordStats").innerHTML = `
    <div class="word-stat-grid">
      <div><strong>${payload.total_words}</strong><span>正式词库</span></div>
      <div><strong>${payload.new_count}</strong><span>未开始</span></div>
      <div><strong>${payload.reviewed_today}</strong><span>今日打卡</span></div>
      <div><strong>${payload.due_count}</strong><span>待复习</span></div>
    </div>
    <div class="word-status-list">
      ${statusRows
        .map(
          (item) => `
            <p>
              <span>${escapeHtml(item.name_zh)}</span>
              <strong>${item.count}</strong>
            </p>
          `
        )
        .join("")}
    </div>
  `;
}

function renderWordReviewPool(payload) {
  state.wordReviewPool = payload;
  const words = payload.words || [];
  $("#reviewPoolMeta").textContent = `${payload.total} 个词`;
  $("#startReviewWordsBtn").disabled = !payload.total;
  if (!payload.total) {
    $("#reviewPoolBox").classList.add("muted");
    $("#reviewPoolBox").textContent = "暂无复习词。";
    return;
  }
  $("#reviewPoolBox").classList.remove("muted");
  $("#reviewPoolBox").innerHTML = `
    <div class="review-pool-list">
      ${words
        .slice(0, 12)
        .map(
          (word) => `
            <p class="review-pool-item">
              <strong>${escapeHtml(word.word)}</strong>
              <span>${escapeHtml(word.meaning_zh || "暂无释义")}</span>
            </p>
          `
        )
        .join("")}
    </div>
  `;
}

async function loadWordReviewPool() {
  if (!state.authenticated) {
    $("#reviewPoolBox").classList.add("muted");
    $("#reviewPoolBox").textContent = "请先登录后查看复习词库。";
    $("#reviewPoolMeta").textContent = "未登录";
    $("#startReviewWordsBtn").disabled = true;
    return;
  }
  try {
    const payload = await requestJson(`/api/words/review-pool?limit=80&${queryForActiveUser("words")}`);
    renderWordReviewPool(payload);
  } catch (error) {
    $("#reviewPoolBox").classList.add("muted");
    $("#reviewPoolBox").textContent = error.message;
    $("#reviewPoolMeta").textContent = "读取失败";
    $("#startReviewWordsBtn").disabled = true;
  }
}

async function loadWordStatus() {
  if (!state.authenticated) {
    $("#wordStats").classList.add("muted");
    $("#wordStats").textContent = "请先登录后开始单词打卡。";
    $("#wordMeta").textContent = "未登录";
    await loadWordReviewPool();
    return;
  }
  try {
    const payload = await requestJson(`/api/words/status?${queryForActiveUser("words")}`);
    renderWordStatus(payload);
    await loadWordReviewPool();
  } catch (error) {
    $("#wordStats").textContent = error.message;
    $("#wordMeta").textContent = "读取失败";
  }
}

function currentWord() {
  return state.wordSession?.words?.[state.currentWordIndex] || null;
}

function freshWordStats() {
  return { unknown: 0, fuzzy: 0, known: 0 };
}

function reviewedWordCount() {
  return (state.wordSession?.words || []).filter((word) => word.session_result).length;
}

function reviewHintForResult(result) {
  if (result === "known") return "已记录为认识。";
  if (result === "fuzzy") return "已记录为模糊。";
  if (result === "unknown") return "已记录为不认识。";
  return "";
}

function resetWordFeedbackForm() {
  $("#wordFeedbackForm").classList.add("hidden");
  $("#wordFeedbackText").value = "";
  $("#submitWordFeedbackBtn").disabled = false;
  $("#submitWordFeedbackBtn").textContent = "提交报错";
}

function setWordActionLoading(isLoading) {
  for (const button of document.querySelectorAll("[data-word-result]")) {
    button.disabled = isLoading;
  }
  $("#prevWordBtn").disabled = isLoading;
  $("#nextWordBtn").disabled = isLoading;
  $("#markWordWrongBtn").disabled = isLoading;
}

function setWordActionDisabled(isDisabled) {
  for (const button of document.querySelectorAll("[data-word-result]")) {
    button.disabled = isDisabled;
  }
}

function resetWordEmpty() {
  $("#wordEmpty").innerHTML = `
    <h2>开始一次单词打卡</h2>
    <p>优先复习到期词，不够时自动补充新词。</p>
  `;
  $("#wordSessionSummary").classList.add("hidden");
  $("#wordSessionSummary").innerHTML = "";
}

function renderWordSummary() {
  const stats = state.wordSessionStats || freshWordStats();
  const total = state.wordSession?.words?.length || 0;
  $("#wordCard").classList.add("hidden");
  $("#wordEmpty").classList.add("hidden");
  $("#wordSessionSummary").classList.remove("hidden");
  $("#wordSessionMeta").textContent = `完成 ${reviewedWordCount()}/${total}`;
  $("#wordSessionSummary").innerHTML = `
    <h2>本次打卡完成</h2>
    <div class="word-summary-grid">
      <div><strong>${stats.known}</strong><span>认识</span></div>
      <div><strong>${stats.fuzzy}</strong><span>模糊</span></div>
      <div><strong>${stats.unknown}</strong><span>不认识</span></div>
    </div>
    <button class="secondary" type="button" data-word-summary-prev>回到上一词</button>
  `;
}

function shouldShowSummary() {
  const words = state.wordSession?.words || [];
  return words.length > 0 && state.currentWordIndex >= words.length && words.every((word) => word.session_result);
}

function renderCurrentWord() {
  const words = state.wordSession?.words || [];
  const word = currentWord();
  if (shouldShowSummary()) {
    renderWordSummary();
    return;
  }
  if (!word) {
    $("#wordCard").classList.add("hidden");
    $("#wordEmpty").classList.remove("hidden");
    $("#wordSessionSummary").classList.add("hidden");
    $("#wordEmpty").innerHTML = `
      <h2>${words.length ? "本次打卡完成" : "暂无可打卡单词"}</h2>
      <p>${words.length ? "今天的记录已经写入当前学生账号。" : "当前没有可抽取的已审核单词。"}</p>
    `;
    $("#wordSessionMeta").textContent = words.length ? `完成 ${words.length}/${words.length}` : "无单词";
    return;
  }

  $("#wordEmpty").classList.add("hidden");
  $("#wordSessionSummary").classList.add("hidden");
  $("#wordCard").classList.remove("hidden");
  $("#wordIndex").textContent = `${state.currentWordIndex + 1}/${words.length}`;
  $("#wordProgressTag").textContent = word.progress_status_zh || "未开始";
  const resultLabel = WORD_RESULT_LABELS[word.session_result];
  $("#wordResultTag").classList.toggle("hidden", !resultLabel);
  $("#wordResultTag").textContent = resultLabel ? `已记录：${resultLabel}` : "";
  $("#wordText").textContent = word.word;
  resetWordFeedbackForm();
  $("#wordPart").textContent = [word.part_of_speech, word.source_page ? `来源页 ${word.source_page}` : ""]
    .filter(Boolean)
    .join(" · ");
  const hasReviewed = Boolean(word.session_result);
  $("#wordMeaning").classList.toggle("hidden", !hasReviewed);
  $("#wordMeaning").innerHTML = hasReviewed
    ? `<strong>词义</strong><p>${escapeHtml(word.meaning_zh || "暂无释义")}</p>`
    : "";
  const examples = word.examples || [];
  $("#wordExamples").classList.toggle("hidden", !hasReviewed || examples.length === 0);
  $("#wordExamples").innerHTML = examples.length
    ? `
      <strong>例句</strong>
      ${examples.map((example) => `<p>${escapeHtml(example)}</p>`).join("")}
    `
    : "";
  $(".word-actions").classList.toggle("hidden", hasReviewed);
  $(".word-nav").classList.toggle("hidden", !hasReviewed);
  $("#wordHint").textContent = hasReviewed
    ? reviewHintForResult(word.session_result)
    : "先判断自己是否认识这个词。选择后会显示释义。";
  const done = reviewedWordCount();
  $("#wordSessionMeta").textContent = `${done}/${words.length} 已处理`;
  $("#wordProgressBar").style.width = `${Math.round((done / Math.max(words.length, 1)) * 100)}%`;
  setWordActionLoading(false);
  setWordActionDisabled(hasReviewed);
  $("#prevWordBtn").disabled = state.currentWordIndex <= 0;
  $("#nextWordBtn").textContent = state.currentWordIndex >= words.length - 1 ? "完成本次" : "下一词";
  $("#nextWordBtn").disabled = !hasReviewed;
  $("#markWordWrongBtn").disabled = !hasReviewed || word.session_result === "unknown";
}

async function startWordSession(mode = "mixed") {
  if (!state.authenticated) {
    openAccountMenu();
    $("#activeUserHint").textContent = "请先登录或注册，再开始单词打卡。";
    return;
  }
  $("#startWordsBtn").disabled = true;
  $("#startWordsBtn").textContent = "抽取中...";
  resetWordEmpty();
  try {
    const payload = await requestJson("/api/words/session", {
      method: "POST",
      body: JSON.stringify({
        count: Number($("#wordCountInput").value || 20),
        mode,
        exam_system: currentWordExam().system,
        level: currentWordExam().level,
      }),
    });
    state.wordSession = payload;
    state.currentWordIndex = 0;
    state.wordSessionStats = freshWordStats();
    if (payload.status) {
      renderWordStatus(payload.status);
    }
    await loadWordReviewPool();
    renderCurrentWord();
  } catch (error) {
    $("#wordHint").textContent = error.message;
  } finally {
    $("#startWordsBtn").disabled = false;
    $("#startWordsBtn").textContent = "开始打卡";
  }
}

async function reviewCurrentWord(result) {
  const word = currentWord();
  if (!word) return;
  if (word.session_result) return;
  setWordActionLoading(true);
  $("#wordHint").textContent = "正在记录...";
  try {
    const payload = await requestJson("/api/words/review", {
      method: "POST",
      body: JSON.stringify({
        vocabulary_item_id: word.vocabulary_item_id,
        result,
        exam_system: currentWordExam().system,
        level: currentWordExam().level,
      }),
    });
    word.session_result = result;
    word.progress_status_zh = payload.word?.progress_status_zh || word.progress_status_zh;
    state.wordSessionStats[result] += 1;
    if (payload.status) {
      renderWordStatus(payload.status);
    }
    await loadWordReviewPool();
    renderCurrentWord();
  } catch (error) {
    $("#wordHint").textContent = error.message;
    setWordActionLoading(false);
  }
}

function showPreviousWord() {
  const words = state.wordSession?.words || [];
  if (!words.length) return;
  state.currentWordIndex = Math.max(0, state.currentWordIndex - 1);
  renderCurrentWord();
}

function showNextWord() {
  const words = state.wordSession?.words || [];
  if (!words.length) return;
  const word = currentWord();
  if (word && !word.session_result) return;
  state.currentWordIndex += 1;
  renderCurrentWord();
}

async function markCurrentWordWrong() {
  const word = currentWord();
  if (!word || !word.session_result || word.session_result === "unknown") return;
  const previousResult = word.session_result;
  setWordActionLoading(true);
  $("#wordHint").textContent = "正在改为不认识...";
  try {
    const payload = await requestJson("/api/words/review", {
      method: "POST",
      body: JSON.stringify({
        vocabulary_item_id: word.vocabulary_item_id,
        result: "unknown",
        previous_result: previousResult,
        correction: true,
        exam_system: currentWordExam().system,
        level: currentWordExam().level,
      }),
    });
    state.wordSessionStats[previousResult] = Math.max(0, state.wordSessionStats[previousResult] - 1);
    state.wordSessionStats.unknown += 1;
    word.session_result = "unknown";
    word.progress_status_zh = payload.word?.progress_status_zh || "学习中";
    if (payload.status) {
      renderWordStatus(payload.status);
    }
    await loadWordReviewPool();
    renderCurrentWord();
  } catch (error) {
    $("#wordHint").textContent = error.message;
    setWordActionLoading(false);
  }
}

function toggleWordFeedbackForm() {
  if (!currentWord()) return;
  $("#wordFeedbackForm").classList.toggle("hidden");
  if (!$("#wordFeedbackForm").classList.contains("hidden")) {
    $("#wordFeedbackText").focus();
  }
}

async function submitWordFeedback() {
  if (!state.authenticated) {
    openAccountMenu();
    $("#activeUserHint").textContent = "请先登录后提交单词报错。";
    return;
  }
  const word = currentWord();
  if (!word) return;
  const feedbackText = $("#wordFeedbackText").value.trim();
  if (!feedbackText) {
    $("#wordHint").textContent = "请先写一下这个单词哪里有问题。";
    return;
  }
  $("#submitWordFeedbackBtn").disabled = true;
  $("#submitWordFeedbackBtn").textContent = "提交中...";
  try {
    await requestJson("/api/words/feedback", {
      method: "POST",
      body: JSON.stringify({
        vocabulary_item_id: word.vocabulary_item_id,
        feedback_text: feedbackText,
      }),
    });
    $("#wordHint").textContent = "已收到单词报错，我会在词库清洗时优先处理。";
    resetWordFeedbackForm();
  } catch (error) {
    $("#wordHint").textContent = error.message;
    $("#submitWordFeedbackBtn").disabled = false;
    $("#submitWordFeedbackBtn").textContent = "提交报错";
  }
}

async function submitProductFeedback() {
  if (!state.authenticated) {
    openAccountMenu();
    $("#activeUserHint").textContent = "请先登录后提交建议。";
    return;
  }
  const feedbackText = $("#productFeedbackText").value.trim();
  if (!feedbackText) {
    $("#productFeedbackMeta").textContent = "请先填写";
    return;
  }
  $("#submitProductFeedbackBtn").disabled = true;
  $("#submitProductFeedbackBtn").textContent = "提交中...";
  try {
    await requestJson("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        page: state.activeView,
        feedback_text: feedbackText,
      }),
    });
    $("#productFeedbackText").value = "";
    $("#productFeedbackMeta").textContent = "已收到";
  } catch (error) {
    $("#productFeedbackMeta").textContent = error.message;
  } finally {
    $("#submitProductFeedbackBtn").disabled = false;
    $("#submitProductFeedbackBtn").textContent = "提交建议";
  }
}

async function refreshStudentData() {
  if (!state.authenticated) {
    $("#profileSummary").classList.add("muted");
    $("#profileSummary").textContent = "请先登录后查看能力画像。";
    $("#wrongbookBox").classList.add("muted");
    $("#wrongbookBox").textContent = "请先登录后查看错题本。";
    $("#wrongbookMeta").textContent = "未登录";
    $("#wordStats").classList.add("muted");
    $("#wordStats").textContent = "请先登录后开始单词打卡。";
    $("#wordMeta").textContent = "未登录";
    await loadWordReviewPool();
    return;
  }
  if (state.activeView === "study") {
    await loadStudyCenter();
  }
  try {
    await loadProfile();
  } catch (error) {
    $("#profileSummary").textContent = error.message;
  }
  try {
    await loadWrongbook();
  } catch (error) {
    $("#wrongbookBox").textContent = error.message;
  }
  if (state.activeView === "words") {
    await loadWordStatus();
  }
}

function selectOnlyQuestionType(code) {
  for (const input of document.querySelectorAll('input[name="questionType"]')) {
    input.checked = input.value === code;
  }
  $("#countInput").value = 10;
}

function selectedValues(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map((input) => input.value);
}

function setSubmitLoading(isLoading) {
  const button = $("#quizForm button[type='submit']");
  button.disabled = isLoading;
  button.textContent = isLoading ? "批改中..." : "提交批改";
  if (isLoading) {
    $("#answerHint").innerHTML = `<span class="loader"></span><span>正在批改中，讲解生成后会一起显示。</span>`;
  }
}

const KNOWLEDGE_CATEGORY_NAMES = {
  grammar: "语法与词汇",
  reading: "阅读理解",
  listening: "听力",
  literature: "俄罗斯文学",
  culture: "俄罗斯国情",
};

function percentageText(value) {
  return value === null || value === undefined ? "暂无" : `${Math.round(Number(value) * 100)}%`;
}

function renderStudyCenter(payload) {
  state.studyCenter = payload;
  const name = state.activeUser?.display_name || "同学";
  $("#studyGreeting").textContent = `${name}，今天从最需要的地方开始`;

  const tasks = payload.today.tasks || [];
  $("#todayPlanMeta").textContent = `${payload.today.completed_tasks}/${payload.today.task_count} 已完成`;
  $("#todayTasks").classList.remove("muted");
  $("#todayTasks").innerHTML = tasks.map((task, index) => {
    const unit = task.task_type === "words" ? "词" : "题";
    const progress = task.target ? Math.min(task.completed / task.target * 100, 100) : 100;
    const actionText = task.is_completed
      ? task.task_type === "wrongbook" ? "查看错题本" : "再练一组"
      : task.task_type === "words" ? "开始学习" : task.task_type === "wrongbook" ? "开始订正" : "开始训练";
    return `
      <article class="today-task ${task.is_completed ? "done" : ""}">
        <div class="task-index">${task.is_completed ? "✓" : index + 1}</div>
        <div class="task-copy">
          <strong>${escapeHtml(task.label)}${task.target_name_zh ? ` · ${escapeHtml(task.target_name_zh)}` : ""}</strong>
          <span>${escapeHtml(task.reason || "根据今日学习状态安排")}</span>
          <small>${task.target ? `${task.completed}/${task.target} ${unit}` : "今日无需处理"}${task.is_completed ? " · 已完成" : ""}</small>
        </div>
        <div class="task-progress" aria-label="完成 ${Math.round(progress)}%"><span style="width:${progress}%"></span></div>
        <button type="button" class="secondary" data-study-action="${escapeHtml(task.task_type)}" data-study-mode="${escapeHtml(task.mode || "")}" data-daily-task-id="${task.task_id}">${actionText}</button>
      </article>
    `;
  }).join("");

  const seven = payload.periods.seven_days;
  const thirty = payload.periods.thirty_days;
  $("#periodSummary").classList.remove("muted");
  $("#periodSummary").innerHTML = `
    <div><strong>${seven.attempted}</strong><span>近 7 天答题</span><small>${percentageText(seven.accuracy)} 正确率</small></div>
    <div><strong>${thirty.attempted}</strong><span>近 30 天答题</span><small>${percentageText(thirty.accuracy)} 正确率</small></div>
    <div><strong>${thirty.sessions}</strong><span>近 30 天练习</span><small>次完整提交</small></div>
  `;

  const maxAttempts = Math.max(...payload.daily_trend.map((item) => item.attempted), 1);
  $("#dailyTrend").innerHTML = payload.daily_trend.map((item) => {
    const date = new Date(`${item.date}T00:00:00`);
    const label = `${date.getMonth() + 1}/${date.getDate()}`;
    const height = Math.max(Math.round(item.attempted / maxAttempts * 100), item.attempted ? 8 : 2);
    return `
      <div class="trend-day" title="${label} · ${item.attempted} 题 · ${percentageText(item.accuracy)}">
        <div class="trend-bar"><span style="height:${height}%"></span></div>
        <strong>${item.attempted}</strong>
        <span>${label}</span>
      </div>
    `;
  }).join("");

  const byType = new Map((payload.question_type_mastery || []).map((item) => [item.target_code, item]));
  $("#studyTypeMastery").classList.remove("muted");
  $("#studyTypeMastery").innerHTML = profileTypeOrder().map(([code, name]) => {
    const item = byType.get(code);
    const score = Number(item?.mastery_score || 0);
    return `
      <div class="study-type-row">
        <div><strong>${name}</strong><span>${item?.mastery_status_zh || "数据不足"} · ${item?.attempt_count || 0} 题</span></div>
        <div class="meter"><span style="width:${Math.max(score, 3)}%"></span></div>
        <b>${score}</b>
      </div>
    `;
  }).join("");

  const grouped = new Map();
  for (const item of payload.knowledge_mastery || []) {
    if (!grouped.has(item.category)) grouped.set(item.category, []);
    grouped.get(item.category).push(item);
  }
  $("#knowledgeMap").classList.remove("muted");
  const categoryOrder = ["grammar", "reading", "listening", "literature", "culture"];
  const orderedGroups = Array.from(grouped.entries()).sort(
    ([left], [right]) => categoryOrder.indexOf(left) - categoryOrder.indexOf(right)
  );
  $("#knowledgeMap").innerHTML = orderedGroups.map(([category, items]) => `
    <section class="knowledge-group">
      <div class="knowledge-group-head">
        <h3>${escapeHtml(KNOWLEDGE_CATEGORY_NAMES[category] || category)}</h3>
        <span>${items.length} 个知识点</span>
      </div>
      <div class="knowledge-list">
        ${items.map((item) => `
          <button type="button" class="knowledge-item ${masteryClass(item.mastery_status)}" data-knowledge-code="${escapeHtml(item.target_code)}">
            <span><strong>${escapeHtml(item.target_name_zh)}</strong><small>${item.attempt_count} 次作答 · ${item.question_count} 道可练 · ${escapeHtml(item.mastery_status_zh)}</small></span>
            <b>${item.attempt_count ? item.mastery_score : "--"}</b>
          </button>
        `).join("")}
      </div>
    </section>
  `).join("");
}

async function loadStudyCenter() {
  if (!state.authenticated) {
    $("#todayTasks").classList.add("muted");
    $("#todayTasks").textContent = "请先登录后查看今日学习安排。";
    return;
  }
  try {
    renderStudyCenter(await requestJson(`/api/study-center?${queryForActiveUser()}`));
  } catch (error) {
    $("#todayTasks").classList.add("muted");
    $("#todayTasks").textContent = error.message;
  }
}

function updateQuizProgress() {
  const questions = state.quiz?.questions || [];
  if (!questions.length) {
    $("#quizProgressWrap").classList.add("hidden");
    return;
  }
  const answered = questions.filter((question) => document.querySelector(`input[name="q${question.quiz_number}"]:checked`)).length;
  const percentage = Math.round((answered / questions.length) * 100);
  $("#quizProgressWrap").classList.remove("hidden");
  $("#quizProgressBar").style.width = `${percentage}%`;
  $("#quizProgressText").textContent = `${answered}/${questions.length} 已作答`;
}

async function generateQuiz(mode = "random", targetCode = "", dailyTaskId = 0) {
  if (!state.authenticated) {
    openAccountMenu();
    $("#activeUserHint").textContent = "请先登录或注册，再开始练习。";
    return;
  }
  showView("practice");
  const regularButton = $("#generateBtn");
  const weaknessButton = document.querySelector("[data-start-weakness]");
  regularButton.disabled = true;
  regularButton.textContent = "生成中...";
  if (weaknessButton && mode === "weakness_review") {
    weaknessButton.disabled = true;
    weaknessButton.textContent = "正在准备...";
  }
  try {
    const payload = {
      count: ["weakness_review", "knowledge_point"].includes(mode)
        ? Number(state.profile?.next_training?.count || 10)
        : Number($("#countInput").value || 10),
      exam_system: currentExam().system,
      level: currentExam().level,
      seed: Date.now(),
      mode,
    };
    if (mode === "knowledge_point") {
      payload.target_code = targetCode;
    } else if (mode !== "weakness_review") {
      payload.question_types = selectedValues("questionType");
      payload.years = selectedValues("year").map(Number);
    }
    if (dailyTaskId) payload.daily_task_id = Number(dailyTaskId);
    state.quiz = await requestJson("/api/quiz", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.result = null;
    state.explanation = null;
    state.latestThreadId = null;
    renderQuiz(state.quiz);
    $("#resultBox").classList.add("muted");
    $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = "批改后自动生成薄弱点、复习方案和可追问问题。";
  } catch (error) {
    $("#resultBox").classList.remove("muted");
    $("#resultBox").textContent = error.message;
  } finally {
    regularButton.disabled = false;
    regularButton.textContent = "生成练习";
    if (weaknessButton) {
      weaknessButton.disabled = false;
      weaknessButton.textContent = "开始专项训练";
    }
  }
}

function renderQuiz(quiz) {
  $("#emptyState").classList.add("hidden");
  $("#quizForm").classList.remove("hidden");
  const quizLabel = quiz.mode === "diagnostic"
    ? "入门诊断"
    : quiz.mode === "weakness_review"
      ? `专项 · ${quiz.training?.target_name_zh || "薄弱点训练"}`
      : quiz.mode === "knowledge_point"
        ? `专项 · ${quiz.training?.target_name_zh || "知识点训练"}`
        : quiz.mode === "wrongbook_review"
          ? "错题重练"
      : currentExam().label;
  const fallbackLabel = quiz.training?.fallback_used ? " · 含同类补充" : "";
  $("#quizMeta").textContent = `${quiz.count} 题 · ${quizLabel}${fallbackLabel}`;
  $("#answerHint").textContent = "";

  const renderedPassages = new Set();
  $("#questionList").innerHTML = quiz.questions
    .map((question) => {
      let passage = "";
      if (question.passage) {
        const passageKey = question.passage.id || `${question.passage.title}-${question.passage.body}`;
        if (!renderedPassages.has(passageKey)) {
          renderedPassages.add(passageKey);
          passage = `<div class="passage"><div class="passage-head"><strong>${escapeHtml(question.passage.title || "阅读文章")}</strong><span>整篇文章</span></div><div class="passage-body">${escapeHtml(question.passage.body || "")}</div></div>`;
        }
      }
      return `
        <article class="question" data-question-id="${question.question_id}" data-quiz-number="${question.quiz_number}">
          <div class="qhead">
            <span class="badge">${escapeHtml(question.quiz_number)}</span>
            <span class="badge">${escapeHtml(question.question_type_name)}</span>
            <span class="source">${escapeHtml(question.source.label)} · 原题 ${escapeHtml(question.source.question_number)}</span>
          </div>
          ${passage}
          <p class="stem">${escapeHtml(question.stem)}</p>
          <div class="options">
            ${question.options
              .map(
                (option) => `
                  <label class="option" data-option="${escapeHtml(option.key)}">
                    <input type="radio" name="q${question.quiz_number}" value="${escapeHtml(option.key)}" />
                    <span>${escapeHtml(option.key)}. ${escapeHtml(option.text)}</span>
                  </label>
                `
              )
              .join("")}
          </div>
          <div class="question-explanation hidden" data-explanation-for="${question.quiz_number}"></div>
        </article>
      `;
    })
    .join("");
  for (const input of $("#questionList").querySelectorAll('input[type="radio"]')) {
    input.addEventListener("change", updateQuizProgress);
  }
  updateQuizProgress();
}

async function submitQuiz(event) {
  event.preventDefault();
  if (!state.quiz) return;

  const answers = state.quiz.questions.map((question) => {
    const selected = document.querySelector(`input[name="q${question.quiz_number}"]:checked`);
    return {
      quiz_number: question.quiz_number,
      question_id: question.question_id,
      selected_answer: selected?.value || "",
    };
  });

  setSubmitLoading(true);
  applyQuestionExplanations([]);
  $("#resultBox").classList.add("muted");
  $("#resultBox").textContent = "正在批改中...";
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "正在同步生成错题讲解...";
  try {
    const sessionMode = state.quiz.mode === "diagnostic"
      ? "mock_exam"
      : state.quiz.mode === "weakness_review"
        ? "weakness_review"
        : state.quiz.mode === "knowledge_point"
          ? "knowledge_point"
          : state.quiz.mode === "wrongbook_review"
            ? "weakness_review"
        : "random";
    state.result = await requestJson("/api/grade", {
      method: "POST",
      body: JSON.stringify({
        title: currentExam().label + " student practice",
        mode: sessionMode,
        exam_system: currentExam().system,
        level: currentExam().level,
        answers,
      }),
    });
    state.explanation = state.result.explanation || null;
    if (state.result.profile) {
      renderProfile(state.result.profile);
    }
    renderResult(state.result);
    markAnswers(state.result);
    renderExplanation(state.explanation, state.result.explanation_error);
    await loadWrongbook();
    $("#answerHint").textContent = "已批改";
  } catch (error) {
    $("#answerHint").textContent = error.message;
  } finally {
    setSubmitLoading(false);
  }
}

function renderResult(result) {
  const weaknessHtml = result.weakness
    .map(
      (item) => `
        <div class="weakness">
          <strong>${item.knowledge_point_name_zh}</strong>
          <span>${item.attempted_count} 题，错 ${item.wrong_count} 题，正确率 ${Math.round(item.accuracy * 100)}%</span>
          <p>${item.advice_zh}</p>
        </div>
      `
    )
    .join("");

  const wrongHtml = result.wrong_questions.length
    ? `<div class="wrong"><strong>${result.wrong_questions.length} 道错题</strong><span>逐题解析会显示在对应题目下方。</span></div>`
    : `<div class="weakness"><strong>无错题</strong><span>可以继续生成新练习。</span></div>`;

  $("#resultBox").classList.remove("muted");
  $("#resultBox").innerHTML = `
    <div class="score">
      <div><strong>${Math.round(result.accuracy * 100)}%</strong><span>正确率</span></div>
      <div><strong>${result.correct_count}/${result.total_questions}</strong><span>答对题数</span></div>
    </div>
    ${weaknessHtml}
    ${wrongHtml}
  `;
}

function markAnswers(result) {
  for (const question of result.graded_questions) {
    const article = document.querySelector(`[data-quiz-number="${question.quiz_number}"]`);
    if (!article) continue;
    for (const option of article.querySelectorAll(".option")) {
      option.classList.remove("correct", "wrong");
      const key = option.dataset.option;
      if (key === question.correct_answer) option.classList.add("correct");
      if (key === question.selected_answer && !question.is_correct) option.classList.add("wrong");
    }
  }
}

function applyQuestionExplanations(explanations) {
  for (const box of document.querySelectorAll(".question-explanation")) {
    box.classList.add("hidden");
    box.textContent = "";
  }
  for (const item of explanations || []) {
    const box = document.querySelector(`[data-explanation-for="${item.quiz_number}"]`);
    if (!box) continue;
    box.classList.remove("hidden");
    box.textContent = item.explanation_zh || "";
  }
}

function renderExplanation(explanation, error) {
  if (error) {
    $("#threadBox").classList.remove("muted");
    $("#threadBox").textContent = `批改已完成，但错题解析生成失败：${error}`;
    return;
  }
  if (!explanation) {
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = "本次没有生成错题解析。";
    return;
  }
  if (explanation.thread_id) {
    state.latestThreadId = explanation.thread_id;
  }
  applyQuestionExplanations(explanation.question_explanations || []);
  $("#threadBox").classList.remove("muted");
  $("#threadBox").textContent = explanation.study_advice_zh || explanation.assistant_text || "本次没有整体建议。";
}

async function sendFollowup() {
  const message = $("#followupText").value.trim();
  if (!state.latestThreadId) {
    $("#threadBox").textContent = "请先完成一次带错题解析的批改。";
    return;
  }
  if (!message) {
    $("#threadBox").textContent = "请先输入追问。";
    return;
  }
  if (!$("#externalConsent").checked) {
    $("#threadBox").textContent = "请先勾选同意发送本对话上下文到 DeepSeek。";
    return;
  }

  $("#followupBtn").disabled = true;
  $("#followupBtn").textContent = "发送中...";
  try {
    const payload = await requestJson("/api/followup", {
      method: "POST",
      body: JSON.stringify({
        thread_id: state.latestThreadId,
        message,
        confirm_external_send: true,
      }),
    });
    $("#threadBox").classList.remove("muted");
    $("#threadBox").textContent = payload.assistant_text;
    $("#followupText").value = "";
  } catch (error) {
    $("#threadBox").textContent = error.message;
  } finally {
    $("#followupBtn").disabled = false;
    $("#followupBtn").textContent = "发送追问";
  }
}

async function selectExam(system, scope = "practice") {
  const currentSystem = scope === "words" ? state.selectedWordExam : state.selectedExam;
  if (!["TEM8_RU", "TEM4_RU"].includes(system) || system === currentSystem) return;
  if (scope === "words") {
    state.selectedWordExam = system;
    localStorage.setItem("aieyu.wordExam", system);
    state.wordStatus = null;
    state.wordReviewPool = null;
    state.wordSession = null;
    state.currentWordIndex = 0;
    state.wordSessionStats = null;
    $("#wordCard").classList.add("hidden");
    $("#wordEmpty").classList.remove("hidden");
    resetWordEmpty();
    $("#wordSessionMeta").textContent = "尚未开始";
    renderExamContext();
    await loadWordStatus();
    return;
  }
  state.selectedExam = system;
  localStorage.setItem("aieyu.practiceExam", system);
  renderExamContext();
  clearStudentState();
  try {
    renderStatus(await requestJson("/api/status?" + queryForActiveUser()));
    await refreshStudentData();
  } catch (error) {
    $("#statusSummary").textContent = error.message;
  }
}

async function startStudyWords() {
  state.selectedWordExam = state.selectedExam;
  localStorage.setItem("aieyu.wordExam", state.selectedWordExam);
  renderExamContext();
  showView("words");
  await loadWordStatus();
  const mode = state.wordStatus?.due_count ? "review" : "mixed";
  await startWordSession(mode);
}

async function handleStudyAction(action, mode, dailyTaskId = 0) {
  if (action === "questions") {
    if (mode === "diagnostic") {
      startDiagnostic();
    } else {
      generateQuiz("weakness_review", "", dailyTaskId);
    }
    return;
  }
  if (action === "words") {
    startStudyWords();
    return;
  }
  if (action === "wrongbook") {
    showView("wrongbook");
    await loadWrongbook();
    if ((state.wrongbook?.pending_count || 0) > 0) await startWrongbookReview();
  }
}

async function init() {
  renderExamContext();
  try {
    renderStatus(await requestJson("/api/status?" + queryForActiveUser()));
  } catch (error) {
    $("#statusSummary").textContent = error.message;
  }
  try {
    await loadAuthStatus();
  } catch (error) {
    $("#activeUserHint").textContent = error.message;
  }
  await refreshStudentData();
}

for (const button of document.querySelectorAll("[data-exam-system]")) {
  button.addEventListener("click", () => selectExam(button.dataset.examSystem, button.dataset.examScope || "practice"));
}

async function startDiagnostic() {
  showView("practice");
  $("#countInput").value = 30;
  for (const input of document.querySelectorAll('input[name="questionType"]')) {
    input.checked = DIAGNOSTIC_TYPES.includes(input.value);
  }
  for (const input of document.querySelectorAll('input[name="year"]')) {
    input.checked = true;
  }
  $("#diagnosticBtn").disabled = true;
  $("#diagnosticBtn").textContent = "生成中...";
  try {
    await generateQuiz("diagnostic");
  } finally {
    $("#diagnosticBtn").disabled = false;
    $("#diagnosticBtn").textContent = "开始 30 题诊断";
  }
}

$("#generateBtn").addEventListener("click", () => generateQuiz());
$("#diagnosticBtn").addEventListener("click", startDiagnostic);
for (const button of document.querySelectorAll(".navbtn")) {
  button.addEventListener("click", () => showView(button.dataset.view));
}
$("#accountButton").addEventListener("click", toggleAccountMenu);
$("#loginBtn").addEventListener("click", () => submitAuth("login"));
$("#registerBtn").addEventListener("click", () => submitAuth("register"));
$("#logoutBtn").addEventListener("click", logoutUser);
$("#refreshWrongbookBtn").addEventListener("click", loadWrongbook);
$("#reviewPendingBtn").addEventListener("click", () => startWrongbookReview());
$("#reviewSelectedBtn").addEventListener("click", () => startWrongbookReview([...state.wrongbookSelected]));
$("#wrongbookTypeFilter").addEventListener("change", (event) => {
  state.wrongbookFilters.type = event.target.value;
  renderWrongbookList();
});
$("#wrongbookKnowledgeFilter").addEventListener("change", (event) => {
  state.wrongbookFilters.knowledge = event.target.value;
  renderWrongbookList();
});
$("#wrongbookSearch").addEventListener("input", (event) => {
  state.wrongbookFilters.search = event.target.value;
  renderWrongbookList();
});
$("#wrongbookStatusFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-wrong-status]");
  if (!button) return;
  state.wrongbookFilters.status = button.dataset.wrongStatus;
  renderWrongbookList();
});
$("#wrongbookBox").addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-wrongbook-select]");
  if (!checkbox) return;
  const questionId = Number(checkbox.dataset.wrongbookSelect);
  if (checkbox.checked) state.wrongbookSelected.add(questionId);
  else state.wrongbookSelected.delete(questionId);
  updateWrongbookSelection();
});
$("#wrongbookBox").addEventListener("click", (event) => {
  const favorite = event.target.closest("[data-wrongbook-favorite]");
  if (favorite) {
    const questionId = Number(favorite.dataset.wrongbookFavorite);
    const item = state.wrongbook?.items?.find((entry) => Number(entry.question_id) === questionId);
    if (item) saveWrongbookPreference(questionId, !item.is_favorite);
    return;
  }
  const save = event.target.closest("[data-wrongbook-save]");
  if (save) saveWrongbookPreference(Number(save.dataset.wrongbookSave));
});
$("#startWordsBtn").addEventListener("click", () => startWordSession());
$("#startReviewWordsBtn").addEventListener("click", () => startWordSession("review"));
$("#prevWordBtn").addEventListener("click", showPreviousWord);
$("#nextWordBtn").addEventListener("click", showNextWord);
$("#markWordWrongBtn").addEventListener("click", markCurrentWordWrong);
$("#toggleWordFeedbackBtn").addEventListener("click", toggleWordFeedbackForm);
$("#submitWordFeedbackBtn").addEventListener("click", submitWordFeedback);
$("#submitProductFeedbackBtn").addEventListener("click", submitProductFeedback);
$("#closeTranslatorBtn").addEventListener("click", () => {
  window.getSelection()?.removeAllRanges();
  hideSelectionTranslator();
});
$("#selectionTranslator").addEventListener("pointerdown", () => {
  state.selectionTranslation.interacting = true;
  window.setTimeout(() => { state.selectionTranslation.interacting = false; }, 500);
});
$("#selectionTranslator").addEventListener("click", (event) => {
  if (event.target.closest("[data-translate-with-ai]")) translateCurrentSelection(true);
});
for (const button of document.querySelectorAll("[data-word-result]")) {
  button.addEventListener("click", () => reviewCurrentWord(button.dataset.wordResult));
}
$("#wordSessionSummary").addEventListener("click", (event) => {
  if (!event.target.closest("[data-word-summary-prev]")) return;
  const words = state.wordSession?.words || [];
  if (!words.length) return;
  state.currentWordIndex = words.length - 1;
  renderCurrentWord();
});
$("#profileSummary").addEventListener("click", (event) => {
  const weaknessButton = event.target.closest("[data-start-weakness]");
  if (weaknessButton) {
    generateQuiz("weakness_review");
    return;
  }
  const button = event.target.closest("[data-practice-type]");
  if (!button) return;
  selectOnlyQuestionType(button.dataset.practiceType);
});
$("#todayTasks").addEventListener("click", (event) => {
  const button = event.target.closest("[data-study-action]");
  if (!button) return;
  handleStudyAction(
    button.dataset.studyAction,
    button.dataset.studyMode || "",
    Number(button.dataset.dailyTaskId || 0),
  );
});
$("#knowledgeMap").addEventListener("click", (event) => {
  const button = event.target.closest("[data-knowledge-code]");
  if (!button) return;
  generateQuiz("knowledge_point", button.dataset.knowledgeCode);
});
$("#quizForm").addEventListener("submit", submitQuiz);
$("#followupBtn").addEventListener("click", sendFollowup);
document.addEventListener("click", (event) => {
  if (!event.target.closest(".account-menu")) {
    closeAccountMenu();
  }
});
document.addEventListener("selectionchange", scheduleSelectionInspection);
document.addEventListener("mouseup", scheduleSelectionInspection);
document.addEventListener("touchend", scheduleSelectionInspection, { passive: true });
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") hideSelectionTranslator();
});

init();
showView(state.activeView);
