const editor = document.getElementById("codeEditor");
const highlightLayer = document.getElementById("highlightLayer");
const lineNumbers = document.getElementById("lineNumbers");
const runButton = document.getElementById("runButton");
const readLessonButton = document.getElementById("readLessonButton");
const readOutputButton = document.getElementById("readOutputButton");
const clearButton = document.getElementById("clearButton");
const needHintButton = document.getElementById("needHintButton");
const explainErrorButton = document.getElementById("explainErrorButton");
const lessonTitle = document.getElementById("lessonTitle");
const lessonGoal = document.getElementById("lessonGoal");
const lessonHint = document.getElementById("lessonHint");
const lessonChallenge = document.getElementById("lessonChallenge");
const lessonList = document.getElementById("lessonList");
const builderList = document.getElementById("builderList");
const outputView = document.getElementById("outputView");
const errorBox = document.getElementById("errorBox");
const simpleExplain = document.getElementById("simpleExplain");
const coachMessage = document.getElementById("coachMessage");
const statusBadge = document.getElementById("statusBadge");
const progressBadge = document.getElementById("progressBadge");
const celebrationBadge = document.getElementById("celebrationBadge");
const tipList = document.getElementById("tipList");
const systemMode = document.getElementById("systemMode");
const urlList = document.getElementById("urlList");

const APP_VERSION = "kids-alpha-v1";
const DRAFT_KEY = "alpha-kids-draft";
const PROGRESS_KEY = "alpha-kids-progress";
const ACTIVITY_KEY = "alpha-kids-activity";

let guideState = null;
let activeActivity = null;
let currentErrorLine = null;
let currentErrorColumn = null;
let lastRunResult = null;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function getProgressState() {
    try {
        const raw = localStorage.getItem(PROGRESS_KEY);
        if (!raw) {
            return [];
        }
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function saveProgressState(progressIds) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progressIds));
}

function setStatus(text, mode) {
    statusBadge.textContent = text;
    statusBadge.className = `status ${mode}`;
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
        return "<span class='editor-line tok-placeholder'>Type Alpha code here, then press Run My Code.</span>";
    }

    const highlighted = applySyntaxHighlighting(escapeHtml(source));
    return highlighted
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
    const rows = [];
    for (let index = 1; index <= totalLines; index += 1) {
        const classes = currentErrorLine === index ? "is-error" : "";
        rows.push(`<span class="${classes}">${index}</span>`);
    }
    lineNumbers.innerHTML = rows.join("");
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
}

function speakText(text) {
    if (!("speechSynthesis" in window)) {
        coachMessage.textContent = "This browser cannot speak out loud, but the lesson still works.";
        return;
    }

    const trimmed = String(text || "").trim();
    if (!trimmed) {
        coachMessage.textContent = "There is nothing to read right now.";
        return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(trimmed);
    utterance.rate = 0.96;
    utterance.pitch = 1.08;
    window.speechSynthesis.speak(utterance);
}

function buildSimpleErrorHelp(errorText) {
    const text = String(errorText || "");
    if (!text) {
        return "Your code is okay right now. Keep exploring.";
    }
    if (text.includes("then")) {
        return "One of your if lines needs the word 'then' at the end.";
    }
    if (text.includes("do")) {
        return "A while, repeat, or with line is missing the word 'do'.";
    }
    if (text.includes("end")) {
        return "A block opened, but it did not close with 'end'.";
    }
    if (text.includes("NameError")) {
        return "Alpha saw a name it does not know yet. Check your spelling and make sure you created it with set or function.";
    }
    if (text.includes("SyntaxError")) {
        return "This line has code in the wrong shape. Read the lesson hint and compare your punctuation or keywords.";
    }
    if (text.includes("TypeError")) {
        return "Two pieces of data do not fit together yet. Try changing a number to text with str(...), or check the values you used.";
    }
    return "Read the highlighted line first, then make one small fix and run again.";
}

function showSimpleErrorHelp(text, mode = "show") {
    if (mode === "hide" || !text) {
        simpleExplain.classList.add("hidden");
        simpleExplain.textContent = "";
        return;
    }
    simpleExplain.textContent = text;
    simpleExplain.classList.remove("hidden");
}

function setActiveActivity(activity, options = {}) {
    activeActivity = activity;
    lessonTitle.textContent = activity.title;
    lessonGoal.textContent = activity.goal;
    lessonHint.textContent = activity.hint;
    lessonChallenge.textContent = activity.challenge;
    localStorage.setItem(ACTIVITY_KEY, activity.id);

    if (options.replaceCode !== false) {
        editor.value = `${activity.source.trim()}\n`;
        clearEditorError();
        syncEditorView();
        saveDraft();
    }

    const lessonCards = Array.from(document.querySelectorAll(".lesson-card[data-lesson-id]"));
    lessonCards.forEach((card) => {
        card.classList.toggle("is-active", card.dataset.lessonId === activity.id);
    });

    coachMessage.textContent = `Mission ready: ${activity.goal}`;
}

function updateProgressBadge() {
    const completedIds = getProgressState();
    const total = guideState?.lessons?.length || 0;
    progressBadge.textContent = `${completedIds.length} of ${total} lessons completed`;

    const lessonCards = Array.from(document.querySelectorAll(".lesson-card[data-lesson-id]"));
    lessonCards.forEach((card) => {
        card.classList.toggle("is-complete", completedIds.includes(card.dataset.lessonId));
    });
}

function renderLessons() {
    lessonList.innerHTML = "";
    guideState.lessons.forEach((lesson) => {
        const card = document.createElement("article");
        card.className = "lesson-card";
        card.dataset.lessonId = lesson.id;
        card.innerHTML = `
            <h3>${escapeHtml(lesson.title)}</h3>
            <p>${escapeHtml(lesson.goal)}</p>
            <button type="button" class="secondary">Open Lesson</button>
        `;
        card.querySelector("button").addEventListener("click", () => {
            setActiveActivity(lesson);
        });
        lessonList.appendChild(card);
    });
    updateProgressBadge();
}

function renderBuilders() {
    builderList.innerHTML = "";
    guideState.builders.forEach((builder) => {
        const card = document.createElement("article");
        card.className = "builder-card";
        card.innerHTML = `
            <h3>${escapeHtml(builder.title)}</h3>
            <p>${escapeHtml(builder.description)}</p>
            <button type="button">Build This</button>
        `;
        card.querySelector("button").addEventListener("click", () => {
            setActiveActivity(
                {
                    id: builder.id,
                    title: builder.title,
                    goal: builder.description,
                    hint: builder.tip,
                    challenge: "Change the words, numbers, or names to make it yours.",
                    source: builder.source,
                },
                { replaceCode: true },
            );
            celebrationBadge.textContent = `${builder.title} is loaded and ready to play.`;
        });
        builderList.appendChild(card);
    });
}

function renderTips() {
    tipList.innerHTML = "";
    guideState.coach_tips.forEach((tip) => {
        const item = document.createElement("li");
        item.textContent = tip;
        tipList.appendChild(item);
    });
}

async function refreshSystemInfo() {
    const data = await requestJSON("/api/system");
    systemMode.textContent = data.share_lan
        ? "Live sharing is on. Friends on the same safe Wi-Fi can open Alpha Kids."
        : "Local mode is on. This studio is running on your current computer.";

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

function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) {
        return;
    }

    navigator.serviceWorker.register(`/sw.js?v=${APP_VERSION}`, { updateViaCache: "none" })
        .then((registration) => registration.update().catch(() => {}))
        .catch(() => {});
}

async function runAlpha() {
    setStatus("Running", "working");
    coachMessage.textContent = "Alpha Kids is checking your code now.";
    errorBox.classList.add("hidden");
    showSimpleErrorHelp("", "hide");
    saveDraft();

    try {
        const result = await requestJSON("/api/run", {
            method: "POST",
            body: JSON.stringify({ code: editor.value }),
        });
        lastRunResult = result;
        outputView.textContent = result.output_text || "(Your code ran without printing anything yet.)";

        if (result.error_text) {
            setEditorError(result.error_line, result.error_column);
            syncEditorView();
            errorBox.textContent = result.error_text;
            errorBox.classList.remove("hidden");
            showSimpleErrorHelp(buildSimpleErrorHelp(result.error_text));
            celebrationBadge.textContent = "A tiny bug popped up. Fix it and try again.";
            setStatus("Try Again", "error");
            coachMessage.textContent = "Look for the highlighted line. One small fix can do it.";
            return;
        }

        clearEditorError();
        syncEditorView();
        const celebrationText = guideState.celebrations[
            Math.floor(Math.random() * guideState.celebrations.length)
        ];
        celebrationBadge.textContent = celebrationText;
        setStatus("Success", "success");
        coachMessage.textContent = "Your program worked. Try changing it to make it even more fun.";
        showSimpleErrorHelp("", "hide");

        if (activeActivity && guideState.lessons.some((lesson) => lesson.id === activeActivity.id)) {
            const completedIds = getProgressState();
            if (!completedIds.includes(activeActivity.id)) {
                completedIds.push(activeActivity.id);
                saveProgressState(completedIds);
                updateProgressBadge();
            }
        }
    } catch (error) {
        lastRunResult = null;
        clearEditorError();
        syncEditorView();
        outputView.textContent = "The browser could not talk to Alpha Kids Studio.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        showSimpleErrorHelp("Check that the Python kids server is running, then refresh the page.");
        celebrationBadge.textContent = "The studio connection needs help.";
        setStatus("Offline", "error");
        coachMessage.textContent = "Start the kids server again, then press refresh.";
    }
}

function clearEditor() {
    editor.value = "";
    lastRunResult = null;
    clearEditorError();
    syncEditorView();
    saveDraft();
    outputView.textContent = 'Press "Run My Code" to see your result.';
    errorBox.classList.add("hidden");
    showSimpleErrorHelp("", "hide");
    celebrationBadge.textContent = "Fresh page, fresh ideas.";
    setStatus("Ready", "idle");
    coachMessage.textContent = "The editor is clear. Load a lesson or write your own idea.";
}

function explainCurrentError() {
    if (lastRunResult?.error_text) {
        const helpText = buildSimpleErrorHelp(lastRunResult.error_text);
        showSimpleErrorHelp(helpText);
        coachMessage.textContent = helpText;
        speakText(helpText);
        return;
    }

    const defaultHelp = activeActivity
        ? activeActivity.hint
        : "Try loading a lesson, then compare your code with the example.";
    showSimpleErrorHelp(defaultHelp);
    coachMessage.textContent = defaultHelp;
}

function onEditorInput() {
    clearEditorError();
    syncEditorView();
    saveDraft();
}

editor.addEventListener("input", onEditorInput);
editor.addEventListener("scroll", syncEditorView);
editor.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        runAlpha();
    }
});

runButton.addEventListener("click", runAlpha);
clearButton.addEventListener("click", clearEditor);
needHintButton.addEventListener("click", () => {
    const hintText = activeActivity?.hint || "Pick a lesson card to get a friendly hint.";
    coachMessage.textContent = hintText;
    showSimpleErrorHelp(hintText);
    speakText(hintText);
});
readLessonButton.addEventListener("click", () => {
    const text = [
        lessonTitle.textContent,
        lessonGoal.textContent,
        `Hint: ${lessonHint.textContent}`,
        `Challenge: ${lessonChallenge.textContent}`,
    ].join(". ");
    speakText(text);
});
readOutputButton.addEventListener("click", () => {
    const text = lastRunResult?.error_text || outputView.textContent;
    speakText(text);
});
explainErrorButton.addEventListener("click", explainCurrentError);

window.addEventListener("DOMContentLoaded", async () => {
    registerServiceWorker();
    syncEditorView();

    try {
        const [guide] = await Promise.all([
            requestJSON("/api/guide"),
            refreshSystemInfo(),
        ]);
        guideState = guide;
        document.title = guide.name;
        renderLessons();
        renderBuilders();
        renderTips();

        const savedActivityId = localStorage.getItem(ACTIVITY_KEY);
        const draft = localStorage.getItem(DRAFT_KEY);
        const chosenActivity =
            guide.lessons.find((lesson) => lesson.id === savedActivityId)
            || guide.builders.find((builder) => builder.id === savedActivityId)
            || guide.lessons[0];

        if (guide.lessons.some((lesson) => lesson.id === chosenActivity.id)) {
            setActiveActivity(chosenActivity, { replaceCode: !draft });
        } else {
            setActiveActivity(
                {
                    id: chosenActivity.id,
                    title: chosenActivity.title,
                    goal: chosenActivity.description,
                    hint: chosenActivity.tip,
                    challenge: "Change something small and make it your own.",
                    source: chosenActivity.source,
                },
                { replaceCode: !draft },
            );
        }

        if (draft) {
            editor.value = draft;
            syncEditorView();
        }

        updateProgressBadge();
        celebrationBadge.textContent = "Pick a lesson card and press Run My Code.";
        setStatus("Ready", "idle");
    } catch (error) {
        outputView.textContent = "Alpha Kids Studio could not load.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        showSimpleErrorHelp("Start the kids server with Python, then refresh this page.");
        setStatus("Offline", "error");
    }
});
