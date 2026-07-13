/**
 * PH-Lending Pro — Dashboard Page
 */
const DashboardPage = {
    async render() {
        const content = document.getElementById('page-content');

        const [stats, collections, recentPayments, overdueAlerts] = await Promise.all([
            App.api('get_dashboard_stats'),
            App.api('get_today_collections'),
            App.api('get_recent_payments', 5),
            App.api('get_overdue_alerts'),
        ]);

        const criticalCount = overdueAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length;

        content.innerHTML = `
            <!-- Stats Grid -->
            <div class="dashboard-stats grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 stagger">
                ${UI.statCard('banknote', 'Active Capital', UI.formatCurrency(stats.active_capital), 'blue', `${stats.active_loans} active loans`)}
                ${UI.statCard('trending-up', 'Interest Collected', UI.formatCurrency(stats.interest_collected), 'green', `from ${UI.formatCurrency(stats.total_collected)} received`)}
                ${UI.statCard('alert-triangle', 'Default Rate', stats.delinquency_rate + '%', 'red', `${stats.defaulted_loans} defaulted loans`)}
                ${UI.statCard('users', 'Total Clients', stats.client_count, 'purple', `${stats.active_loans} active borrowers`)}
            </div>

            ${overdueAlerts.length > 0 ? `
            <!-- Overdue Alert Banner -->
            <div class="glass-card p-4 mb-5 cursor-pointer" onclick="App.navigate('alerts')"
                 style="border: 1px solid rgba(255,59,48,0.30); background: rgba(255,59,48,0.06);">
                <div class="flex items-center justify-between gap-3 flex-wrap">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0"
                             style="background: rgba(255,59,48,0.12);">
                            <i data-lucide="bell-ring" class="w-5 h-5 animate-bounce" style="color:#FF3B30"></i>
                        </div>
                        <div>
                            <p class="font-bold text-sm" style="color:#FF3B30">
                                ${overdueAlerts.length} client${overdueAlerts.length > 1 ? 's' : ''} with overdue payment${overdueAlerts.length > 1 ? 's' : ''}
                                ${criticalCount > 0 ? `— <span style="color:#FF2D55">${criticalCount} critical${criticalCount > 1 ? '' : ''}</span>` : ''}
                            </p>
                            <p class="text-xs" style="color:var(--text-tertiary)">
                                Total due: ${UI.formatCurrency(overdueAlerts.reduce((s, a) => s + a.total_overdue_amount, 0))}
                                • Click to view alerts and send SMS
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs px-3 py-1 rounded-full font-semibold"
                              style="background:#FF3B30; color:white;">
                            View Alerts →
                        </span>
                    </div>
                </div>
                ${criticalCount > 0 ? `
                <div class="mt-3 pt-3 flex flex-wrap gap-2" style="border-top: 0.5px solid rgba(255,59,48,0.15);">
                    ${overdueAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').slice(0, 4).map(a => `
                        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs"
                             style="background: rgba(255,59,48,0.08); border: 1px solid rgba(255,59,48,0.15);">
                            <div class="w-1.5 h-1.5 rounded-full" style="background:#FF3B30"></div>
                            <span style="color:var(--text-primary)">${a.first_name} ${a.last_name}</span>
                            <span style="color:#FF3B30; font-weight:600">${a.days_overdue}d</span>
                        </div>
                    `).join('')}
                    ${overdueAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length > 4 ?
                        `<span class="text-xs px-2 py-1" style="color:var(--text-tertiary)">+${overdueAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length - 4} more…</span>` : ''}
                </div>` : ''}
            </div>` : ''}

            <div class="dashboard-main-grid grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Today's Collections -->
                <div class="lg:col-span-2 glass-card p-5">
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-xl">
                                <i data-lucide="calendar-check" class="w-5 h-5 text-amber-600 dark:text-amber-400"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-800 dark:text-white">Today's Collections</h3>
                                <p class="text-xs text-gray-400 dark:text-slate-500">${new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</p>
                            </div>
                        </div>
                        <span class="badge badge-pending">${collections.length} due</span>
                    </div>
                    
                    ${collections.length === 0 ? `
                        <div class="text-center py-8">
                            <i data-lucide="check-circle" class="w-10 h-10 text-green-400 mx-auto mb-2"></i>
                            <p class="text-gray-400 dark:text-slate-500">No collections due today</p>
                        </div>
                    ` : `
                        <div class="space-y-2 max-h-80 overflow-y-auto">
                            ${collections.map(c => `
                                <div class="flex items-center justify-between p-3 rounded-xl bg-gray-50/50 dark:bg-slate-800/50 hover:bg-gray-100/50 dark:hover:bg-slate-700/50 transition cursor-pointer"
                                     onclick="App.navigate('loan_detail', {id: ${c.loan_id}})">
                                    <div class="flex items-center gap-3">
                                        <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                                            ${c.first_name[0]}${c.last_name[0]}
                                        </div>
                                        <div>
                                            <p class="font-semibold text-sm text-gray-800 dark:text-white">${c.first_name} ${c.last_name}</p>
                                            <p class="text-xs text-gray-400 dark:text-slate-500">${c.client_id} • Month ${c.month_number}</p>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <p class="font-bold text-sm text-gray-800 dark:text-white">${UI.formatCurrency(c.total_due)}</p>
                                        <p class="text-xs text-gray-400 dark:text-slate-500">${c.contact || 'No contact'}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="mt-3 pt-3 border-t border-gray-100 dark:border-slate-700/50 flex justify-between items-center">
                            <span class="text-sm text-gray-500 dark:text-slate-400">Total Expected</span>
                            <span class="font-bold text-lg text-amber-600 dark:text-amber-400">${UI.formatCurrency(stats.today_amount)}</span>
                        </div>
                    `}
                </div>

                <!-- Recent Payments -->
                <div class="glass-card p-5">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                            <i data-lucide="trending-up" class="w-5 h-5 text-green-600 dark:text-green-400"></i>
                        </div>
                        <h3 class="font-bold text-gray-800 dark:text-white">Recent Payments</h3>
                    </div>
                    
                    ${recentPayments.length === 0 ? `
                        <p class="text-center text-gray-400 dark:text-slate-500 py-8 text-sm">No payments recorded yet</p>
                    ` : `
                        <div class="space-y-3">
                            ${recentPayments.map(p => `
                                <div class="flex items-center justify-between">
                                    <div>
                                        <p class="text-sm font-medium text-gray-700 dark:text-slate-300">${p.first_name} ${p.last_name}</p>
                                        <p class="text-xs text-gray-400 dark:text-slate-500">${UI.formatDate(p.payment_date)} • ${(p.payment_method || 'cash').replace('_', ' ').toUpperCase()}</p>
                                    </div>
                                    <span class="text-sm font-bold text-green-600 dark:text-green-400">+${UI.formatCurrency(p.amount)}</span>
                                </div>
                            `).join('')}
                        </div>
                    `}
                </div>
            </div>

            <!-- Quick Summary Bar -->
            <div class="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4 stagger">
                <div class="glass-card p-4 flex items-center gap-4 cursor-pointer" onclick="App.navigate('calendar')">
                    <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                        <i data-lucide="calendar" class="w-5 h-5 text-blue-600 dark:text-blue-400"></i>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-800 dark:text-white">Collection Calendar</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">View upcoming collections →</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-4 cursor-pointer" onclick="App.navigate('alerts')"
                     style="${overdueAlerts.length > 0 ? 'border: 1px solid rgba(255,59,48,0.25);' : ''}">
                    <div class="p-2 rounded-xl" style="background: ${overdueAlerts.length > 0 ? 'rgba(255,59,48,0.10)' : 'rgba(255,59,48,0.06)'}">
                        <i data-lucide="bell-ring" class="w-5 h-5" style="color:#FF3B30"></i>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-800 dark:text-white">
                            Alerts
                            ${overdueAlerts.length > 0 ? `<span class="ml-1 text-xs font-bold px-1.5 py-0.5 rounded-full text-white" style="background:#FF3B30">${overdueAlerts.length}</span>` : ''}
                        </p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Overdue & SMS →</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-4 cursor-pointer" onclick="App.navigate('settings')">
                    <div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
                        <i data-lucide="download" class="w-5 h-5 text-purple-600 dark:text-purple-400"></i>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-800 dark:text-white">Export Data</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Excel, backup, sync →</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-4 cursor-pointer" onclick="App.navigate('commissions')">
                    <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-xl">
                        <i data-lucide="gift" class="w-5 h-5 text-amber-600 dark:text-amber-400"></i>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-800 dark:text-white">Referral Commissions</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Track referrals →</p>
                    </div>
                </div>
            </div>
        `;
    }
};
