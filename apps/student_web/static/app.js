const state = {
  quiz: null,
  result: null,
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
    renderQuiz(state.quiz);
    $("#resultBox").classList.add("muted");
    $("#resultBox").textContent = "提交后显示正确率和薄弱点。";
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = "提交批改后可生成本次错题讲解。";
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

  $("#answerHint").textContent = "正在批改...";
  try {
    state.result = await requestJson("/api/grade", {
      method: "POST",
      body: JSON.stringify({ title: "AIeyu student practice", answers }),
    });
    renderResult(state.result);
    markAnswers(state.result);
    $("#answerHint").textContent = "已批改";
    $("#threadBox").classList.add("muted");
    $("#threadBox").textContent = state.result.wrong_count
      ? "可以生成本次错题讲解。"
      : "这次没有错题，继续保持。";
  } catch (error) {
    $("#answerHint").textContent = error.message;
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
    ? result.wrong_questions
        .map(
          (item) => `
            <div class="wrong">
              <strong>第 ${item.quiz_number} 题 · ${item.source.label}</strong>
              <span>你选 ${item.selected_answer || "未答"}，正确答案 ${item.correct_answer}</span>
            </div>
          `
        )
        .join("")
    : `<div class="weakness"><strong>全部答对</strong><span>这轮非常稳。</span></div>`;

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

async function generateExplanation() {
  if (!state.result?.quiz_session_id) {
    $("#threadBox").textContent = "请先提交批改，再生成错题讲解。";
    return;
  }
  if (!state.result.wrong_count) {
    $("#threadBox").textContent = "这次没有错题，暂时不需要生成错题讲解。";
    return;
  }
  if (!$("#explainConsent").checked) {
    $("#threadBox").textContent = "请先勾选同意发送本次错题数据到 DeepSeek。";
    return;
  }

  $("#generateExplainBtn").disabled = true;
  $("#generateExplainBtn").textContent = "生成中...";
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "正在生成错题讲解，稍等一下。";
  try {
    const payload = await requestJson("/api/explain", {
      method: "POST",
      body: JSON.stringify({
        quiz_session_id: state.result.quiz_session_id,
        confirm_external_send: true,
      }),
    });
    if (payload.thread_id) {
      state.latestThreadId = payload.thread_id;
    }
    $("#threadBox").classList.remove("muted");
    $("#threadBox").textContent = payload.assistant_text;
  } catch (error) {
    $("#threadBox").textContent = error.message;
  } finally {
    $("#generateExplainBtn").disabled = false;
    $("#generateExplainBtn").textContent = "生成错题讲解";
  }
}

async function loadThread() {
  $("#threadBox").classList.add("muted");
  $("#threadBox").textContent = "正在读取讲解...";
  try {
    const payload = await requestJson(`/api/thread?id=${state.latestThreadId}`);
    const assistantMessages = payload.messages.filter((item) => item.role === "assistant");
    $("#threadBox").classList.remove("muted");
    $("#threadBox").textContent = assistantMessages.at(-1)?.content || "当前线程还没有讲解。";
  } catch (error) {
    $("#threadBox").textContent = error.message;
  }
}

async function sendFollowup() {
  const message = $("#followupText").value.trim();
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
$("#generateExplainBtn").addEventListener("click", generateExplanation);
$("#loadThreadBtn").addEventListener("click", loadThread);
$("#followupBtn").addEventListener("click", sendFollowup);

init();
