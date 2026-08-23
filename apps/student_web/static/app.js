const state = {
  users: [],
  authenticated: false,
  activeUser: null,
  activeUserId: 0,
  activeView: localStorage.getItem("aieyu.activeView") || "practice",
  quiz: null,
  result: null,
  explanation: null,
  profile: null,
  wrongbook: null,
  wordStatus: null,
  wordSession: null,
  currentWordIndex: 0,
  wordSessionStats: null,
  latestThreadId: 1,
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

function queryForActiveUser() {
  return "";
}

function showView(view) {
  const nextView = ["practice", "words", "wrongbook"].includes(view) ? view : "practice";
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
  $("#statusSummary").innerHTML = `
    <p><strong>${status.question_count}</strong> 道已审核题</p>
    <p>${status.years.map((item) => `${item.year} 年 ${item.count} 题`).join(" · ")}</p>
    <p>DeepSeek：${status.deepseek_configured ? "已配置" : "未配置"}</p>
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
  state.wordStatus = null;
  state.wordSession = null;
  state.currentWordIndex = 0;
  state.wordSessionStats = null;
  state.latestThreadId = null;
  $("#emptyState").classList.remove("hidden");
  $("#quizForm").classList.add("hidden");
  $("#quizMeta").textContent = "尚未生成练习";
  $("#resultBox").classList.add("muted");
  $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "批改后自动生成薄弱点、复习方案和可追问问题。";
  $("#wordCard").classList.add("hidden");
  $("#wordEmpty").classList.remove("hidden");
  resetWordEmpty();
  $("#wordSessionMeta").textContent = "尚未开始";
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

function renderProfile(profile) {
  state.profile = profile;
  const byType = new Map((profile.question_type_mastery || []).map((item) => [item.target_code, item]));
  const items = TYPE_ORDER.map(([code, name]) => {
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
    ? `<p class="profile-next">建议优先：${profile.next_training.target_name_zh}</p>`
    : `<p class="profile-next">数据还不够，建议先完成入门诊断。</p>`;

  $("#profileSummary").classList.remove("muted");
  $("#profileSummary").innerHTML = `${items}${next}`;
}

async function loadProfile() {
  const profile = await requestJson(`/api/profile?${queryForActiveUser()}`);
  renderProfile(profile);
}

function renderWrongbook(payload) {
  state.wrongbook = payload;
  const box = $("#wrongbookBox");
  if (!payload.items || !payload.items.length) {
    box.classList.add("muted");
    box.innerHTML = "当前学生还没有错题。完成一次练习后会自动沉淀到这里。";
    $("#wrongbookMeta").textContent = "0 道";
    return;
  }

  $("#wrongbookMeta").textContent = `${payload.pending_count} 道待巩固 · ${payload.corrected_count} 道已订正`;
  box.classList.remove("muted");
  box.innerHTML = `
    <div class="wrongbook-list">
      ${payload.items
        .map((item) => {
          const source = item.source?.label || `${item.source?.year || ""} 年真题`;
          const passageTitle = item.passage?.title ? `<p class="mini">阅读文章：${escapeHtml(item.passage.title)}</p>` : "";
          return `
            <article class="wrongbook-item ${item.status === "pending" ? "pending" : "corrected"}">
              <div class="wrongbook-head">
                <strong>${escapeHtml(item.status_zh)}</strong>
                <span>${escapeHtml(item.question_type_name)} · ${escapeHtml(source)}</span>
              </div>
              ${passageTitle}
              <p>${escapeHtml(item.stem)}</p>
              <p class="mini">最近作答：${escapeHtml(item.selected_answer || "未作答")} · 正确答案：${escapeHtml(item.correct_answer)}</p>
              <p class="mini">累计 ${item.seen_count} 次，错 ${item.wrong_count} 次</p>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
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

function renderWordStatus(payload) {
  state.wordStatus = payload;
  $("#wordMeta").textContent = `${payload.reviewed_today} 个今日已打卡 · ${payload.due_count} 个待复习`;

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

async function loadWordStatus() {
  if (!state.authenticated) {
    $("#wordStats").classList.add("muted");
    $("#wordStats").textContent = "请先登录后开始单词打卡。";
    $("#wordMeta").textContent = "未登录";
    return;
  }
  try {
    const payload = await requestJson(`/api/words/status?${queryForActiveUser()}`);
    renderWordStatus(payload);
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
  if (result === "known") return "已记录为认识：这个词不会进入复习词库。";
  if (result === "fuzzy") return "已记录为模糊：2 天后会再次复习。";
  if (result === "unknown") return "已记录为不认识：会每天复习，直到你标记为认识。";
  return "";
}

function setWordActionLoading(isLoading) {
  for (const button of document.querySelectorAll("[data-word-result]")) {
    button.disabled = isLoading;
  }
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
    <p class="mini muted">认识的词不进入复习词库；模糊词 2 天后复习；不认识的词每天复习直到认识。</p>
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
  $("#nextWordBtn").textContent = state.currentWordIndex >= words.length - 1 ? "完成本次" : "下一词";
  $("#nextWordBtn").disabled = !hasReviewed;
  $("#markWordWrongBtn").disabled = !hasReviewed || word.session_result === "unknown";
}

async function startWordSession() {
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
      }),
    });
    state.wordSession = payload;
    state.currentWordIndex = 0;
    state.wordSessionStats = freshWordStats();
    if (payload.status) {
      renderWordStatus(payload.status);
    }
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
      }),
    });
    word.session_result = result;
    word.progress_status_zh = payload.word?.progress_status_zh || word.progress_status_zh;
    state.wordSessionStats[result] += 1;
    if (payload.status) {
      renderWordStatus(payload.status);
    }
    renderCurrentWord();
  } catch (error) {
    $("#wordHint").textContent = error.message;
    setWordActionLoading(false);
  }
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
      }),
    });
    state.wordSessionStats[previousResult] = Math.max(0, state.wordSessionStats[previousResult] - 1);
    state.wordSessionStats.unknown += 1;
    word.session_result = "unknown";
    word.progress_status_zh = payload.word?.progress_status_zh || "学习中";
    if (payload.status) {
      renderWordStatus(payload.status);
    }
    renderCurrentWord();
  } catch (error) {
    $("#wordHint").textContent = error.message;
    setWordActionLoading(false);
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
    return;
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

async function generateQuiz(mode = "random") {
  if (!state.authenticated) {
    openAccountMenu();
    $("#activeUserHint").textContent = "请先登录或注册，再开始练习。";
    return;
  }
  showView("practice");
  $("#generateBtn").disabled = true;
  $("#generateBtn").textContent = "生成中...";
  try {
    const payload = {
      count: Number($("#countInput").value || 10),
      question_types: selectedValues("questionType"),
      years: selectedValues("year").map(Number),
      seed: Date.now(),
    };
    if (mode === "diagnostic") {
      payload.mode = "diagnostic";
    }
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
    $("#generateBtn").disabled = false;
    $("#generateBtn").textContent = "生成练习";
  }
}

function renderQuiz(quiz) {
  $("#emptyState").classList.add("hidden");
  $("#quizForm").classList.remove("hidden");
  $("#quizMeta").textContent = `${quiz.count} 题 · ${quiz.mode === "diagnostic" ? "入门诊断" : "俄语专八"}`;
  $("#answerHint").textContent = "";

  const renderedPassages = new Set();
  $("#questionList").innerHTML = quiz.questions
    .map((question) => {
      let passage = "";
      if (question.passage) {
        const passageKey = question.passage.id || `${question.passage.title}-${question.passage.body}`;
        if (!renderedPassages.has(passageKey)) {
          renderedPassages.add(passageKey);
          passage = `<div class="passage"><strong>${question.passage.title || "阅读文章"}</strong>\n${question.passage.body}</div>`;
        }
      }
      return `
        <article class="question" data-question-id="${question.question_id}" data-quiz-number="${question.quiz_number}">
          <div class="qhead">
            <span class="badge">${question.quiz_number}</span>
            <span class="badge">${question.question_type_name}</span>
            <span class="source">${question.source.label} · 原题 ${question.source.question_number}</span>
          </div>
          ${passage}
          <p class="stem">${question.stem}</p>
          <div class="options">
            ${question.options
              .map(
                (option) => `
                  <label class="option" data-option="${option.key}">
                    <input type="radio" name="q${question.quiz_number}" value="${option.key}" />
                    <span>${optionLabel(option)}</span>
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
    state.result = await requestJson("/api/grade", {
      method: "POST",
      body: JSON.stringify({ title: "AIeyu student practice", answers }),
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
    $("#threadBox").textContent = `批改已完成，但 AI 讲解生成失败：${error}`;
    return;
  }
  if (!explanation) {
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = "本次没有生成 AI 讲解。";
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
    $("#threadBox").textContent = "请先完成一次带 AI 讲解的批改。";
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

async function init() {
  try {
    renderStatus(await requestJson("/api/status"));
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
$("#startWordsBtn").addEventListener("click", startWordSession);
$("#nextWordBtn").addEventListener("click", showNextWord);
$("#markWordWrongBtn").addEventListener("click", markCurrentWordWrong);
for (const button of document.querySelectorAll("[data-word-result]")) {
  button.addEventListener("click", () => reviewCurrentWord(button.dataset.wordResult));
}
$("#profileSummary").addEventListener("click", (event) => {
  const button = event.target.closest("[data-practice-type]");
  if (!button) return;
  selectOnlyQuestionType(button.dataset.practiceType);
});
$("#quizForm").addEventListener("submit", submitQuiz);
$("#followupBtn").addEventListener("click", sendFollowup);
document.addEventListener("click", (event) => {
  if (!event.target.closest(".account-menu")) {
    closeAccountMenu();
  }
});

init();
showView(state.activeView);
