/**
 * PH-Lending Pro — System Logs Page
 * Display persistent logs for debugging. All errors, warnings and events
 * are shown here with date/time, and survive application restarts.
 */

window.LogsPage = {
    _refreshInterval: null,
    _currentFilter: 'ALL',
    _autoRefresh: false,

    render() {
        return `
        <div class="logs-page">
            <!-- Header -->
            <div class="page-header" style="margin-bottom: 1.5rem;">
                <div>
                    <h1 class="page-title" style="display:flex;align-items:center;gap:0.5rem;">
                        <span style="font-size:1.4rem;">🪵</span> Journal Système
                    </h1>
                    <p class="page-subtitle">All errors and events are saved here — even after restarting</p>
                </div>
                <div style="display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
                    <label style="display:flex;align-items:center;gap:0.5rem;font-size:0.85rem;color:var(--text-secondary);cursor:pointer;">
                        <input type="checkbox" id="log-auto-refresh" style="cursor:pointer;">
                        Auto-actualiser (10s)
                    </label>
                    <button class="btn btn-secondary" id="log-open-folder-btn" onclick="LogsPage.openLogFolder()">
                        📂 Open Folder
                    </button>
                    <button class="btn btn-secondary" id="log-refresh-btn" onclick="LogsPage.loadLogs()">
                        🔄 Actualiser
                    </button>
                    <button class="btn btn-danger" id="log-clear-btn" onclick="LogsPage.clearLogs()">
                        🗑️ Effacer les logs
                    </button>
                </div>
            </div>

            <!-- Stats cards -->
            <div class="logs-stats-row" id="logs-stats-row">
                <div class="log-stat-card">
                    <div class="log-stat-icon">📄</div>
                    <div>
                        <div class="log-stat-value" id="stat-size">—</div>
                        <div class="log-stat-label">Taille fichier</div>
                    </div>
                </div>
                <div class="log-stat-card log-stat-errors">
                    <div class="log-stat-icon">🔴</div>
                    <div>
                        <div class="log-stat-value" id="stat-errors">—</div>
                        <div class="log-stat-label">Total Errors</div>
                    </div>
                </div>
                <div class="log-stat-card log-stat-warnings">
                    <div class="log-stat-icon">🟡</div>
                    <div>
                        <div class="log-stat-value" id="stat-warnings">—</div>
                        <div class="log-stat-label">Avertissements</div>
                    </div>
                </div>
                <div class="log-stat-card">
                    <div class="log-stat-icon">📍</div>
                    <div>
                        <div class="log-stat-value" id="stat-lines">—</div>
                        <div class="log-stat-label">Lignes totales</div>
                    </div>
                </div>
                <div class="log-stat-card" style="flex:1.5;">
                    <div class="log-stat-icon">🗂️</div>
                    <div style="overflow:hidden;">
                        <div class="log-stat-value" id="stat-path" style="font-size:0.7rem;word-break:break-all;opacity:0.7;">—</div>
                        <div class="log-stat-label">Chemin du fichier</div>
                    </div>
                </div>
            </div>

            <!-- Filters -->
            <div class="logs-filter-bar">
                <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                    <button class="log-filter-btn active" data-level="ALL" onclick="LogsPage.setFilter('ALL', this)">Tous</button>
                    <button class="log-filter-btn" data-level="ERROR" onclick="LogsPage.setFilter('ERROR', this)">
                        <span class="log-badge log-badge-error">ERREUR</span>
                    </button>
                    <button class="log-filter-btn" data-level="CRITICAL" onclick="LogsPage.setFilter('CRITICAL', this)">
                        <span class="log-badge log-badge-critical">CRITIQUE</span>
                    </button>
                    <button class="log-filter-btn" data-level="WARNING" onclick="LogsPage.setFilter('WARNING', this)">
                        <span class="log-badge log-badge-warning">AVERT.</span>
                    </button>
                    <button class="log-filter-btn" data-level="INFO" onclick="LogsPage.setFilter('INFO', this)">
                        <span class="log-badge log-badge-info">INFO</span>
                    </button>
                    <button class="log-filter-btn" data-level="DEBUG" onclick="LogsPage.setFilter('DEBUG', this)">
                        <span class="log-badge log-badge-debug">DEBUG</span>
                    </button>
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <label style="font-size:0.8rem;color:var(--text-secondary);">Afficher:</label>
                    <select id="log-limit-select" style="background:var(--bg-tertiary);color:var(--text-primary);border:1px solid var(--border-color);border-radius:6px;padding:4px 8px;font-size:0.82rem;" onchange="LogsPage.loadLogs()">
                        <option value="50">50 derniers</option>
                        <option value="200" selected>200 derniers</option>
                        <option value="500">500 derniers</option>
                        <option value="1000">1000 derniers</option>
                    </select>
                </div>
            </div>

            <!-- Log entries -->
            <div class="log-entries-container" id="log-entries-container">
                <div class="loading-state" id="logs-loading">
                    <div class="spinner"></div>
                    <p>Chargement des logs...</p>
                </div>
                <div id="log-entries-list" style="display:none;"></div>
                <div class="empty-state" id="logs-empty" style="display:none;">
                    <div style="font-size:3rem;margin-bottom:1rem;">📭</div>
                    <h3>No logs found</h3>
                    <p>No entries match the selected filter.</p>
                </div>
            </div>
        </div>
        `;
    },

    async init() {
        await this.loadStats();
        await this.loadLogs();

        // Auto-refresh toggle
        document.getElementById('log-auto-refresh').addEventListener('change', (e) => {
            this._autoRefresh = e.target.checked;
            if (this._autoRefresh) {
                this._refreshInterval = setInterval(() => this.loadLogs(), 10000);
            } else {
                clearInterval(this._refreshInterval);
            }
        });
    },

    async loadStats() {
        try {
            const stats = await pywebview.api.get_log_stats();
            if (stats && stats.exists) {
                document.getElementById('stat-size').textContent = stats.size_kb + ' KB';
                document.getElementById('stat-errors').textContent = stats.errors.toLocaleString();
                document.getElementById('stat-warnings').textContent = stats.warnings.toLocaleString();
                document.getElementById('stat-lines').textContent = stats.total_lines.toLocaleString();
                document.getElementById('stat-path').textContent = stats.path || '—';
            } else {
                document.getElementById('stat-size').textContent = '0 KB';
                document.getElementById('stat-errors').textContent = '0';
                document.getElementById('stat-warnings').textContent = '0';
                document.getElementById('stat-lines').textContent = '0';
                document.getElementById('stat-path').textContent = '(aucun log encore)';
            }
        } catch (e) {
            console.error('Could not load log stats', e);
        }
    },

    async loadLogs() {
        const limit = parseInt(document.getElementById('log-limit-select')?.value || 200);
        const loading = document.getElementById('logs-loading');
        const list = document.getElementById('log-entries-list');
        const empty = document.getElementById('logs-empty');

        if (loading) loading.style.display = 'flex';
        if (list) list.style.display = 'none';
        if (empty) empty.style.display = 'none';

        try {
            const result = await pywebview.api.get_logs(limit, this._currentFilter);
            const entries = result?.entries || [];

            if (loading) loading.style.display = 'none';

            if (entries.length === 0) {
                if (empty) empty.style.display = 'flex';
                return;
            }

            if (list) {
                list.style.display = 'block';
                list.innerHTML = entries.map(e => this.renderEntry(e)).join('');
            }

            // Refresh stats too
            await this.loadStats();
        } catch (e) {
            if (loading) loading.style.display = 'none';
            if (list) {
                list.style.display = 'block';
                list.innerHTML = `<div class="log-entry log-entry-error">
                    <span class="log-badge log-badge-error">ERREUR</span>
                    <span>Impossible de charger les logs: ${e.message || e}</span>
                </div>`;
            }
        }
    },

    renderEntry(entry) {
        const level = (entry.level || 'INFO').trim();
        const levelClass = {
            'ERROR': 'error',
            'CRITICAL': 'critical',
            'WARNING': 'warning',
            'INFO': 'info',
            'DEBUG': 'debug'
        }[level] || 'info';

        const levelLabel = {
            'ERROR': 'ERREUR',
            'CRITICAL': 'CRITIQUE',
            'WARNING': 'AVERT.',
            'INFO': 'INFO',
            'DEBUG': 'DEBUG'
        }[level] || level;

        // Multi-line messages (e.g. tracebacks)
        const lines = (entry.message || '').split('\n');
        const firstLine = lines[0];
        const restLines = lines.slice(1).join('\n').trim();

        const hasTraceback = restLines.length > 0;
        const id = 'log_' + Math.random().toString(36).substr(2, 9);

        return `
        <div class="log-entry log-entry-${levelClass}">
            <div class="log-entry-header">
                <span class="log-badge log-badge-${levelClass}">${levelLabel}</span>
                <span class="log-timestamp">🕐 ${entry.timestamp || ''}</span>
                ${entry.source ? `<span class="log-source">${entry.source}</span>` : ''}
                <span class="log-message-text">${this.escapeHtml(firstLine)}</span>
                ${hasTraceback ? `<button class="log-expand-btn" onclick="LogsPage.toggleTraceback('${id}')">▼ Détails</button>` : ''}
            </div>
            ${hasTraceback ? `<pre class="log-traceback" id="${id}" style="display:none;">${this.escapeHtml(restLines)}</pre>` : ''}
        </div>`;
    },

    toggleTraceback(id) {
        const el = document.getElementById(id);
        if (!el) return;
        const btn = el.previousElementSibling?.querySelector('.log-expand-btn');
        if (el.style.display === 'none') {
            el.style.display = 'block';
            if (btn) btn.textContent = '▲ Masquer';
        } else {
            el.style.display = 'none';
            if (btn) btn.textContent = '▼ Détails';
        }
    },

    setFilter(level, btn) {
        this._currentFilter = level;
        document.querySelectorAll('.log-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.loadLogs();
    },

    async clearLogs() {
        if (!confirm('Effacer tous les logs actuels ? (Les anciens fichiers de rotation sont conservés)')) return;
        try {
            const r = await pywebview.api.clear_logs();
            if (r?.success) {
                showToast('Logs effacés avec succès.', 'success');
                await this.loadLogs();
            } else {
                showToast('Impossible d\'effacer les logs.', 'error');
            }
        } catch (e) {
            showToast('Error: ' + e, 'error');
        }
    },

    async openLogFolder() {
        try {
            const stats = await pywebview.api.get_log_stats();
            if (stats?.log_dir) {
                await pywebview.api.open_file(stats.log_dir);
            }
        } catch (e) {
            showToast('Cannot open folder.', 'error');
        }
    },

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    destroy() {
        if (this._refreshInterval) {
            clearInterval(this._refreshInterval);
            this._refreshInterval = null;
        }
    }
};
