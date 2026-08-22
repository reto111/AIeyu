const state = {
  users: [],
  activeUserId: Number(localStorage.getItem("aieyu.activeUserId") || 1),
  activeView: localStorage.getItem("aieyu.activeView") || "practice",
  quiz: null,
  result: null,
  explanation: null,
  profile: null,
  wrongbook: null,
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

function optionLabel(item) {
  return `${item.key}. ${item.text}`;
}

function activeUserId() {
  return Number(state.activeUserId || 1);
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
  return `user_id=${encodeURIComponent(activeUserId())}`;
}

function showView(view) {
  const nextView = ["practice", "wrongbook"].includes(view) ? view : "practice";
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

function renderUsers(usersPayload) {
  state.users = usersPayload.users || [];
  const stored = activeUserId();
  const exists = state.users.some((user) => Number(user.id) === stored);
  state.activeUserId = exists ? stored : Number(usersPayload.default_user_id || state.users[0]?.id || 1);
  localStorage.setItem("aieyu.activeUserId", String(state.activeUserId));

  const select = $("#userSelect");
  select.innerHTML = state.users
    .map(
      (user) => `
        <option value="${user.id}" ${Number(user.id) === activeUserId() ? "selected" : ""}>
          ${escapeHtml(user.display_name)}
        </option>
      `
    )
    .join("");
  const current = state.users.find((user) => Number(user.id) === activeUserId());
  $("#activeUserHint").textContent = current
    ? `当前记录写入：${current.display_name}`
    : "当前使用默认学生账号";
}

async function loadUsers() {
  const payload = await requestJson("/api/users");
  renderUsers(payload);
}

async function createUser() {
  const input = $("#newUserName");
  const displayName = input.value.trim();
  if (!displayName) {
    $("#activeUserHint").textContent = "请先填写学生姓名。";
    return;
  }
  $("#createUserBtn").disabled = true;
  $("#createUserBtn").textContent = "新增中...";
  try {
    const payload = await requestJson("/api/users", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName }),
    });
    state.activeUserId = Number(payload.user.id);
    localStorage.setItem("aieyu.activeUserId", String(state.activeUserId));
    input.value = "";
    await loadUsers();
    await refreshStudentData();
    showView("practice");
  } catch (error) {
    $("#activeUserHint").textContent = error.message;
  } finally {
    $("#createUserBtn").disabled = false;
    $("#createUserBtn").textContent = "新增";
  }
}

async function switchUser(userId) {
  state.activeUserId = Number(userId);
  localStorage.setItem("aieyu.activeUserId", String(state.activeUserId));
  state.quiz = null;
  state.result = null;
  state.explanation = null;
  state.latestThreadId = null;
  $("#emptyState").classList.remove("hidden");
  $("#quizForm").classList.add("hidden");
  $("#quizMeta").textContent = "尚未生成练习";
  $("#resultBox").classList.add("muted");
  $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "批改后自动生成薄弱点、复习方案和可追问问题。";
  renderUsers({ users: state.users, default_user_id: 1 });
  await refreshStudentData();
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
  const payload = await requestJson(`/api/wrongbook?${queryForActiveUser()}`);
  renderWrongbook(payload);
}

async function refreshStudentData() {
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
  showView("practice");
  $("#generateBtn").disabled = true;
  $("#generateBtn").textContent = "生成中...";
  try {
    const payload = {
      user_id: activeUserId(),
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
      body: JSON.stringify({ user_id: activeUserId(), title: "AIeyu student practice", answers }),
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
        user_id: activeUserId(),
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
    await loadUsers();
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
$("#userSelect").addEventListener("change", (event) => switchUser(event.target.value));
$("#createUserBtn").addEventListener("click", createUser);
$("#refreshWrongbookBtn").addEventListener("click", loadWrongbook);
$("#profileSummary").addEventListener("click", (event) => {
  const button = event.target.closest("[data-practice-type]");
  if (!button) return;
  selectOnlyQuestionType(button.dataset.practiceType);
});
$("#quizForm").addEventListener("submit", submitQuiz);
$("#followupBtn").addEventListener("click", sendFollowup);

init();
showView(state.activeView);
