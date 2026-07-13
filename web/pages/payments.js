/**
 * PH-Lending Pro — All Payments Page (Enhanced)
 * Shows payment history with: loan amount, paid total, remaining balance, months remaining.
 */
const PaymentsPage = {
    currentPage: 1,
    filterMonth: '',
    filterClient: '',

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="space-y-4">
                <!-- Controls -->
                <div class="flex flex-wrap gap-3 items-center justify-between">
                    <div class="flex flex-wrap gap-2">
                        <div class="relative">
                            <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                            <input type="text" id="payments-search" class="input pl-10" placeholder="Search client..."
                                   value="${this.filterClient}" oninput="PaymentsPage.onSearch(this.value)">
                        </div>
                        <div>
                            <input type="month" id="payments-month" class="input" value="${this.filterMonth}"
                                   onchange="PaymentsPage.onMonthFilter(this.value)" title="Filter by month">
                        </div>
                        ${this.filterMonth || this.filterClient ? `
                            <button onclick="PaymentsPage.clearFilters()" class="btn btn-ghost btn-sm text-red-500">
                                <i data-lucide="x" class="w-4 h-4"></i> Clear
                            </button>
                        ` : ''}
                    </div>
                    <div id="payments-summary-badge"></div>
                </div>

                <!-- Table container -->
                <div id="payments-table">${UI.skeleton(8)}</div>

                <!-- Monthly earnings summary -->
                <div id="monthly-earnings-panel" class="hidden"></div>
            </div>
        `;
        lucide.createIcons();
        await Promise.all([this.loadPayments(), this.loadMonthlyEarnings()]);
    },

    async loadPayments() {
        const payments = await App.api('get_all_payments_detailed', 500);
        const container = document.getElementById('payments-table');
        const badge = document.getElementById('payments-summary-badge');

        // Apply filters
        let filtered = payments;
        if (this.filterClient) {
            const q = this.filterClient.toLowerCase();
            filtered = filtered.filter(p =>
                p.first_name.toLowerCase().includes(q) ||
                p.last_name.toLowerCase().includes(q) ||
                String(p.client_id).toLowerCase().includes(q) ||
                String(p.loan_id).includes(q)
            );
        }
        if (this.filterMonth) {
            filtered = filtered.filter(p => p.payment_date && p.payment_date.startsWith(this.filterMonth));
        }

        // Summary badge
        const totalFiltered = filtered.reduce((s, p) => s + p.amount, 0);
        if (badge) {
            badge.innerHTML = `
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/30">
                    <i data-lucide="receipt" class="w-4 h-4 text-blue-500"></i>
                    <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">${filtered.length} payments</span>
                    <span class="text-sm font-bold text-blue-600 dark:text-blue-400">${UI.formatCurrency(totalFiltered)}</span>
                </div>
            `;
            lucide.createIcons({ nodes: [badge] });
        }

        if (filtered.length === 0) {
            container.innerHTML = UI.emptyState('receipt', 'No Payments Found',
                this.filterClient || this.filterMonth ? 'No payments match your filters.' : 'No payments have been recorded yet.'
            );
            lucide.createIcons();
            return;
        }

        container.innerHTML = `
            <div class="glass-card overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="data-table min-w-[900px]">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Client</th>
                                <th>Loan #</th>
                                <th class="text-right">Payment</th>
                                <th class="text-right">Total Paid</th>
                                <th class="text-right">Remaining</th>
                                <th class="text-center">Progress</th>
                                <th class="text-center">Months Left</th>
                                <th>Method</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${filtered.map(p => {
            const paidPct = p.total_due > 0
                ? Math.min(100, Math.round((p.total_paid_on_loan / p.total_due) * 100))
                : 0;
            const isFullyPaid = p.loan_status === 'paid';
            const barColor = isFullyPaid ? 'bg-green-500' :
                p.loan_status === 'defaulted' ? 'bg-red-400' :
                    paidPct >= 75 ? 'bg-blue-500' : 'bg-blue-400';
            return `
                                <tr>
                                    <td>
                                        <div>
                                            <p class="text-sm font-semibold text-gray-800 dark:text-white">${UI.formatDateShort(p.payment_date)}</p>
                                            <p class="text-xs text-gray-400 dark:text-slate-500">${p.payment_date ? new Date(p.payment_date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short' }) : ''}</p>
                                        </div>
                                    </td>
                                    <td>
                                        <div class="flex items-center gap-2">
                                            <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
                                                ${p.first_name[0]}${p.last_name[0]}
                                            </div>
                                            <div class="min-w-0">
                                                <p class="text-sm font-semibold text-gray-800 dark:text-white truncate max-w-[120px]">${p.first_name} ${p.last_name}</p>
                                                <p class="text-xs text-gray-400 dark:text-slate-500 font-mono">${p.client_id}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div>
                                            <button onclick="App.navigate('loan_detail', {id: ${p.loan_id}})"
                                                    class="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                                                #${p.loan_id}
                                            </button>
                                            <p class="text-[10px] text-gray-400 dark:text-slate-500">${UI.formatCurrency(p.principal)} • ${p.term_months}mo</p>
                                        </div>
                                    </td>
                                    <td class="text-right">
                                        <span class="font-bold text-green-600 dark:text-green-400">${UI.formatCurrency(p.amount)}</span>
                                        ${p.notes ? `<p class="text-[10px] text-gray-400 dark:text-slate-500 italic truncate max-w-[80px]">${p.notes}</p>` : ''}
                                    </td>
                                    <td class="text-right">
                                        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">${UI.formatCurrency(p.total_paid_on_loan)}</span>
                                        <p class="text-[10px] text-gray-400 dark:text-slate-500">of ${UI.formatCurrency(p.total_due)}</p>
                                    </td>
                                    <td class="text-right">
                                        ${isFullyPaid ? `
                                            <span class="text-xs font-bold text-green-600 dark:text-green-400">✓ PAID</span>
                                        ` : `
                                            <span class="text-sm font-semibold text-orange-600 dark:text-orange-400">${UI.formatCurrency(p.remaining_balance)}</span>
                                        `}
                                    </td>
                                    <td>
                                        <div class="flex items-center gap-1.5 justify-center">
                                            <div class="w-16 h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                                <div class="h-1.5 rounded-full ${barColor} transition-all" style="width:${paidPct}%"></div>
                                            </div>
                                            <span class="text-[10px] text-gray-400">${paidPct}%</span>
                                        </div>
                                    </td>
                                    <td class="text-center">
                                        ${isFullyPaid ? `
                                            <span class="text-xs text-green-600 dark:text-green-400 font-bold">Done</span>
                                        ` : `
                                            <div>
                                                <span class="text-sm font-bold ${p.months_remaining <= 2 ? 'text-orange-500' : 'text-gray-700 dark:text-gray-200'}">${p.months_remaining}</span>
                                                <p class="text-[10px] text-gray-400 dark:text-slate-500">months</p>
                                            </div>
                                        `}
                                    </td>
                                    <td>
                                        ${this._methodBadge(p.payment_method)}
                                    </td>
                                    <td>
                                        <div class="flex items-center gap-1">
                                            <button onclick="PaymentsPage.generateReceipt(${p.payment_id})"
                                                    class="btn btn-sm btn-ghost" title="Generate Receipt">
                                                <i data-lucide="file-text" class="w-4 h-4"></i>
                                            </button>
                                            <button onclick="PaymentsPage.showVoidPaymentModal(${p.payment_id}, ${Number(p.amount || 0)})"
                                                    class="btn btn-sm btn-ghost text-red-500" title="Void payment">
                                                <i data-lucide="undo-2" class="w-4 h-4"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `}).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        lucide.createIcons();
    },

    async loadMonthlyEarnings() {
        const earnings = await App.api('get_monthly_earnings');
        const panel = document.getElementById('monthly-earnings-panel');
        if (!panel || earnings.length === 0) return;

        const maxAmount = Math.max(...earnings.map(m => m.total_collected));

        panel.classList.remove('hidden');
        panel.innerHTML = `
            <div class="glass-card p-5">
                <div class="flex items-center gap-3 mb-5">
                    <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                        <i data-lucide="bar-chart-2" class="w-5 h-5 text-green-600 dark:text-green-400"></i>
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-800 dark:text-white">Total Collected Per Month</h3>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Last 24 months — click on a month to filter</p>
                    </div>
                    <div class="ml-auto text-right">
                        <p class="text-xl font-bold text-green-600 dark:text-green-400">${UI.formatCurrency(earnings.reduce((s, m) => s + m.total_collected, 0))}</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Total all time</p>
                    </div>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    ${earnings.map(m => {
            const monthLabel = new Date(m.month + '-01').toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            const pct = maxAmount > 0 ? Math.round((m.total_collected / maxAmount) * 100) : 0;
            const isFiltered = this.filterMonth === m.month;
            return `
                            <div class="cursor-pointer p-3 rounded-xl border transition
                                        ${isFiltered ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700' : 'border-gray-200/50 dark:border-slate-700/30 hover:border-blue-200 dark:hover:border-blue-800/50 hover:bg-gray-50/50 dark:hover:bg-slate-800/30'}"
                                 onclick="PaymentsPage.onMonthFilter('${m.month}')">
                                <div class="h-10 bg-gray-100 dark:bg-slate-700/50 rounded-lg overflow-hidden flex items-end mb-2">
                                    <div class="w-full rounded-lg transition-all ${isFiltered ? 'bg-blue-500' : 'bg-green-400'}"
                                         style="height:${Math.max(15, pct)}%"></div>
                                </div>
                                <p class="text-xs font-bold text-gray-700 dark:text-gray-200 text-center">${monthLabel}</p>
                                <p class="text-xs text-green-600 dark:text-green-400 font-semibold text-center">${UI.formatCurrency(m.total_collected)}</p>
                                <p class="text-[10px] text-gray-400 dark:text-slate-500 text-center">${m.payment_count} pmts</p>
                            </div>
                        `;
        }).join('')}
                </div>
            </div>
        `;
        lucide.createIcons();
    },

    _methodBadge(method) {
        const badges = {
            cash: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
            gcash: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
            bank_transfer: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
            check: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
        };
        const cls = badges[method] || 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300';
        const label = (method || 'cash').replace('_', ' ');
        return `<span class="px-2 py-0.5 rounded-full text-xs font-medium capitalize ${cls}">${label}</span>`;
    },

    onSearch(val) {
        this.filterClient = val;
        clearTimeout(this._st);
        this._st = setTimeout(() => this.loadPayments(), 300);
    },

    onMonthFilter(val) {
        this.filterMonth = val;
        // Update the input if triggered from the chart
        const monthInput = document.getElementById('payments-month');
        if (monthInput && monthInput.value !== val) monthInput.value = val;
        this.loadPayments();
        this.loadMonthlyEarnings();
    },

    clearFilters() {
        this.filterClient = '';
        this.filterMonth = '';
        const searchInput = document.getElementById('payments-search');
        const monthInput = document.getElementById('payments-month');
        if (searchInput) searchInput.value = '';
        if (monthInput) monthInput.value = '';
        this.loadPayments();
        this.loadMonthlyEarnings();
    },

    async generateReceipt(paymentId) {
        UI.toast('Generating receipt...', 'info');
        try {
            const result = await App.api('generate_receipt', paymentId);
            if (result && result.success) {
                UI.toast('Receipt generated!', 'success');
            } else {
                UI.toast('Error: ' + (result?.error || 'Could not generate receipt'), 'error');
            }
        } catch (e) {
            UI.toast('Error generating receipt', 'error');
        }
    },

    showVoidPaymentModal(paymentId, amount) {
        UI.showModal('Void Payment', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl" style="background:rgba(255,59,48,0.06); border:1px solid rgba(255,59,48,0.2);">
                    <p class="text-sm font-semibold" style="color:var(--apple-red)">This removes ${UI.formatCurrency(amount)} from totals without deleting the original record.</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Reason *</label>
                    <input id="void-payment-reason" class="input" placeholder="Example: duplicate entry" autocomplete="off">
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="PaymentsPage.submitVoidPayment(${paymentId})" class="btn btn-danger">
                        <i data-lucide="undo-2" class="w-4 h-4"></i> Void Payment
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        lucide.createIcons();
        setTimeout(() => document.getElementById('void-payment-reason')?.focus(), 100);
    },

    async submitVoidPayment(paymentId) {
        const reason = document.getElementById('void-payment-reason')?.value?.trim() || '';
        if (reason.length < 3) {
            UI.toast('Reason is required.', 'warning');
            return;
        }
        const result = await App.api('void_payment', paymentId, reason);
        if (result && result.success) {
            UI.closeModal();
            UI.toast('Payment voided.', 'success');
            await App.refreshAlertsBadge();
            await Promise.all([this.loadPayments(), this.loadMonthlyEarnings()]);
        } else {
            UI.toast(result?.error || 'Could not void payment.', 'error');
        }
    }
};
