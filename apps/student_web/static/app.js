const state = {
  quiz: null,
  result: null,
  explanation: null,
  latestThreadId: 1,
};

const $ = (selector) => document.querySelector(selector);

function optionLabel(item) {
  return `${item.key}. ${item.text}`;
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

async function generateQuiz() {
  $("#generateBtn").disabled = true;
  $("#generateBtn").textContent = "生成中...";
  try {
    const payload = {
      count: Number($("#countInput").value || 10),
      question_types: selectedValues("questionType"),
      years: selectedValues("year").map(Number),
      seed: Date.now(),
    };
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
    $("#threadBox").textContent = "批改后自动生成薄弱点、复习方案和巩固练习。";
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
  $("#quizMeta").textContent = `${quiz.count} 题 · 俄语专八`;
  $("#answerHint").textContent = "";

  $("#questionList").innerHTML = quiz.questions
    .map((question) => {
      const passage = question.passage
        ? `<div class="passage"><strong>${question.passage.title || "阅读文章"}</strong>\n${question.passage.body}</div>`
        : "";
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
    renderResult(state.result);
    markAnswers(state.result);
    renderExplanation(state.explanation, state.result.explanation_error);
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
}

$("#generateBtn").addEventListener("click", generateQuiz);
$("#quizForm").addEventListener("submit", submitQuiz);
$("#followupBtn").addEventListener("click", sendFollowup);

init();
