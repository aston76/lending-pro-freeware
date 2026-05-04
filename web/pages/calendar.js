/**
 * PH-Lending Pro — Collection Calendar Page
 * Enhanced: Day-of-month filter, payment validation, monthly earnings.
 */
const CalendarPage = {
    currentDate: new Date(),
    selectedDay: null,
    dayCollections: [],

    async render() {
        const content = document.getElementById('page-content');
        const today = new Date().toISOString().split('T')[0];
        const todayCollections = await App.api('get_today_collections');
        const monthlyEarnings = await App.api('get_monthly_earnings');

        // Get month range for calendar
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = firstDay.toISOString().split('T')[0];
        const endDate = lastDay.toISOString().split('T')[0];
        const monthCollections = await App.api('get_collections_range', startDate, endDate);

        // Build collection map
        const collectionMap = {};
        monthCollections.forEach(c => {
            collectionMap[c.due_date] = c;
        });

        const monthName = this.currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

        // Monthly earnings stats
        const currentMonthKey = `${year}-${String(month + 1).padStart(2, '0')}`;
        const currentMonthData = monthlyEarnings.find(m => m.month === currentMonthKey);
        const totalThisMonth = currentMonthData ? currentMonthData.total_collected : 0;
        const paymentCountThisMonth = currentMonthData ? currentMonthData.payment_count : 0;

        content.innerHTML = `
            <!-- Top stats row -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                <div class="glass-card p-4 flex items-center gap-3">
                    <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-xl">
                        <i data-lucide="calendar-check" class="w-5 h-5 text-amber-600 dark:text-amber-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Today's Due</p>
                        <p class="font-bold text-gray-800 dark:text-white">${todayCollections.length} clients</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-3">
                    <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                        <i data-lucide="banknote" class="w-5 h-5 text-green-600 dark:text-green-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Today's Amount</p>
                        <p class="font-bold text-green-700 dark:text-green-400">${UI.formatCurrency(todayCollections.reduce((s, c) => s + c.total_due, 0))}</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-3">
                    <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                        <i data-lucide="trending-up" class="w-5 h-5 text-blue-600 dark:text-blue-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Collected This Month</p>
                        <p class="font-bold text-blue-700 dark:text-blue-400">${UI.formatCurrency(totalThisMonth)}</p>
                    </div>
                </div>
                <div class="glass-card p-4 flex items-center gap-3">
                    <div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
                        <i data-lucide="receipt" class="w-5 h-5 text-purple-600 dark:text-purple-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Payments This Month</p>
                        <p class="font-bold text-purple-700 dark:text-purple-400">${paymentCountThisMonth}</p>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- LEFT PANEL -->
                <div class="space-y-4">
                    <!-- Today's Collections -->
                    <div class="glass-card p-5">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-xl">
                                <i data-lucide="calendar-check" class="w-5 h-5 text-amber-600 dark:text-amber-400"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-800 dark:text-white">Today's Collections</h3>
                                <p class="text-xs text-gray-400 dark:text-slate-500">${new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</p>
                            </div>
                        </div>

                        ${todayCollections.length === 0 ? `
                            <div class="text-center py-6">
                                <i data-lucide="check-circle" class="w-10 h-10 text-green-400 mx-auto mb-2"></i>
                                <p class="text-sm text-gray-400 dark:text-slate-500">No collections due today!</p>
                            </div>
                        ` : `
                            <div class="space-y-2 max-h-[40vh] overflow-y-auto">
                                ${todayCollections.map(c => `
                                    <div class="p-3 rounded-xl bg-amber-50/50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/20 cursor-pointer hover:bg-amber-100/50 dark:hover:bg-amber-900/20 transition"
                                         onclick="App.navigate('loan_detail', {id: ${c.loan_id}})">
                                        <div class="flex justify-between items-start mb-1">
                                            <div>
                                                <p class="font-semibold text-sm text-gray-800 dark:text-white">${c.first_name} ${c.last_name}</p>
                                                <p class="text-xs text-gray-400 dark:text-slate-500">${c.client_id} • Loan #${c.loan_id}</p>
                                            </div>
                                            <span class="font-bold text-amber-600 dark:text-amber-400">${UI.formatCurrency(c.total_due)}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            <div class="mt-3 pt-3 border-t border-gray-100 dark:border-slate-700/50 flex justify-between">
                                <span class="text-sm text-gray-500 dark:text-slate-400">Total</span>
                                <span class="font-bold text-amber-600 dark:text-amber-400">
                                    ${UI.formatCurrency(todayCollections.reduce((s, c) => s + c.total_due, 0))}
                                </span>
                            </div>
                        `}
                    </div>

                    <!-- Day-of-Month Collections Filter -->
                    <div class="glass-card p-5">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl">
                                <i data-lucide="filter" class="w-5 h-5 text-indigo-600 dark:text-indigo-400"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-800 dark:text-white">Collections by Day</h3>
                                <p class="text-xs text-gray-400 dark:text-slate-500">Who pays on day X every month?</p>
                            </div>
                        </div>
                        <div class="flex gap-2 mb-4">
                            <div class="flex-1">
                                <label class="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Day of Month (1–31)</label>
                                <input id="day-filter-input" type="number" min="1" max="31" class="input" placeholder="e.g. 15"
                                       value="${this.selectedDay || ''}"
                                       onkeydown="if(event.key==='Enter') CalendarPage.loadDayCollections()">
                            </div>
                            <div class="flex items-end">
                                <button onclick="CalendarPage.loadDayCollections()" class="btn btn-primary">
                                    <i data-lucide="search" class="w-4 h-4"></i> Show
                                </button>
                            </div>
                        </div>
                        <!-- Quick day buttons -->
                        <div class="flex flex-wrap gap-1 mb-3">
                            ${[1, 5, 10, 15, 20, 25, 30].map(d => `
                                <button onclick="CalendarPage.quickDay(${d})"
                                        class="text-xs px-2 py-1 rounded-lg border transition ${this.selectedDay === d ? 'bg-indigo-500 text-white border-indigo-500' : 'border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-400 hover:border-indigo-300 hover:text-indigo-600'}">
                                    ${d}
                                </button>
                            `).join('')}
                        </div>
                        <div id="day-collections-container">
                            ${this.selectedDay ? '<div class="text-center py-4 text-gray-400 dark:text-slate-500 text-sm">Loading...</div>' : '<p class="text-xs text-gray-400 dark:text-slate-500 text-center py-3">Select a day to view collectors</p>'}
                        </div>
                    </div>

                    <!-- Monthly Earnings Summary -->
                    <div class="glass-card p-5">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                                <i data-lucide="bar-chart-2" class="w-5 h-5 text-green-600 dark:text-green-400"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-800 dark:text-white">Monthly Earnings</h3>
                                <p class="text-xs text-gray-400 dark:text-slate-500">Total collected per month</p>
                            </div>
                        </div>
                        ${monthlyEarnings.length === 0 ? `
                            <p class="text-sm text-gray-400 dark:text-slate-500 text-center py-4">No payments recorded yet</p>
                        ` : `
                            <div class="space-y-2 max-h-64 overflow-y-auto">
                                ${monthlyEarnings.map(m => {
            const monthLabel = new Date(m.month + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            const isCurrentMonth = m.month === currentMonthKey;
            const maxAmount = Math.max(...monthlyEarnings.map(x => x.total_collected));
            const pct = maxAmount > 0 ? Math.round((m.total_collected / maxAmount) * 100) : 0;
            return `
                                        <div class="flex items-center gap-2">
                                            <span class="text-xs text-gray-500 dark:text-slate-400 w-16 flex-shrink-0 ${isCurrentMonth ? 'font-bold text-blue-600 dark:text-blue-400' : ''}">${monthLabel}</span>
                                            <div class="flex-1 h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                <div class="h-2 rounded-full transition-all ${isCurrentMonth ? 'bg-blue-500' : 'bg-green-400'}" style="width:${pct}%"></div>
                                            </div>
                                            <span class="text-xs font-semibold text-gray-700 dark:text-gray-200 w-20 text-right flex-shrink-0">${UI.formatCurrency(m.total_collected)}</span>
                                        </div>
                                        <p class="text-[10px] text-gray-400 dark:text-slate-600 pl-18 -mt-1 ml-[68px]">${m.payment_count} payments • ${m.unique_clients} clients</p>
                                    `;
        }).join('')}
                            </div>
                        `}
                    </div>
                </div>

                <!-- Calendar -->
                <div class="lg:col-span-2 glass-card p-5">
                    <div class="flex items-center justify-between mb-4">
                        <button onclick="CalendarPage.prevMonth()" class="btn btn-ghost btn-icon">
                            <i data-lucide="chevron-left" class="w-5 h-5"></i>
                        </button>
                        <h3 class="text-lg font-bold text-gray-800 dark:text-white">${monthName}</h3>
                        <button onclick="CalendarPage.nextMonth()" class="btn btn-ghost btn-icon">
                            <i data-lucide="chevron-right" class="w-5 h-5"></i>
                        </button>
                    </div>

                    <!-- Day headers -->
                    <div class="grid grid-cols-7 gap-1 mb-2">
                        ${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d =>
            `<div class="text-center text-xs font-semibold text-gray-400 dark:text-slate-500 py-2">${d}</div>`
        ).join('')}
                    </div>

                    <!-- Calendar grid -->
                    <div class="grid grid-cols-7 gap-1" id="calendar-grid">
                        ${this.buildCalendarGrid(year, month, collectionMap, today)}
                    </div>

                    <!-- Selected Day Details -->
                    <div id="day-details" class="mt-4 ${this._pendingDayDetail ? '' : 'hidden'}"></div>
                </div>
            </div>
        `;
        lucide.createIcons();

        // Auto-load selected day if set
        if (this.selectedDay) {
            this.loadDayCollections();
        }
    },

    buildCalendarGrid(year, month, collectionMap, today) {
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startPad = firstDay.getDay();
        let html = '';

        for (let i = 0; i < startPad; i++) {
            html += '<div class="calendar-day text-gray-300 dark:text-slate-700"></div>';
        }

        for (let d = 1; d <= lastDay.getDate(); d++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const isToday = dateStr === today;
            const collection = collectionMap[dateStr];
            const hasCollection = !!collection;

            html += `
                <div class="calendar-day ${isToday ? 'today' : ''} ${hasCollection ? 'has-collection' : ''}
                            ${hasCollection ? 'font-semibold' : 'text-gray-600 dark:text-slate-400'}"
                     onclick="CalendarPage.showDayDetail('${dateStr}')"
                     title="${hasCollection ? `${collection.count} collections — ${UI.formatCurrency(collection.total_amount)}` : ''}">
                    ${d}
                    ${hasCollection && !isToday ? `<span class="text-[9px] text-amber-600 dark:text-amber-400 font-bold">${collection.count}</span>` : ''}
                </div>
            `;
        }

        return html;
    },

    async showDayDetail(dateStr) {
        const collections = await App.api('get_collections_by_date', dateStr);
        const el = document.getElementById('day-details');

        if (collections.length === 0) {
            el.classList.add('hidden');
            return;
        }

        el.classList.remove('hidden');
        el.innerHTML = `
            <div class="p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700/30">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="font-semibold text-sm text-gray-800 dark:text-white">
                        Collections for ${UI.formatDate(dateStr)} (${collections.length})
                    </h4>
                    <span class="font-bold text-green-600 dark:text-green-400 text-sm">
                        ${UI.formatCurrency(collections.reduce((s, c) => s + c.total_due, 0))}
                    </span>
                </div>
                <div class="space-y-2">
                    ${collections.map(c => `
                        <div class="flex items-center justify-between p-2.5 rounded-lg bg-white dark:bg-slate-700/50 border border-gray-100 dark:border-slate-600/30 cursor-pointer hover:border-blue-200 dark:hover:border-blue-800/50 transition"
                             onclick="App.navigate('loan_detail', {id: ${c.loan_id}})">
                            <div>
                                <span class="font-semibold text-sm text-gray-800 dark:text-white">${c.first_name} ${c.last_name}</span>
                                <span class="text-xs text-gray-400 dark:text-slate-500 ml-2">Loan #${c.loan_id}</span>
                            </div>
                            <span class="font-bold text-sm text-gray-700 dark:text-gray-200">${UI.formatCurrency(c.total_due)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    quickDay(day) {
        this.selectedDay = day;
        document.getElementById('day-filter-input').value = day;
        this.loadDayCollections();
        // Refresh quick buttons highlight
        document.querySelectorAll('.quick-day-btn').forEach(b => b.classList.remove('active'));
    },

    async loadDayCollections() {
        const input = document.getElementById('day-filter-input');
        const day = parseInt(input ? input.value : this.selectedDay);
        if (!day || day < 1 || day > 31) {
            UI.toast('Please enter a valid day (1–31)', 'warning');
            return;
        }
        this.selectedDay = day;
        const container = document.getElementById('day-collections-container');
        if (!container) return;

        container.innerHTML = `<div class="text-center py-4"><div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div></div>`;

        const collections = await App.api('get_collections_by_day_of_month', day);
        this.dayCollections = collections;

        if (collections.length === 0) {
            container.innerHTML = `<p class="text-xs text-gray-400 dark:text-slate-500 text-center py-3">No active loans due on day ${day}</p>`;
            return;
        }

        // Group by loan (one entry per loan, next upcoming due date)
        const loanMap = {};
        collections.forEach(c => {
            const key = c.loan_id;
            if (!loanMap[key] || c.due_date < loanMap[key].due_date) {
                loanMap[key] = c;
            }
        });
        const unique = Object.values(loanMap);

        const totalDue = unique.reduce((s, c) => s + c.monthly_payment, 0);

        container.innerHTML = `
            <div class="space-y-0">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-xs font-semibold text-gray-600 dark:text-slate-300">${unique.length} clients pay on day ${day}</p>
                    <p class="text-xs font-bold text-indigo-600 dark:text-indigo-400">${UI.formatCurrency(totalDue)}/mo</p>
                </div>
                <div class="space-y-1.5 max-h-56 overflow-y-auto">
                    ${unique.map(c => {
            return `
                        <div class="flex items-center justify-between p-2 rounded-lg bg-indigo-50/50 dark:bg-indigo-900/10 border border-indigo-100 dark:border-indigo-800/20 group">
                            <div class="min-w-0 flex-1">
                                <p class="font-semibold text-xs text-gray-800 dark:text-white truncate">${c.first_name} ${c.last_name}</p>
                                <p class="text-[10px] text-gray-400 dark:text-slate-500">Loan #${c.loan_id} • ${c.contact || '—'}</p>
                            </div>
                            <div class="text-right flex-shrink-0 ml-2">
                                <p class="font-bold text-xs text-indigo-600 dark:text-indigo-400">${UI.formatCurrency(c.monthly_payment)}</p>
                                <button onclick="CalendarPage.quickRecord(${c.loan_id}, ${c.monthly_payment}, '${c.first_name} ${c.last_name}')"
                                        class="text-[10px] px-2 py-0.5 bg-green-500 hover:bg-green-600 text-white rounded-md font-medium transition mt-0.5 opacity-0 group-hover:opacity-100">
                                    ✓ Record
                                </button>
                            </div>
                        </div>
                    `}).join('')}
                </div>
                <button onclick="CalendarPage.validateAllDay(${day})" class="btn btn-success btn-sm w-full mt-3">
                    <i data-lucide="check-circle" class="w-4 h-4"></i>
                    Validate All Payments for Day ${day}
                </button>
            </div>
        `;
        setTimeout(() => lucide.createIcons(), 50);
    },

    quickRecord(loanId, amount, clientName) {
        const today = new Date().toISOString().split('T')[0];
        UI.showModal(`Record Payment — ${clientName}`, `
            <form onsubmit="CalendarPage.submitQuickPayment(event, ${loanId})" class="space-y-4">
                <div class="p-3 rounded-xl bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/30">
                    <p class="text-sm text-green-700 dark:text-green-400 font-medium">Loan #${loanId} — ${clientName}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Amount (₱) *</label>
                        <input name="amount" type="number" class="input" required step="0.01" value="${amount}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Date *</label>
                        <input name="payment_date" type="date" class="input" required value="${today}">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Method</label>
                    <select name="method" class="input select">
                        <option value="cash">Cash</option>
                        <option value="gcash">GCash</option>
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="check">Check</option>
                    </select>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <input name="notes" class="input" placeholder="Optional notes...">
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-success">
                        <i data-lucide="check" class="w-4 h-4"></i> Confirm Payment
                    </button>
                </div>
            </form>
        `, { width: 'max-w-md' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async submitQuickPayment(e, loanId) {
        e.preventDefault();
        const form = e.target;
        UI.toast('Recording payment...', 'info');
        const result = await App.api('record_payment',
            loanId,
            parseFloat(form.amount.value),
            form.method.value,
            form.payment_date.value,
            form.notes.value
        );
        UI.closeModal();
        if (result && result.success !== false) {
            UI.toast('Payment recorded successfully!', 'success');
            SoundEngine.success();
            // Refresh day collections
            if (this.selectedDay) this.loadDayCollections();
        } else {
            UI.toast('Error: ' + (result?.error || 'Could not record payment'), 'error');
        }
    },

    validateAllDay(day) {
        const loanMap = {};
        this.dayCollections.forEach(c => {
            if (!loanMap[c.loan_id]) loanMap[c.loan_id] = c;
        });
        const unique = Object.values(loanMap);

        if (unique.length === 0) {
            UI.toast('No clients to validate', 'warning');
            return;
        }

        const today = new Date().toISOString().split('T')[0];

        UI.showModal(`Bulk Payment Validation — Day ${day}`, `
            <div class="space-y-4">
                <p class="text-sm text-gray-600 dark:text-slate-400">
                    The following <strong>${unique.length}</strong> clients have payments scheduled on day <strong>${day}</strong>.
                    Select which payments to confirm today.
                </p>
                <div class="space-y-2 max-h-64 overflow-y-auto">
                    ${unique.map((c, i) => `
                        <label class="flex items-center gap-3 p-2.5 rounded-xl border border-gray-200 dark:border-slate-600 cursor-pointer hover:bg-blue-50/30 dark:hover:bg-slate-700/30 transition">
                            <input type="checkbox" id="bulk-pay-${i}" class="w-4 h-4 accent-blue-500" checked>
                            <div class="flex-1 min-w-0">
                                <p class="font-semibold text-sm text-gray-800 dark:text-white">${c.first_name} ${c.last_name}</p>
                                <p class="text-xs text-gray-400 dark:text-slate-500">Loan #${c.loan_id} • ${c.contact || '—'}</p>
                            </div>
                            <span class="font-bold text-sm text-green-600 dark:text-green-400 flex-shrink-0">${UI.formatCurrency(c.monthly_payment)}</span>
                            <input type="hidden" id="bulk-loan-${i}" value="${c.loan_id}">
                            <input type="hidden" id="bulk-amount-${i}" value="${c.monthly_payment}">
                        </label>
                    `).join('')}
                </div>
                <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl">
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400">Payment Date</label>
                    <input id="bulk-pay-date" type="date" class="input flex-1" value="${today}">
                    <select id="bulk-pay-method" class="input select flex-1">
                        <option value="cash">Cash</option>
                        <option value="gcash">GCash</option>
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="check">Check</option>
                    </select>
                </div>
                <div class="flex gap-3 justify-end">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="CalendarPage.submitBulkPayments(${unique.length})" class="btn btn-success">
                        <i data-lucide="check-circle" class="w-4 h-4"></i> Validate Selected
                    </button>
                </div>
            </div>
        `, { width: 'max-w-lg' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async submitBulkPayments(count) {
        const payDate = document.getElementById('bulk-pay-date')?.value;
        const payMethod = document.getElementById('bulk-pay-method')?.value || 'cash';
        if (!payDate) { UI.toast('Please set a payment date', 'warning'); return; }

        UI.closeModal();
        let success = 0, errors = 0;

        for (let i = 0; i < count; i++) {
            const checkbox = document.getElementById(`bulk-pay-${i}`);
            if (!checkbox || !checkbox.checked) continue;

            const loanId = document.getElementById(`bulk-loan-${i}`)?.value;
            const amount = parseFloat(document.getElementById(`bulk-amount-${i}`)?.value || 0);
            if (!loanId || !amount) continue;

            try {
                const result = await App.api('record_payment', parseInt(loanId), amount, payMethod, payDate, 'Bulk validation');
                if (result && result.success === false) errors++;
                else success++;
            } catch (e) {
                errors++;
            }
        }

        if (success > 0) {
            UI.toast(`✅ ${success} payment${success > 1 ? 's' : ''} recorded successfully!`, 'success');
            SoundEngine.success();
        }
        if (errors > 0) {
            UI.toast(`⚠️ ${errors} payment${errors > 1 ? 's' : ''} failed`, 'warning');
        }

        // Refresh
        await this.render();
    },

    prevMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.render();
    },

    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.render();
    }
};
