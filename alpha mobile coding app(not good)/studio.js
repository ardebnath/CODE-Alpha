const editor = document.getElementById("codeEditor");
const highlightLayer = document.getElementById("highlightLayer");
const lineNumbers = document.getElementById("lineNumbers");
const runButton = document.getElementById("runButton");
const saveButton = document.getElementById("saveButton");
const clearButton = document.getElementById("clearButton");
const bottomRunButton = document.getElementById("bottomRunButton");
const bottomSampleButton = document.getElementById("bottomSampleButton");
const bottomSaveButton = document.getElementById("bottomSaveButton");
const bottomResultButton = document.getElementById("bottomResultButton");
const installButton = document.getElementById("installButton");
const speakOutputButton = document.getElementById("speakOutputButton");
const refreshSavedButton = document.getElementById("refreshSavedButton");
const noteNameInput = document.getElementById("noteNameInput");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const outputView = document.getElementById("outputView");
const pythonView = document.getElementById("pythonView");
const errorBox = document.getElementById("errorBox");
const systemMode = document.getElementById("systemMode");
const snippetRow = document.getElementById("snippetRow");
const sampleList = document.getElementById("sampleList");
const savedList = document.getElementById("savedList");
const tipList = document.getElementById("tipList");
const urlList = document.getElementById("urlList");
const tabButtons = Array.from(document.querySelectorAll(".tab-button[data-tab]"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel[data-tab-panel]"));

const APP_VERSION = "alpha-mobile-v1";
const DRAFT_KEY = "alpha-mobile-draft";
const NOTEBOOK_KEY = "alpha-mobile-notebooks";
const ACTIVE_TAB_KEY = "alpha-mobile-tab";

let guideState = null;
let currentErrorLine = null;
let currentErrorColumn = null;
let activeTab = localStorage.getItem(ACTIVE_TAB_KEY) || "code";
let deferredInstallPrompt = null;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function setStatus(text, mode, detail = "") {
    statusBadge.textContent = text;
    statusBadge.className = `status ${mode}`;
    statusText.textContent = detail || "Ready.";
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

function readNotebooks() {
    try {
        const raw = localStorage.getItem(NOTEBOOK_KEY);
        if (!raw) {
            return [];
        }
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function writeNotebooks(notebooks) {
    localStorage.setItem(NOTEBOOK_KEY, JSON.stringify(notebooks));
}

function saveDraft() {
    const draft = {
        name: noteNameInput.value,
        code: editor.value,
    };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

function loadDraft() {
    try {
        const raw = localStorage.getItem(DRAFT_KEY);
        if (!raw) {
            return null;
        }
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === "object" ? parsed : null;
    } catch {
        return null;
    }
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
        return "<span class='editor-line tok-placeholder'>Type Alpha code here, or load a sample card.</span>";
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

function setActiveTab(tabName) {
    activeTab = tabName;
    localStorage.setItem(ACTIVE_TAB_KEY, tabName);
    tabButtons.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.tab === tabName);
    });
    tabPanels.forEach((panel) => {
        const isActive = panel.dataset.tabPanel === tabName;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
    });
}

function insertTextAtCursor(insertText) {
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const currentText = editor.value;
    editor.value = `${currentText.slice(0, start)}${insertText}${currentText.slice(end)}`;
    const nextPosition = start + insertText.length;
    editor.selectionStart = nextPosition;
    editor.selectionEnd = nextPosition;
    editor.focus();
    saveDraft();
    syncEditorView();
}

function renderSnippets() {
    snippetRow.innerHTML = "";
    guideState.quick_snippets.forEach((snippet) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "snippet-chip";
        button.textContent = snippet.title;
        button.addEventListener("click", () => {
            insertTextAtCursor(snippet.insert);
            setStatus("Inserted", "idle", `${snippet.title} snippet added to the editor.`);
        });
        snippetRow.appendChild(button);
    });
}

function renderSamples() {
    sampleList.innerHTML = "";
    guideState.featured_samples.forEach((sample) => {
        const card = document.createElement("article");
        card.className = "sample-card";
        card.innerHTML = `
            <h3>${escapeHtml(sample.title)}</h3>
            <p>${escapeHtml(sample.source.split("\n")[0] || "Alpha sample")}</p>
            <div class="card-actions">
                <button class="secondary" type="button">Load Sample</button>
            </div>
        `;
        card.querySelector("button").addEventListener("click", () => {
            noteNameInput.value = sample.key;
            editor.value = `${sample.source.trim()}\n`;
            clearEditorError();
            syncEditorView();
            saveDraft();
            setActiveTab("code");
            setStatus("Sample loaded", "idle", `${sample.title} is ready to run.`);
        });
        sampleList.appendChild(card);
    });
}

function renderTips() {
    tipList.innerHTML = "";
    guideState.tips.forEach((tip) => {
        const item = document.createElement("li");
        item.textContent = tip;
        tipList.appendChild(item);
    });
}

function renderSavedNotebooks() {
    const notebooks = readNotebooks();
    savedList.innerHTML = "";

    if (!notebooks.length) {
        savedList.innerHTML = "<p class='tok-placeholder'>Save your first mobile Alpha notebook on this device.</p>";
        return;
    }

    notebooks.forEach((notebook) => {
        const card = document.createElement("article");
        card.className = "saved-card";
        card.innerHTML = `
            <h3>${escapeHtml(notebook.name)}</h3>
            <p>${escapeHtml(notebook.updated_at)}</p>
            <div class="card-actions">
                <button class="secondary" type="button">Open</button>
                <button type="button">Delete</button>
            </div>
        `;

        const [openButton, deleteButton] = card.querySelectorAll("button");
        openButton.addEventListener("click", () => {
            noteNameInput.value = notebook.name;
            editor.value = notebook.code;
            clearEditorError();
            syncEditorView();
            saveDraft();
            setActiveTab("code");
            setStatus("Opened", "success", `${notebook.name} loaded from this device.`);
        });
        deleteButton.addEventListener("click", () => {
            const next = readNotebooks().filter((item) => item.name !== notebook.name);
            writeNotebooks(next);
            renderSavedNotebooks();
            setStatus("Deleted", "idle", `${notebook.name} removed from local saves.`);
        });
        savedList.appendChild(card);
    });
}

function saveCurrentNotebook() {
    const name = noteNameInput.value.trim();
    if (!name) {
        setStatus("Name needed", "error", "Give your notebook a name before saving.");
        return;
    }

    const notebooks = readNotebooks().filter((item) => item.name !== name);
    notebooks.unshift({
        name,
        code: editor.value,
        updated_at: new Date().toLocaleString(),
    });
    writeNotebooks(notebooks.slice(0, 20));
    saveDraft();
    renderSavedNotebooks();
    setStatus("Saved", "success", `${name} is saved on this device.`);
}

async function refreshSystemInfo() {
    const data = await requestJSON("/api/system");
    systemMode.textContent = data.share_lan
        ? "Shared on local Wi-Fi"
        : "Local phone mode";

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

function registerInstallPrompt() {
    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredInstallPrompt = event;
        installButton.classList.remove("hidden");
    });

    installButton.addEventListener("click", async () => {
        if (!deferredInstallPrompt) {
            return;
        }
        deferredInstallPrompt.prompt();
        await deferredInstallPrompt.userChoice;
        deferredInstallPrompt = null;
        installButton.classList.add("hidden");
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

function speakOutput() {
    if (!("speechSynthesis" in window)) {
        setStatus("No speech", "idle", "This browser cannot read output aloud.");
        return;
    }
    const text = errorBox.classList.contains("hidden")
        ? outputView.textContent
        : errorBox.textContent;
    if (!text.trim()) {
        return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
}

async function runAlpha() {
    setStatus("Running", "working", "Executing Alpha code...");
    errorBox.classList.add("hidden");
    saveDraft();

    try {
        const result = await requestJSON("/api/run", {
            method: "POST",
            body: JSON.stringify({ code: editor.value }),
        });

        outputView.textContent = result.output_text || "(Program completed with no output)";
        pythonView.textContent = result.translated_code || "(No translated Python was generated)";

        if (result.error_text) {
            setEditorError(result.error_line, result.error_column);
            syncEditorView();
            errorBox.textContent = result.error_text;
            errorBox.classList.remove("hidden");
            setStatus("Error", "error", result.error_text);
        } else {
            clearEditorError();
            syncEditorView();
            setStatus(
                "Success",
                "success",
                `Run #${result.run_id} finished in ${Number(result.duration_ms).toFixed(2)} ms.`,
            );
        }

        setActiveTab("result");
    } catch (error) {
        clearEditorError();
        syncEditorView();
        outputView.textContent = "The browser could not talk to Alpha Mobile Coding App.";
        pythonView.textContent = "";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Offline", "error", "Start the Python mobile app server and try again.");
        setActiveTab("result");
    }
}

function clearEditor() {
    editor.value = "";
    clearEditorError();
    syncEditorView();
    outputView.textContent = "Run Alpha code to see the result.";
    pythonView.textContent = "Translated Python will appear here.";
    errorBox.classList.add("hidden");
    saveDraft();
    setStatus("Ready", "idle", "The editor is clear.");
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

noteNameInput.addEventListener("input", saveDraft);
runButton.addEventListener("click", runAlpha);
saveButton.addEventListener("click", saveCurrentNotebook);
clearButton.addEventListener("click", clearEditor);
bottomRunButton.addEventListener("click", runAlpha);
bottomSaveButton.addEventListener("click", saveCurrentNotebook);
bottomSampleButton.addEventListener("click", () => setActiveTab("samples"));
bottomResultButton.addEventListener("click", () => setActiveTab("result"));
speakOutputButton.addEventListener("click", speakOutput);
refreshSavedButton.addEventListener("click", renderSavedNotebooks);

tabButtons.forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.tab));
});

window.addEventListener("DOMContentLoaded", async () => {
    setActiveTab(activeTab);
    registerInstallPrompt();
    registerServiceWorker();
    syncEditorView();

    try {
        const [guide] = await Promise.all([
            requestJSON("/api/guide"),
            refreshSystemInfo(),
        ]);
        guideState = guide;
        document.title = guide.name;
        renderSnippets();
        renderSamples();
        renderTips();
        renderSavedNotebooks();

        const draft = loadDraft();
        if (draft) {
            noteNameInput.value = draft.name || noteNameInput.value;
            editor.value = draft.code || "";
        } else if (guide.featured_samples.length) {
            noteNameInput.value = guide.featured_samples[0].key;
            editor.value = `${guide.featured_samples[0].source.trim()}\n`;
        }

        syncEditorView();
        setStatus("Ready", "idle", "Mobile Alpha is ready to code.");
    } catch (error) {
        outputView.textContent = "Alpha Mobile Coding App could not load.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Load failed", "error", "Start the Python mobile app server and refresh.");
        setActiveTab("result");
    }
});
