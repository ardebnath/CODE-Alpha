const editor = document.getElementById("codeEditor");
const highlightLayer = document.getElementById("highlightLayer");
const lineNumbers = document.getElementById("lineNumbers");
const runButton = document.getElementById("runButton");
const mobileRunButton = document.getElementById("mobileRunButton");
const clearButton = document.getElementById("clearButton");
const outputButton = document.getElementById("outputButton");
const mobileOutputButton = document.getElementById("mobileOutputButton");
const outputView = document.getElementById("outputView");
const pythonView = document.getElementById("pythonView");
const errorBox = document.getElementById("errorBox");
const statusBadge = document.getElementById("statusBadge");
const timingText = document.getElementById("timingText");
const sampleList = document.getElementById("sampleList");
const ruleList = document.getElementById("ruleList");
const bridgeList = document.getElementById("bridgeList");
const requirementList = document.getElementById("requirementList");
const historyList = document.getElementById("historyList");
const moduleList = document.getElementById("moduleList");
const packageList = document.getElementById("packageList");
const extensionNotes = document.getElementById("extensionNotes");
const urlList = document.getElementById("urlList");
const systemMode = document.getElementById("systemMode");
const draftStatus = document.getElementById("draftStatus");
const installAppButton = document.getElementById("installAppButton");
const outputPanel = document.getElementById("outputPanel");
const accountMessage = document.getElementById("accountMessage");
const authView = document.getElementById("authView");
const userView = document.getElementById("userView");
const usernameInput = document.getElementById("usernameInput");
const passwordInput = document.getElementById("passwordInput");
const loginButton = document.getElementById("loginButton");
const registerButton = document.getElementById("registerButton");
const currentUsername = document.getElementById("currentUsername");
const currentUserFolder = document.getElementById("currentUserFolder");
const currentProjectFolder = document.getElementById("currentProjectFolder");
const projectNameInput = document.getElementById("projectNameInput");
const saveProjectButton = document.getElementById("saveProjectButton");
const refreshProjectsButton = document.getElementById("refreshProjectsButton");
const logoutButton = document.getElementById("logoutButton");
const currentPasswordInput = document.getElementById("currentPasswordInput");
const newPasswordInput = document.getElementById("newPasswordInput");
const changePasswordButton = document.getElementById("changePasswordButton");
const projectPanelMessage = document.getElementById("projectPanelMessage");
const projectList = document.getElementById("projectList");
const tabButtons = Array.from(document.querySelectorAll(".tab-button[data-tab]"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel[data-tab-panel]"));

const DRAFT_KEY = "alpha-studio-draft";
const SESSION_KEY = "alpha-studio-session";
const APP_SHELL_VERSION = "alpha-studio-v6";
const TAB_ANIMATION_MS = 280;

let deferredInstallPrompt = null;
let guideState = null;
let currentErrorLine = null;
let currentErrorColumn = null;
let activeTabName = tabButtons.find((button) => button.classList.contains("is-active"))?.dataset.tab || "workspace";
let tabMotionToken = 0;
let sessionToken = localStorage.getItem(SESSION_KEY) || "";
let accountState = {
    authenticated: false,
    user: null,
    projects: [],
};

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function setSessionToken(token) {
    sessionToken = token || "";
    if (sessionToken) {
        localStorage.setItem(SESSION_KEY, sessionToken);
        return;
    }
    localStorage.removeItem(SESSION_KEY);
}

function setAccountMessage(text, mode = "info") {
    accountMessage.textContent = text;
    accountMessage.className = "account-message";
    if (mode === "success") {
        accountMessage.classList.add("is-success");
    } else if (mode === "error") {
        accountMessage.classList.add("is-error");
    }
}

function requestJSON(url, options = {}) {
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }
    if (sessionToken) {
        headers.set("X-Alpha-Session", sessionToken);
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

        if (response.status === 401) {
            setSessionToken("");
            renderAccountState(
                {
                    authenticated: false,
                    user: null,
                    projects: [],
                    user_data_folder: "alpha_user_data",
                },
                "Your Alpha account session expired. Sign in again.",
                "error",
            );
        }
        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }
        return data;
    });
}

function setStatus(text, mode) {
    statusBadge.textContent = text;
    statusBadge.className = `status ${mode}`;
}

function getTabPanel(tabName) {
    return tabPanels.find((panel) => panel.dataset.tabPanel === tabName) || null;
}

function setActiveTabButton(tabName) {
    tabButtons.forEach((button) => {
        const isActive = button.dataset.tab === tabName;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-selected", String(isActive));
        button.tabIndex = isActive ? 0 : -1;
    });
}

function activateTab(tabName, options = {}) {
    const nextPanel = getTabPanel(tabName);
    if (!nextPanel) {
        return;
    }

    const currentPanel = getTabPanel(activeTabName);
    setActiveTabButton(tabName);

    if (currentPanel === nextPanel) {
        nextPanel.hidden = false;
        nextPanel.classList.add("is-active");
        nextPanel.classList.remove("is-leaving");
        nextPanel.setAttribute("aria-hidden", "false");
        activeTabName = tabName;
        return;
    }

    const motionToken = ++tabMotionToken;

    if (currentPanel) {
        window.clearTimeout(currentPanel.hideTimer);
        window.clearTimeout(currentPanel.enterTimer);
        currentPanel.classList.remove("is-entering");
        currentPanel.classList.add("is-leaving");
        currentPanel.setAttribute("aria-hidden", "true");
        currentPanel.hideTimer = window.setTimeout(() => {
            if (motionToken !== tabMotionToken) {
                return;
            }
            currentPanel.hidden = true;
            currentPanel.classList.remove("is-active", "is-leaving");
        }, TAB_ANIMATION_MS);
    }

    window.clearTimeout(nextPanel.hideTimer);
    window.clearTimeout(nextPanel.enterTimer);
    nextPanel.hidden = false;
    nextPanel.classList.remove("is-leaving");
    nextPanel.classList.add("is-active");
    nextPanel.setAttribute("aria-hidden", "false");
    void nextPanel.offsetWidth;
    nextPanel.classList.add("is-entering");
    nextPanel.enterTimer = window.setTimeout(() => {
        if (motionToken !== tabMotionToken) {
            return;
        }
        nextPanel.classList.remove("is-entering");
    }, TAB_ANIMATION_MS + 40);

    activeTabName = tabName;

    if (options.focusButton !== false) {
        tabButtons.find((button) => button.dataset.tab === tabName)?.focus({ preventScroll: true });
    }
}

function initializeTabs() {
    setActiveTabButton(activeTabName);
    tabPanels.forEach((panel) => {
        const isActive = panel.dataset.tabPanel === activeTabName;
        panel.hidden = !isActive;
        panel.classList.toggle("is-active", isActive);
        panel.classList.remove("is-entering", "is-leaving");
        panel.setAttribute("aria-hidden", String(!isActive));
    });

    tabButtons.forEach((button, index) => {
        button.addEventListener("click", () => activateTab(button.dataset.tab, { focusButton: false }));
        button.addEventListener("keydown", (event) => {
            if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
                return;
            }

            event.preventDefault();
            let nextIndex = index;

            if (event.key === "ArrowRight") {
                nextIndex = (index + 1) % tabButtons.length;
            } else if (event.key === "ArrowLeft") {
                nextIndex = (index - 1 + tabButtons.length) % tabButtons.length;
            } else if (event.key === "Home") {
                nextIndex = 0;
            } else if (event.key === "End") {
                nextIndex = tabButtons.length - 1;
            }

            const nextButton = tabButtons[nextIndex];
            nextButton.focus();
            activateTab(nextButton.dataset.tab, { focusButton: false });
        });
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
        return "<span class='editor-line tok-placeholder'>Start typing Alpha code...</span>";
    }

    const highlighted = applySyntaxHighlighting(escapeHtml(source));
    const lines = highlighted.split("\n");

    return lines
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
        rows.push(`<span class="${classes}" data-line="${index}">${index}</span>`);
    }
    lineNumbers.innerHTML = rows.join("");
}

function clearEditorError() {
    currentErrorLine = null;
    currentErrorColumn = null;
}

function setEditorError(lineNumber, columnNumber = null) {
    currentErrorLine = Number.isFinite(Number(lineNumber)) ? Number(lineNumber) : null;
    currentErrorColumn = Number.isFinite(Number(columnNumber)) ? Number(columnNumber) : null;
}

function syncEditorView() {
    highlightLayer.innerHTML = `${highlightAlpha(editor.value)}\n`;
    highlightLayer.scrollTop = editor.scrollTop;
    highlightLayer.scrollLeft = editor.scrollLeft;
    lineNumbers.scrollTop = editor.scrollTop;
    updateLineNumbers();
}

function saveDraft() {
    localStorage.setItem(DRAFT_KEY, editor.value);
    draftStatus.textContent = `Draft saved at ${new Date().toLocaleTimeString()}.`;
}

function loadDraft(fallbackCode) {
    const savedDraft = localStorage.getItem(DRAFT_KEY);
    if (savedDraft) {
        editor.value = savedDraft;
        draftStatus.textContent = "Restored your last draft from this browser.";
        return;
    }

    editor.value = `${fallbackCode.trim()}\n`;
}

function renderProjects(projects) {
    projectList.innerHTML = "";

    if (!accountState.authenticated) {
        projectList.innerHTML = "<p class='history-empty'>Sign in to save and load projects from your personal Alpha folder.</p>";
        return;
    }

    if (!projects.length) {
        projectList.innerHTML = "<p class='history-empty'>No saved projects yet. Save the code in your editor to create the first one.</p>";
        return;
    }

    projects.forEach((project) => {
        const card = document.createElement("article");
        card.className = "project-card";
        card.innerHTML = `
            <div class="project-top">
                <div>
                    <h3>${escapeHtml(project.name)}</h3>
                    <p class="project-meta">${escapeHtml(project.file_name)} | ${escapeHtml(project.updated_at)}</p>
                </div>
                <span class="package-state is-installed">${Number(project.size_bytes || 0)} bytes</span>
            </div>
            <p class="project-preview">${escapeHtml(project.preview || "Empty Alpha file.")}</p>
            <div class="project-actions">
                <button type="button" class="primary">Load</button>
                <button type="button">Delete</button>
            </div>
        `;

        const [loadButton, deleteButton] = card.querySelectorAll("button");
        loadButton.addEventListener("click", () => loadSavedProject(project.project_key));
        deleteButton.addEventListener("click", () => deleteSavedProject(project.project_key, project.name));
        projectList.appendChild(card);
    });
}

function renderAccountState(data, message = null, messageMode = "info") {
    accountState = {
        authenticated: Boolean(data.authenticated),
        user: data.user || null,
        projects: Array.isArray(data.projects) ? data.projects : [],
    };

    authView.classList.toggle("hidden", accountState.authenticated);
    userView.classList.toggle("hidden", !accountState.authenticated);

    if (!accountState.authenticated) {
        currentUsername.textContent = "Not signed in";
        currentUserFolder.textContent = `User data root: ${data.user_data_folder || "alpha_user_data"}`;
        currentProjectFolder.textContent = "Sign in to create your own project folder.";
        projectNameInput.value = "";
        projectPanelMessage.textContent = "Sign in to save and load Alpha projects from your own folder.";
        setAccountMessage(
            message || "Create a user or sign in to save Alpha projects in your own local folder.",
            messageMode,
        );
        renderProjects([]);
        return;
    }

    currentUsername.textContent = accountState.user.username;
    currentUserFolder.textContent = `User folder: ${accountState.user.user_folder}`;
    currentProjectFolder.textContent = `Project folder: ${accountState.user.project_folder}`;
    projectPanelMessage.textContent = `Projects for ${accountState.user.username} are stored in ${accountState.user.project_folder}.`;
    if (!projectNameInput.value.trim()) {
        projectNameInput.value = `${accountState.user.username.toLowerCase()}_project`;
    }
    setAccountMessage(
        message || `${accountState.user.project_count} saved project(s) are ready for ${accountState.user.username}.`,
        messageMode,
    );
    renderProjects(accountState.projects);
}

async function refreshAccountState() {
    const data = await requestJSON("/api/account/status");
    if (!data.authenticated && sessionToken) {
        setSessionToken("");
    }
    renderAccountState(data);
}

function requireSignedInAccount(actionText) {
    if (accountState.authenticated) {
        return true;
    }
    activateTab("workspace", { focusButton: false });
    setAccountMessage(`Sign in first to ${actionText}.`, "error");
    setStatus("Account required", "error");
    timingText.textContent = "Create a user or log in to use personal project storage.";
    return false;
}

function getProjectNameForSave() {
    const typedName = projectNameInput.value.trim();
    if (typedName) {
        return typedName;
    }

    const generatedName = `alpha_project_${new Date().toISOString().slice(0, 19).replaceAll(":", "-")}`;
    projectNameInput.value = generatedName;
    return generatedName;
}

async function handleAuthRequest(route, payload, successMessage) {
    const data = await requestJSON(route, {
        method: "POST",
        body: JSON.stringify(payload),
    });

    if (data.session) {
        setSessionToken(data.session);
    }

    passwordInput.value = "";
    currentPasswordInput.value = "";
    newPasswordInput.value = "";
    renderAccountState(data, successMessage || data.message, "success");
    setStatus("Account ready", "success");
    timingText.textContent = data.message || successMessage || "Account updated.";
}

async function loginAccount() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
        setAccountMessage("Enter both username and password to sign in.", "error");
        return;
    }

    try {
        await handleAuthRequest(
            "/api/account/login",
            { username, password },
            `Signed in as ${username}.`,
        );
    } catch (error) {
        setAccountMessage(error.message, "error");
    }
}

async function registerAccount() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
        setAccountMessage("Enter both username and password to create a new user.", "error");
        return;
    }

    try {
        await handleAuthRequest(
            "/api/account/register",
            { username, password },
            `Created user ${username}.`,
        );
    } catch (error) {
        setAccountMessage(error.message, "error");
    }
}

async function logoutAccount() {
    try {
        const data = await requestJSON("/api/account/logout", {
            method: "POST",
            body: JSON.stringify({}),
        });
        setSessionToken("");
        renderAccountState(data, "Signed out of Alpha Studio.", "info");
        setStatus("Signed out", "idle");
        timingText.textContent = "Account session closed.";
    } catch (error) {
        setSessionToken("");
        renderAccountState(
            {
                authenticated: false,
                user: null,
                projects: [],
                user_data_folder: "alpha_user_data",
            },
            "Signed out locally, but the server response failed.",
            "error",
        );
        setStatus("Signed out", "idle");
        timingText.textContent = error.message;
    }
}

async function changeAccountPassword() {
    if (!requireSignedInAccount("change your password")) {
        return;
    }

    const currentPassword = currentPasswordInput.value;
    const newPassword = newPasswordInput.value;
    if (!currentPassword || !newPassword) {
        setAccountMessage("Enter both the current password and the new password.", "error");
        return;
    }

    try {
        const data = await requestJSON("/api/account/password", {
            method: "POST",
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
        currentPasswordInput.value = "";
        newPasswordInput.value = "";
        renderAccountState(data, data.message || "Password changed.", "success");
        setStatus("Password updated", "success");
        timingText.textContent = data.message || "Account password updated.";
    } catch (error) {
        setAccountMessage(error.message, "error");
    }
}

async function saveCurrentProject() {
    if (!requireSignedInAccount("save projects")) {
        return;
    }

    try {
        const data = await requestJSON("/api/projects/save", {
            method: "POST",
            body: JSON.stringify({
                name: getProjectNameForSave(),
                code: editor.value,
            }),
        });
        projectNameInput.value = data.project?.name || projectNameInput.value;
        renderAccountState(data, data.message || "Project saved.", "success");
        setStatus("Project saved", "success");
        timingText.textContent = data.message || "Project saved to your user folder.";
    } catch (error) {
        setAccountMessage(error.message, "error");
        setStatus("Save failed", "error");
        timingText.textContent = error.message;
    }
}

async function loadSavedProject(projectKey) {
    if (!requireSignedInAccount("load saved projects")) {
        return;
    }

    try {
        const data = await requestJSON("/api/projects/load", {
            method: "POST",
            body: JSON.stringify({ project_key: projectKey }),
        });

        editor.value = `${String(data.code || "").replace(/\s+$/u, "")}\n`;
        projectNameInput.value = data.project?.name || projectKey;
        clearEditorError();
        syncEditorView();
        saveDraft();
        activateTab("workspace", { focusButton: false });
        editor.focus();
        outputView.textContent = "Output will appear here.";
        pythonView.textContent = "Translated Python will appear here.";
        errorBox.classList.add("hidden");
        renderAccountState(data, data.message || "Project loaded.", "success");
        setStatus("Project loaded", "success");
        timingText.textContent = data.message || "Saved project loaded into the editor.";
    } catch (error) {
        setAccountMessage(error.message, "error");
        setStatus("Load failed", "error");
        timingText.textContent = error.message;
    }
}

async function deleteSavedProject(projectKey, projectName) {
    if (!requireSignedInAccount("delete saved projects")) {
        return;
    }

    if (!window.confirm(`Delete saved project "${projectName}"?`)) {
        return;
    }

    try {
        const data = await requestJSON("/api/projects/delete", {
            method: "POST",
            body: JSON.stringify({ project_key: projectKey }),
        });
        renderAccountState(data, data.message || "Project deleted.", "success");
        if (projectNameInput.value.trim().toLowerCase() === String(projectName).trim().toLowerCase()) {
            projectNameInput.value = "";
        }
        setStatus("Project deleted", "success");
        timingText.textContent = data.message || "Saved project removed.";
    } catch (error) {
        setAccountMessage(error.message, "error");
        setStatus("Delete failed", "error");
        timingText.textContent = error.message;
    }
}

function renderGuide(data) {
    guideState = data;
    document.title = `${data.name} Studio`;
    moduleList.textContent = data.safe_modules.join(", ");

    sampleList.innerHTML = "";
    Object.entries(data.sample_programs).forEach(([key, item]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = item.title;
        button.className = "pill";
        button.addEventListener("click", () => {
            editor.value = `${item.source.trim()}\n`;
            clearEditorError();
            syncEditorView();
            saveDraft();
            activateTab("workspace", { focusButton: false });
            editor.focus();
            setStatus("Sample loaded", "idle");
            outputView.textContent = "Output will appear here.";
            pythonView.textContent = "Translated Python will appear here.";
            errorBox.classList.add("hidden");
        });
        sampleList.appendChild(button);

        if (key === data.default_sample && !localStorage.getItem(DRAFT_KEY)) {
            loadDraft(item.source);
        }
    });

    ruleList.innerHTML = "";
    data.rules.forEach((rule) => {
        const card = document.createElement("article");
        card.className = "rule-card";
        card.innerHTML = `
            <div class="rule-keyword">${rule.keyword}</div>
            <code>${rule.syntax}</code>
            <p>${rule.description}</p>
        `;
        ruleList.appendChild(card);
    });

    bridgeList.innerHTML = "";
    data.bridges.forEach((bridge) => {
        const card = document.createElement("article");
        card.className = "bridge-card";
        card.innerHTML = `
            <h3>${bridge.name}</h3>
            <p>${bridge.description}</p>
            <code>${bridge.notes}</code>
        `;
        bridgeList.appendChild(card);
    });

    requirementList.innerHTML = "";
    data.requirements.forEach((item) => {
        const row = document.createElement("li");
        row.textContent = item;
        requirementList.appendChild(row);
    });

    extensionNotes.innerHTML = "";
    data.extension_notes.forEach((note) => {
        const row = document.createElement("p");
        row.textContent = note;
        extensionNotes.appendChild(row);
    });

    renderPackages(data.available_packages);
    syncEditorView();
}

function renderPackages(packages) {
    packageList.innerHTML = "";

    packages.forEach((packageInfo) => {
        const card = document.createElement("article");
        card.className = "package-card";
        const tags = packageInfo.tags.map((tag) => `<span>${tag}</span>`).join("");
        card.innerHTML = `
            <div class="package-top">
                <div>
                    <h3>${packageInfo.title}</h3>
                    <p>${packageInfo.description}</p>
                </div>
                <div class="package-state ${packageInfo.installed ? "is-installed" : "is-available"}">
                    ${packageInfo.installed ? "Installed" : "Available"}
                </div>
            </div>
            <div class="tag-row">${tags}</div>
            <p class="package-exports">Exports: ${packageInfo.exports.join(", ")}</p>
            <button class="${packageInfo.installed ? "" : "primary"}" type="button">
                ${packageInfo.installed ? "Remove" : "Install"}
            </button>
        `;

        const actionButton = card.querySelector("button");
        actionButton.addEventListener("click", async () => {
            const route = packageInfo.installed ? "/api/packages/remove" : "/api/packages/install";
            const result = await requestJSON(route, {
                method: "POST",
                body: JSON.stringify({ name: packageInfo.name }),
            });
            renderPackages(result.available_packages);
            setStatus(packageInfo.installed ? "Package removed" : "Package installed", "success");
            timingText.textContent = `${packageInfo.title} package updated.`;
        });

        packageList.appendChild(card);
    });
}

function renderHistory(runs) {
    historyList.innerHTML = "";

    if (!runs.length) {
        historyList.innerHTML = "<p class='history-empty'>No runs yet. Execute a program to start tracking history.</p>";
        return;
    }

    runs.forEach((run) => {
        const item = document.createElement("article");
        item.className = "history-item";
        item.innerHTML = `
            <div>
                <strong>#${run.id}</strong>
                <span class="history-status ${run.status}">${run.status}</span>
            </div>
            <p>${run.created_at}</p>
            <p>${Number(run.duration_ms).toFixed(2)} ms</p>
            <p>${run.error_text || "Completed successfully."}</p>
        `;
        historyList.appendChild(item);
    });
}

async function refreshHistory() {
    const data = await requestJSON("/api/history");
    renderHistory(data.runs);
}

async function refreshSystemInfo() {
    const data = await requestJSON("/api/system");
    systemMode.textContent = data.share_lan
        ? "LAN live mode is enabled"
        : "Local mode is enabled";

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
    activateTab("workspace", { focusButton: false });
    setStatus("Running", "working");
    timingText.textContent = "Executing Alpha code...";
    errorBox.classList.add("hidden");
    saveDraft();

    try {
        const result = await requestJSON("/api/run", {
            method: "POST",
            body: JSON.stringify({ code: editor.value }),
        });

        outputView.textContent = result.output_text || "(Program completed with no output)";
        pythonView.textContent = result.translated_code || "(No translated code was generated)";
        timingText.textContent = `Run #${result.run_id} finished in ${Number(result.duration_ms).toFixed(2)} ms.`;

        if (result.error_text) {
            setEditorError(result.error_line, result.error_column);
            syncEditorView();
            errorBox.textContent = result.error_text;
            errorBox.classList.remove("hidden");
            setStatus("Error", "error");
        } else {
            clearEditorError();
            syncEditorView();
            setStatus("Success", "success");
        }

        await refreshHistory();
        outputPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        clearEditorError();
        syncEditorView();
        outputView.textContent = "The request could not be completed.";
        pythonView.textContent = "";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Request failed", "error");
        timingText.textContent = "The browser could not talk to the Alpha server.";
    }
}

function clearEditor() {
    editor.value = "";
    clearEditorError();
    outputView.textContent = "Output will appear here.";
    pythonView.textContent = "Translated Python will appear here.";
    errorBox.classList.add("hidden");
    setStatus("Ready", "idle");
    timingText.textContent = "Editor cleared.";
    saveDraft();
    syncEditorView();
}

function showOutputPanel() {
    activateTab("workspace", { focusButton: false });
    outputPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function registerInstallPrompt() {
    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredInstallPrompt = event;
        installAppButton.classList.remove("hidden");
    });

    installAppButton.addEventListener("click", async () => {
        if (!deferredInstallPrompt) {
            return;
        }
        deferredInstallPrompt.prompt();
        await deferredInstallPrompt.userChoice;
        deferredInstallPrompt = null;
        installAppButton.classList.add("hidden");
    });
}

function registerServiceWorker() {
    if ("serviceWorker" in navigator) {
        let isReloading = false;
        navigator.serviceWorker.addEventListener("controllerchange", () => {
            if (isReloading) {
                return;
            }
            isReloading = true;
            window.location.reload();
        });

        navigator.serviceWorker.register(`/sw.js?v=${APP_SHELL_VERSION}`, { updateViaCache: "none" })
            .then((registration) => {
                if (registration.waiting) {
                    registration.waiting.postMessage({ type: "SKIP_WAITING" });
                }

                registration.addEventListener("updatefound", () => {
                    const worker = registration.installing;
                    if (!worker) {
                        return;
                    }

                    worker.addEventListener("statechange", () => {
                        if (worker.state === "installed" && navigator.serviceWorker.controller) {
                            worker.postMessage({ type: "SKIP_WAITING" });
                        }
                    });
                });

                return registration.update().catch(() => {});
            })
            .catch(() => {
                draftStatus.textContent = "Service worker registration failed, but the editor still works.";
            });
    }
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
mobileRunButton.addEventListener("click", runAlpha);
clearButton.addEventListener("click", clearEditor);
outputButton.addEventListener("click", showOutputPanel);
mobileOutputButton.addEventListener("click", showOutputPanel);
loginButton.addEventListener("click", loginAccount);
registerButton.addEventListener("click", registerAccount);
logoutButton.addEventListener("click", logoutAccount);
saveProjectButton.addEventListener("click", saveCurrentProject);
refreshProjectsButton.addEventListener("click", refreshAccountState);
changePasswordButton.addEventListener("click", changeAccountPassword);

passwordInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        loginAccount();
    }
});

window.addEventListener("DOMContentLoaded", async () => {
    initializeTabs();
    registerInstallPrompt();
    registerServiceWorker();

    try {
        const [guide] = await Promise.all([
            requestJSON("/api/guide"),
            refreshHistory(),
            refreshSystemInfo(),
            refreshAccountState(),
        ]);
        renderGuide(guide);
        syncEditorView();
    } catch (error) {
        outputView.textContent = "Alpha Studio could not load.";
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");
        setStatus("Load failed", "error");
        timingText.textContent = "Check that the Python server is running.";
    }
});
