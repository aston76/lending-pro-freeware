/**
 * Lending Pro Freeware — Alerts Page
 * Overdue payment alerts + SMS notification system.
 * Dual-mode SMS: iPhone connected to Mac (Continuity) OR API (Semaphore/Twilio)
 */
const AlertsPage = {
    _alerts: [],
    _filter: 'all',  // all | critical | high | medium | low
    _currentAlert: null,  // Store current alert for modal use

    async render() {
        const content = document.getElementById('page-content');

        const [alerts, settings, templates] = await Promise.all([
            App.api('get_overdue_alerts'),
            App.api('get_settings'),
            App.api('get_sms_templates'),
        ]);

        this._alerts = alerts;
        this._settings = settings;
        this._templates = templates;

        // Severity counts
        const counts = { all: alerts.length, critical: 0, high: 0, medium: 0, low: 0 };
        alerts.forEach(a => counts[a.severity]++);

        const totalDue = alerts.reduce((s, a) => s + a.total_overdue_amount, 0);

        content.innerHTML = `
            <!-- Header Stats Strip -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5 stagger">
                ${this._statStrip('alert-triangle', 'Overdue Clients', counts.all, '#FF3B30', '#FF3B30')}
                ${this._statStrip('flame', 'Critical (60d+)', counts.critical, '#FF2D55', '#FF2D55')}
                ${this._statStrip('clock', 'Urgent (30-59d)', counts.high, '#FF9500', '#FF9500')}
                ${this._statStrip('banknote', 'Total Due', UI.formatCurrency(totalDue), '#007AFF', '#007AFF')}
            </div>

            <!-- Filter bar -->
            <div class="glass-card p-4 mb-4">
                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs font-semibold uppercase tracking-wider" style="color:var(--text-tertiary)">Filter:</span>
                    ${[
                { key: 'all', label: 'All', count: counts.all, color: 'btn-ghost' },
                { key: 'critical', label: 'Critical', count: counts.critical, color: 'btn-danger' },
                { key: 'high', label: 'Urgent', count: counts.high, color: '' },
                { key: 'medium', label: 'Moderate', count: counts.medium, color: '' },
                { key: 'low', label: 'Minor', count: counts.low, color: '' },
            ].map(f => `
                        <button id="alert-filter-${f.key}" onclick="AlertsPage.setFilter('${f.key}')"
                            class="btn btn-sm ${this._filter === f.key ? 'btn-primary' : 'btn-ghost'}">
                            ${f.label} <span class="ml-1 opacity-70">(${f.count})</span>
                        </button>
                    `).join('')}
                    <div class="flex-1"></div>
                    ${counts.all > 0 ? `
                    <button onclick="AlertsPage.sendBulkSMS()" class="btn btn-sm"
                        style="background:#17845b; color:white;">
                        <i data-lucide="message-square" class="w-3.5 h-3.5"></i>
                        Bulk SMS
                    </button>` : ''}
                </div>
            </div>

            <!-- Alerts List -->
            <div id="alerts-list">
                ${this._renderAlertsList(alerts)}
            </div>
        `;

        lucide.createIcons();
    },

    _statStrip(icon, label, value, color, glowColor) {
        return `
            <div class="glass-card p-4 flex items-center gap-3">
                <div class="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0"
                     style="background: ${color}22; border: 1px solid ${color}33;">
                    <i data-lucide="${icon}" class="w-5 h-5" style="color:${color}"></i>
                </div>
                <div>
                    <p class="text-xs font-medium" style="color:var(--text-tertiary)">${label}</p>
                    <p class="text-lg font-bold leading-tight" style="color:var(--text-primary)">${value}</p>
                </div>
            </div>
        `;
    },

    _renderAlertsList(alerts) {
        const filtered = this._filter === 'all'
            ? alerts
            : alerts.filter(a => a.severity === this._filter);

        if (filtered.length === 0) {
            if (alerts.length === 0) {
                return UI.emptyState(
                    'check-circle-2',
                    'No overdue payments!',
                    'All your clients are up to date. Great job!',
                    `<button onclick="App.navigate('dashboard')" class="btn btn-primary">
                        <i data-lucide="layout-dashboard" class="w-4 h-4"></i> Dashboard
                    </button>`
                );
            }
            return `<div class="glass-card p-8 text-center">
                <p class="text-gray-400 dark:text-slate-500">No clients in this category</p>
            </div>`;
        }

        return `
            <div class="space-y-3">
                ${filtered.map(alert => this._alertCard(alert)).join('')}
            </div>
        `;
    },

    _alertCard(a) {
        const sev = {
            critical: { color: '#FF2D55', bg: 'rgba(255,45,85,0.08)', border: 'rgba(255,45,85,0.25)', label: 'CRITICAL', barW: '100%' },
            high: { color: '#FF9500', bg: 'rgba(255,149,0,0.08)', border: 'rgba(255,149,0,0.25)', label: 'URGENT', barW: '75%' },
            medium: { color: '#FFCC00', bg: 'rgba(255,204,0,0.08)', border: 'rgba(255,204,0,0.25)', label: 'MODERATE', barW: '50%' },
            low: { color: '#34C759', bg: 'rgba(52,199,89,0.08)', border: 'rgba(52,199,89,0.25)', label: 'MINOR', barW: '25%' },
        }[a.severity];

        const name = `${a.first_name} ${a.last_name}`;
        const initials = `${a.first_name[0]}${a.last_name[0]}`.toUpperCase();
        const hasPhone = a.contact && a.contact.trim().length > 3;

        // Store alert data safely using index into _alerts array
        const alertIndex = this._alerts.findIndex(x => x.loan_id === a.loan_id);

        return `
            <div class="glass-card overflow-hidden" style="border: 1px solid ${sev.border}; background: ${sev.bg};">
                <!-- Severity bar -->
                <div style="height:3px; width:${sev.barW}; background:${sev.color};"></div>

                <div class="p-4">
                    <div class="flex items-start gap-4">
                        <!-- Avatar + severity badge -->
                        <div class="relative flex-shrink-0">
                            <div class="w-11 h-11 rounded-2xl flex items-center justify-center text-white text-sm font-bold"
                                 style="background:${sev.color};">
                                ${initials}
                            </div>
                            <div class="absolute -bottom-1 -right-1 text-[10px] px-1 rounded-full font-bold"
                                 style="background:${sev.color}; color:white; font-size:9px;">
                                ${a.days_overdue}d
                            </div>
                        </div>

                        <!-- Info -->
                        <div class="flex-1 min-w-0">
                            <div class="flex items-start justify-between gap-2 flex-wrap">
                                <div>
                                    <div class="flex items-center gap-2 flex-wrap">
                                        <button onclick="App.navigate('client_detail', {id: '${a.client_id}'})"
                                            class="font-bold text-sm hover:underline" style="color:var(--text-primary)">
                                            ${name}
                                        </button>
                                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
                                              style="background:${sev.color}22; color:${sev.color}; border:1px solid ${sev.color}44;">
                                            ${sev.label}
                                        </span>
                                    </div>
                                    <p class="text-xs mt-0.5" style="color:var(--text-tertiary)">
                                        ${a.client_id} • Loan #${a.loan_id}
                                    </p>
                                </div>
                                <div class="text-right">
                                    <p class="font-bold text-sm" style="color:${sev.color}">
                                        ${UI.formatCurrency(a.total_overdue_amount)}
                                    </p>
                                    <p class="text-xs" style="color:var(--text-tertiary)">
                                        ${a.missed_count} missed installment${a.missed_count > 1 ? 's' : ''}
                                    </p>
                                </div>
                            </div>

                            <!-- Details row -->
                            <div class="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs" style="color:var(--text-secondary)">
                                <span>
                                    <i data-lucide="calendar-x" class="w-3 h-3 inline-block mr-1 opacity-60"></i>
                                    First overdue: ${UI.formatDate(a.earliest_due)}
                                </span>
                                <span>
                                    <i data-lucide="credit-card" class="w-3 h-3 inline-block mr-1 opacity-60"></i>
                                    Monthly: ${UI.formatCurrency(a.monthly_payment)}
                                </span>
                                ${hasPhone ? `
                                <button onclick="AlertsPage._copyPhone('${a.contact}')"
                                    class="flex items-center gap-1 hover:text-blue-500 transition cursor-pointer"
                                    title="Copy number">
                                    <i data-lucide="phone" class="w-3 h-3 opacity-60"></i>
                                    <span class="font-mono">${a.contact}</span>
                                </button>` : `
                                <span class="opacity-40">
                                    <i data-lucide="phone-off" class="w-3 h-3 inline-block mr-1 opacity-60"></i>
                                    No contact info
                                </span>`}
                            </div>
                        </div>
                    </div>

                    <!-- Action buttons -->
                    <div class="flex flex-wrap gap-2 mt-3 pt-3"
                         style="border-top: 0.5px solid rgba(255,255,255,0.07);">
                        ${hasPhone ? `
                        <button onclick="AlertsPage.openSmsModal(${alertIndex})"
                            class="btn btn-sm btn-primary flex items-center gap-1.5">
                            <i data-lucide="send" class="w-3.5 h-3.5"></i> Send SMS
                        </button>
                        <button onclick="AlertsPage._callPhone('${a.contact}')"
                            class="btn btn-sm btn-ghost flex items-center gap-1.5">
                            <i data-lucide="phone-call" class="w-3.5 h-3.5"></i> Call
                        </button>` : `
                        <span class="text-xs italic" style="color:var(--text-tertiary)">
                            No phone number —
                            <button onclick="App.navigate('client_detail', {id: '${a.client_id}'})"
                                class="text-blue-500 hover:underline">Edit profile</button>
                        </span>`}
                        <button onclick="App.navigate('loan_detail', {id: ${a.loan_id}})"
                            class="btn btn-sm btn-ghost flex items-center gap-1.5">
                            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> View Loan
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    setFilter(f) {
        this._filter = f;

        // Update button states
        ['all', 'critical', 'high', 'medium', 'low'].forEach(k => {
            const btn = document.getElementById(`alert-filter-${k}`);
            if (btn) {
                btn.className = btn.className.replace('btn-primary', 'btn-ghost');
                if (k === f) btn.className = btn.className.replace('btn-ghost', 'btn-primary');
            }
        });

        // Re-render list
        const list = document.getElementById('alerts-list');
        if (list) {
            list.innerHTML = this._renderAlertsList(this._alerts);
            lucide.createIcons();
        }
    },

    // ─── SMS Modal ───────────────────────────────────────────────
    // alertIndex is the index into this._alerts array (safe, no JSON-in-HTML)
    openSmsModal(alertIndex) {
        const alert = this._alerts[alertIndex];
        if (!alert) return;

        // Store current alert for use by send/apply functions
        this._currentAlert = alert;

        const settings = this._settings || {};
        const templates = this._templates || [];
        const companyName = settings.company_name || App.appName;
        const companyPhone = settings.company_phone || '';

        const fillTemplate = (tpl) => {
            return tpl
                .replace(/{name}/g, `${alert.first_name} ${alert.last_name}`)
                .replace(/{amount}/g, UI.formatCurrency(alert.total_overdue_amount))
                .replace(/{date}/g, alert.earliest_due)
                .replace(/{days}/g, alert.days_overdue)
                .replace(/{company}/g, companyName)
                .replace(/{phone}/g, companyPhone || '[your number]');
        };

        const firstTemplate = templates.length > 0 ? fillTemplate(templates[0].text) : '';

        UI.showModal(`Send SMS to ${alert.first_name} ${alert.last_name}`, `
            <div class="space-y-4">
                <!-- Client info strip -->
                <div class="flex items-center gap-3 p-3 rounded-xl"
                     style="background: var(--surface-2);">
                    <div class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                         style="background:var(--accent);">
                        ${alert.first_name[0]}${alert.last_name[0]}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="font-semibold text-sm" style="color:var(--text-primary)">${alert.first_name} ${alert.last_name}</p>
                        <p class="text-xs font-mono" style="color:var(--text-secondary)">${alert.contact}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs font-bold" style="color:#FF3B30">${UI.formatCurrency(alert.total_overdue_amount)}</p>
                        <p class="text-xs" style="color:var(--text-tertiary)">${alert.days_overdue} days overdue</p>
                    </div>
                </div>

                <!-- Template selector -->
                <div>
                    <label class="text-xs font-semibold uppercase tracking-wider mb-2 block"
                           style="color:var(--text-tertiary)">Message Template</label>
                    <div class="flex flex-wrap gap-2 mb-3">
                        ${templates.map((t, i) => `
                            <button type="button" onclick="AlertsPage._applyTemplate(${i})"
                                class="btn btn-sm btn-ghost sms-tpl-btn" id="tpl-btn-${i}">
                                ${t.name}
                            </button>
                        `).join('')}
                        <button type="button" onclick="AlertsPage._clearSmsText()"
                            class="btn btn-sm btn-ghost"><i data-lucide="pencil" class="w-3.5 h-3.5"></i>Custom</button>
                    </div>
                </div>

                <!-- Message textarea -->
                <div>
                    <label class="text-xs font-semibold uppercase tracking-wider mb-1.5 block"
                           style="color:var(--text-tertiary)">Message</label>
                    <textarea id="sms-text" rows="5"
                        class="input w-full font-mono text-sm leading-relaxed resize-none"
                        placeholder="Write your message here…"
                        oninput="AlertsPage._updateSmsCount()">${firstTemplate}</textarea>
                    <div class="flex justify-between mt-1">
                        <p class="text-xs" style="color:var(--text-tertiary)">
                            Variables: <code>{name}</code>, <code>{amount}</code>, <code>{date}</code>, <code>{days}</code>, <code>{company}</code>, <code>{phone}</code>
                        </p>
                        <p id="sms-char-count" class="text-xs font-mono" style="color:var(--text-tertiary)">
                            ${firstTemplate.length} / 160
                        </p>
                    </div>
                </div>

                <!-- Send method -->
                <div>
                    <label class="text-xs font-semibold uppercase tracking-wider mb-2 block"
                           style="color:var(--text-tertiary)">Send Method</label>
                    <div class="grid grid-cols-2 gap-3">
                        <label class="flex items-start gap-3 p-3 rounded-xl cursor-pointer border-2 transition"
                               style="border-color: var(--accent); background: var(--accent)11;"
                               id="method-phone-card">
                            <input type="radio" name="sms-method" value="phone" checked
                                   onchange="AlertsPage._toggleMethodCard()"
                                   class="mt-0.5 accent-blue-500">
                            <div>
                                <p class="text-sm font-semibold flex items-center gap-1.5" style="color:var(--text-primary)">
                                    <i data-lucide="smartphone" class="w-3.5 h-3.5"></i>
                                    iPhone (Mac Continuity)
                                </p>
                                <p class="text-xs mt-0.5" style="color:var(--text-tertiary)">
                                    Opens Messages with pre-filled message. Requires iPhone connected via Handoff.
                                </p>
                            </div>
                        </label>
                        <label class="flex items-start gap-3 p-3 rounded-xl cursor-pointer border-2 transition"
                               style="border-color: var(--surface-2); background: transparent;"
                               id="method-api-card">
                            <input type="radio" name="sms-method" value="api"
                                   onchange="AlertsPage._toggleMethodCard()"
                                   class="mt-0.5 accent-blue-500">
                            <div>
                                <p class="text-sm font-semibold flex items-center gap-1.5" style="color:var(--text-primary)">
                                    <i data-lucide="globe" class="w-3.5 h-3.5"></i>
                                    SMS API
                                </p>
                                <p class="text-xs mt-0.5" style="color:var(--text-tertiary)">
                                    Send via Semaphore (PH) or Twilio. Requires API key in Settings.
                                </p>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- Action buttons -->
                <div class="flex gap-3 justify-end pt-2" style="border-top: 0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="AlertsPage._sendSms()"
                        class="btn btn-primary flex items-center gap-2">
                        <i data-lucide="send" class="w-4 h-4"></i>
                        Send
                    </button>
                </div>
            </div>
        `, { width: 'max-w-2xl' });

        // Auto-select first template button
        setTimeout(() => {
            const btn = document.getElementById('tpl-btn-0');
            if (btn) btn.classList.add('btn-primary');
            lucide.createIcons();
        }, 50);
    },

    // Use this._currentAlert (set in openSmsModal) — no JSON-in-HTML issues
    _applyTemplate(index) {
        const alert = this._currentAlert;
        if (!alert) return;

        const tpl = this._templates[index];
        if (!tpl) return;

        const settings = this._settings || {};
        const companyName = settings.company_name || App.appName;
        const companyPhone = settings.company_phone || '';

        const filled = tpl.text
            .replace(/{name}/g, `${alert.first_name} ${alert.last_name}`)
            .replace(/{amount}/g, UI.formatCurrency(alert.total_overdue_amount))
            .replace(/{date}/g, alert.earliest_due)
            .replace(/{days}/g, alert.days_overdue)
            .replace(/{company}/g, companyName)
            .replace(/{phone}/g, companyPhone || '[your number]');

        const ta = document.getElementById('sms-text');
        if (ta) {
            ta.value = filled;
            this._updateSmsCount();
        }

        // Highlight active template button
        document.querySelectorAll('.sms-tpl-btn').forEach((b, i) => {
            b.classList.toggle('btn-primary', i === index);
            b.classList.toggle('btn-ghost', i !== index);
        });
        SoundEngine.click();
    },

    _clearSmsText() {
        const ta = document.getElementById('sms-text');
        if (ta) { ta.value = ''; ta.focus(); this._updateSmsCount(); }
        document.querySelectorAll('.sms-tpl-btn').forEach(b => {
            b.classList.remove('btn-primary');
            b.classList.add('btn-ghost');
        });
    },

    _updateSmsCount() {
        const ta = document.getElementById('sms-text');
        const el = document.getElementById('sms-char-count');
        if (ta && el) {
            const len = ta.value.length;
            el.textContent = `${len} / 160`;
            el.style.color = len > 160 ? 'var(--apple-red)' : 'var(--text-tertiary)';
        }
    },

    _toggleMethodCard() {
        const method = document.querySelector('input[name="sms-method"]:checked')?.value;
        const phoneCard = document.getElementById('method-phone-card');
        const apiCard = document.getElementById('method-api-card');
        if (!phoneCard || !apiCard) return;
        if (method === 'phone') {
            phoneCard.style.borderColor = 'var(--accent)';
            phoneCard.style.background = 'color-mix(in srgb, var(--accent) 8%, transparent)';
            apiCard.style.borderColor = 'var(--surface-2)';
            apiCard.style.background = 'transparent';
        } else {
            apiCard.style.borderColor = 'var(--accent)';
            apiCard.style.background = 'color-mix(in srgb, var(--accent) 8%, transparent)';
            phoneCard.style.borderColor = 'var(--surface-2)';
            phoneCard.style.background = 'transparent';
        }
        SoundEngine.toggle();
    },

    async _sendSms() {
        const alert = this._currentAlert;
        const message = document.getElementById('sms-text')?.value?.trim();
        const method = document.querySelector('input[name="sms-method"]:checked')?.value || 'phone';

        if (!message) {
            UI.toast('Please write a message before sending.', 'warning');
            return;
        }
        if (!alert || !alert.contact || alert.contact.length < 4) {
            UI.toast('Invalid phone number.', 'error');
            return;
        }

        UI.closeModal();
        UI.toast('Sending SMS…', 'info');

        let result;
        if (method === 'phone') {
            result = await App.api('send_sms_via_phone', alert.contact, message);
        } else {
            result = await App.api('send_sms_via_api', alert.contact, message);
        }

        if (result.success) {
            if (method === 'phone') {
                if (result.method === 'phone_fallback') {
                    UI.toast('AppleScript unavailable. Messages opened via sms://.', 'warning');
                } else {
                    UI.toast('SMS sent via Messages.app (iPhone Continuity).', 'success');
                }
            } else {
                UI.toast(`SMS sent via ${result.provider || 'API'}.`, 'success');
            }
            SoundEngine.success();
        } else {
            UI.toast('Failed: ' + (result.error || 'Unknown error'), 'error');
        }
    },

    _copyPhone(phone) {
        navigator.clipboard.writeText(phone).then(() => {
            UI.toast(`Number copied: ${phone}`, 'success');
            SoundEngine.click();
        }).catch(() => UI.toast('Could not copy', 'error'));
    },

    _callPhone(phone) {
        const clean = phone.replace(/\s/g, '');
        window.open(`tel:${clean}`);
        UI.toast(`Calling ${phone}...`, 'info');
    },

    // ─── Bulk SMS ────────────────────────────────────────────────
    sendBulkSMS() {
        const filtered = this._filter === 'all'
            ? this._alerts
            : this._alerts.filter(a => a.severity === this._filter);

        const withPhone = filtered.filter(a => a.contact && a.contact.trim().length > 3);
        const noPhone = filtered.length - withPhone.length;
        const templates = this._templates || [];

        UI.showModal(`Bulk SMS — ${filtered.length} client${filtered.length > 1 ? 's' : ''}`, `
            <div class="space-y-4">
                <div class="p-3 rounded-xl" style="background: var(--surface-2);">
                    <p class="text-sm" style="color:var(--text-primary)">
                        <strong>${withPhone.length}</strong> client${withPhone.length > 1 ? 's' : ''} with phone number
                        ${noPhone > 0 ? `• <span style="color:#FF9500">${noPhone} without contact (skipped)</span>` : ''}
                    </p>
                </div>

                <div>
                    <label class="text-xs font-semibold uppercase tracking-wider mb-2 block"
                           style="color:var(--text-tertiary)">Template to use</label>
                    <select id="bulk-tpl-select" class="input select w-full">
                        ${templates.map((t, i) => `<option value="${i}">${t.name}</option>`).join('')}
                    </select>
                </div>

                <div class="max-h-48 overflow-y-auto space-y-2">
                    ${withPhone.map(a => `
                        <div class="flex items-center gap-2 p-2 rounded-lg text-sm"
                             style="background: var(--surface-2);">
                            <div class="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                                 style="background: ${{ critical: '#FF2D55', high: '#FF9500', medium: '#FFCC00', low: '#34C759' }[a.severity]}">
                                ${a.first_name[0]}${a.last_name[0]}
                            </div>
                            <span style="color:var(--text-primary)" class="flex-1">${a.first_name} ${a.last_name}</span>
                            <span class="font-mono text-xs" style="color:var(--text-secondary)">${a.contact}</span>
                            <span class="text-xs font-bold" style="color:#FF3B30">${a.days_overdue}d</span>
                        </div>
                    `).join('')}
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <label class="flex items-center gap-2 p-3 rounded-xl cursor-pointer border-2"
                           style="border-color:var(--accent)">
                        <input type="radio" name="bulk-method" value="phone" checked class="accent-blue-500">
                        <div>
                            <p class="text-sm font-semibold" style="color:var(--text-primary)">iPhone (Continuity)</p>
                            <p class="text-xs" style="color:var(--text-tertiary)">Opens Messages for each client</p>
                        </div>
                    </label>
                    <label class="flex items-center gap-2 p-3 rounded-xl cursor-pointer border-2"
                           style="border-color:var(--surface-2)">
                        <input type="radio" name="bulk-method" value="api" class="accent-blue-500">
                        <div>
                            <p class="text-sm font-semibold" style="color:var(--text-primary)">SMS API</p>
                            <p class="text-xs" style="color:var(--text-tertiary)">Direct automatic send</p>
                        </div>
                    </label>
                </div>

                <div class="flex gap-3 justify-end pt-2" style="border-top: 0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="AlertsPage._sendBulk()" class="btn btn-primary">
                        <i data-lucide="send" class="w-4 h-4"></i>
                        Send to ${withPhone.length} client${withPhone.length > 1 ? 's' : ''}
                    </button>
                </div>
            </div>
        `, { width: 'max-w-lg' });
        lucide.createIcons();
    },

    async _sendBulk() {
        const tplIndex = parseInt(document.getElementById('bulk-tpl-select')?.value || '0');
        const method = document.querySelector('input[name="bulk-method"]:checked')?.value || 'phone';
        const tpl = this._templates[tplIndex];
        const settings = this._settings || {};
        const companyName = settings.company_name || App.appName;
        const companyPhone = settings.company_phone || '';

        if (!tpl) {
            UI.toast('No template selected.', 'warning');
            return;
        }

        const filtered = this._filter === 'all' ? this._alerts : this._alerts.filter(a => a.severity === this._filter);
        const withPhone = filtered.filter(a => a.contact && a.contact.trim().length > 3);

        UI.closeModal();

        let sent = 0, failed = 0;
        for (const a of withPhone) {
            const message = tpl.text
                .replace(/{name}/g, `${a.first_name} ${a.last_name}`)
                .replace(/{amount}/g, UI.formatCurrency(a.total_overdue_amount))
                .replace(/{date}/g, a.earliest_due)
                .replace(/{days}/g, a.days_overdue)
                .replace(/{company}/g, companyName)
                .replace(/{phone}/g, companyPhone || '[number]');

            const fn = method === 'phone' ? 'send_sms_via_phone' : 'send_sms_via_api';
            const res = await App.api(fn, a.contact, message);

            if (res.success) {
                sent++;
                // Small delay for iPhone method to avoid overwhelming Messages.app
                if (method === 'phone') await new Promise(r => setTimeout(r, 800));
            } else {
                failed++;
            }
        }

        if (method === 'phone') {
            UI.toast(`${sent} SMS sent via Messages.app (iPhone Continuity). Each client has their own conversation.`, 'success');
        } else {
            if (failed === 0) {
                UI.toast(`${sent} SMS sent successfully.`, 'success');
            } else {
                UI.toast(`${sent} sent, ${failed} failed.`, 'warning');
            }
        }
        SoundEngine.success();
    },
};
