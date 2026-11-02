/* ==========================================================================
   BluetoothCare — logika antarmuka
   Tanpa dependensi eksternal. Semua data dinamis di-escape sebelum dirender.
   ========================================================================== */

(() => {
  "use strict";

  const ROUTES = ["beranda", "konsultasi", "hasil", "pengetahuan", "tentang"];
  const STORAGE_ANSWERS = "bluetoothcare:answers:v1";
  const STORAGE_RESULT = "bluetoothcare:result:v1";
  const TITLES = {
    beranda: "Sistem Pakar Diagnosis Bluetooth — Laptop Windows",
    konsultasi: "Konsultasi — BluetoothCare",
    hasil: "Hasil Diagnosis — BluetoothCare",
    pengetahuan: "Basis Pengetahuan — BluetoothCare",
    tentang: "Tentang Sistem — BluetoothCare",
  };
  const TAB_NAMES = ["facts", "rules", "conclusions", "scenarios", "sources"];

  const state = {
    kb: null,
    answers: {},
    result: null,
    activeTab: "facts",
    toastTimer: null,
    submitting: false,
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const els = {
    navToggle: $("#nav-toggle"),
    nav: $("#primary-nav"),
    globalAlert: $("#global-alert"),
    globalAlertText: $("#global-alert-text"),
    globalAlertClose: $("#global-alert-close"),
    form: $("#consult-form"),
    questionGroups: $("#question-groups"),
    progressCount: $("#progress-count"),
    progressBar: $("#progress-bar"),
    progressTrack: $(".progress-track"),
    formError: $("#form-error"),
    resetBtn: $("#reset-form"),
    submitBtn: $("#submit-answers"),
    resultEmpty: $("#result-empty"),
    resultBody: $("#result-body"),
    resultTitle: $("#result-title"),
    resultSubtitle: $("#result-subtitle"),
    resultTime: $("#result-time"),
    resultSummary: $("#result-summary"),
    diagnosisSection: $("#diagnosis-section"),
    diagnosisCaption: $("#diagnosis-caption"),
    diagnosisList: $("#diagnosis-list"),
    traceContent: $("#trace-content"),
    reconsultTop: $("#reconsult-top"),
    reconsultBottom: $("#reconsult-bottom"),
    downloadBtn: $("#download-result"),
    downloadBottom: $("#download-result-bottom"),
    printBtn: $("#print-result"),
    kbLoading: $("#kb-loading"),
    kbContent: $("#kb-content"),
    kbCompliance: $("#kb-compliance"),
    factsTable: $("#facts-table"),
    rulesTable: $("#rules-table"),
    conclusionsContent: $("#conclusions-content"),
    scenariosTable: $("#scenarios-table"),
    sourcesContent: $("#sources-content"),
    tabCountFacts: $("#tab-count-facts"),
    tabCountRules: $("#tab-count-rules"),
    tabCountConclusions: $("#tab-count-conclusions"),
    tabCountScenarios: $("#tab-count-scenarios"),
    tabCountSources: $("#tab-count-sources"),
    toast: $("#toast"),
  };

  const defaultSubmitHtml = els.submitBtn ? els.submitBtn.innerHTML : "";

  /* ------------------------------------------------------------------------
     Utilitas
     ------------------------------------------------------------------------ */

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => {
      const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return map[character];
    });
  }

  function currentRoute() {
    const hash = window.location.hash.replace(/^#/, "");
    return ROUTES.includes(hash) ? hash : "beranda";
  }

  function formatMs(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";
    return `${new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 }).format(number)} ms`;
  }

  function formatDateTime(iso) {
    if (!iso) return "—";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleString("id-ID", { dateStyle: "long", timeStyle: "short" });
  }

  function groupLabel(groupId) {
    if (!state.kb) return groupId || "—";
    const group = (state.kb.meta.groups || []).find((item) => item.id === groupId);
    return group ? group.label : groupId || "—";
  }

  function updatePublicStats() {
    if (!state.kb || !state.kb.stats) return;
    $$("[data-stat]").forEach((element) => {
      const value = state.kb.stats[element.dataset.stat];
      if (value !== undefined && value !== null) element.textContent = String(value);
    });
  }

  function highlightOperators(label) {
    return escapeHtml(label)
      .replace(/\b(DAN|ATAU)\b/g, '<span class="op">$1</span>')
      .replace(/\b(TIDAK)\b/g, '<span class="op">$1</span>');
  }

  function showToast(message) {
    if (!els.toast) return;
    els.toast.textContent = message;
    els.toast.hidden = false;
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => {
      els.toast.hidden = true;
    }, 4200);
  }

  function showGlobalAlert(message) {
    if (!els.globalAlert) return;
    els.globalAlertText.textContent = message;
    els.globalAlert.hidden = false;
  }

  function hideGlobalAlert() {
    if (els.globalAlert) els.globalAlert.hidden = true;
  }

  function setNavOpen(open) {
    if (!els.navToggle || !els.nav) return;
    els.navToggle.setAttribute("aria-expanded", String(open));
    els.navToggle.setAttribute("aria-label", open ? "Tutup menu navigasi" : "Buka menu navigasi");
    els.nav.classList.toggle("is-open", open);
  }

  function closeNav() {
    setNavOpen(false);
  }

  function setSubmitting(loading) {
    state.submitting = loading;
    if (!els.submitBtn) return;
    els.submitBtn.disabled = loading;
    if (loading) {
      els.submitBtn.textContent = "Menjalankan inferensi…";
    } else {
      els.submitBtn.innerHTML = defaultSubmitHtml;
    }
  }

  /* ------------------------------------------------------------------------
     Sesi lokal
     ------------------------------------------------------------------------ */

  function restoreSession() {
    try {
      const answers = JSON.parse(window.sessionStorage.getItem(STORAGE_ANSWERS) || "null");
      if (answers && typeof answers === "object") {
        Object.entries(answers).forEach(([factId, value]) => {
          if (typeof value === "boolean") state.answers[factId] = value;
        });
      }
      const result = JSON.parse(window.sessionStorage.getItem(STORAGE_RESULT) || "null");
      if (
        result &&
        (result.status === "diagnosed" || result.status === "inconclusive") &&
        Array.isArray(result.trace) &&
        result.stats
      ) {
        state.result = result;
        if (result.answers && typeof result.answers === "object") {
          Object.entries(result.answers).forEach(([factId, value]) => {
            if (typeof value === "boolean" && !(factId in state.answers)) {
              state.answers[factId] = value;
            }
          });
        }
      }
    } catch (error) {
      // sessionStorage dapat diblokir oleh mode privat; aplikasi tetap berjalan.
    }
  }

  function persistAnswers() {
    try {
      window.sessionStorage.setItem(STORAGE_ANSWERS, JSON.stringify(state.answers));
    } catch (error) {
      // abaikan
    }
  }

  function persistResult() {
    try {
      window.sessionStorage.setItem(STORAGE_RESULT, JSON.stringify(state.result));
    } catch (error) {
      // abaikan
    }
  }

  function clearSession() {
    try {
      window.sessionStorage.removeItem(STORAGE_ANSWERS);
      window.sessionStorage.removeItem(STORAGE_RESULT);
    } catch (error) {
      // abaikan
    }
  }

  /* ------------------------------------------------------------------------
     Navigasi
     ------------------------------------------------------------------------ */

  function renderRoute() {
    const route = currentRoute();

    $$(".view").forEach((view) => {
      view.hidden = view.dataset.view !== route;
    });

    $$(".main-nav a").forEach((link) => {
      const active = link.dataset.route === route;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    document.title = TITLES[route] || TITLES.beranda;
    closeNav();

    if (route === "hasil") {
      renderResult();
    } else if (route === "pengetahuan") {
      if (state.kb) {
        renderKnowledge();
        switchTab(state.activeTab);
      }
    } else if (route === "konsultasi") {
      updateProgress();
    }

    window.scrollTo({ top: 0, behavior: "auto" });
  }

  /* ------------------------------------------------------------------------
     Memuat basis pengetahuan
     ------------------------------------------------------------------------ */

  async function loadKnowledge() {
    if (!els.questionGroups) return;
    els.questionGroups.innerHTML = `
      <div class="loading-block" role="status">
        <span class="spinner" aria-hidden="true"></span>
        Memuat pertanyaan dari basis pengetahuan…
      </div>`;
    if (els.kbLoading) {
      els.kbLoading.hidden = false;
      els.kbLoading.innerHTML = `<span class="spinner" aria-hidden="true"></span> Memuat basis pengetahuan…`;
    }
    if (els.kbContent) els.kbContent.hidden = true;
    if (els.submitBtn) els.submitBtn.disabled = true;

    try {
      const response = await fetch("/api/knowledge", { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`Server mengembalikan status ${response.status}.`);
      const data = await response.json();
      if (!data || !Array.isArray(data.facts) || !Array.isArray(data.rules)) {
        throw new Error("Format basis pengetahuan tidak dikenali.");
      }
      state.kb = data;
      updatePublicStats();

      // Buang jawaban lama yang tidak dikenal oleh basis pengetahuan saat ini.
      const knownFacts = new Set(data.facts.map((fact) => fact.id));
      Object.keys(state.answers).forEach((factId) => {
        if (!knownFacts.has(factId)) delete state.answers[factId];
      });

      renderQuestionGroups();
      renderKnowledge();
      restoreFormAnswers();
      updateProgress();
      hideGlobalAlert();
      if (els.submitBtn) els.submitBtn.disabled = false;
    } catch (error) {
      const message =
        "Basis pengetahuan gagal dimuat. Pastikan server berjalan (python app.py), lalu muat ulang halaman.";
      showGlobalAlert(message);
      if (els.questionGroups) {
        els.questionGroups.innerHTML = `
          <div class="alert alert-error" role="alert">
            ${escapeHtml(message)}
            <button type="button" class="btn btn-ghost" data-retry-kb style="margin-top:12px">Coba lagi</button>
          </div>`;
      }
      if (els.kbLoading) {
        els.kbLoading.innerHTML = `
          <div>
            <p>${escapeHtml(message)}</p>
            <button type="button" class="btn btn-ghost" data-retry-kb style="margin-top:12px">Coba lagi</button>
          </div>`;
      }
      if (els.submitBtn) els.submitBtn.disabled = true;
    }
  }

  function renderQuestionGroups() {
    if (!state.kb || !els.questionGroups) return;
    const groups = state.kb.meta.groups || [];
    const factsByGroup = new Map();
    state.kb.facts.forEach((fact) => {
      const key = fact.group || "lainnya";
      if (!factsByGroup.has(key)) factsByGroup.set(key, []);
      factsByGroup.get(key).push(fact);
    });

    const order = groups.map((group) => group.id);
    factsByGroup.forEach((_, key) => {
      if (!order.includes(key)) order.push(key);
    });

    const html = order
      .map((groupId, index) => {
        const facts = factsByGroup.get(groupId) || [];
        if (!facts.length) return "";
        const group = groups.find((item) => item.id === groupId) || {
          label: groupId,
          description: "",
        };
        return `
          <fieldset class="question-group">
            <legend class="sr-only">${escapeHtml(group.label)}</legend>
            <div class="group-head">
              <span class="group-number" aria-hidden="true">${index + 1}</span>
              <div>
                <div class="group-title">
                  ${escapeHtml(group.label)}
                  <small>${facts.length} pertanyaan · wajib dijawab</small>
                </div>
                <p class="group-desc">${escapeHtml(group.description || "")}</p>
              </div>
            </div>
            <div class="question-list">
              ${facts
                .map(
                  (fact) => `
                <div class="question" data-fact="${escapeHtml(fact.id)}">
                  <div class="question-text">
                    <div class="question-main">
                      <span class="q-code">${escapeHtml(fact.id)}</span>
                      <p class="question-label" id="q-${escapeHtml(fact.id)}-label">${escapeHtml(fact.text)}</p>
                    </div>
                    <p class="q-hint" id="hint-${escapeHtml(fact.id)}">${escapeHtml(fact.hint || "")}</p>
                  </div>
                  <div class="segmented" role="radiogroup" aria-labelledby="q-${escapeHtml(fact.id)}-label" aria-describedby="hint-${escapeHtml(fact.id)}">
                    <label>
                      <input type="radio" name="${escapeHtml(fact.id)}" value="true">
                      <span>Ya</span>
                    </label>
                    <label>
                      <input type="radio" name="${escapeHtml(fact.id)}" value="false">
                      <span>Tidak</span>
                    </label>
                  </div>
                </div>`
                )
                .join("")}
            </div>
          </fieldset>`;
      })
      .join("");

    els.questionGroups.innerHTML = html;
  }

  function restoreFormAnswers() {
    if (!els.form) return;
    Object.entries(state.answers).forEach(([factId, value]) => {
      const input = els.form.querySelector(
        `input[name="${factId}"][value="${value ? "true" : "false"}"]`
      );
      if (input) input.checked = true;
    });
  }

  function updateProgress() {
    if (!state.kb || !els.progressCount) return;
    const total = state.kb.facts.length;
    const answered = state.kb.facts.filter(
      (fact) => typeof state.answers[fact.id] === "boolean"
    ).length;
    els.progressCount.textContent = `${answered} / ${total}`;
    if (els.progressBar) {
      els.progressBar.style.width = `${total ? (answered / total) * 100 : 0}%`;
    }
    if (els.progressTrack) {
      els.progressTrack.setAttribute("aria-valuenow", String(answered));
      els.progressTrack.setAttribute("aria-valuemax", String(total));
    }
  }

  function clearInvalid() {
    if (!els.form) return;
    $$(".question.is-invalid", els.form).forEach((question) => {
      question.classList.remove("is-invalid");
      $$("input", question).forEach((input) => input.removeAttribute("aria-invalid"));
    });
  }

  function markInvalid(factIds) {
    if (!els.form || !Array.isArray(factIds)) return;
    let firstInput = null;
    factIds.forEach((factId) => {
      const question = els.form.querySelector(`.question[data-fact="${factId}"]`);
      if (!question) return;
      question.classList.add("is-invalid");
      $$("input", question).forEach((input) => input.setAttribute("aria-invalid", "true"));
      if (!firstInput) firstInput = question.querySelector("input");
    });
    if (firstInput) {
      firstInput.focus({ preventScroll: true });
      const question = firstInput.closest(".question");
      if (question) question.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function showFormError(message) {
    if (!els.formError) return;
    els.formError.textContent = message;
    els.formError.hidden = false;
    els.formError.focus({ preventScroll: true });
    els.formError.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearFormError() {
    if (!els.formError) return;
    els.formError.hidden = true;
    els.formError.textContent = "";
  }

  /* ------------------------------------------------------------------------
     Form konsultasi
     ------------------------------------------------------------------------ */

  function onAnswerChange(event) {
    const input = event.target.closest('input[type="radio"]');
    if (!input || !input.name) return;
    state.answers[input.name] = input.value === "true";
    persistAnswers();
    updateProgress();
    const question = input.closest(".question");
    if (question) {
      question.classList.remove("is-invalid");
      $$("input", question).forEach((radio) => radio.removeAttribute("aria-invalid"));
    }
    if (state.kb) {
      const complete = state.kb.facts.every(
        (fact) => typeof state.answers[fact.id] === "boolean"
      );
      if (complete) clearFormError();
    }
  }

  function resetForm() {
    if (els.form) els.form.reset();
    state.answers = {};
    persistAnswers();
    clearInvalid();
    clearFormError();
    updateProgress();
    showToast("Semua jawaban dikosongkan. Silakan mulai kembali.");
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!state.kb) {
      showFormError("Basis pengetahuan belum siap. Muat ulang halaman atau jalankan server.");
      return;
    }
    if (state.submitting) return;

    const formData = new FormData(els.form);
    const collected = {};
    const missing = [];
    state.kb.facts.forEach((fact) => {
      const value = formData.get(fact.id);
      if (value === "true" || value === "false") {
        collected[fact.id] = value === "true";
      } else {
        missing.push(fact.id);
      }
    });

    state.answers = collected;
    persistAnswers();
    updateProgress();
    clearInvalid();

    if (missing.length) {
      markInvalid(missing);
      showFormError(
        `Masih ada ${missing.length} pertanyaan yang belum dijawab (${missing.join(
          ", "
        )}). Jawab semua pertanyaan dengan Ya atau Tidak sebelum memproses diagnosis.`
      );
      return;
    }

    clearFormError();
    setSubmitting(true);

    try {
      const response = await fetch("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ answers: state.answers }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (Array.isArray(data.missing) && data.missing.length) markInvalid(data.missing);
        throw new Error(data.error || `Inferensi gagal (status ${response.status}).`);
      }

      state.result = data;
      if (data.answers) state.answers = data.answers;
      persistAnswers();
      persistResult();
      showToast(
        data.status === "diagnosed"
          ? "Diagnosis berhasil disusun. Membuka hasil…"
          : "Inferensi selesai. Belum ada diagnosis yang cocok."
      );

      if (currentRoute() === "hasil") renderRoute();
      else window.location.hash = "#hasil";
    } catch (error) {
      showFormError(
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan saat memproses jawaban. Coba lagi."
      );
    } finally {
      setSubmitting(false);
    }
  }

  /* ------------------------------------------------------------------------
     Hasil diagnosis
     ------------------------------------------------------------------------ */

  function renderResult() {
    if (!els.resultEmpty || !els.resultBody) return;
    const hasResult = Boolean(state.result);
    els.resultEmpty.hidden = hasResult;
    els.resultBody.hidden = !hasResult;
    if (!hasResult) return;

    const result = state.result;
    const diagnosed = result.status === "diagnosed";
    const diagnoses = Array.isArray(result.diagnoses) ? result.diagnoses : [];

    els.resultTitle.textContent = diagnosed ? "Diagnosis ditemukan" : "Belum dapat disimpulkan";
    els.resultSubtitle.textContent = diagnosed
      ? diagnoses.length === 1
        ? `Satu kemungkinan penyebab paling sesuai dengan ${result.stats.yes} gejala yang Anda pilih.`
        : `${diagnoses.length} kemungkinan penyebab ditemukan dari ${result.stats.yes} gejala yang Anda pilih. Periksa mulai dari prioritas 1.`
      : "Kombinasi gejala yang Anda pilih belum membentuk pola diagnosis. Tinjau gejala terdeteksi dan saran pemeriksaan tambahan di bawah.";
    els.resultTime.textContent = `Konsultasi ${formatDateTime(
      result.generated_at
    )} · ${result.stats.answered} dari ${result.stats.facts_total} pertanyaan dijawab · ${
      result.stats.yes
    } gejala "Ya"`;

    const verdict = diagnosed
      ? `
        <div class="verdict-card verdict-diagnosed">
          <div class="verdict-icon" aria-hidden="true">✓</div>
          <div class="verdict-copy">
            <p class="verdict-eyebrow">Inferensi selesai</p>
            <h2>${
              diagnoses.length === 1
                ? "Satu diagnosis ditemukan"
                : `${diagnoses.length} diagnosis ditemukan`
            }</h2>
            <p>Prioritas hanya mengatur urutan pemeriksaan, bukan menghapus diagnosis lain. Mulai dari langkah perbaikan pada prioritas pertama, lalu periksa diagnosis berikutnya bila masalah berlanjut.</p>
          </div>
        </div>`
      : `
        <div class="verdict-card verdict-inconclusive">
          <div class="verdict-icon" aria-hidden="true">!</div>
          <div class="verdict-copy">
            <p class="verdict-eyebrow">Belum dapat disimpulkan</p>
            <h2>Tidak ada aturan diagnosis yang terpenuhi</h2>
            <p>${escapeHtml(result.inconclusive?.message || "")}</p>
          </div>
        </div>`;

    const stats = `
      <div class="stat-strip">
        <div><span>Waktu inferensi</span><strong>${formatMs(result.stats.elapsed_ms)}</strong></div>
        <div><span>Iterasi</span><strong>${escapeHtml(result.stats.iterations)}</strong></div>
        <div><span>Aturan aktif</span><strong>${escapeHtml(result.stats.rules_fired)} / ${escapeHtml(
          result.stats.rules_total
        )}</strong></div>
        <div><span>Fakta "Ya"</span><strong>${escapeHtml(result.stats.yes)} / ${escapeHtml(
          result.stats.facts_total
        )}</strong></div>
      </div>`;

    let extra = "";
    if (!diagnosed) {
      const detected = result.inconclusive?.detected_facts || [];
      const suggestions = result.inconclusive?.suggestions || [];
      extra = `
        <div class="inconclusive-grid">
          <section class="info-panel">
            <h3>Gejala yang sudah terdeteksi</h3>
            ${
              detected.length
                ? `<ul class="facts-list">${detected
                    .map(
                      (fact) =>
                        `<li><span class="fact-code">${escapeHtml(fact.id)}</span><span>${escapeHtml(
                          fact.text
                        )}</span></li>`
                    )
                    .join("")}</ul>
                   <p class="derived-note">Gejala tunggal ini belum cukup untuk menjalankan aturan diagnosis.</p>`
                : `<p class="empty-mini">Tidak ada gejala yang dijawab "Ya".</p>`
            }
          </section>
          <section class="info-panel">
            <h3>Yang perlu dicek</h3>
            <ol class="advice-list">${suggestions
              .map((suggestion) => `<li>${escapeHtml(suggestion)}</li>`)
              .join("")}</ol>
            <p class="derived-note"><a href="#konsultasi">Periksa kembali jawaban</a> bila ada pengamatan baru, lalu proses ulang. Anda juga dapat memilih <strong>Konsultasi ulang</strong> untuk memulai dari awal.</p>
          </section>
        </div>`;
    }

    els.resultSummary.innerHTML = verdict + stats + extra;

    els.diagnosisSection.hidden = !diagnosed;
    if (diagnosed) {
      els.diagnosisCaption.textContent =
        diagnoses.length === 1
          ? "Satu diagnosis paling sesuai dengan pola gejala Anda."
          : `${diagnoses.length} diagnosis ditemukan. Prioritas hanya mengatur urutan pemeriksaan, bukan menghapus diagnosis lain.`;
      els.diagnosisList.innerHTML = diagnoses.map(renderDiagnosis).join("");
    } else {
      els.diagnosisList.innerHTML = "";
    }

    els.traceContent.innerHTML = renderTrace(result);
  }

  function renderDiagnosis(diagnosis) {
    const causes = (diagnosis.derivation?.causes || [])
      .map((cause) => renderCause(cause, diagnosis, false))
      .join("");

    return `
      <article class="diagnosis-card">
        <div class="diagnosis-head">
          <div class="diagnosis-meta">
            ${
              diagnosis.priority
                ? `<span class="priority-badge">Prioritas ${escapeHtml(diagnosis.priority)}</span>`
                : ""
            }
            <span class="code-chip">${escapeHtml(diagnosis.id)}</span>
            ${
              diagnosis.rule_ids && diagnosis.rule_ids.length
                ? `<span class="badge badge-slate">Aturan ${diagnosis.rule_ids
                    .map((rule) => escapeHtml(rule))
                    .join(" · ")}</span>`
                : ""
            }
          </div>
          <h3>${escapeHtml(diagnosis.text)}</h3>
          ${diagnosis.summary ? `<p>${escapeHtml(diagnosis.summary)}</p>` : ""}
        </div>
        <div class="advice-block">
          <h4>Langkah perbaikan</h4>
          <ol class="advice-list">
            ${(diagnosis.advice || []).map((step) => `<li>${escapeHtml(step)}</li>`).join("")}
          </ol>
        </div>
        <details class="why">
          <summary>Mengapa diagnosis ini muncul?</summary>
          <div class="why-body">
            <p class="derived-note">Aturan yang membentuk <strong>${escapeHtml(
              diagnosis.id
            )}</strong> beserta fakta pendukungnya:</p>
            <div class="reason-tree">
              ${
                causes ||
                '<p class="empty-mini">Tidak ada aturan yang tercatat untuk diagnosis ini.</p>'
              }
            </div>
          </div>
        </details>
      </article>`;
  }

  function renderCause(cause, target, compact) {
    const sentence = compact
      ? ""
      : `<p class="rule-if">JIKA ${escapeHtml(cause.premise_sentence)} MAKA <strong>${escapeHtml(
          target.id
        )}</strong> (${escapeHtml(target.text)}).</p>`;
    const antecedents = (cause.antecedents || [])
      .map(
        (antecedent) =>
          `<li class="antecedent-item${
            antecedent.kind === "conclusion" ? " is-conclusion" : ""
          }">${renderReasonNode(antecedent, true)}</li>`
      )
      .join("");
    return `
      <div class="cause">
        <div class="cause-head">
          <span class="rule-chip">${escapeHtml(cause.rule_id)}</span>
          <span>JIKA ${escapeHtml(cause.premise_label)} MAKA <strong>${escapeHtml(
            target.id
          )}</strong></span>
        </div>
        ${sentence}
        <ul class="antecedent-list">${antecedents}</ul>
      </div>`;
  }

  function renderReasonNode(node, compact) {
    if (!node || node.kind === "fact" || node.kind === "cycle") {
      return `<span class="ant-code">${escapeHtml(node?.id || "")}</span>${escapeHtml(
        node?.text || ""
      )}`;
    }
    const causes = (node.causes || [])
      .map((cause) => renderCause(cause, node, true))
      .join("");
    return `<span class="ant-code">${escapeHtml(node.id)}</span><strong>${escapeHtml(
      node.text
    )}</strong>${causes ? `<div class="nested-causes">${causes}</div>` : ""}`;
  }

  function factListItems(facts) {
    return (facts || [])
      .map(
        (fact) =>
          `<li><span class="fact-code">${escapeHtml(fact.id)}</span><span>${escapeHtml(
            fact.text
          )}</span></li>`
      )
      .join("");
  }

  function conclusionItems(items) {
    return (items || [])
      .map(
        (item) =>
          `<li><span class="conclusion-code${
            item.type === "final" ? " is-final" : ""
          }">${escapeHtml(item.id)}</span> ${escapeHtml(item.text)}</li>`
      )
      .join("");
  }

  function renderTrace(result) {
    const inputFacts = result.input_facts || [];
    const intermediate = result.working_memory?.intermediate || [];
    const final = result.working_memory?.final || [];
    const trace = result.trace || [];
    const statusBadge =
      result.status === "diagnosed"
        ? '<span class="badge badge-green">Diagnosis ditemukan</span>'
        : '<span class="badge badge-amber">Tidak ada aturan aktif</span>';

    const summaryBadges = `
      <div class="trace-summary">
        <span class="badge badge-blue">Forward chaining</span>
        ${statusBadge}
        <span class="badge badge-slate">${escapeHtml(result.stats.iterations)} iterasi</span>
        <span class="badge badge-slate">${escapeHtml(result.stats.rules_fired)} aturan dijalankan</span>
        <span class="badge badge-cyan">${formatMs(result.stats.elapsed_ms)}</span>
      </div>`;

    const columns = `
      <div class="trace-columns">
        <div class="trace-panel">
          <h3>Fakta masukan (dijawab "Ya")</h3>
          ${
            inputFacts.length
              ? `<ul class="facts-list">${factListItems(inputFacts)}</ul>`
              : '<p class="empty-mini">Tidak ada fakta masukan yang bernilai Ya.</p>'
          }
        </div>
        <div class="trace-panel">
          <h3>Fakta turunan</h3>
          <div class="derived-groups">
            <div class="derived-group">
              <h4>Kesimpulan antara (K)</h4>
              ${
                intermediate.length
                  ? `<ul>${conclusionItems(intermediate)}</ul>`
                  : '<p class="empty-mini">Belum ada kesimpulan antara.</p>'
              }
            </div>
            <div class="derived-group">
              <h4>Diagnosis akhir (H)</h4>
              ${
                final.length
                  ? `<ul>${conclusionItems(final)}</ul>`
                  : '<p class="empty-mini">Belum ada diagnosis akhir.</p>'
              }
            </div>
          </div>
        </div>
      </div>`;

    if (!trace.length) {
      return `${summaryBadges}${columns}
        <div class="info-panel">
          <h3>Tabel iterasi</h3>
          <p class="empty-mini">Tidak ada aturan yang berjalan. Kombinasi fakta belum memenuhi premis aturan mana pun.</p>
        </div>`;
    }

    const rows = trace
      .map(
        (record) => `
        <tr>
          <td class="mono">${escapeHtml(record.iteration)}</td>
          <td class="mono"><strong>${escapeHtml(record.rule_id)}</strong><br><span class="badge badge-slate">${escapeHtml(
            record.source || "—"
          )}</span></td>
          <td><span class="rule-premise">${highlightOperators(record.premise_label)}</span></td>
          <td><span class="conclusion-code${
            record.conclusion_type === "final" ? " is-final" : ""
          }">${escapeHtml(record.conclusion)}</span> ${escapeHtml(record.conclusion_text)}</td>
          <td>${
            record.is_new
              ? '<span class="status-baru">baru</span>'
              : '<span class="status-lama">sudah ada</span>'
          }</td>
        </tr>`
      )
      .join("");

    return `${summaryBadges}${columns}
      <div class="table-scroll">
        <table class="data-table trace-table">
          <caption class="sr-only">Jejak aturan per iterasi</caption>
          <thead>
            <tr>
              <th scope="col">Iterasi</th>
              <th scope="col">Aturan</th>
              <th scope="col">Premis</th>
              <th scope="col">Kesimpulan</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <p class="derived-note">Aturan yang sudah dijalankan tidak diulang. Siklus berhenti ketika tidak ada aturan baru yang aktif. Status <strong>baru</strong> berarti kesimpulan belum ada di memori kerja.</p>`;
  }

  /* ------------------------------------------------------------------------
     Ekspor hasil
     ------------------------------------------------------------------------ */

  function reasonLinesForText(nodes, indent, add) {
    (nodes || []).forEach((node) => {
      if (node.kind === "fact" || node.kind === "cycle") {
        add(`${indent}- ${node.id}: ${node.text}`);
        return;
      }
      add(`${indent}- ${node.id}: ${node.text}`);
      (node.causes || []).forEach((cause) => {
        add(`${indent}  ${cause.rule_id}: JIKA ${cause.premise_sentence} MAKA ${node.id}`);
        reasonLinesForText(cause.antecedents, `${indent}    `, add);
      });
    });
  }

  function buildTextReport(result) {
    const lines = [];
    const add = (line = "") => lines.push(line);
    const meta = state.kb?.meta || {};

    add("=".repeat(72));
    add((meta.title || "SISTEM PAKAR DIAGNOSIS BLUETOOTH").toUpperCase());
    add("Forward Chaining · Windows 10/11");
    add("=".repeat(72));
    add(`Waktu konsultasi : ${formatDateTime(result.generated_at)}`);
    add(`Status           : ${result.status === "diagnosed" ? "Diagnosis ditemukan" : "Belum dapat disimpulkan"}`);
    add(`Pertanyaan       : ${result.stats.answered} dijawab, ${result.stats.yes} bernilai Ya`);
    add(`Inferensi        : ${result.stats.iterations} iterasi, ${result.stats.rules_fired} aturan, ${formatMs(result.stats.elapsed_ms)}`);
    add();
    add("FAKTA YANG DIJAWAB \"YA\"");
    add("-".repeat(72));
    if (result.input_facts.length) {
      result.input_facts.forEach((fact) => add(`- ${fact.id}: ${fact.text}`));
    } else {
      add("- (tidak ada)");
    }
    add();

    if (result.status === "diagnosed") {
      add("DIAGNOSIS (URUT PRIORITAS)");
      add("-".repeat(72));
      result.diagnoses.forEach((diagnosis, index) => {
        add(`${index + 1}. [${diagnosis.id}] ${diagnosis.text} (Prioritas ${diagnosis.priority ?? "—"})`);
        if (diagnosis.summary) add(`   Ringkasan: ${diagnosis.summary}`);
        add("   Langkah perbaikan:");
        (diagnosis.advice || []).forEach((step, stepIndex) => {
          add(`   ${stepIndex + 1}) ${step}`);
        });
        add("   Alasan:");
        (diagnosis.derivation?.causes || []).forEach((cause) => {
          add(`   - ${cause.rule_id}: JIKA ${cause.premise_sentence} MAKA ${diagnosis.id} (${diagnosis.text})`);
          reasonLinesForText(cause.antecedents, "     ", add);
        });
        add();
      });
    } else {
      add("BELUM DAPAT DISIMPULKAN");
      add("-".repeat(72));
      add(result.inconclusive?.message || "Tidak ada diagnosis yang cocok.");
      add();
      add("Gejala terdeteksi:");
      const detected = result.inconclusive?.detected_facts || [];
      if (detected.length) {
        detected.forEach((fact) => add(`- ${fact.id}: ${fact.text}`));
      } else {
        add("- (tidak ada)");
      }
      add();
      add("Yang perlu dicek:");
      (result.inconclusive?.suggestions || []).forEach((suggestion, index) => {
        add(`${index + 1}) ${suggestion}`);
      });
      add();
    }

    add("JEJAK PENALARAN");
    add("-".repeat(72));
    if (result.trace.length) {
      let lastIteration = null;
      result.trace.forEach((record) => {
        if (record.iteration !== lastIteration) {
          add(`Iterasi ${record.iteration}:`);
          lastIteration = record.iteration;
        }
        add(`- ${record.rule_id} | JIKA ${record.premise_sentence} | MAKA ${record.conclusion} (${record.conclusion_text}) [${record.is_new ? "baru" : "sudah ada"}]`);
      });
    } else {
      add("- Tidak ada aturan yang berjalan.");
    }
    add();
    add("Fakta turunan:");
    const intermediate = result.working_memory?.intermediate || [];
    const final = result.working_memory?.final || [];
    if (intermediate.length) {
      intermediate.forEach((item) => add(`- ${item.id}: ${item.text}`));
    }
    if (final.length) {
      final.forEach((item) => add(`- ${item.id}: ${item.text}`));
    }
    if (!intermediate.length && !final.length) add("- (tidak ada)");
    add();
    add("=".repeat(72));
    add(meta.disclaimer || "Hasil sistem adalah diagnosis awal, bukan pengganti pemeriksaan teknisi.");
    add("Dihasilkan oleh BluetoothCare · Sistem Pakar (TI22604).");

    return `\ufeff${lines.join("\r\n")}`;
  }

  function downloadResult() {
    if (!state.result) {
      showToast("Belum ada hasil konsultasi yang dapat diunduh.");
      return;
    }
    const text = buildTextReport(state.result);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const date = new Date(state.result.generated_at || Date.now());
    const stamp = Number.isNaN(date.getTime())
      ? "konsultasi"
      : `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(
          date.getDate()
        ).padStart(2, "0")}-${String(date.getHours()).padStart(2, "0")}${String(
          date.getMinutes()
        ).padStart(2, "0")}`;
    const link = document.createElement("a");
    link.href = url;
    link.download = `hasil-diagnosis-bluetooth-${stamp}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1200);
    showToast("Hasil konsultasi diunduh sebagai berkas teks.");
  }

  function printResult() {
    if (!state.result) {
      showToast("Belum ada hasil konsultasi yang dapat dicetak.");
      return;
    }
    $$("details").forEach((details) => {
      details.open = true;
    });
    window.print();
  }

  function reconsult() {
    clearSession();
    state.answers = {};
    state.result = null;
    if (els.form) els.form.reset();
    clearInvalid();
    clearFormError();
    updateProgress();
    showToast("Sesi konsultasi dikosongkan. Silakan mulai kembali.");
    if (currentRoute() === "konsultasi") renderRoute();
    else window.location.hash = "#konsultasi";
  }

  /* ------------------------------------------------------------------------
     Basis pengetahuan
     ------------------------------------------------------------------------ */

  function renderKnowledge() {
    if (!state.kb || !els.kbContent) return;
    if (els.kbLoading) els.kbLoading.hidden = true;
    els.kbContent.hidden = false;

    const data = state.kb;
    const stats = data.stats || {};
    updatePublicStats();

    if (els.tabCountFacts) els.tabCountFacts.textContent = stats.facts ?? data.facts.length;
    if (els.tabCountRules) els.tabCountRules.textContent = stats.rules ?? data.rules.length;
    if (els.tabCountConclusions)
      els.tabCountConclusions.textContent =
        stats.intermediate + stats.final || data.conclusions.length;
    if (els.tabCountScenarios)
      els.tabCountScenarios.textContent = stats.scenarios ?? data.meta.test_scenarios?.length ?? 0;
    if (els.tabCountSources) els.tabCountSources.textContent = stats.sources ?? data.sources.length;

    if (els.kbCompliance) {
      els.kbCompliance.innerHTML = (data.compliance || [])
        .map((item) => {
          const valueLabel =
            item.label === "Operator AND/OR"
              ? item.met
                ? "Didukung"
                : "Belum didukung"
              : `${item.actual} / min. ${item.minimum}`;
          return `
            <div class="compliance-item${item.met ? "" : " is-missing"}">
              <span class="compliance-check" aria-hidden="true">${item.met ? "✓" : "!"}</span>
              <div>
                <strong>${escapeHtml(item.label)}</strong>
                <span>${escapeHtml(valueLabel)}</span>
              </div>
            </div>`;
        })
        .join("");
    }

    renderFactsTable();
    renderRulesTable();
    renderConclusions();
    renderScenarios();
    renderSources();
  }

  function renderFactsTable() {
    if (!els.factsTable || !state.kb) return;
    const rows = state.kb.facts
      .map(
        (fact) => `
        <tr>
          <td class="mono"><strong>${escapeHtml(fact.id)}</strong></td>
          <td>${escapeHtml(fact.text)}</td>
          <td><span class="group-label group-${escapeHtml(fact.group)}">${escapeHtml(
            groupLabel(fact.group)
          )}</span></td>
          <td>${escapeHtml(fact.hint || "—")}</td>
        </tr>`
      )
      .join("");

    els.factsTable.innerHTML = `
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">Kode</th>
              <th scope="col">Fakta / gejala</th>
              <th scope="col">Kelompok</th>
              <th scope="col">Keterangan untuk pengguna</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderRulesTable() {
    if (!els.rulesTable || !state.kb) return;
    const conclusions = new Map(state.kb.conclusions.map((item) => [item.id, item]));
    const rows = state.kb.rules
      .map((rule) => {
        const conclusion = conclusions.get(rule.then);
        const isFinal = conclusion?.type === "final";
        return `
          <tr>
            <td class="mono"><strong>${escapeHtml(rule.id)}</strong></td>
            <td><span class="rule-premise">${highlightOperators(rule.premise_label)}</span></td>
            <td>
              <span class="conclusion-code${isFinal ? " is-final" : ""}">${escapeHtml(
          rule.then
        )}</span>
              ${escapeHtml(conclusion?.text || "")}
            </td>
            <td class="mono">${escapeHtml(rule.source || "—")}</td>
          </tr>`;
      })
      .join("");

    els.rulesTable.innerHTML = `
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">Kode</th>
              <th scope="col">Premis (JIKA)</th>
              <th scope="col">Kesimpulan (MAKA)</th>
              <th scope="col">Sumber</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderConclusions() {
    if (!els.conclusionsContent || !state.kb) return;
    const intermediate = state.kb.conclusions.filter((item) => item.type === "intermediate");
    const final = state.kb.conclusions
      .filter((item) => item.type === "final")
      .sort((left, right) => (left.priority ?? 99) - (right.priority ?? 99));

    const intermediateRows = intermediate
      .map(
        (item) => `
        <tr>
          <td class="mono"><span class="conclusion-code">${escapeHtml(item.id)}</span></td>
          <td><strong>${escapeHtml(item.text)}</strong></td>
          <td>${escapeHtml(item.summary || "—")}</td>
        </tr>`
      )
      .join("");

    const finalRows = final
      .map(
        (item) => `
        <tr>
          <td class="mono">${escapeHtml(item.priority ?? "—")}</td>
          <td class="mono"><span class="conclusion-code is-final">${escapeHtml(item.id)}</span></td>
          <td><strong>${escapeHtml(item.text)}</strong></td>
          <td>${escapeHtml(item.summary || "—")}</td>
        </tr>`
      )
      .join("");

    els.conclusionsContent.innerHTML = `
      <div class="conclusion-section">
        <h3>Kesimpulan antara <span>${intermediate.length} aturan turunan</span></h3>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr><th scope="col">Kode</th><th scope="col">Kesimpulan</th><th scope="col">Ringkasan</th></tr>
            </thead>
            <tbody>${intermediateRows}</tbody>
          </table>
        </div>
      </div>
      <div class="conclusion-section">
        <h3>Diagnosis akhir <span>${final.length} diagnosis · urut prioritas</span></h3>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr><th scope="col">Prioritas</th><th scope="col">Kode</th><th scope="col">Diagnosis</th><th scope="col">Ringkasan</th></tr>
            </thead>
            <tbody>${finalRows}</tbody>
          </table>
        </div>
        <p class="derived-note">Prioritas mengatur urutan pemeriksaan: masalah pada laptop diperiksa lebih dulu, lalu kondisi perangkat, lalu lingkungan. Prioritas tidak menghapus diagnosis lain.</p>
      </div>`;
  }

  function renderScenarios() {
    if (!els.scenariosTable || !state.kb) return;
    const facts = new Map(state.kb.facts.map((fact) => [fact.id, fact]));
    const scenarios = state.kb.meta.test_scenarios || [];

    const rows = scenarios
      .map((scenario) => {
        const factChips = (scenario.facts || [])
          .map((factId) => {
            const fact = facts.get(factId);
            return `<span class="badge badge-slate" title="${escapeHtml(
              fact?.text || ""
            )}">${escapeHtml(factId)}</span>`;
          })
          .join(" ");
        const ruleChips = (scenario.rules || [])
          .map((ruleId) => `<span class="badge badge-blue">${escapeHtml(ruleId)}</span>`)
          .join(" ");
        return `
          <tr>
            <td class="mono">${escapeHtml(scenario.no)}</td>
            <td>${factChips || "—"}</td>
            <td>${ruleChips || '<span class="badge badge-slate">tidak ada</span>'}</td>
            <td>${
              scenario.result
                ? `<span class="conclusion-code is-final">${escapeHtml(scenario.result)}</span>`
                : '<span class="badge badge-amber">Belum dapat disimpulkan</span>'
            }</td>
            <td>${escapeHtml(scenario.note || "")}</td>
          </tr>`;
      })
      .join("");

    els.scenariosTable.innerHTML = `
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">No</th>
              <th scope="col">Fakta masukan</th>
              <th scope="col">Aturan yang berjalan</th>
              <th scope="col">Hasil diharapkan</th>
              <th scope="col">Catatan</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderSources() {
    if (!els.sourcesContent || !state.kb) return;
    const cards = (state.kb.sources || [])
      .map((source) => {
        const verified = source.status === "terverifikasi";
        return `
          <article class="source-card">
            <div class="source-top">
              <div>
                <h3>${escapeHtml(source.id)} · ${escapeHtml(source.title)}</h3>
                <p class="source-publisher">${escapeHtml(source.publisher || "—")}</p>
              </div>
              <span class="badge ${verified ? "badge-green" : "badge-amber"}">${
          verified ? "Terverifikasi" : "Perlu dilengkapi"
        }</span>
            </div>
            <p>${escapeHtml(source.contribution || "")}</p>
            <div class="source-meta">
              ${
                source.url
                  ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${
                      verified ? "Buka sumber" : "Tautan sumber"
                    } ↗</a>`
                  : "<span>URL belum diisi</span>"
              }
              ${source.accessed ? `<span>Diakses ${escapeHtml(source.accessed)}</span>` : ""}
            </div>
          </article>`;
      })
      .join("");

    els.sourcesContent.innerHTML = `<div class="sources-grid">${cards}</div>`;
  }

  function switchTab(name) {
    const tab = TAB_NAMES.includes(name) ? name : "facts";
    state.activeTab = tab;

    TAB_NAMES.forEach((tabName) => {
      const button = $(`.tab-button[data-tab="${tabName}"]`);
      const panel = $(`#tab-${tabName}`);
      const active = tabName === tab;
      if (button) {
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", String(active));
        button.tabIndex = active ? 0 : -1;
      }
      if (panel) panel.hidden = !active;
    });
  }

  /* ------------------------------------------------------------------------
     Peristiwa
     ------------------------------------------------------------------------ */

  function bindEvents() {
    if (els.navToggle) {
      els.navToggle.addEventListener("click", () => {
        const open = els.navToggle.getAttribute("aria-expanded") !== "true";
        setNavOpen(open);
      });
    }

    if (els.globalAlertClose) {
      els.globalAlertClose.addEventListener("click", hideGlobalAlert);
    }

    window.addEventListener("hashchange", renderRoute);

    if (els.form) {
      els.form.addEventListener("change", onAnswerChange);
      els.form.addEventListener("submit", onSubmit);
    }

    if (els.resetBtn) els.resetBtn.addEventListener("click", resetForm);
    if (els.reconsultTop) els.reconsultTop.addEventListener("click", reconsult);
    if (els.reconsultBottom) els.reconsultBottom.addEventListener("click", reconsult);
    if (els.downloadBtn) els.downloadBtn.addEventListener("click", downloadResult);
    if (els.downloadBottom) els.downloadBottom.addEventListener("click", downloadResult);
    if (els.printBtn) els.printBtn.addEventListener("click", printResult);

    const tabs = $(".tabs");
    if (tabs) {
      tabs.addEventListener("click", (event) => {
        const button = event.target.closest(".tab-button");
        if (button) switchTab(button.dataset.tab);
      });
      tabs.addEventListener("keydown", (event) => {
        const buttons = $$(".tab-button", tabs);
        const index = buttons.indexOf(document.activeElement);
        if (index < 0) return;
        let nextIndex = null;
        if (event.key === "ArrowRight") nextIndex = (index + 1) % buttons.length;
        else if (event.key === "ArrowLeft") nextIndex = (index - 1 + buttons.length) % buttons.length;
        else if (event.key === "Home") nextIndex = 0;
        else if (event.key === "End") nextIndex = buttons.length - 1;
        if (nextIndex !== null) {
          event.preventDefault();
          const next = buttons[nextIndex];
          switchTab(next.dataset.tab);
          next.focus();
        }
      });
    }

    document.addEventListener("click", (event) => {
      const retry = event.target.closest("[data-retry-kb]");
      if (retry) {
        hideGlobalAlert();
        loadKnowledge();
        return;
      }

      const link = event.target.closest('a[href^="#"]');
      if (link) {
        const hash = link.getAttribute("href").slice(1);
        if (link.dataset.openTab) {
          state.activeTab = link.dataset.openTab;
          if (currentRoute() === "pengetahuan") {
            event.preventDefault();
            switchTab(state.activeTab);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        }
        if (ROUTES.includes(hash) && currentRoute() === hash) {
          event.preventDefault();
          renderRoute();
        }
      }

      if (!event.target.closest(".site-header")) closeNav();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeNav();
    });

    window.addEventListener("beforeprint", () => {
      $$("details").forEach((details) => {
        details.open = true;
      });
    });
  }

  function init() {
    restoreSession();
    bindEvents();

    const pathRoutes = {
      "/konsultasi": "konsultasi",
      "/hasil": "hasil",
      "/pengetahuan": "pengetahuan",
      "/tentang": "tentang",
    };
    const pathname = window.location.pathname.replace(/\/+$/, "") || "/";
    const hashIsValid = ROUTES.includes(window.location.hash.slice(1));
    const route = hashIsValid ? window.location.hash.slice(1) : pathRoutes[pathname] || "beranda";
    if (!hashIsValid) {
      window.history.replaceState(null, "", `#${route}`);
    }

    renderRoute();
    loadKnowledge();
    updateProgress();
  }

  init();
})();
