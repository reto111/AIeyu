'use strict';
// Original, deliberately simple fixtures. No production content, API or storage.
const bank = [
  {id:'d1',skill:'地点与第六格',stem:'Я живу в _____.',choices:['Москва','Москве','Москву','Москвой'],answer:1,explain:'这里表示“住在莫斯科”，是位置而非运动方向。в 表示静态地点时支配第六格，Москва 的第六格形式是 Москве。',tip:'先区分“在哪里”（где）与“到哪里”（куда），再选择格。'},
  {id:'d2',skill:'直接宾语与第四格',stem:'Анна читает интересную _____.',choices:['книга','книге','книги','книгу'],answer:3,explain:'читать（读）的直接宾语用第四格。阴性名词 книга 变为 книгу，形容词 интересную 也与其保持一致。',tip:'先找到动词，再问“读什么”（что），确认直接宾语。'},
  {id:'d3',skill:'介词与第三格',stem:'Благодаря _____ мы закончили работу вовремя.',choices:['твою помощь','твоей помощью','твоей помощи','твоя помощь'],answer:2,explain:'благодаря 表示“多亏”，支配第三格。短语 твоя помощь 在这里变为 твоей помощи。',tip:'介词要求的格比中文词序更可靠：благодаря + 第三格。'},
  {id:'l1',skill:'地点与第六格',stem:'Студенты занимаются в _____.',choices:['библиотеку','библиотека','библиотеке','библиотекой'],answer:2,explain:'学生们“在图书馆学习”，表示静态位置。библиотека 的第六格形式是 библиотеке。',tip:'用 где 提问，巩固 в + 第六格。'},
  {id:'l2',skill:'地点与第六格',stem:'Мой брат сейчас в _____.',choices:['школе','школу','школа','школой'],answer:0,explain:'“哥哥/弟弟现在在学校”表示位置，школа 在 в 后用第六格 школе。',tip:'句子没有运动方向，不能因为看见 в 就选第四格。'},
  {id:'a1',skill:'直接宾语与第四格',stem:'Я вижу новую _____.',choices:['машина','машину','машине','машиной'],answer:1,explain:'вижу（看见）的直接宾语用第四格：машина → машину。новую 与名词性、数、格一致。',tip:'看见什么？用第四格回答。'},
  {id:'a2',skill:'直接宾语与第四格',stem:'Мы слушаем _____.',choices:['музыка','музыке','музыкой','музыку'],answer:3,explain:'слушать（听）支配第四格直接宾语。музыка 的第四格形式是 музыку。',tip:'听音乐：слушать музыку。'},
  {id:'p1',skill:'介词与第三格',stem:'Благодаря _____ я понял правило.',choices:['учителем','учителю','учителя','учитель'],answer:1,explain:'благодаря 支配第三格。учитель 的第三格形式为 учителю，意为“多亏老师”。',tip:'不要把“多亏老师”按工具意义误选第五格。'},
  {id:'p2',skill:'介词与第三格',stem:'Благодаря _____ мы быстро нашли дорогу.',choices:['карта','карту','карте','картой'],answer:2,explain:'“多亏地图，我们很快找到了路。”благодаря 后的 карта 用第三格 карте。',tip:'把介词和所支配的格一起记忆。'}
];
const words = [
  {word:'кни́га',meaning:'书；书籍',kind:'阴性名词',example:'Я читаю книгу.',translation:'我正在读书。'},
  {word:'учи́ться',meaning:'学习；求学',kind:'未完成体动词',example:'Я учусь в университете.',translation:'我在大学学习。'},
  {word:'по́мощь',meaning:'帮助；援助',kind:'阴性名词',example:'Спасибо за помощь.',translation:'谢谢你的帮助。'},
  {word:'вре́мя',meaning:'时间',kind:'中性名词',example:'У меня есть время.',translation:'我有时间。'}
];
let history=[], current=bank.slice(0,3), answers={}, submitted=false, mode='diagnostic';
let queue=[0,1,2,3], learned=new Set(), flipped=false;
const $=selector=>document.querySelector(selector);
function navigate(view,updateHash=true){
  if(!['home','practice','words','about'].includes(view))view='home';
  document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==view);
  document.querySelectorAll('[data-view]').forEach(el=>{if(el.dataset.view===view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
  $('#location').textContent={home:'学习中心',practice:'迷你诊断',words:'单词卡',about:'项目说明'}[view];
  if(view==='home')renderHome();
  if(view==='words')renderWords();
  if(updateHash&&location.hash!==`#${view}`)location.hash=view;
}
function latestMistakes(){const latest=new Map();history.forEach(a=>latest.set(a.id,a));return [...latest.values()].filter(a=>!a.correct);}
function renderHome(){
  const right=history.filter(a=>a.correct).length, wrong=latestMistakes();
  $('#metrics').innerHTML=`<div class="metric"><strong>${history.length}</strong><span>已提交作答次数（含重练）</span></div><div class="metric"><strong>${history.length?Math.round(right/history.length*100)+'%':'—'}</strong><span>本次正确率 · 非能力评级</span></div><div class="metric"><strong>${wrong.length}</strong><span>最新一次仍答错的题目</span></div>`;
  $('#recommendation').innerHTML=history.length?`<p>${wrong.length?`先练「${wrong[0].skill}」，看看换一个句子能否选对。`:'这组样例已完成，可以再练一组新句子。'}样本很少，暂不判断长期掌握度。</p><button data-start="targeted">${wrong.length?'练习薄弱点':'继续巩固'} ↗</button>`:'<p>从 3 道基础样例开始，体验诊断与反馈。完成前不生成能力结论。</p><button data-start="diagnostic">开始迷你诊断 ↗</button>';
  $('#mistakes').innerHTML=wrong.length?wrong.map(a=>`<div class="mistake-item"><span>${a.skill}</span><br><span lang="ru">${bank.find(q=>q.id===a.id).stem}</span></div>`).join(''):'<p>还没有待复习错题。答错的题目会保留在这里，并提供解析。</p>';
  if(wrong.length)$('#mistakes').innerHTML+='<button id="review-mistakes">查看错题解析 ↗</button>';
}
function begin(kind){
  mode=kind;submitted=false;answers={};
  if(kind==='diagnostic')current=bank.slice(0,3);
  else {const skill=latestMistakes()[0]?.skill || bank[0].skill;current=bank.slice(3).filter(q=>q.skill===skill);}
  renderQuiz();navigate('practice');$('#main').focus();
}
function renderQuiz(){
  $('#practice-title').textContent=mode==='diagnostic'?'3 题迷你诊断':mode==='review'?'本次错题解析':`专项巩固 · ${current[0].skill}`;
  $('#practice-intro').textContent=mode==='review'?'回看最近一次错误与对应规则；重复查看不会计入作答。':mode==='diagnostic'?'先试着选择答案，再看看每道题背后的规则。':'用不同句子练习同一规则；本演示题池有限，再次巩固可能重复。';
  const score=current.filter(q=>answers[q.id]===q.answer).length;
  $('#quiz').innerHTML=(submitted&&mode!=='review'?`<div class="result" role="status"><strong>${score} / ${current.length} 回答正确</strong><p>这只是本次样例作答结果。样本不足，不能据此判断长期能力或考试水平。</p></div>`:'')+current.map((q,index)=>`<article class="question"><div class="q-meta">${String(index+1).padStart(2,'0')} / ${q.skill}</div><fieldset ${submitted?'disabled':''}><legend lang="ru">${q.stem}</legend><div class="options">${q.choices.map((choice,i)=>`<label class="option ${submitted&&i===q.answer?'correct':''} ${submitted&&answers[q.id]===i&&i!==q.answer?'incorrect':''}"><input type="radio" name="${q.id}" value="${i}" ${answers[q.id]===i?'checked':''}><span lang="ru">${choice}</span>${submitted&&i===q.answer?'<span class="answer-tag">正确答案</span>':''}</label>`).join('')}</div></fieldset>${submitted?`<div class="explanation"><b class="${answers[q.id]===q.answer?'right':'wrong'}">${answers[q.id]===q.answer?'回答正确':'需要再练'} · ${q.skill}</b><p>${q.explain}</p><details><summary>下次怎样判断？</summary><p>${q.tip}</p></details><p class="fine">演示预写解析 · 未调用 AI</p></div>`:''}</article>`).join('');
  document.querySelectorAll('.option.incorrect').forEach(option=>{const tag=document.createElement('span');tag.className='answer-tag';tag.textContent='你的选择';option.append(tag);});
  $('#quiz-message').textContent='';
  $('#quiz-actions').innerHTML=submitted?'<button class="primary" data-start="targeted">练习薄弱点 / 继续巩固 ↗</button><button data-view="home">查看学习中心</button><button data-start="diagnostic">重做诊断</button>':'<button class="primary" id="submit">提交并查看解析 ↗</button><button data-view="home">返回学习中心</button>';
}
function submit(){
  if(submitted)return;
  if(current.some(q=>answers[q.id]===undefined)){$('#quiz-message').textContent='还有题目未选择答案，请完成后再提交。';return;}
  history.push(...current.map(q=>({id:q.id,skill:q.skill,choice:answers[q.id],correct:answers[q.id]===q.answer})));
  submitted=true;renderQuiz();$('#practice-title').scrollIntoView({block:'start'});
}
function review(){
  const wrong=latestMistakes();if(!wrong.length)return;
  mode='review';current=wrong.map(a=>bank.find(q=>q.id===a.id));answers=Object.fromEntries(wrong.map(a=>[a.id,a.choice]));submitted=true;renderQuiz();navigate('practice');
}
function renderWords(){
  if(!queue.length){$('#word-card').innerHTML='<p class="eyebrow">SESSION COMPLETE</p><h2>这 4 个词，已完成一轮回忆。</h2><p class="muted">一次记住不代表长期掌握，隔一段时间再试试。</p>';$('#word-actions').innerHTML='<button class="primary" id="restart-words">再来一轮</button>';return;}
  const w=words[queue[0]];
  $('#word-card').innerHTML=`<p class="eyebrow">已标记记住 ${learned.size} / 4 · 待回忆 ${queue.length}</p><p class="word" lang="ru">${w.word}</p><p class="muted">${w.kind}</p>${flipped?`<p class="meaning">${w.meaning}</p><p lang="ru">${w.example}</p><p class="muted">${w.translation}</p>`:'<p class="fine">试着回忆中文意思，再翻面检查。</p>'}`;
  $('#word-actions').innerHTML=flipped?'<button id="again">再练一次</button><button class="primary" id="known">已记住 →</button>':'<button class="primary" id="flip">翻面查看释义</button>';
}
document.addEventListener('change',event=>{if(event.target.matches('#quiz input')&&!submitted)answers[event.target.name]=Number(event.target.value);});
document.addEventListener('click',event=>{
  const b=event.target.closest('button');if(!b)return;
  if(b.dataset.view)navigate(b.dataset.view);
  if(b.dataset.start)begin(b.dataset.start);
  if(b.id==='submit')submit();
  if(b.id==='review-mistakes')review();
  if(b.id==='flip'){flipped=true;renderWords();}
  if(b.id==='again'||b.id==='known'){const index=queue.shift();if(b.id==='again')queue.push(index);else learned.add(index);flipped=false;renderWords();}
  if(b.id==='restart-words'){queue=[0,1,2,3];learned=new Set();flipped=false;renderWords();}
  if(b.id==='reset'){history=[];answers={};current=bank.slice(0,3);submitted=false;mode='diagnostic';queue=[0,1,2,3];learned=new Set();flipped=false;renderQuiz();navigate('home');}
});
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1),false));
renderQuiz();navigate(location.hash.slice(1)||'home',false);
