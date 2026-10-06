const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let currentLevel = "A1", currentTopic = "", currentWord = null, selectedAnswer = null;
let examWords = [], examIndex = 0, examCorrect = 0, listeningSelected = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}
async function api(url, options) {
  const response = await fetch(url, options);
  let body = {};
  try { body = await response.json(); } catch (_) { /* handled by status below */ }
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}
function speakGerman(text, rate = 1) {
  if (!("speechSynthesis" in window)) return toast("Speech is not supported in this browser.");
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "de-DE"; utterance.rate = rate; utterance.pitch = 1; utterance.volume = 1;
  const germanVoice = speechSynthesis.getVoices().find(v => v.lang.toLowerCase().startsWith("de"));
  if (germanVoice) utterance.voice = germanVoice;
  speechSynthesis.speak(utterance);
}
function stopGermanAudio() { if ("speechSynthesis" in window) speechSynthesis.cancel(); }
function toast(message) { const el = $("#toast"); el.textContent = message; el.classList.add("show"); setTimeout(() => el.classList.remove("show"), 2200); }
function showView(name) {
  stopGermanAudio();
  $$(".view").forEach(v => v.classList.toggle("active-view", v.id === name));
  $$(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  const titles = {dashboard:"Good morning, Bharath ✦", vocabulary:"Vocabulary library", practice:"Choose a topic", listening:"Listening practice", exams:"Practice exams", review:"Review mistakes"};
  $("#page-title").innerHTML = titles[name] || titles.dashboard;
  if (name === "vocabulary") loadVocabulary();
  if (name === "practice") loadTopics(currentLevel);
  if (name === "review") loadMistakes();
}
async function loadMistakes() {
  let words;
  try { words = await api("/api/mistakes"); } catch (error) { return toast(error.message); }
  const target = $("#review-content");
  if (!words.length) { target.className = "empty-state"; target.textContent = "No mistakes yet. Complete a practice session and your missed words will appear here."; return; }
  target.className = "vocab-grid";
  target.innerHTML = words.map(w => `<article class="vocab-card"><span class="badge">${w.misses} miss${w.misses === 1 ? "" : "es"}</span><h3>${escapeHtml(w.article || "")} ${escapeHtml(w.german)}</h3><div class="meaning">${escapeHtml(w.english)}</div><div class="pron">🗣 ${escapeHtml(w.pronunciation)}</div><button class="audio" data-speak="${escapeHtml(`${w.article || ""} ${w.german}`)}">🔊 Listen</button></article>`).join("");
  $$("[data-speak]").forEach(b => b.addEventListener("click", () => speakGerman(b.dataset.speak)));
}
async function stats() {
  let s;
  try { s = await api("/api/stats"); } catch (error) { return toast(error.message); }
  $("#learned").textContent = s.attempts; $("#accuracy").textContent = `${s.accuracy}%`; $("#streak").textContent = s.attempts ? "1" : "0";
}
async function loadTopics(level = "A1") {
  currentLevel = level;
  let topics;
  try { topics = await api(`/api/topics?level=${encodeURIComponent(level)}`); } catch (error) { return toast(error.message); }
  $("#practice-topics").innerHTML = topics.map(t => `<div class="practice-card" data-topic="${escapeHtml(t.name)}"><div><strong>${escapeHtml(t.name)}</strong><small>50 questions · ${level}</small></div><button class="secondary">Practice →</button></div>`).join("");
  $$("#practice-topics .practice-card").forEach(b => b.addEventListener("click", () => startQuiz(b.dataset.topic)));
}
async function loadTopicPreview() {
  let topics;
  try { topics = await api("/api/topics?level=A1"); } catch (error) { return toast(error.message); }
  $("#topic-preview").innerHTML = topics.slice(0, 3).map(t => `<div class="topic-card" data-topic-preview="${t.name}"><strong>${t.name}</strong><small>50 words · A1</small></div>`).join("");
  $$("#topic-preview .topic-card").forEach(b => b.addEventListener("click", () => { showView("vocabulary"); $("#topic-filter").value = b.dataset.topicPreview; loadVocabulary(); }));
}
async function loadTopicFilter() {
  let all;
  try { all = [...await api("/api/topics?level=A1"), ...await api("/api/topics?level=A2")]; } catch (error) { return toast(error.message); }
  $("#topic-filter").innerHTML = `<option value="">All topics</option>${all.map(t => `<option>${t.name}</option>`).join("")}`;
}
async function loadVocabulary() {
  const params = new URLSearchParams({q: $("#search").value, level: $("#level-filter").value, topic: $("#topic-filter").value});
  let words;
  try { words = await api(`/api/vocabulary?${params}`); } catch (error) { return toast(error.message); }
  $("#vocab-list").innerHTML = words.length ? words.map(w => `<article class="vocab-card"><span class="badge">${escapeHtml(w.level)}</span><h3>${escapeHtml(w.article ? w.article + " " : "")}${escapeHtml(w.german)}</h3><div class="meaning">${escapeHtml(w.english)}</div><div class="pron">🗣 ${escapeHtml(w.pronunciation)}</div><div class="audio-row"><button class="audio" data-speak="${escapeHtml(`${w.article ? w.article + " " : ""}${w.german}`)}">🔊 Listen</button><button class="audio" data-speak="${escapeHtml(w.example_de)}">🔊 Example</button></div><div class="example">${escapeHtml(w.example_de)}<br><span>${escapeHtml(w.example_en)}</span></div><small>Plural: ${escapeHtml(w.plural)} · ${escapeHtml(w.topic)}</small></article>`).join("") : '<div class="empty-state">No vocabulary matches that search.</div>';
  $$("[data-speak]").forEach(b => b.addEventListener("click", () => speakGerman(b.dataset.speak)));
}
async function startQuiz(topic) {
  currentTopic = topic; let words;
  try { words = await api(`/api/vocabulary?level=${currentLevel}&topic=${encodeURIComponent(topic)}`); } catch (error) { return toast(error.message); }
  if (!words.length) return toast("No vocabulary is available for this topic.");
  currentWord = words[Math.floor(Math.random() * words.length)]; selectedAnswer = null;
  const distractors = words.filter(w => w.id !== currentWord.id).sort(() => Math.random() - .5).slice(0, 3);
  const options = [currentWord, ...distractors].sort(() => Math.random() - .5);
  $("#quiz").classList.remove("hidden");
  $("#quiz").innerHTML = `<p class="eyebrow">${escapeHtml(currentLevel)} · ${escapeHtml(topic)}</p><h2>What does this German word mean?</h2><h3>${escapeHtml(currentWord.article ? currentWord.article + " " : "")}${escapeHtml(currentWord.german)}</h3><p class="pron">${escapeHtml(currentWord.pronunciation)}</p><button class="audio" id="quiz-audio">🔊 Listen</button><div class="options">${options.map(o => `<button class="option" data-id="${o.id}">${escapeHtml(o.english)}</button>`).join("")}</div><div class="quiz-actions"><button class="primary" id="submit-answer">Check answer <span>→</span></button></div>`;
  $$("#quiz .option").forEach(b => b.addEventListener("click", () => { $$("#quiz .option").forEach(x => x.classList.remove("selected")); b.classList.add("selected"); selectedAnswer = Number(b.dataset.id); }));
  $("#quiz-audio").onclick = () => speakGerman(`${currentWord.article || ""} ${currentWord.german}`);
  $("#submit-answer").onclick = async () => { if (selectedAnswer === null) return toast("Choose an answer first."); const correct = selectedAnswer === currentWord.id; try { await api("/api/attempt", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({vocab_id:currentWord.id, correct})}); } catch (error) { return toast(error.message); } toast(correct ? "Correct! Gut gemacht 🎉" : `Not quite — ${currentWord.english}`); stats(); setTimeout(() => startQuiz(topic), 700); };
}
async function startExam(level) {
  let words;
  try { words = await api(`/api/vocabulary?level=${level}`); } catch (error) { return toast(error.message); }
  if (words.length < 4) return toast("Not enough vocabulary for an exam.");
  examWords = words.sort(() => Math.random() - .5).slice(0, 50);
  examIndex = 0; examCorrect = 0; showView("practice"); renderExamQuestion(level);
}
function renderExamQuestion(level) {
  const word = examWords[examIndex], distractors = examWords.filter(w => w.id !== word.id).slice(0, 3);
  const options = [word, ...distractors].sort(() => Math.random() - .5);
  $("#quiz").classList.remove("hidden");
  $("#quiz").innerHTML = `<p class="eyebrow">${level} MIXED EXAM · ${examIndex + 1} / ${examWords.length}</p><h2>What does this German word mean?</h2><h3>${escapeHtml(word.article ? word.article + " " : "")}${escapeHtml(word.german)}</h3><button class="audio" id="exam-audio">🔊 Listen</button><div class="options">${options.map(o => `<button class="option" data-id="${o.id}">${escapeHtml(o.english)}</button>`).join("")}</div><div class="quiz-actions"><button class="primary" id="exam-next">Save answer <span>→</span></button></div>`;
  let answer = null;
  $$("#quiz .option").forEach(button => button.onclick = () => { $$("#quiz .option").forEach(x => x.classList.remove("selected")); button.classList.add("selected"); answer = Number(button.dataset.id); });
  $("#exam-audio").onclick = () => speakGerman(`${word.article || ""} ${word.german}`);
  $("#exam-next").onclick = () => {
    if (answer === null) return toast("Choose an answer first.");
    if (answer === word.id) examCorrect += 1;
    examIndex += 1;
    if (examIndex === examWords.length) {
      const percentage = Math.round(examCorrect / examWords.length * 100);
      $("#quiz").innerHTML = `<p class="eyebrow">${level} MIXED EXAM COMPLETE</p><h2>Exam results</h2><p>You scored <strong>${examCorrect} / ${examWords.length}</strong> (${percentage}%).</p><button class="primary" id="back-to-exams">Back to exams <span>→</span></button>`;
      $("#back-to-exams").onclick = () => showView("exams");
    } else renderExamQuestion(level);
  };
}
function startListening() {
  const card = $("#listening-card"); card.classList.remove("hidden");
  card.innerHTML = `<p class="eyebrow">QUESTION 1 / 50</p><h2>What does the speaker say?</h2><p class="pron">Listen carefully. The transcript will appear after you answer.</p><div class="quiz-actions"><button class="primary" id="play-listening">🔊 Play audio</button><button class="audio" id="stop-listening">⏹ Stop</button><button class="audio" id="replay-listening">🔁 Replay</button></div><div class="speed"><button class="audio speed-btn" data-rate=".75">🐢 0.75x</button><button class="audio speed-btn" data-rate="1">▶ 1.0x</button><button class="audio speed-btn" data-rate="1.25">⚡ 1.25x</button></div><div class="options"><button class="option">I go to school.</button><button class="option">I go to work.</button><button class="option">I go home.</button><button class="option">I go to the station.</button></div><button class="primary" id="submit-listening">Submit answer <span>→</span></button>`;
  let rate = 1, sentence = "Ich gehe zur Schule."; listeningSelected = null;
  $("#play-listening").onclick = () => speakGerman(sentence, rate); $("#replay-listening").onclick = () => speakGerman(sentence, rate); $("#stop-listening").onclick = stopGermanAudio;
  $$(".speed-btn").forEach(b => b.onclick = () => { rate = Number(b.dataset.rate); toast(`Playback speed ${rate}x`); });
  $$("#listening-card .option").forEach((b, index) => b.onclick = () => { $$("#listening-card .option").forEach(x => x.classList.remove("selected")); b.classList.add("selected"); listeningSelected = index; });
  $("#submit-listening").onclick = () => {
    if (listeningSelected === null) return toast("Choose an answer first.");
    const correct = listeningSelected === 0;
    $("#listening-card .option").forEach(x => x.disabled = true);
    $("#submit-listening").disabled = true;
    $("#listening-card").insertAdjacentHTML("beforeend", `<div class="result"><p>${correct ? "✅" : "❌"} <strong>${correct ? "Correct!" : "Incorrect"}</strong></p><p>German: ${sentence}<br>English: I go to school.</p><button class="audio" id="listen-again">🔊 Listen again</button><button class="secondary" id="next-listening">Next question →</button></div>`);
    $("#listen-again").onclick = () => speakGerman(sentence, rate);
    $("#next-listening").onclick = startListening;
  };
}
$$("[data-view]").forEach(b => b.addEventListener("click", () => showView(b.dataset.view)));
$$("[data-level]").forEach(b => b.addEventListener("click", () => { currentLevel = b.dataset.level; showView("practice"); loadTopics(currentLevel); }));
$$("[data-practice-level]").forEach(b => b.addEventListener("click", () => { $$(".segmented button").forEach(x => x.classList.remove("selected")); b.classList.add("selected"); loadTopics(b.dataset.practiceLevel); }));
$("#search").addEventListener("input", loadVocabulary); $("#level-filter").addEventListener("change", loadVocabulary); $("#topic-filter").addEventListener("change", loadVocabulary);
$("#start-listening").onclick = startListening;
$$("[data-exam]").forEach(b => b.onclick = () => startExam(b.dataset.exam));
loadTopicPreview(); loadTopicFilter(); stats();
