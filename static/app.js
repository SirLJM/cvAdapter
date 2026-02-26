let analysisResult = null;

document.addEventListener("DOMContentLoaded", () => {
    loadVersions();
    setupNavigation();

    document.getElementById("analyze-btn").addEventListener("click", analyze);
    document.getElementById("finalize-btn").addEventListener("click", finalize);
    document.getElementById("select-all-btn").addEventListener("click", () => toggleAll(true));
    document.getElementById("deselect-all-btn").addEventListener("click", () => toggleAll(false));
});

function setupNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const view = btn.dataset.view;
            document.getElementById("analyze-view").classList.toggle("hidden", view !== "analyze");
            document.getElementById("history-view").classList.toggle("hidden", view !== "history");

            if (view === "history") loadHistory();
        });
    });
}

async function loadVersions() {
    const res = await fetch("/api/versions");
    const data = await res.json();

    const versionSelect = document.getElementById("version");
    const languageSelect = document.getElementById("language");

    data.versions.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v.toUpperCase();
        versionSelect.appendChild(opt);
    });

    data.languages.forEach(l => {
        const opt = document.createElement("option");
        opt.value = l;
        opt.textContent = l.toUpperCase();
        languageSelect.appendChild(opt);
    });
}

async function analyze() {
    const version = document.getElementById("version").value;
    const language = document.getElementById("language").value;
    const jobDescription = document.getElementById("job-description").value.trim();

    if (!jobDescription) {
        alert("Please paste a job description.");
        return;
    }

    document.getElementById("results").classList.add("hidden");
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("analyze-btn").disabled = true;

    try {
        const res = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ version, language, job_description: jobDescription }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Analysis failed");
        }

        analysisResult = await res.json();
        analysisResult.version = version;
        analysisResult.language = language;
        analysisResult.job_description = jobDescription;

        renderDiff(analysisResult);
    } catch (e) {
        showError(e.message);
    } finally {
        document.getElementById("loading").classList.add("hidden");
        document.getElementById("analyze-btn").disabled = false;
    }
}

function renderDiff(result) {
    document.getElementById("job-title").textContent = result.job_title;
    const container = document.getElementById("changes-list");
    container.innerHTML = "";

    if (result.changes.length === 0) {
        container.innerHTML = '<p class="history-empty">No changes suggested. Your CV already matches well!</p>';
        document.getElementById("results").classList.remove("hidden");
        return;
    }

    result.changes.forEach((change, idx) => {
        const card = document.createElement("div");
        card.className = "change-card";
        card.innerHTML = `
            <div class="change-header">
                <input type="checkbox" checked data-index="${idx}" data-path="${change.field_path}">
                <span class="change-section">${change.section}</span>
                <span class="change-path">${change.field_path}</span>
                <span class="change-reason">${change.reason}</span>
            </div>
            <div class="change-body">
                <div class="change-original">
                    <div class="change-label">Original</div>
                    ${escapeHtml(String(change.original_value))}
                </div>
                <div class="change-adapted">
                    <div class="change-label">Adapted</div>
                    ${escapeHtml(String(change.adapted_value))}
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    document.getElementById("results").classList.remove("hidden");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function toggleAll(checked) {
    document.querySelectorAll('#changes-list input[type="checkbox"]').forEach(cb => {
        cb.checked = checked;
    });
}

async function finalize() {
    if (!analysisResult) return;

    const accepted = [];
    document.querySelectorAll('#changes-list input[type="checkbox"]:checked').forEach(cb => {
        accepted.push(cb.dataset.path);
    });

    if (accepted.length === 0) {
        alert("Please select at least one change.");
        return;
    }

    document.getElementById("results").classList.add("hidden");
    document.getElementById("generating").classList.remove("hidden");

    const companyName = document.getElementById("company-name").value.trim() || null;
    const positionTitle = document.getElementById("position-title").value.trim() || null;
    const applicationDate = document.getElementById("application-date").value || null;
    const offerLink = document.getElementById("offer-link").value.trim() || null;

    try {
        const res = await fetch("/api/finalize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                version: analysisResult.version,
                language: analysisResult.language,
                job_description: analysisResult.job_description,
                job_title: analysisResult.job_title,
                original_data: analysisResult.original_data,
                adapted_data: analysisResult.adapted_data,
                changes: analysisResult.changes,
                accepted_paths: accepted,
                company_name: companyName,
                position_title: positionTitle,
                application_date: applicationDate,
                offer_link: offerLink,
            }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "PDF generation failed");
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `cv_adapted.pdf`;
        a.click();
        URL.revokeObjectURL(url);

        document.getElementById("results").classList.remove("hidden");
    } catch (e) {
        showError(e.message);
        document.getElementById("results").classList.remove("hidden");
    } finally {
        document.getElementById("generating").classList.add("hidden");
    }
}

async function loadHistory() {
    const container = document.getElementById("history-list");
    container.innerHTML = '<div class="spinner"></div>';

    try {
        const res = await fetch("/api/history");
        const items = await res.json();

        if (items.length === 0) {
            container.innerHTML = '<p class="history-empty">No history yet.</p>';
            return;
        }

        container.innerHTML = "";
        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";

            let meta = `${item.cv_version.toUpperCase()} / ${item.language.toUpperCase()} &mdash; ${new Date(item.created_at).toLocaleString()}`;

            let trackingHtml = "";
            const parts = [];
            if (item.company_name) parts.push(escapeHtml(item.company_name));
            if (item.position_title) parts.push(escapeHtml(item.position_title));
            if (item.application_date) parts.push(item.application_date);
            if (parts.length > 0) {
                trackingHtml = `<span class="history-tracking">${parts.join(" &middot; ")}</span>`;
            }

            let linkHtml = "";
            if (item.offer_link) {
                linkHtml = `<a class="history-link" href="${escapeHtml(item.offer_link)}" target="_blank" rel="noopener">Offer</a>`;
            }

            div.innerHTML = `
                <div class="history-info">
                    <span class="history-title">${escapeHtml(item.job_title)}</span>
                    ${trackingHtml}
                    <span class="history-meta">${meta}</span>
                </div>
                <div class="history-actions">
                    ${linkHtml}
                    <button class="secondary-btn" onclick="downloadPdf('${item.id}')">Download PDF</button>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        container.innerHTML = `<p class="error-message">${escapeHtml(e.message)}</p>`;
    }
}

function downloadPdf(id) {
    window.open(`/api/history/${id}/pdf`, "_blank");
}

function showError(message) {
    const existing = document.querySelector(".error-message");
    if (existing) existing.remove();

    const div = document.createElement("div");
    div.className = "error-message";
    div.textContent = message;
    document.querySelector(".form-section").appendChild(div);

    setTimeout(() => div.remove(), 8000);
}
