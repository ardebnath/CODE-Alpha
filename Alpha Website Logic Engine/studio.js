const editor = document.getElementById("codeEditor");
const highlightLayer = document.getElementById("highlightLayer");
const lineNumbers = document.getElementById("lineNumbers");
const runButton = document.getElementById("runButton");
const saveButton = document.getElementById("saveButton");
const clearButton = document.getElementById("clearButton");
const apiExampleButton = document.getElementById("apiExampleButton");
const templateList = document.getElementById("templateList");
const savedList = document.getElementById("savedList");
const formDataInput = document.getElementById("formDataInput");
const adminDataInput = document.getElementById("adminDataInput");
const apiExampleView = document.getElementById("apiExampleView");
const outputView = document.getElementById("outputView");
const responseView = document.getElementById("responseView");
const pythonView = document.getElementById("pythonView");
const errorBox = document.getElementById("errorBox");
const scriptNameInput = document.getElementById("scriptNameInput");
const scriptDescriptionInput = document.getElementById("scriptDescriptionInput");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const logList = document.getElementById("logList");
const tipList = document.getElementById("tipList");
const featureList = document.getElementById("featureList");
const systemMode = document.getElementById("systemMode");
const savedCount = document.getElementById("savedCount");
const urlList = document.getElementById("urlList");

const APP_VERSION = "alpha-web-engine-v1";
const DRAFT_KEY = "alpha-web-engine-draft";

let guideState = null;
let currentErrorLine = null;
let currentErrorColumn = null;
let activeTemplateKey = null;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function requestJSON(url, options = {}) {
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    return fetch(url, {
        ...options,
        headers,
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

function setStatus(text, mode, detail = "") {
    statusBadge.textContent = text;
    statusBadge.className = `status ${mode}`;
    statusText.textContent = detail || "Ready.";
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
        return "<span class='editor-line tok-placeholder'>Load a template or write Alpha website logic here...</span>";
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
    const draft = {
        scriptName: scriptNameInput.value,
        description: scriptDescriptionInput.value,
        code: editor.value,
        formData: formDataInput.value,
        adminData: adminDataInput.value,
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
        if (!parsed || typeof parsed !== "object") {
            return null;
        }
        return parsed;
    } catch {
        return null;
    }
}

function parseJsonInput(text, label) {
    try {
        const parsed = JSON.parse(text || "{}");
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
            throw new Error(`${label} must be a JSON object.`);
        }
        return parsed;
    } catch (error) {
        throw new Error(`${label} is not valid JSON. ${error.message}`);
    }
}

function setFormAndAdminDefaults() {
    formDataInput.value = `${JSON.stringify(guideState.default_form_data, null, 2)}\n`;
    adminDataInput.value = `${JSON.stringify(guideState.default_admin_data, null, 2)}\n`;
}

function updateApiExample() {
    const scriptKey = scriptNameInput.value.trim().toLowerCase().replace(/\s+/g, "_") || "contact_form";
    let formData = {};
    let adminData = {};
    try {
        formData = parseJsonInput(formDataInput.value, "Form Data");
        adminData = parseJsonInput(adminDataInput.value, "Admin Data");
    } catch (error) {
        apiExampleView.textContent = error.message;
        return;
    }

    apiExampleView.textContent = JSON.stringify(
        {
            route: "/api/public/execute",
            method: "POST",
            payload: {
                script_key: scriptKey,
                form_data: formData,
                admin_data: adminData,
            },
        },
        null,
        2,
    );
}

function renderTips() {
    tipList.innerHTML = "";
    featureList.innerHTML = "";

    guideState.tips.forEach((tip) => {
        const item = document.createElement("li");
        item.textContent = tip;
        tipList.appendChild(item);
    });

    guideState.features.forEach((feature) => {
        const item = document.createElement("li");
        item.textContent = feature;
        featureList.appendChild(item);
    });
}

function loadTemplate(template) {
    activeTemplateKey = template.key;
    scriptNameInput.value = template.key;
    scriptDescriptionInput.value = template.description;
    editor.value = `${template.source.trim()}\n`;
    clearEditorError();
    syncEditorView();
    saveDraft();
    updateApiExample();
    setStatus("Template loaded", "idle", `${template.title} is ready in the editor.`);
}

function renderTemplates() {
    templateList.innerHTML = "";
    guideState.templates.forEach((template) => {
        const card = document.createElement("article");
        card.className = "template-card";
        card.innerHTML = `
            <h3>${escapeHtml(template.title)}</h3>
            <p>${escapeHtml(template.description)}</p>
            <div class="card-actions">
                <button class="secondary" type="button">Load Template</button>
            </div>
        `;
        card.querySelector("button").addEventListener("click", () => loadTemplate(template));
        templateList.appendChild(card);
    });
}

function renderSavedScripts(savedScripts) {
    savedCount.textContent = String(savedScripts.length);
    savedList.innerHTML = "";

    if (!savedScripts.length) {
        savedList.innerHTML = "<p class='tok-placeholder'>Save your first reusable website logic script here.</p>";
        return;
    }

    savedScripts.forEach((script) => {
        const card = document.createElement("article");
        card.className = "saved-card";
        card.innerHTML = `
            <h3>${escapeHtml(script.name)}</h3>
            <p>${escapeHtml(script.description || "No description yet.")}</p>
            <p>Path: ${escapeHtml(script.path)}</p>
            <div class="card-actions">
                <button class="secondary" type="button">Load</button>
                <button type="button">Delete</button>
            </div>
        `;

        const [loadButton, deleteButton] = card.querySelectorAll("button");
        loadButton.addEventListener("click", () => loadSavedScript(script.key));
        deleteButton.addEventListener("click", () => deleteSavedScript(script.key, script.name));
        savedList.appendChild(card);
    });
}

function renderLogs(logs) {
    logList.innerHTML = "";

    if (!logs.length) {
        logList.innerHTML = "<p class='tok-placeholder'>Run a script to create website engine logs.</p>";
        return;
    }

    logs.forEach((log) => {
        const card = document.createElement("article");
        card.className = "log-card";
        const resultText = JSON.stringify(log.website_result ?? {}, null, 2);
        card.innerHTML = `
            <strong>${escapeHtml(log.script_name || "unsaved_logic")}</strong>
            <div class="log-meta">
                <span>${escapeHtml(log.logged_at || "")}</span>
                <span>${escapeHtml(log.status || "")}</span>
                <span>${escapeHtml(String(log.duration_ms || 0))} ms</span>
            </div>
            <p>${escapeHtml(log.error_text || log.output_text || "Run completed without extra output.")}</p>
            <pre>${escapeHtml(resultText)}</pre>
        `;
        logList.appendChild(card);
    });
}

async function refreshLogs() {
    const data = await requestJSON("/api/logs");
    renderLogs(data.logs || []);
}

async function refreshSystemInfo() {
    const data = await requestJSON("/api/system");
    systemMode.textContent = data.share_lan
        ? "LAN shared mode"
        : "Local engine mode";

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

async function loadSavedScript(scriptKey) {
    try {
        const data = await requestJSON("/api/scripts/load", {
            method: "POST",
            body: JSON.stringify({ script_key: scriptKey }),
        });
        scriptNameInput.value = data.script.name;
        scriptDescriptionInput.value = data.script.description;
        editor.value = `${String(data.code || "").replace(/\s+$/u, "")}\n`;
        clearEditorError();
        syncEditorView();
        saveDraft();
        updateApiExample();
        setStatus("Script loaded", "idle", `${data.script.name} is ready in the editor.`);
    } catch (error) {
        setStatus("Load failed", "error", error.message);
    }
}

async function deleteSavedScript(scriptKey, scriptName) {
    if (!window.confirm(`Delete saved script "${scriptName}"?`)) {
        return;
    }

    try {
        const data = await requestJSON("/api/scripts/delete", {
            method: "POST",
            body: JSON.stringify({ script_key: scriptKey }),
        });
        renderSavedScripts(data.saved_scripts || []);
        setStatus("Deleted", "success", `${scriptName} was removed from saved scripts.`);
    } catch (error) {
        setStatus("Delete failed", "error", error.message);
    }
}

async function saveScript() {
    try {
        const data = await requestJSON("/api/scripts/save", {
            method: "POST",
            body: JSON.stringify({
                name: scriptNameInput.value,
                description: scriptDescriptionInput.value,
                code: editor.value,
            }),
        });
        renderSavedScripts(data.saved_scripts || []);
        setStatus("Saved", "success", `${data.script.name} is saved and ready for public execute calls.`);
    } catch (error) {
        setStatus("Save failed", "error", error.message);
    }
}

async function runLogic() {
    let formData = {};
    let adminData = {};

    try {
        formData = parseJsonInput(formDataInput.value, "Form Data");
        adminData = parseJsonInput(adminDataInput.value, "Admin Data");
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        responseView.textContent = "{}";
        setStatus("JSON error", "error", error.message);
        return;
    }

    setStatus("Running", "working", "Executing Alpha website logic...");
    errorBox.classList.add("hidden");
    saveDraft();
    updateApiExample();

    try {
        const result = await requestJSON("/api/run", {
            method: "POST",
            body: JSON.stringify({
                script_name: scriptNameInput.value || "unsaved_logic",
                code: editor.value,
                form_data: formData,
                admin_data: adminData,
            }),
        });

        outputView.textContent = result.output_text || "(No Alpha output was produced.)";
        responseView.textContent = JSON.stringify(result.website_result ?? {}, null, 2);
        pythonView.textContent = result.translated_code || "(No translated Python was generated.)";

        if (result.error_text) {
            setEditorError(result.error_line, result.error_column);
            syncEditorView();
            errorBox.textContent = result.error_text;
            errorBox.classList.remove("hidden");
            setStatus("Logic error", "error", result.error_text);
        } else {
            clearEditorError();
            syncEditorView();
            setStatus(
                "Success",
                "success",
                `Run #${result.run_id} finished in ${Number(result.duration_ms).toFixed(2)} ms.`,
            );
        }

        await refreshLogs();
    } catch (error) {
        clearEditorError();
        syncEditorView();
        outputView.textContent = "The browser could not talk to the website logic engine.";
        responseView.textContent = "{}";
        pythonView.textContent = "";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Request failed", "error", error.message);
    }
}

function clearEditor() {
    editor.value = "";
    clearEditorError();
    syncEditorView();
    outputView.textContent = "Run a script to see Alpha output here.";
    responseView.textContent = "{}";
    pythonView.textContent = "Translated Python will appear here.";
    errorBox.classList.add("hidden");
    setStatus("Ready", "idle", "The editor is clear. Load a template or saved script.");
    saveDraft();
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
        runLogic();
    }
});

formDataInput.addEventListener("input", () => {
    saveDraft();
    updateApiExample();
});

adminDataInput.addEventListener("input", () => {
    saveDraft();
    updateApiExample();
});

scriptNameInput.addEventListener("input", () => {
    saveDraft();
    updateApiExample();
});

scriptDescriptionInput.addEventListener("input", saveDraft);
runButton.addEventListener("click", runLogic);
saveButton.addEventListener("click", saveScript);
clearButton.addEventListener("click", clearEditor);
apiExampleButton.addEventListener("click", updateApiExample);

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
        renderTemplates();
        renderSavedScripts(guide.saved_scripts || []);
        renderLogs(guide.recent_logs || []);
        renderTips();

        const draft = loadDraft();
        if (draft) {
            scriptNameInput.value = draft.scriptName || "contact_form";
            scriptDescriptionInput.value = draft.description || "Website logic rule";
            editor.value = draft.code || "";
            formDataInput.value = draft.formData || "";
            adminDataInput.value = draft.adminData || "";
            syncEditorView();
        } else {
            setFormAndAdminDefaults();
            loadTemplate(guide.templates[0]);
        }

        if (!formDataInput.value.trim() || !adminDataInput.value.trim()) {
            setFormAndAdminDefaults();
        }

        updateApiExample();
        setStatus("Ready", "idle", "Templates, scripts, and payload editors are ready.");
    } catch (error) {
        outputView.textContent = "Alpha Website Logic Engine could not load.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Load failed", "error", "Start the engine server and refresh the page.");
    }
});
