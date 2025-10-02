const AUTOSAVE_MS = 800;
const THEME_DEFAULT = "boeing";
const THEMES = {
    boeing: { label: "Boeing Classic" },
    sticky_note: { label: "Sticky Note" },
};

const editor = document.getElementById("editor");
const checklistListEl = document.getElementById("checklistList");
const toastEl = document.getElementById("toast");
const importModal = document.getElementById("importModal");
const importText = document.getElementById("importText");
const loginModal = document.getElementById("loginModal");
const saveStatusEl = document.getElementById("saveStatus");
const undoBtn = document.getElementById("undoAction");
const redoBtn = document.getElementById("redoAction");
const exportBtn = document.getElementById("exportChecklist");
const printBtn = document.getElementById("printChecklist");
const themeSelect = document.getElementById("themeSelect");

document.body.dataset.theme = THEME_DEFAULT;
if (themeSelect) {
    themeSelect.innerHTML = Object.entries(THEMES)
        .map(([value, config]) => `<option value="${value}">${config.label}</option>`)
        .join("");
    themeSelect.value = THEME_DEFAULT;
    themeSelect.disabled = true;
}

const state = {
    authHeader: null,
    checklists: [],
    activeId: null,
    activeTheme: THEME_DEFAULT,
};

class ChecklistStore {
    constructor() {
        this.state = null;
        this.listeners = new Set();
        this.history = [];
        this.future = [];
        this.dirty = false;
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    load(checklist) {
        this.state = deepClone(checklist);
        if (!this.state.theme) {
            this.state.theme = THEME_DEFAULT;
        }
        this.history = [];
        this.future = [];
        this.dirty = false;
        this.emit({ render: true, reason: "load" });
    }

    mutate(updater, { render = false } = {}) {
        if (!this.state) return;
        if (!this.state.theme) {
            this.state.theme = THEME_DEFAULT;
        }
        const next = deepClone(this.state);
        if (!next.theme) {
            next.theme = THEME_DEFAULT;
        }
        updater(next);
        next.theme = next.theme || THEME_DEFAULT;
        this.history.push(deepClone(this.state));
        if (this.history.length > 50) {
            this.history.shift();
        }
        this.state = next;
        this.future = [];
        this.dirty = true;
        this.emit({ render });
    }

    undo() {
        if (!this.history.length || !this.state) return;
        const previous = this.history.pop();
        this.future.push(deepClone(this.state));
        this.state = deepClone(previous);
        if (!this.state.theme) {
            this.state.theme = THEME_DEFAULT;
        }
        this.dirty = true;
        this.emit({ render: true, reason: "undo" });
    }

    redo() {
        if (!this.future.length || !this.state) return;
        const next = this.future.pop();
        this.history.push(deepClone(this.state));
        this.state = deepClone(next);
        if (!this.state.theme) {
            this.state.theme = THEME_DEFAULT;
        }
        this.dirty = true;
        this.emit({ render: true, reason: "redo" });
    }

    markClean() {
        this.dirty = false;
        this.emit({ render: false, reason: "saved" });
    }

    canUndo() {
        return this.history.length > 0;
    }

    canRedo() {
        return this.future.length > 0;
    }

    getState() {
        if (!this.state) {
            return null;
        }
        const clone = deepClone(this.state);
        if (!clone.theme) {
            clone.theme = THEME_DEFAULT;
        }
        return clone;
    }

    emit(meta = {}) {
        const payload = {
            dirty: this.dirty,
            canUndo: this.canUndo(),
            canRedo: this.canRedo(),
            ...meta,
        };
        for (const listener of this.listeners) {
            listener(this.state ? deepClone(this.state) : null, payload);
        }
    }
}

const store = new ChecklistStore();
let saveTimer = null;
let lastSaveError = null;

const API = {
    async request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        if (!(options.body instanceof FormData) && options.body && !headers.has("Content-Type")) {
            headers.set("Content-Type", "application/json");
        }
        if (state.authHeader) {
            headers.set("Authorization", state.authHeader);
        }
        const response = await fetch(path, { ...options, headers, credentials: "include" });
        if (response.status === 401) {
            showLogin();
            throw new Error("Unauthorized");
        }
        if (!response.ok) {
            let message = response.statusText;
            try {
                const payload = await response.json();
                message = payload?.error?.message || message;
            } catch (error) {
                // ignore parse failures
            }
            throw new Error(message);
        }
        if (response.status === 204) {
            return null;
        }
        const contentType = response.headers.get("Content-Type") || "";
        if (contentType.includes("application/json")) {
            const body = await response.json();
            return body.data ?? body;
        }
        return response.text();
    },
    listChecklists() {
        return this.request("/api/checklists");
    },
    createChecklist(payload) {
        return this.request("/api/checklists", { method: "POST", body: JSON.stringify(payload) });
    },
    updateChecklist(id, payload) {
        return this.request(`/api/checklists/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    },
    fetchChecklist(id) {
        return this.request(`/api/checklists/${id}`);
    },
    importChecklist(id, yamlText) {
        const endpoint = id ? `/api/checklists/${id}/import` : "/api/checklists/import";
        return this.request(endpoint, { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: yamlText });
    },
    exportChecklist(id) {
        return this.request(`/api/checklists/${id}/export`);
    },
};

function deepClone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }
    return JSON.parse(JSON.stringify(value));
}

function createId() {
    if (crypto?.randomUUID) {
        return crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2, 10);
}

function applyTheme(theme) {
    const resolved = THEMES[theme] ? theme : THEME_DEFAULT;
    document.body.dataset.theme = resolved;
    if (themeSelect && themeSelect.value !== resolved) {
        themeSelect.value = resolved;
    }
    state.activeTheme = resolved;
}

const EXPORT_FILENAME_MAX = 28;

function sanitizeFilenameSegment(value) {
    let base = (value || "checklist").toString().toLowerCase();
    base = base.replace(/[^a-z0-9]+/g, "_");
    base = base.replace(/_+/g, "_");
    base = base.replace(/^_+|_+$/g, "");
    if (!base) {
        base = "checklist";
    }
    if (base.length > EXPORT_FILENAME_MAX) {
        base = base.slice(0, EXPORT_FILENAME_MAX);
    }
    return base;
}

function resolveExportFilename() {
    let source = null;
    try {
        if (typeof store !== "undefined" && store && typeof store.getState === "function") {
            const current = store.getState();
            if (current && (current.slug || current.title)) {
                source = current.slug || current.title;
            }
        }
    } catch (error) {
        // store might not be initialised yet
    }
    if (!source) {
        const active = state.checklists.find ? state.checklists.find((item) => item.id === state.activeId) : null;
        if (active && (active.slug || active.title)) {
            source = active.slug || active.title;
        }
    }
    const base = sanitizeFilenameSegment(source);
    return `${base}_chklst.yaml`;
}
function showToast(message, variant = "info") {
    toastEl.textContent = message;
    toastEl.dataset.variant = variant;
    toastEl.hidden = false;
    setTimeout(() => {
        toastEl.hidden = true;
    }, 3200);
}

function showLogin() {
    loginModal.hidden = false;
    document.getElementById("loginPassword").value = "";
}

function hideLogin() {
    loginModal.hidden = true;
}

function updateSaveStatus(text, variant = "idle") {
    saveStatusEl.textContent = text;
    saveStatusEl.dataset.variant = variant;
}

async function initialize() {
    try {
        updateSaveStatus("Loading...", "pending");
        const checklists = await API.listChecklists();
        state.checklists = checklists.map((item) => ({
            ...item,
            theme: item.theme || THEME_DEFAULT,
        }));
        renderChecklistList();
        updateSaveStatus("Idle");
        if (checklists.length) {
            await loadChecklist(checklists[0].id);
        } else {
            editor.innerHTML = '<p class="empty">No checklists yet. Create a new one to begin.</p>';
        }
    } catch (error) {
        updateSaveStatus("Error", "error");
        console.error(error);
        showToast(error.message || "Unable to load checklists", "error");
    }
}

async function loadChecklist(id) {
    try {
        updateSaveStatus("Loading...", "pending");
        const checklist = await API.fetchChecklist(id);
        state.activeId = checklist.id;
        state.activeTheme = checklist.theme || THEME_DEFAULT;
        renderChecklistList();
        store.load(checklist);
        updateSaveStatus("Loaded", "success");
    } catch (error) {
        updateSaveStatus("Error", "error");
        console.error(error);
        showToast(error.message || "Unable to open checklist", "error");
    }
}

function renderChecklistList() {
    checklistListEl.innerHTML = "";
    state.checklists.forEach((item) => {
        const li = document.createElement("li");
        li.dataset.id = item.id;
        li.classList.toggle("active", item.id === state.activeId);
        li.innerHTML = `<strong>${escapeHtml(item.title)}</strong><span class="meta">Updated ${formatRelativeTime(item.updated_at)}</span>`;
        checklistListEl.appendChild(li);
    });
}

function renderEditor(checklist) {
    if (!checklist) {
        editor.innerHTML = '<p class="empty">Select a checklist to start editing.</p>';
        exportBtn.disabled = true;
        printBtn.disabled = true;
        return;
    }

    exportBtn.disabled = false;
    printBtn.disabled = false;

    const container = document.createElement("div");
    container.className = "editor-inner";
    container.innerHTML = `
        <div class="editor-meta">
            <form class="checklist-form">
                <label>Title<input type="text" name="title" value="${escapeHtml(checklist.title)}" /></label>
                <label>Author<input type="text" name="author" value="${escapeHtml(checklist.author || "")}" /></label>
                <label>Revision<input type="text" name="revision" value="${escapeHtml(checklist.revision || "")}" /></label>
            </form>
        </div>
        <div class="sections" id="sections"></div>
        <button id="addSection" class="ghost">Add Section</button>
    `;

    editor.replaceChildren(container);
    const sectionsEl = container.querySelector("#sections");
    const sortedSections = checklist.sections.slice().sort((a, b) => (a.position || 0) - (b.position || 0));
    sortedSections.forEach((section) => {
        sectionsEl.appendChild(renderSection(section));
    });
}

function renderSection(section) {
    const template = document.getElementById("sectionTemplate");
    const sectionEl = template.content.firstElementChild.cloneNode(true);
    sectionEl.dataset.sectionId = section.id;
    sectionEl.querySelector(".section-title").value = section.title;
    const itemsContainer = sectionEl.querySelector(".items");
    const sortedItems = section.items.slice().sort((a, b) => (a.position || 0) - (b.position || 0));
    sortedItems.forEach((item) => {
        itemsContainer.appendChild(renderItem(item));
    });
    return sectionEl;
}

function renderItem(item) {
    const template = document.getElementById("itemTemplate");
    const itemEl = template.content.firstElementChild.cloneNode(true);
    itemEl.dataset.itemId = item.id;
    itemEl.querySelector(".item-left").value = item.left_text || "";
    itemEl.querySelector(".item-right").value = item.right_text || "";
    return itemEl;
}

function escapeHtml(value) {
    if (value == null) return "";
    return String(value).replace(/[&<>"]/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
    }[char]));
}

function formatRelativeTime(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    const diff = Date.now() - date.getTime();
    const minutes = Math.round(diff / 60000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    return `${days}d ago`;
}

function scheduleSave() {
    if (saveTimer) {
        clearTimeout(saveTimer);
    }
    updateSaveStatus("Editing...", "editing");
    saveTimer = setTimeout(() => {
        saveTimer = null;
        performSave();
    }, AUTOSAVE_MS);
}

async function performSave() {
    const current = store.getState();
    if (!current) return;
    updateSaveStatus("Saving...", "pending");
    try {
        const payload = normalizePayload(current);
        const saved = await API.updateChecklist(current.id, payload);
        store.markClean();
        updateSaveStatus("Saved", "success");
        lastSaveError = null;
        const summary = {
            id: saved.id,
            title: saved.title,
            author: saved.author,
            revision: saved.revision,
            updated_at: saved.updated_at,
            slug: saved.slug,
            theme: saved.theme || THEME_DEFAULT,
        };
        const index = state.checklists.findIndex((item) => item.id === saved.id);
        if (index >= 0) {
            state.checklists[index] = summary;
        } else {
            state.checklists.unshift(summary);
        }
        renderChecklistList();
    } catch (error) {
        lastSaveError = error;
        updateSaveStatus("Error", "error");
        console.error(error);
        showToast(error.message || "Failed to save", "error");
    }
}

function normalizePayload(checklist) {
    return {
        id: checklist.id,
        title: checklist.title,
        author: checklist.author,
        revision: checklist.revision,
        theme: checklist.theme || THEME_DEFAULT,
        sections: checklist.sections.map((section, index) => ({
            id: section.id,
            title: section.title,
            position: index + 1,
            items: section.items.map((item, idx) => ({
                id: item.id,
                left_text: item.left_text,
                right_text: item.right_text,
                format: item.format || {},
                position: idx + 1,
            })),
        })),
    };
}

function handleEditorInput(event) {
    const target = event.target;
    if (target.matches("input[name='title']")) {
        store.mutate((draft) => {
            draft.title = target.value;
        });
        syncListTitle(target.value);
        scheduleSave();
        return;
    }
    if (target.matches("input[name='author']")) {
        store.mutate((draft) => {
            draft.author = target.value;
        });
        scheduleSave();
        return;
    }
    if (target.matches("input[name='revision']")) {
        store.mutate((draft) => {
            draft.revision = target.value;
        });
        scheduleSave();
        return;
    }
    if (target.matches(".section-title")) {
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        store.mutate((draft) => {
            const section = draft.sections.find((item) => item.id === sectionId);
            if (section) {
                section.title = target.value;
            }
        });
        scheduleSave();
        return;
    }
    if (target.matches(".item-left") || target.matches(".item-right")) {
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        const itemId = target.closest(".editor-item")?.dataset.itemId;
        const field = target.matches(".item-left") ? "left_text" : "right_text";
        store.mutate((draft) => {
            const section = draft.sections.find((item) => item.id === sectionId);
            const item = section?.items.find((entry) => entry.id === itemId);
            if (item) {
                item[field] = target.value;
            }
        });
        scheduleSave();
    }
}

function handleEditorClick(event) {
    const target = event.target;
    if (target.matches("#addSection")) {
        event.preventDefault();
        store.mutate((draft) => {
            draft.sections.push({
                id: createId(),
                title: "NEW SECTION",
                items: [
                    {
                        id: createId(),
                        left_text: "",
                        right_text: "",
                        format: {},
                    },
                ],
            });
        }, { render: true });
        scheduleSave();
        return;
    }

    if (target.matches(".add-item")) {
        event.preventDefault();
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        store.mutate((draft) => {
            const section = draft.sections.find((s) => s.id === sectionId);
            if (!section) return;
            section.items.push({
                id: createId(),
                left_text: "",
                right_text: "",
                format: {},
            });
        }, { render: true });
        scheduleSave();
        return;
    }

    if (target.matches(".remove-item")) {
        event.preventDefault();
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        const itemId = target.closest(".editor-item")?.dataset.itemId;
        store.mutate((draft) => {
            const section = draft.sections.find((s) => s.id === sectionId);
            if (!section) return;
            section.items = section.items.filter((item) => item.id !== itemId);
        }, { render: true });
        scheduleSave();
        return;
    }

    if (target.matches(".remove-section")) {
        event.preventDefault();
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        store.mutate((draft) => {
            draft.sections = draft.sections.filter((section) => section.id !== sectionId);
        }, { render: true });
        scheduleSave();
        return;
    }

    if (target.matches(".move-section-up") || target.matches(".move-section-down")) {
        event.preventDefault();
        const direction = target.matches(".move-section-up") ? -1 : 1;
        const sectionId = target.closest(".editor-section")?.dataset.sectionId;
        store.mutate((draft) => {
            const index = draft.sections.findIndex((section) => section.id === sectionId);
            if (index < 0) return;
            const swapIndex = index + direction;
            if (swapIndex < 0 || swapIndex >= draft.sections.length) return;
            const [section] = draft.sections.splice(index, 1);
            draft.sections.splice(swapIndex, 0, section);
        }, { render: true });
        scheduleSave();
    }
}

function syncListTitle(title) {
    const index = state.checklists.findIndex((item) => item.id === state.activeId);
    if (index >= 0) {
        state.checklists[index] = { ...state.checklists[index], title };
        renderChecklistList();
    }
}

function setupEventListeners() {
    if (themeSelect) {
        themeSelect.addEventListener("change", (event) => {
            const value = event.target.value || THEME_DEFAULT;
            applyTheme(value);
            const current = store.getState();
            if (current) {
                store.mutate((draft) => {
                    draft.theme = value;
                }, { render: false });
                scheduleSave();
            }
        });
    }

    checklistListEl.addEventListener("click", (event) => {
        const li = event.target.closest("li[data-id]");
        if (!li) return;
        const id = li.dataset.id;
        if (!id || id === state.activeId) return;
        loadChecklist(id);
    });

    editor.addEventListener("input", handleEditorInput);
    editor.addEventListener("click", handleEditorClick);

    undoBtn.addEventListener("click", (event) => {
        event.preventDefault();
        store.undo();
        scheduleSave();
    });

    redoBtn.addEventListener("click", (event) => {
        event.preventDefault();
        store.redo();
        scheduleSave();
    });

    document.getElementById("createChecklist").addEventListener("click", async () => {
        try {
            updateSaveStatus("Creating...", "pending");
            const payload = {
                title: "Untitled Checklist",
                theme: state.activeTheme || THEME_DEFAULT,
                sections: [
                    {
                        title: "PREFLIGHT",
                        items: [
                            { left_text: "Oxygen", right_text: "SET", format: {} },
                        ],
                    },
                ],
            };
            const checklist = await API.createChecklist(payload);
            const summary = {
                id: checklist.id,
                title: checklist.title,
                author: checklist.author,
                revision: checklist.revision,
                updated_at: checklist.updated_at,
                slug: checklist.slug,
                theme: checklist.theme || THEME_DEFAULT,
            };
            state.checklists.unshift(summary);
            renderChecklistList();
            await loadChecklist(checklist.id);
            updateSaveStatus("Created", "success");
        } catch (error) {
            updateSaveStatus("Error", "error");
            console.error(error);
            showToast(error.message || "Failed to create checklist", "error");
        }
    });

    const fileInput = document.getElementById("importFile");
    document.getElementById("importChecklist").addEventListener("click", () => {
        fileInput.value = "";
        fileInput.click();
    });

    document.getElementById("pasteChecklist").addEventListener("click", () => {
        importModal.hidden = false;
        importText.value = "";
        importText.focus();
    });

    fileInput.addEventListener("change", async (event) => {
        const [file] = event.target.files || [];
        if (!file) {
            return;
        }
        try {
            const text = await file.text();
            updateSaveStatus("Importing...", "pending");
            const checklist = await API.importChecklist(state.activeId, text);
            const summary = {
                id: checklist.id,
                title: checklist.title,
                author: checklist.author,
                revision: checklist.revision,
                updated_at: checklist.updated_at,
                slug: checklist.slug,
                theme: checklist.theme || THEME_DEFAULT,
            };
            const idx = state.checklists.findIndex((item) => item.id === checklist.id);
            if (idx >= 0) {
                state.checklists[idx] = summary;
            } else {
                state.checklists.unshift(summary);
            }
            renderChecklistList();
            await loadChecklist(checklist.id);
            showToast(`Imported ${file.name}`, "success");
            updateSaveStatus("Imported", "success");
        } catch (error) {
            updateSaveStatus("Error", "error");
            console.error(error);
            showToast(error.message || "Failed to import checklist", "error");
        } finally {
            event.target.value = "";
        }
    });

    document.getElementById("cancelImport").addEventListener("click", () => {
        importModal.hidden = true;
    });

    document.getElementById("confirmImport").addEventListener("click", async () => {
        const yamlText = importText.value.trim();
        if (!yamlText) {
            showToast("Paste YAML or Markdown to import", "error");
            return;
        }
        try {
            updateSaveStatus("Importing...", "pending");
            const checklist = await API.importChecklist(state.activeId, yamlText);
            importModal.hidden = true;
            const summary = {
                id: checklist.id,
                title: checklist.title,
                author: checklist.author,
                revision: checklist.revision,
                updated_at: checklist.updated_at,
                slug: checklist.slug,
                theme: checklist.theme || THEME_DEFAULT,
            };
            const idx = state.checklists.findIndex((item) => item.id === checklist.id);
            if (idx >= 0) {
                state.checklists[idx] = summary;
            } else {
                state.checklists.unshift(summary);
            }
            renderChecklistList();
            await loadChecklist(checklist.id);
            showToast("Checklist imported", "success");
            updateSaveStatus("Imported", "success");
        } catch (error) {
            updateSaveStatus("Error", "error");
            console.error(error);
            showToast(error.message || "Failed to import checklist", "error");
        }
    });

    exportBtn.addEventListener("click", async () => {
        const activeId = state.activeId;
        if (!activeId) return;
        try {
            const yamlText = await API.exportChecklist(activeId);
            const blob = new Blob([yamlText], { type: "text/yaml" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = resolveExportFilename();
            document.body.appendChild(link);
            link.click();
            URL.revokeObjectURL(link.href);
            link.remove();
            showToast("YAML exported", "success");
        } catch (error) {
            console.error(error);
            showToast(error.message || "Export failed", "error");
        }
    });

    printBtn.addEventListener("click", () => {
        if (!state.activeId) return;
        window.open(`/api/checklists/${state.activeId}/print`, "_blank");
    });

    document.getElementById("loginSubmit").addEventListener("click", () => {
        const username = document.getElementById("loginUsername").value.trim() || "crew";
        const password = document.getElementById("loginPassword").value;
        if (!password) {
            showToast("Password required", "error");
            return;
        }
        state.authHeader = "Basic " + btoa(`${username}:${password}`);
        hideLogin();
        initialize();
    });
}

store.subscribe((checklist, meta) => {
    const themeValue = checklist?.theme || state.activeTheme || THEME_DEFAULT;
    applyTheme(themeValue);
    if (themeSelect) {
        themeSelect.disabled = !checklist;
    }
    undoBtn.disabled = !meta.canUndo;
    redoBtn.disabled = !meta.canRedo;
    if (meta.render) {
        renderEditor(checklist);
    }
});

function bootstrap() {
    setupEventListeners();
    showLogin();
}

bootstrap();


















