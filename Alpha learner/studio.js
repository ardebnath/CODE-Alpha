const editor = document.getElementById("codeEditor");
const highlightLayer = document.getElementById("highlightLayer");
const lineNumbers = document.getElementById("lineNumbers");
const runButton = document.getElementById("runButton");
const nextLessonButton = document.getElementById("nextLessonButton");
const hintButton = document.getElementById("hintButton");
const resetProgressButton = document.getElementById("resetProgressButton");
const clearButton = document.getElementById("clearButton");
const restoreButton = document.getElementById("restoreButton");
const loadQuickWinButton = document.getElementById("loadQuickWinButton");
const markDoneButton = document.getElementById("markDoneButton");
const lessonTitle = document.getElementById("lessonTitle");
const lessonGoal = document.getElementById("lessonGoal");
const lessonHint = document.getElementById("lessonHint");
const lessonChallenge = document.getElementById("lessonChallenge");
const lessonCheckpoint = document.getElementById("lessonCheckpoint");
const completedCount = document.getElementById("completedCount");
const activeTrackName = document.getElementById("activeTrackName");
const statusText = document.getElementById("statusText");
const progressBadge = document.getElementById("progressBadge");
const lessonLevel = document.getElementById("lessonLevel");
const lessonDuration = document.getElementById("lessonDuration");
const lessonKeywords = document.getElementById("lessonKeywords");
const lessonExplain = document.getElementById("lessonExplain");
const coachBox = document.getElementById("coachBox");
const trackList = document.getElementById("trackList");
const quickWinList = document.getElementById("quickWinList");
const outputView = document.getElementById("outputView");
const errorBox = document.getElementById("errorBox");
const friendlyExplain = document.getElementById("friendlyExplain");
const draftStatus = document.getElementById("draftStatus");
const runBadge = document.getElementById("runBadge");
const quizList = document.getElementById("quizList");
const quizScore = document.getElementById("quizScore");
const glossaryList = document.getElementById("glossaryList");
const badgeList = document.getElementById("badgeList");
const coachList = document.getElementById("coachList");
const systemMode = document.getElementById("systemMode");
const urlList = document.getElementById("urlList");

const APP_VERSION = "alpha-learn-v1";
const DRAFT_KEY = "alpha-learn-draft";
const PROGRESS_KEY = "alpha-learn-progress";

let guideState = null;
let activeLesson = null;
let currentErrorLine = null;
let currentErrorColumn = null;
let hintIndex = 0;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function requestJSON(url, options = {}) {
    return fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    }).then(async (response) => {
        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }
        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }
        return data;
    });
}

function readProgressState() {
    try {
        const raw = localStorage.getItem(PROGRESS_KEY);
        if (!raw) {
            return { completed: [], activeLessonId: "", runCount: 0, quizCorrect: [] };
        }
        const parsed = JSON.parse(raw);
        return {
            completed: Array.isArray(parsed.completed) ? parsed.completed : [],
            activeLessonId: String(parsed.activeLessonId || ""),
            runCount: Number.isFinite(Number(parsed.runCount)) ? Number(parsed.runCount) : 0,
            quizCorrect: Array.isArray(parsed.quizCorrect) ? parsed.quizCorrect : [],
        };
    } catch {
        return { completed: [], activeLessonId: "", runCount: 0, quizCorrect: [] };
    }
}

function saveProgressState(progress) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
}

function updateProgress(mutator) {
    const next = readProgressState();
    mutator(next);
    saveProgressState(next);
    renderProgress();
    return next;
}

function setStatus(modeText, detailText) {
    statusText.textContent = modeText;
    coachBox.textContent = detailText;
}

function applySyntaxHighlighting(html) {
    let highlighted = html;

    highlighted = highlighted.replace(
        /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g,
        "<span class='tok-string'>$1</span>",
    );
    highlighted = highlighted.replace(
        /(^|\s)([#$].*)$/gm,
        "$1<span class='tok-comment'>$2</span>",
    );
    highlighted = highlighted.replace(
        /\b(note|set|if|otherwise|unless|while|repeat|class|function|package|give|use|try|catch|finally|with|end|stop|skip|assert|raise)\b/g,
        "<span class='tok-keyword'>$1</span>",
    );
    highlighted = highlighted.replace(
        /\b(true|false|nothing|null)\b/gi,
        "<span class='tok-boolean'>$1</span>",
    );
    highlighted = highlighted.replace(
        /\b(\d+(?:\.\d+)?)\b/g,
        "<span class='tok-number'>$1</span>",
    );
    highlighted = highlighted.replace(
        /\b([A-Za-z_]\w*)(?=\()/g,
        "<span class='tok-function'>$1</span>",
    );

    return highlighted;
}

function highlightAlpha(source) {
    if (!source) {
        return "<span class='editor-line tok-placeholder'>Start from a lesson, then edit the code here.</span>";
    }

    return applySyntaxHighlighting(escapeHtml(source))
        .split("\n")
        .map((line, index) => {
            const classes = ["editor-line"];
            if (currentErrorLine === index + 1) {
                classes.push("editor-line-error");
            }
            return `<span class="${classes.join(" ")}">${line || "&nbsp;"}</span>`;
        })
        .join("");
}

function updateLineNumbers() {
    const totalLines = editor.value.split("\n").length;
    const items = [];
    for (let index = 1; index <= totalLines; index += 1) {
        const classes = currentErrorLine === index ? "is-error" : "";
        items.push(`<span class="${classes}">${index}</span>`);
    }
    lineNumbers.innerHTML = items.join("");
}

function syncEditorView() {
    highlightLayer.innerHTML = `${highlightAlpha(editor.value)}\n`;
    highlightLayer.scrollTop = editor.scrollTop;
    highlightLayer.scrollLeft = editor.scrollLeft;
    lineNumbers.scrollTop = editor.scrollTop;
    updateLineNumbers();
}

function clearEditorError() {
    currentErrorLine = null;
    currentErrorColumn = null;
}

function setEditorError(lineNumber, columnNumber = null) {
    currentErrorLine = Number.isFinite(Number(lineNumber)) ? Number(lineNumber) : null;
    currentErrorColumn = Number.isFinite(Number(columnNumber)) ? Number(columnNumber) : null;
}

function saveDraft() {
    localStorage.setItem(DRAFT_KEY, editor.value);
    draftStatus.textContent = "Draft saved in this browser.";
}

function loadDraft() {
    const draft = localStorage.getItem(DRAFT_KEY);
    return typeof draft === "string" ? draft : "";
}

function buildFriendlyError(errorText) {
    const text = String(errorText || "");
    if (!text) {
        return "";
    }
    if (text.includes("then")) {
        return "One of your condition lines needs the word 'then'. Compare it with the lesson example.";
    }
    if (text.includes("end")) {
        return "A block was opened, but Alpha did not find the matching end yet.";
    }
    if (text.includes("NameError")) {
        return "Alpha found a name that was never created. Check your spelling and use set or function first.";
    }
    if (text.includes("SyntaxError")) {
        return "The code shape is off on the highlighted line. Read that line slowly and compare it with the lesson.";
    }
    if (text.includes("TypeError")) {
        return "Two values are not fitting together yet. You may need str(...) for text or a different variable value.";
    }
    return "Read the highlighted line, change one small thing, and run again.";
}

function renderTrackCards() {
    trackList.innerHTML = "";
    guideState.tracks.forEach((track) => {
        const lessons = guideState.lessons.filter((lesson) => lesson.track_id === track.id);
        const trackCard = document.createElement("article");
        trackCard.className = "track-card";
        trackCard.innerHTML = `
            <div class="track-head">
                <div>
                    <h3>${escapeHtml(track.title)}</h3>
                    <p>${escapeHtml(track.summary)}</p>
                </div>
                <span class="track-tag">${escapeHtml(track.goal)}</span>
            </div>
            <div class="lesson-list"></div>
        `;

        const lessonList = trackCard.querySelector(".lesson-list");
        lessons.forEach((lesson) => {
            const lessonCard = document.createElement("button");
            lessonCard.type = "button";
            lessonCard.className = "lesson-card";
            lessonCard.dataset.lessonId = lesson.id;
            lessonCard.innerHTML = `
                <strong>${escapeHtml(lesson.title)}</strong>
                <span>${escapeHtml(lesson.level)} · ${escapeHtml(lesson.duration)}</span>
                <p>${escapeHtml(lesson.goal)}</p>
            `;
            lessonCard.addEventListener("click", () => {
                setActiveLesson(lesson, { replaceCode: true, updateDraft: true });
            });
            lessonList.appendChild(lessonCard);
        });

        trackList.appendChild(trackCard);
    });
}

function renderQuickWins() {
    quickWinList.innerHTML = "";
    guideState.quick_wins.forEach((quickWin, index) => {
        const card = document.createElement("article");
        card.className = "quick-win-card";
        card.innerHTML = `
            <h3>${escapeHtml(quickWin.title)}</h3>
            <p>${escapeHtml(quickWin.description)}</p>
            <button type="button">Load</button>
        `;
        card.querySelector("button").addEventListener("click", () => {
            editor.value = `${quickWin.source.trim()}\n`;
            clearEditorError();
            syncEditorView();
            saveDraft();
            setStatus("Quick win loaded", `${quickWin.title} is now in the editor.`);
            runBadge.textContent = `Quick win ${index + 1} loaded`;
        });
        quickWinList.appendChild(card);
    });
}

function renderGlossary() {
    glossaryList.innerHTML = "";
    guideState.glossary.forEach((item) => {
        const card = document.createElement("article");
        card.className = "glossary-card";
        card.innerHTML = `
            <strong>${escapeHtml(item.term)}</strong>
            <p>${escapeHtml(item.meaning)}</p>
        `;
        glossaryList.appendChild(card);
    });
}

function renderCoachNotes() {
    coachList.innerHTML = "";
    guideState.coach_notes.forEach((note) => {
        const item = document.createElement("li");
        item.textContent = note;
        coachList.appendChild(item);
    });
}

function renderBadges() {
    const progress = readProgressState();
    const completedCountValue = progress.completed.length;
    const earnedTrackIds = guideState.tracks.filter((track) => {
        const trackLessons = guideState.lessons.filter((lesson) => lesson.track_id === track.id);
        return trackLessons.length > 0 && trackLessons.every((lesson) => progress.completed.includes(lesson.id));
    }).map((track) => track.id);

    const badges = [
        { title: "First Run", detail: "Run Alpha code once.", earned: progress.runCount >= 1 },
        { title: "Lesson Starter", detail: "Complete your first lesson.", earned: completedCountValue >= 1 },
        { title: "Path Walker", detail: "Complete three lessons.", earned: completedCountValue >= 3 },
        { title: "Track Finisher", detail: "Finish one full track.", earned: earnedTrackIds.length >= 1 },
        { title: "Alpha Builder", detail: "Complete all Alpha Learn lessons.", earned: completedCountValue === guideState.lessons.length },
    ];

    badgeList.innerHTML = "";
    badges.forEach((badge) => {
        const card = document.createElement("article");
        card.className = `badge-card-mini ${badge.earned ? "is-earned" : "is-locked"}`;
        card.innerHTML = `
            <strong>${escapeHtml(badge.title)}</strong>
            <p>${escapeHtml(badge.detail)}</p>
        `;
        badgeList.appendChild(card);
    });
}

function renderQuiz() {
    const progress = readProgressState();
    quizList.innerHTML = "";
    quizScore.textContent = `${progress.quizCorrect.length} correct`;

    guideState.quizzes.forEach((quiz) => {
        const card = document.createElement("article");
        card.className = "quiz-card";
        card.innerHTML = `
            <h3>${escapeHtml(quiz.question)}</h3>
            <div class="quiz-options"></div>
            <div class="quiz-result" data-result="${escapeHtml(quiz.id)}"></div>
        `;

        const optionBox = card.querySelector(".quiz-options");
        const resultBox = card.querySelector(".quiz-result");

        quiz.options.forEach((option, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = option;
            button.addEventListener("click", () => {
                const correct = index === quiz.answer_index;
                updateProgress((state) => {
                    if (correct && !state.quizCorrect.includes(quiz.id)) {
                        state.quizCorrect.push(quiz.id);
                    }
                });
                resultBox.textContent = correct
                    ? `Correct. ${quiz.explain}`
                    : `Not yet. ${quiz.explain}`;
                renderQuiz();
            });
            optionBox.appendChild(button);
        });

        if (progress.quizCorrect.includes(quiz.id)) {
            resultBox.textContent = `Correct. ${quiz.explain}`;
        }

        quizList.appendChild(card);
    });
}

function renderProgress() {
    const progress = readProgressState();
    completedCount.textContent = `${progress.completed.length} lessons`;
    progressBadge.textContent = `${progress.completed.length} / ${guideState.lessons.length} complete`;

    document.querySelectorAll(".lesson-card[data-lesson-id]").forEach((card) => {
        const lessonId = card.dataset.lessonId;
        card.classList.toggle("is-complete", progress.completed.includes(lessonId));
        card.classList.toggle("is-active", lessonId === activeLesson?.id);
    });

    renderBadges();
    renderQuiz();
}

function setActiveLesson(lesson, options = {}) {
    activeLesson = lesson;
    hintIndex = 0;
    lessonTitle.textContent = lesson.title;
    lessonGoal.textContent = lesson.goal;
    lessonHint.textContent = lesson.hint;
    lessonChallenge.textContent = lesson.challenge;
    lessonCheckpoint.textContent = lesson.checkpoint;
    lessonLevel.textContent = lesson.level;
    lessonDuration.textContent = lesson.duration;
    lessonKeywords.textContent = lesson.keywords.join(" · ");
    lessonExplain.textContent = lesson.explain;
    activeTrackName.textContent = guideState.tracks.find((track) => track.id === lesson.track_id)?.title || "Learning";

    if (options.replaceCode !== false) {
        editor.value = `${lesson.source.trim()}\n`;
        clearEditorError();
        syncEditorView();
    }

    if (options.updateDraft !== false) {
        saveDraft();
    }

    updateProgress((state) => {
        state.activeLessonId = lesson.id;
    });

    setStatus("Lesson ready", lesson.goal);
    renderProgress();
}

function pickNextLesson() {
    if (!activeLesson) {
        return guideState.lessons[0];
    }
    const currentIndex = guideState.lessons.findIndex((lesson) => lesson.id === activeLesson.id);
    return guideState.lessons[(currentIndex + 1) % guideState.lessons.length];
}

async function refreshSystemInfo() {
    const data = await requestJSON("/api/system");
    systemMode.textContent = data.share_lan
        ? "Live sharing is enabled for trusted devices on the same Wi-Fi."
        : "Local mode is enabled for this current device.";

    urlList.innerHTML = "";
    data.urls.forEach((url) => {
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.textContent = url;
        anchor.target = "_blank";
        anchor.rel = "noreferrer";
        urlList.appendChild(anchor);
    });
}

async function runAlpha() {
    setStatus("Running lesson", "Alpha is checking your code now.");
    errorBox.classList.add("hidden");
    friendlyExplain.classList.add("hidden");
    saveDraft();

    try {
        const result = await requestJSON("/api/run", {
            method: "POST",
            body: JSON.stringify({ code: editor.value }),
        });

        outputView.textContent = result.output_text || "(Program completed with no output)";
        runBadge.textContent = `Run #${result.run_id} · ${Number(result.duration_ms).toFixed(2)} ms`;
        updateProgress((state) => {
            state.runCount += 1;
        });

        if (result.error_text) {
            setEditorError(result.error_line, result.error_column);
            syncEditorView();
            errorBox.textContent = result.error_text;
            errorBox.classList.remove("hidden");
            friendlyExplain.textContent = buildFriendlyError(result.error_text);
            friendlyExplain.classList.remove("hidden");
            setStatus("Needs one fix", "Read the highlighted line and make one small correction.");
            return;
        }

        clearEditorError();
        syncEditorView();
        updateProgress((state) => {
            if (activeLesson && !state.completed.includes(activeLesson.id)) {
                state.completed.push(activeLesson.id);
            }
        });
        setStatus("Lesson success", "Nice work. Your code ran successfully.");
        if (activeLesson) {
            coachBox.textContent = `Completed: ${activeLesson.title}. You can improve it or move to the next lesson.`;
        }
    } catch (error) {
        clearEditorError();
        syncEditorView();
        outputView.textContent = "The Alpha Learn server could not be reached.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        friendlyExplain.textContent = "The lesson app could not reach the Alpha runtime. Check whether the server is still running.";
        friendlyExplain.classList.remove("hidden");
        setStatus("Server issue", "Alpha Learn could not talk to the local server.");
    }
}

function resetProgress() {
    localStorage.removeItem(PROGRESS_KEY);
    if (guideState?.lessons?.length) {
        setActiveLesson(guideState.lessons[0], { replaceCode: false, updateDraft: false });
    }
    renderProgress();
    setStatus("Progress reset", "Your lesson progress was cleared in this browser.");
}

function clearEditor() {
    editor.value = "";
    clearEditorError();
    syncEditorView();
    saveDraft();
    outputView.textContent = "Run a lesson to see Alpha output here.";
    errorBox.classList.add("hidden");
    friendlyExplain.classList.add("hidden");
    setStatus("Editor cleared", "You can restore the lesson or load a quick win.");
}

function restoreLesson() {
    if (!activeLesson) {
        return;
    }
    setActiveLesson(activeLesson, { replaceCode: true, updateDraft: true });
    setStatus("Lesson restored", "The original lesson code is back in the editor.");
}

function showNextHint() {
    if (!activeLesson) {
        return;
    }
    const hintOptions = [
        activeLesson.hint,
        `Checkpoint: ${activeLesson.checkpoint}`,
        `Challenge: ${activeLesson.challenge}`,
        `Keywords to use: ${activeLesson.keywords.join(", ")}`,
    ];
    coachBox.textContent = hintOptions[hintIndex % hintOptions.length];
    hintIndex += 1;
}

function loadRandomQuickWin() {
    if (!guideState.quick_wins.length) {
        return;
    }
    const index = Math.floor(Math.random() * guideState.quick_wins.length);
    const quickWin = guideState.quick_wins[index];
    editor.value = `${quickWin.source.trim()}\n`;
    clearEditorError();
    syncEditorView();
    saveDraft();
    setStatus("Quick win loaded", quickWin.description);
}

async function initialize() {
    guideState = await requestJSON("/api/guide");
    renderTrackCards();
    renderQuickWins();
    renderGlossary();
    renderCoachNotes();
    await refreshSystemInfo();

    const progress = readProgressState();
    const savedLesson = guideState.lessons.find((lesson) => lesson.id === progress.activeLessonId);
    const initialLesson = savedLesson || guideState.lessons[0];
    const draft = loadDraft();

    setActiveLesson(initialLesson, { replaceCode: false, updateDraft: false });
    editor.value = draft || `${initialLesson.source.trim()}\n`;
    syncEditorView();
    renderProgress();
    draftStatus.textContent = draft ? "Draft restored from this browser." : "Draft autosave is ready.";
}

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register(`/sw.js?v=${APP_VERSION}`, { updateViaCache: "none" }).catch(() => {});
}

editor.addEventListener("input", () => {
    clearEditorError();
    syncEditorView();
    saveDraft();
});
editor.addEventListener("scroll", syncEditorView);
editor.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        runAlpha();
    }
});

runButton.addEventListener("click", runAlpha);
nextLessonButton.addEventListener("click", () => {
    setActiveLesson(pickNextLesson(), { replaceCode: true, updateDraft: true });
});
hintButton.addEventListener("click", showNextHint);
resetProgressButton.addEventListener("click", resetProgress);
clearButton.addEventListener("click", clearEditor);
restoreButton.addEventListener("click", restoreLesson);
loadQuickWinButton.addEventListener("click", loadRandomQuickWin);
markDoneButton.addEventListener("click", () => {
    if (!activeLesson) {
        return;
    }
    updateProgress((state) => {
        if (!state.completed.includes(activeLesson.id)) {
            state.completed.push(activeLesson.id);
        }
    });
    setStatus("Marked complete", `${activeLesson.title} is now completed in your progress.`);
});

initialize().catch((error) => {
    lessonTitle.textContent = "Alpha Learn could not start";
    lessonGoal.textContent = error.message;
    outputView.textContent = "Start the Alpha Learn server and refresh the browser.";
});
