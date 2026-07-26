/**
 * Lending Pro Freeware — Main Application
 * SPA Router, Apple Design, Sound Engine, pywebview API Bridge
 */

// ─── Sound Engine — iPhone-style subtle sounds ────────────────
// All sounds inspired by iOS HapticFeedback: ultra-low volume,
// very short duration, clean sine waves, never intrusive.
const SoundEngine = {
    enabled: true,

    init() {
        this.enabled = localStorage.getItem('ph-sounds-enabled') !== 'false';
        this._updateHeaderIcon();
    },

    _ensure() {
        if (!this.__ctx) {
            try { this.__ctx = new (window.AudioContext || window.webkitAudioContext)(); }
            catch (e) { return null; }
        }
        if (this.__ctx.state === 'suspended') this.__ctx.resume();
        return this.__ctx;
    },

    _p(fn) {
        if (!this.enabled) return;
        const ctx = this._ensure();
        if (!ctx) return;
        try { fn(ctx); } catch (e) { }
    },

    // ── Tap — ultra-subtle keyboard-style click (like iPhone keyboard) ──
    click() {
        this._p(ctx => {
            const o = ctx.createOscillator(), g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.type = 'sine';
            o.frequency.setValueAtTime(1200, ctx.currentTime);
            o.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.025);
            g.gain.setValueAtTime(0.03, ctx.currentTime);          // très bas
            g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.03);
            o.start(ctx.currentTime);
            o.stop(ctx.currentTime + 0.035);
        });
    },

    // ── Modal open — très doux, quasi imperceptible ─────────────
    modalOpen() {
        this._p(ctx => {
            const o = ctx.createOscillator(), g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.type = 'sine';
            o.frequency.setValueAtTime(600, ctx.currentTime);
            o.frequency.exponentialRampToValueAtTime(900, ctx.currentTime + 0.1);
            g.gain.setValueAtTime(0, ctx.currentTime);
            g.gain.linearRampToValueAtTime(0.025, ctx.currentTime + 0.02);
            g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.12);
            o.start(ctx.currentTime);
            o.stop(ctx.currentTime + 0.13);
        });
    },

    // ── Modal close — léger descente, à peine audible ───────────
    modalClose() {
        this._p(ctx => {
            const o = ctx.createOscillator(), g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.type = 'sine';
            o.frequency.setValueAtTime(800, ctx.currentTime);
            o.frequency.exponentialRampToValueAtTime(500, ctx.currentTime + 0.08);
            g.gain.setValueAtTime(0.02, ctx.currentTime);
            g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.09);
            o.start(ctx.currentTime);
            o.stop(ctx.currentTime + 0.1);
        });
    },

    // ── Success — deux micro-notes (comme "message envoyé" iOS) ─
    success() {
        this._p(ctx => {
            [[0, 880, 0.028], [0.08, 1100, 0.022]].forEach(([t, freq, vol]) => {
                const o = ctx.createOscillator(), g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.type = 'sine'; o.frequency.value = freq;
                g.gain.setValueAtTime(0, ctx.currentTime + t);
                g.gain.linearRampToValueAtTime(vol, ctx.currentTime + t + 0.01);
                g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.14);
                o.start(ctx.currentTime + t);
                o.stop(ctx.currentTime + t + 0.15);
            });
        });
    },

    // ── Error — léger double bip grave, très doux ───────────────
    error() {
        this._p(ctx => {
            [[0, 300, 0.03], [0.09, 220, 0.025]].forEach(([t, freq, vol]) => {
                const o = ctx.createOscillator(), g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.type = 'sine'; o.frequency.value = freq;
                g.gain.setValueAtTime(vol, ctx.currentTime + t);
                g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.1);
                o.start(ctx.currentTime + t);
                o.stop(ctx.currentTime + t + 0.11);
            });
        });
    },

    // ── Navigate — quasi-silencieux, un souffle ─────────────────
    navigate() {
        this._p(ctx => {
            const N = Math.floor(ctx.sampleRate * 0.06);
            const buf = ctx.createBuffer(1, N, ctx.sampleRate);
            const d = buf.getChannelData(0);
            for (let i = 0; i < N; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / N);
            const src = ctx.createBufferSource();
            src.buffer = buf;
            const f = ctx.createBiquadFilter();
            f.type = 'highpass'; f.frequency.value = 3000;
            const g = ctx.createGain();
            src.connect(f); f.connect(g); g.connect(ctx.destination);
            g.gain.setValueAtTime(0.012, ctx.currentTime);        // quasi-silencieux
            g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.06);
            src.start(ctx.currentTime);
        });
    },

    // ── Save — micro-tick propre, très court ────────────────────
    save() {
        this._p(ctx => {
            const o = ctx.createOscillator(), g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.type = 'sine';
            o.frequency.setValueAtTime(1000, ctx.currentTime);
            o.frequency.exponentialRampToValueAtTime(1300, ctx.currentTime + 0.04);
            g.gain.setValueAtTime(0.028, ctx.currentTime);
            g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.07);
            o.start(ctx.currentTime);
            o.stop(ctx.currentTime + 0.08);
        });
    },

    // ── Toggle — deux micro-clics (comme switch iOS) ────────────
    toggle() {
        this._p(ctx => {
            [0, 0.04].forEach((t, i) => {
                const o = ctx.createOscillator(), g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.type = 'sine';
                o.frequency.value = i === 0 ? 900 : 1100;
                g.gain.setValueAtTime(0.02, ctx.currentTime + t);
                g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.04);
                o.start(ctx.currentTime + t);
                o.stop(ctx.currentTime + t + 0.045);
            });
        });
    },

    setEnabled(val) {
        this.enabled = val;
        localStorage.setItem('ph-sounds-enabled', val ? 'true' : 'false');
        this._updateHeaderIcon();
    },

    _updateHeaderIcon() {
        const icon = document.getElementById('sound-icon');
        if (!icon) return;
        icon.setAttribute('data-lucide', this.enabled ? 'volume-2' : 'volume-x');
        lucide.createIcons({ nodes: [icon] });
    }

};

// Donation reminder frequency is stored locally because this offline app does
// not receive Ko-fi payment status.
const DonationSupport = {
    url: 'https://ko-fi.com/astonswissapp',
    weekMs: 7 * 24 * 60 * 60 * 1000,
    quarterMs: 90 * 24 * 60 * 60 * 1000,
    lastPromptKey: 'lpf-donation-last-prompt-at',
    donatedKey: 'lpf-donation-confirmed-at',

    async init() {},

    maybePrompt() {
        const lastPrompt = Number(localStorage.getItem(this.lastPromptKey) || 0);
        const interval = this.hasDonated() ? this.quarterMs : this.weekMs;
        if (!Number.isFinite(lastPrompt) || Date.now() - lastPrompt >= interval) {
            this.show(true);
        }
    },

    hasDonated() {
        return Boolean(localStorage.getItem(this.donatedKey));
    },

    show(recordScheduledPrompt = false) {
        if (recordScheduledPrompt) {
            localStorage.setItem(this.lastPromptKey, String(Date.now()));
        }
        const reminder = this.hasDonated() ? I18n.t('quarterly') : I18n.t('weekly');
        UI.showModal(I18n.t('title'), `
            <div class="text-center space-y-4 py-2">
                <div class="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center"
                     style="background:rgba(255,149,0,0.12); color:#B86700;">
                    <i data-lucide="coffee" class="w-7 h-7"></i>
                </div>
                <div class="space-y-2">
                    <p class="text-sm font-semibold" style="color:var(--text-primary)">
                        ${I18n.t('message')}
                    </p>
                    <p class="text-sm" style="color:var(--text-secondary)">
                        ${I18n.t('minimum')}
                    </p>
                </div>
                <div class="flex flex-wrap gap-2 justify-center pt-1">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">${I18n.t('later')}</button>
                    <button onclick="DonationSupport.confirmDonation()" class="btn btn-ghost">${I18n.t('donated')}</button>
                    <button onclick="DonationSupport.open()" class="btn btn-primary">
                        <i data-lucide="coffee" class="w-4 h-4"></i> ${I18n.t('coffee')}
                    </button>
                </div>
                <p class="text-[11px]" style="color:var(--text-tertiary)">
                    ${reminder}
                </p>
            </div>
        `, { width: 'max-w-md' });
    },

    async open() {
        const result = await App.api('open_url', this.url);
        if (!result?.success) {
            UI.toast(result?.error || 'Impossible d’ouvrir la page de don.', 'error');
            return;
        }
        UI.closeModal();
    },

    confirmDonation() {
        const now = String(Date.now());
        localStorage.setItem(this.donatedKey, now);
        localStorage.setItem(this.lastPromptKey, now);
        UI.closeModal();
        UI.toast(I18n.t('thanks'), 'success');
    }
};

// ─── App ──────────────────────────────────────────────────────
const App = {
    currentPage: 'dashboard',
    currentParams: {},
    darkMode: true,
    currentTheme: 'blue',
    sidebarOpen: false,
    calcExpression: '',
    calcLastResult: false,
    appName: 'Lending Pro Freeware',
    currencyCode: 'PHP',
    language: 'en',
    isDemoOnly: false,
    isDemoEdition: false,

    // ─── Initialize ──────────────────────────────────────────
    async init() {
        while (!window.pywebview || !window.pywebview.api) {
            await new Promise(r => setTimeout(r, 100));
        }

        const savedTheme = localStorage.getItem('ph-lending-theme');
        if (savedTheme === 'light') {
            this.darkMode = false;
            document.documentElement.classList.remove('dark');
        }
        const savedColor = localStorage.getItem('ph-lending-color') || 'blue';
        this.applyColorTheme(savedColor);
        this.updateThemeUI();
        this.checkOnlineStatus();
        const appMode = await pywebview.api.get_app_mode();
        this.appName = appMode.name || this.appName;
        this.isDemoOnly = Boolean(appMode.demo_only);
        this.isDemoEdition = Boolean(appMode.demo_edition);
        this.isDemoMode = Boolean(appMode.demo_active);
        document.title = this.appName;
        const versionLabel = document.getElementById('sidebar-version');
        if (versionLabel) versionLabel.textContent = `v1.3.1 - ${this.appName}`;
        this.updateDemoControl();
        setInterval(() => this.checkOnlineStatus(), 30000);
        this.loadLogo();
        SoundEngine.init();

        // Load company name
        try {
            const settings = await pywebview.api.get_settings();
            this.currencyCode = settings.currency || 'PHP';
            this.language = settings.language || navigator.language || 'en';
            I18n.setLanguage(this.language);
            if (settings.company_name) {
                const el = document.getElementById('sidebar-company-name');
                if (el) el.textContent = settings.company_name;
            }
        } catch (e) { }

        await this.navigate('dashboard');
        lucide.createIcons();
        await DonationSupport.init();
        DonationSupport.maybePrompt();

        // Load and refresh overdue alerts badge
        this.refreshAlertsBadge();
        setInterval(() => this.refreshAlertsBadge(), 5 * 60 * 1000); // every 5 min
    },

    // ─── Alerts Badge ─────────────────────────────────────────
    async refreshAlertsBadge() {
        try {
            const count = await pywebview.api.get_overdue_count();
            const badge = document.getElementById('alerts-badge');
            if (!badge) return;
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.classList.remove('hidden');
                // Pulse animation if critical
                badge.style.animation = 'pulse 2s infinite';
            } else {
                badge.classList.add('hidden');
            }
        } catch (e) { }
    },

    // ─── Logo ────────────────────────────────────────────────
    async loadLogo() {
        try {
            const logo = await pywebview.api.get_logo_base64();
            const container = document.getElementById('sidebar-logo');
            if (!container) return;

            const sz = localStorage.getItem('ph-logo-size') || 'M';
            const sizeMap = { S: ['w-8', 'h-8'], M: ['w-9', 'h-9'], L: ['w-12', 'h-12'] };
            const [w, h] = sizeMap[sz] || sizeMap.M;
            container.classList.remove('w-8', 'h-8', 'w-9', 'h-9', 'w-12', 'h-12');
            container.classList.add(w, h);

            if (logo) {
                container.innerHTML = `<img src="${logo}" class="w-full h-full object-cover rounded-xl">`;
            } else {
                container.innerHTML = `<i data-lucide="landmark" class="w-5 h-5 text-white"></i>`;
                lucide.createIcons();
            }
        } catch (e) { }
    },

    // ─── Demo Control ────────────────────────────────────────
    updateDemoControl() {
        const button = document.getElementById('demo-mode-btn');
        const label = document.getElementById('demo-mode-label');
        const icon = document.getElementById('demo-mode-icon');
        if (!button) return;

        if (!this.isDemoEdition) {
            button.classList.add('hidden');
            button.classList.remove('flex');
            return;
        }

        button.classList.remove('hidden');
        button.classList.add('flex');
        button.title = this.isDemoMode ? 'Quitter le mode démo' : 'Tester le mode démo';
        button.style.cssText = this.isDemoMode
            ? 'background:#B86700; color:white; border:1px solid #B86700;'
            : 'background:rgba(255,149,0,0.12); color:#B86700; border:1px solid rgba(255,149,0,0.28);';
        if (label) label.textContent = this.isDemoMode ? 'Quitter la démo' : 'Tester la démo';
        if (icon) {
            icon.setAttribute('data-lucide', this.isDemoMode ? 'log-out' : 'flask-conical');
            lucide.createIcons({ nodes: [icon] });
        }
    },

    requestDemoMode() {
        this.setDemoMode(!this.isDemoMode);
    },

    async setDemoMode(enabled) {
        const button = document.getElementById('demo-mode-btn');
        if (button?.disabled) return;
        if (button) button.disabled = true;

        try {
            if (enabled) UI.toast('Préparation des données de démonstration…', 'info');
            const result = await this.api('toggle_demo_mode', enabled);
            if (!result?.success) {
                UI.toast(result?.error || 'Impossible de changer le mode démo.', 'error');
                return;
            }

            this.isDemoMode = Boolean(result.demo_active);
            this.isDemoOnly = Boolean(result.demo_only);
            this.isDemoEdition = Boolean(result.demo_edition);
            this.updateDemoControl();

            const settings = await this.api('get_settings');
            this.currencyCode = settings.currency || 'PHP';
            const nameEl = document.getElementById('sidebar-company-name');
            if (nameEl) nameEl.textContent = settings.company_name || this.appName;
            await this.refreshAlertsBadge();
            await this.navigate('dashboard');
            UI.toast(
                enabled ? 'Mode démo activé : données fictives uniquement.' : 'Mode démo quitté : base personnelle active.',
                'success'
            );
        } finally {
            if (button) button.disabled = false;
        }
    },

    // ─── Router ──────────────────────────────────────────────
    async navigate(page, params = {}) {
        this.currentPage = page;
        this.currentParams = params || {};
        SoundEngine.navigate();
        // Update print button tooltip based on context
        this._updatePrintBtn(page);

        if (window.innerWidth < 1024) this.closeSidebar();

        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        const content = document.getElementById('page-content');
        content.innerHTML = UI.skeleton(5);

        const titles = {
            dashboard: ['Dashboard', 'Overview of your lending portfolio'],
            clients: ['Clients', 'Manage your borrower database'],
            client_detail: ['Client Details', 'View client profile and history'],
            loans: ['Loans', 'Manage all loan agreements'],
            loan_detail: ['Loan Details', 'View loan schedule and payments'],
            payments: ['Payments', 'Track all payment transactions'],
            calendar: ['Collection Calendar', "Today's and upcoming collections"],
            alerts: ['Overdue Alerts', 'Late paying clients & SMS notifications'],
            commissions: ['Referral Commissions', 'Track referral earnings'],
            settings: ['Settings', 'Application configuration and backup'],
            help: ['Help & User Guide', 'Complete guide to using Lending Pro Freeware'],
            logs: ['System Logs', 'Persistent logs — errors & events'],
        };

        const [title, subtitle] = titles[page] || ['Lending Pro Freeware', ''];
        document.getElementById('page-title').textContent = title;
        document.getElementById('page-subtitle').textContent = subtitle;

        try {
            switch (page) {
                case 'dashboard': await DashboardPage.render(); break;
                case 'clients': await ClientsPage.render(); break;
                case 'client_detail': await ClientDetailPage.render(params.id); break;
                case 'loans': await LoansPage.render(); break;
                case 'loan_detail': await LoanDetailPage.render(params.id); break;
                case 'payments': await PaymentsPage.render(); break;
                case 'calendar': await CalendarPage.render(); break;
                case 'alerts': await AlertsPage.render(); break;
                case 'commissions': await CommissionsPage.render(); break;
                case 'settings': await SettingsPage.render(); break;
                case 'help': await HelpPage.render(); break;
                case 'logs':
                    content.innerHTML = LogsPage.render();
                    await LogsPage.init();
                    break;
            }
        } catch (err) {
            console.error('Page render error:', err);
            content.innerHTML = `
                <div class="flex flex-col items-center justify-center py-20">
                    <i data-lucide="alert-triangle" class="w-12 h-12 mb-4" style="color: var(--apple-red)"></i>
                    <p class="text-lg font-semibold" style="color: var(--text-primary)">Error loading page</p>
                    <p class="text-sm mt-1" style="color: var(--text-secondary)">${err.message}</p>
                    <button onclick="App.navigate('dashboard')" class="btn btn-primary mt-5">Go to Dashboard</button>
                </div>
            `;
        }

        lucide.createIcons();
        content.classList.add('page-enter');
        setTimeout(() => content.classList.remove('page-enter'), 300);

        // Destroy logs auto-refresh when leaving the page
        if (page !== 'logs') LogsPage.destroy();
    },

    // ─── Sidebar (Mobile) ────────────────────────────────────
    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        document.getElementById('sidebar').classList.toggle('sidebar-mobile-open', this.sidebarOpen);
        document.getElementById('sidebar-overlay').classList.toggle('hidden', !this.sidebarOpen);
    },

    closeSidebar() {
        this.sidebarOpen = false;
        document.getElementById('sidebar').classList.remove('sidebar-mobile-open');
        document.getElementById('sidebar-overlay').classList.add('hidden');
    },

    // ─── Theme ───────────────────────────────────────────────
    toggleTheme() {
        this.darkMode = !this.darkMode;
        document.documentElement.classList.toggle('dark', this.darkMode);
        localStorage.setItem('ph-lending-theme', this.darkMode ? 'dark' : 'light');
        this.updateThemeUI();
        SoundEngine.toggle();
    },

    applyColorTheme(name) {
        this.currentTheme = name;
        if (name === 'blue') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', name);
        }
        localStorage.setItem('ph-lending-color', name);
        document.querySelectorAll('.theme-swatch').forEach(s => {
            s.classList.toggle('active', s.dataset.theme === name);
        });
    },

    updateThemeUI() {
        const icon = document.getElementById('theme-icon');
        const label = document.getElementById('theme-label');
        if (!icon || !label) return;
        if (this.darkMode) {
            icon.setAttribute('data-lucide', 'moon');
            label.textContent = 'Dark Mode';
        } else {
            icon.setAttribute('data-lucide', 'sun');
            label.textContent = 'Light Mode';
        }
        lucide.createIcons();
    },

    // ─── Quick Sound Toggle (header icon) ────────────────────
    quickToggleSound() {
        SoundEngine.setEnabled(!SoundEngine.enabled);
        if (SoundEngine.enabled) SoundEngine.success();
        UI.toast(SoundEngine.enabled ? 'Sounds on.' : 'Sounds off.', 'info');
        // Update settings toggle if visible
        const toggle = document.getElementById('sounds-toggle');
        if (toggle) toggle.checked = SoundEngine.enabled;
    },

    // ─── Online Status ───────────────────────────────────────
    async checkOnlineStatus() {
        try {
            const online = await pywebview.api.is_online();
            const banner = document.getElementById('offline-banner');
            const status = document.getElementById('online-status');
            if (online) {
                banner.classList.add('hidden');
                status.innerHTML = `<div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:var(--apple-green)"></div><span class="hidden sm:inline">Online</span>`;
                status.style.cssText = 'background:rgba(52,199,89,0.12); color:#1A8F3A;';
            } else {
                banner.classList.remove('hidden');
                status.innerHTML = `<div class="w-1.5 h-1.5 rounded-full" style="background:var(--apple-orange)"></div><span class="hidden sm:inline">Offline</span>`;
                status.style.cssText = 'background:rgba(255,149,0,0.12); color:#B86700;';
            }
        } catch (e) { }
    },

    // ─── Quick Actions ───────────────────────────────────────
    showQuickActions() {
        UI.showModal('Quick Actions', `
            <div class="grid grid-cols-2 gap-3">
                <button onclick="UI.closeModal(); ClientsPage.showCreateForm();" class="glass-card p-4 text-left cursor-pointer">
                    <i data-lucide="user-plus" class="w-6 h-6 mb-2" style="color:var(--accent)"></i>
                    <p class="font-semibold text-sm" style="color:var(--text-primary)">New Client</p>
                    <p class="text-xs mt-0.5" style="color:var(--text-secondary)">Add a borrower</p>
                </button>
                <button onclick="UI.closeModal(); LoansPage.showCreateForm();" class="glass-card p-4 text-left cursor-pointer">
                    <i data-lucide="banknote" class="w-6 h-6 mb-2" style="color:var(--apple-green)"></i>
                    <p class="font-semibold text-sm" style="color:var(--text-primary)">New Loan</p>
                    <p class="text-xs mt-0.5" style="color:var(--text-secondary)">Create a loan</p>
                </button>
                <button onclick="UI.closeModal(); LoansPage.statusFilter='active'; App.navigate('loans');" class="glass-card p-4 text-left cursor-pointer">
                    <i data-lucide="receipt" class="w-6 h-6 mb-2" style="color:var(--apple-purple)"></i>
                    <p class="font-semibold text-sm" style="color:var(--text-primary)">Record Payment</p>
                    <p class="text-xs mt-0.5" style="color:var(--text-secondary)">Select active loan →</p>
                </button>
                <button onclick="UI.closeModal(); App.navigate('calendar');" class="glass-card p-4 text-left cursor-pointer">
                    <i data-lucide="calendar-check" class="w-6 h-6 mb-2" style="color:var(--apple-orange)"></i>
                    <p class="font-semibold text-sm" style="color:var(--text-primary)">Collections</p>
                    <p class="text-xs mt-0.5" style="color:var(--text-secondary)">View due today</p>
                </button>
            </div>
        `, { width: 'max-w-md' });
    },

    // ─── Quit ────────────────────────────────────────────────
    quitApp() {
        UI.showModal(`Quit ${this.appName}?`, `
            <div class="text-center space-y-4 py-2">
                <div class="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center"
                     style="background:rgba(255,59,48,0.10)">
                    <i data-lucide="power" class="w-8 h-8" style="color:var(--apple-red)"></i>
                </div>
                <p class="text-sm" style="color:var(--text-secondary)">A backup will be created automatically before closing.</p>
                <div class="flex gap-3 justify-center pt-1">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="App._doQuit()" class="btn btn-danger">
                        <i data-lucide="power" class="w-4 h-4"></i> Quit & Save
                    </button>
                </div>
            </div>
        `, { width: 'max-w-sm' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async _doQuit() {
        UI.closeModal();
        UI.toast('Saving backup...', 'info');
        try { await pywebview.api.quit_app(true); } catch (e) { }
    },

    // ─── AutoSave Indicator ──────────────────────────────────
    _autoSaveTimer: null,
    showAutoSave(state) {
        const el = document.getElementById('autosave-indicator');
        const dot = document.getElementById('autosave-dot');
        const text = document.getElementById('autosave-text');
        if (!el) return;
        clearTimeout(this._autoSaveTimer);
        el.classList.remove('hidden'); el.classList.add('flex');
        if (state === 'saving') {
            el.style.cssText = 'display:flex; background:rgba(0,122,255,0.10); color:var(--accent);';
            dot.style.background = 'var(--accent)';
            dot.classList.add('animate-pulse');
            text.textContent = 'Saving…';
        } else if (state === 'saved') {
            el.style.cssText = 'display:flex; background:rgba(52,199,89,0.10); color:#1A8F3A;';
            dot.style.background = 'var(--apple-green)';
            dot.classList.remove('animate-pulse');
            text.textContent = 'Saved ✓';
            this._autoSaveTimer = setTimeout(() => { el.classList.add('hidden'); el.classList.remove('flex'); }, 2000);
        } else if (state === 'error') {
            el.style.cssText = 'display:flex; background:rgba(255,59,48,0.10); color:var(--apple-red);';
            dot.style.background = 'var(--apple-red)';
            text.textContent = 'Save failed!';
            this._autoSaveTimer = setTimeout(() => { el.classList.add('hidden'); el.classList.remove('flex'); }, 4000);
        }
    },

    // ─── Calculator ──────────────────────────────────────────
    toggleCalculator() {
        const calc = document.getElementById('calculator-widget');
        const hiding = !calc.classList.contains('hidden');
        calc.classList.toggle('hidden');
        lucide.createIcons();
        hiding ? SoundEngine.modalClose() : SoundEngine.modalOpen();
    },

    calcInput(char) {
        if (this.calcLastResult && !'+-*/'.includes(char)) {
            this.calcExpression = '';
        }
        this.calcLastResult = false;
        this.calcExpression += char;
        this._calcUpdateDisplay();
        SoundEngine.click();
    },

    _calcUpdateDisplay() {
        const disp = document.getElementById('calc-display');
        const acBtn = document.querySelector('.calc-btn-light:first-child');
        if (!disp) return;
        const val = this.calcExpression || '0';
        disp.value = val;
        // Adaptive font size based on length
        const len = val.replace('-', '').length;
        disp.style.fontSize = len <= 8 ? '48px' : len <= 10 ? '38px' : len <= 13 ? '30px' : '24px';
        // AC vs C label
        if (acBtn) acBtn.textContent = this.calcExpression ? 'C' : 'AC';
    },

    calcAction(action) {
        switch (action) {
            case 'clear':
                this.calcExpression = '';
                this.calcLastResult = false;
                this._calcUpdateDisplay();
                SoundEngine.click();
                break;
            case 'negate':
                if (this.calcExpression && this.calcExpression !== '0') {
                    this.calcExpression = this.calcExpression.startsWith('-')
                        ? this.calcExpression.slice(1)
                        : '-' + this.calcExpression;
                    this._calcUpdateDisplay();
                    SoundEngine.click();
                }
                break;
            case 'equals':
                try {
                    const result = Function('"use strict"; return (' + this.calcExpression + ')')();
                    this.calcExpression = String(parseFloat(result.toFixed(10)));
                    this.calcLastResult = true;
                    this._calcUpdateDisplay();
                    SoundEngine.save();
                } catch (e) {
                    const disp = document.getElementById('calc-display');
                    if (disp) { disp.value = 'Error'; disp.style.fontSize = '32px'; }
                    this.calcExpression = '';
                    this.calcLastResult = false;
                    SoundEngine.error();
                }
                break;
        }
    },

    startDragCalc(e) {
        if (!e.target.closest('#calc-drag-handle')) return;
        const calc = document.getElementById('calculator-widget');
        const rect = calc.getBoundingClientRect();
        const ox = e.clientX - rect.left, oy = e.clientY - rect.top;
        const move = ev => {
            calc.style.left = (ev.clientX - ox) + 'px';
            calc.style.top = (ev.clientY - oy) + 'px';
            calc.style.right = 'auto';
            calc.style.bottom = 'auto';
        };
        const up = () => {
            document.removeEventListener('mousemove', move);
            document.removeEventListener('mouseup', up);
        };
        document.addEventListener('mousemove', move);
        document.addEventListener('mouseup', up);
    },

    // ─── API Helper ──────────────────────────────────────────
    async api(method, ...args) {
        try {
            return await pywebview.api[method](...args);
        } catch (err) {
            console.error(`API error (${method}):`, err);
            UI.toast(`API Error: ${err.message || 'Unknown error'}`, 'error');
            throw err;
        }
    },

    // ─── Print Button Context ─────────────────────────────────
    _updatePrintBtn(page) {
        const btn = document.getElementById('print-btn');
        if (!btn) return;
        const tips = {
            loan_detail: 'Print — Amortization or Contract',
            client_detail: 'Print — Client Documents',
            dashboard: 'Print Dashboard',
            clients: 'Print Client List',
            loans: 'Print Loans List',
            payments: 'Print Payments',
            calendar: 'Print Calendar',
            alerts: 'Print Alerts',
        };
        btn.title = tips[page] || 'Print this page';
    }
};

// ─── Boot ────────────────────────────────────────────────────
window.addEventListener('pywebviewready', () => App.init());

// ─── AutoSave Utility ────────────────────────────────────────
const AutoSave = {
    _timers: new Map(),

    attach(container, saveFn, debounceMs = 800) {
        if (!container) return;
        container.querySelectorAll('input, select, textarea').forEach(el => {
            const key = Symbol();
            const handler = () => {
                clearTimeout(this._timers.get(key));
                App.showAutoSave('saving');
                this._timers.set(key, setTimeout(async () => {
                    try { await saveFn(); App.showAutoSave('saved'); }
                    catch { App.showAutoSave('error'); }
                }, debounceMs));
            };
            el.addEventListener('input', handler);
            el.addEventListener('change', handler);
        });
    },

    detach() { this._timers.clear(); }
};

// ─── Global Interaction Hooks ────────────────────────────────

// Ripple position tracker
document.addEventListener('mousedown', e => {
    const btn = e.target.closest('.btn');
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    btn.style.setProperty('--rx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%');
    btn.style.setProperty('--ry', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%');
}, true);

// Global click sound (buttons, cards, sidebar — not submits)
document.addEventListener('click', e => {
    if (!SoundEngine.enabled) return;
    const btn = e.target.closest('button:not([type=submit]), .btn:not([type=submit]), .sidebar-link');
    if (!btn) return;
    if (btn.classList.contains('sidebar-link')) return; // navigation handled
    SoundEngine.click();
}, true);

// Form submit sound
document.addEventListener('submit', () => {
    SoundEngine.save();
}, true);

// ─── Global JS Error → Backend Logger ──────────────────────────
window.addEventListener('error', (event) => {
    try {
        const msg = event.message || 'Unknown JS error';
        const src = `${event.filename || '?'}:${event.lineno || 0}`;
        const stack = event.error ? (event.error.stack || '') : '';
        if (window.pywebview && window.pywebview.api) {
            pywebview.api.log_frontend_error(src, msg, stack);
        }
    } catch (e) { /* silent */ }
});

window.addEventListener('unhandledrejection', (event) => {
    try {
        const reason = event.reason;
        const msg = reason instanceof Error ? reason.message : String(reason);
        const stack = reason instanceof Error ? (reason.stack || '') : '';
        if (window.pywebview && window.pywebview.api) {
            pywebview.api.log_frontend_error('Promise', msg, stack);
        }
    } catch (e) { /* silent */ }
});
