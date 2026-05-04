/**
 * PH-Lending Pro — Loan Detail Page
 * Beautiful amortization timeline, payment history, PDF & print.
 */
const LoanDetailPage = {
    loanId: null,

    async render(loanId) {
        this.loanId = loanId;
        const content = document.getElementById('page-content');
        const loan = await App.api('get_loan', loanId);

        if (!loan) {
            content.innerHTML = UI.emptyState('file-x', 'Loan Not Found', 'This loan does not exist.');
            return;
        }

        document.getElementById('page-title').textContent = `Loan #${loan.id}`;
        document.getElementById('page-subtitle').textContent = `${loan.first_name} ${loan.last_name} — ${loan.client_id}`;

        const totalDue = loan.principal + loan.total_interest;
        const paidPct = totalDue > 0 ? Math.min(100, (loan.total_paid / totalDue * 100)).toFixed(1) : 0;

        content.innerHTML = `
            <div class="mb-4 flex items-center justify-between flex-wrap gap-2">
                <button onclick="App.navigate('loans')" class="btn btn-ghost btn-sm">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i> Back to Loans
                </button>
                <div class="flex gap-2 flex-wrap">
                    <button onclick="PrintManager.printLoanDetail(LoanDetailPage.loanId)" class="btn btn-ghost btn-sm">
                        <i data-lucide="printer" class="w-4 h-4"></i> Imprimer
                    </button>
                    <button onclick="PrintManager.openContractPdf(LoanDetailPage.loanId)" class="btn btn-outline btn-sm">
                        <i data-lucide="file-text" class="w-4 h-4"></i> PDF Contract
                    </button>
                    ${loan.status === 'active' ? `
                        <button onclick="LoanDetailPage.showExtendForm()" class="btn btn-sm btn-ghost text-blue-500">
                            <i data-lucide="plus-circle" class="w-4 h-4"></i> Extend Loan
                        </button>
                        <button onclick="LoanDetailPage.markDefaulted()" class="btn btn-sm btn-ghost text-red-500">
                            <i data-lucide="alert-circle" class="w-4 h-4"></i> Mark Defaulted
                        </button>
                    ` : ''}
                </div>
            </div>

            <!-- Loan Summary -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 stagger">
                ${UI.statCard('banknote', 'Principal', UI.formatCurrency(loan.principal), 'blue')}
                ${UI.statCard('percent', 'Total Interest', UI.formatCurrency(loan.total_interest), 'amber', `${loan.interest_rate}% ${loan.interest_type}`)}
                ${UI.statCard('check-circle', 'Total Paid', UI.formatCurrency(loan.total_paid), 'green', `${paidPct}% complete`)}
                ${UI.statCard('clock', 'Remaining', UI.formatCurrency(loan.remaining), loan.remaining <= 0 ? 'green' : 'red', `${loan.term_months} month term`)}
            </div>

            <!-- Progress Bar -->
            <div class="glass-card p-4 mb-6">
                <div class="flex justify-between text-sm mb-2">
                    <span class="font-medium text-gray-600 dark:text-slate-400">Payment Progress</span>
                    <div class="flex items-center gap-2">
                        ${UI.badge(loan.status)}
                        <span class="text-gray-500 dark:text-slate-400">${paidPct}%</span>
                    </div>
                </div>
                <div class="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                    <div class="h-3 rounded-full transition-all duration-500 ${loan.status === 'paid' ? 'bg-gradient-to-r from-green-400 to-emerald-500' : loan.status === 'defaulted' ? 'bg-gradient-to-r from-red-400 to-rose-500' : 'bg-gradient-to-r from-blue-400 to-indigo-500'}"
                         style="width: ${paidPct}%"></div>
                </div>
                <div class="flex justify-between text-xs text-gray-400 dark:text-slate-500 mt-1">
                    <span>${UI.formatCurrency(loan.total_paid)} paid</span>
                    <span>${UI.formatCurrency(totalDue)} total</span>
                </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-5 gap-6">
                <!-- Amortization Schedule — Beautiful Card Style -->
                <div class="xl:col-span-3 glass-card p-5">
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                            <i data-lucide="calendar-range" class="w-5 h-5 text-blue-500"></i> Amortization Schedule
                        </h4>
                        <span class="text-xs text-gray-400 dark:text-slate-500">${loan.schedule.length} months</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="text-xs font-semibold text-gray-500 dark:text-slate-400 border-b border-gray-200 dark:border-slate-700">
                                    <th class="py-3 px-4">#</th>
                                    <th class="py-3 px-4">Due Date</th>
                                    <th class="py-3 px-4 text-right">Principal</th>
                                    <th class="py-3 px-4 text-right">Interest</th>
                                    <th class="py-3 px-4 text-right">Total Due</th>
                                    <th class="py-3 px-4 text-right">Balance</th>
                                    <th class="py-3 px-4 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-slate-800/50">
                            ${(() => {
                let cumulativePaid = 0;
                return loan.schedule.map(s => {
                    const isPast = new Date(s.due_date) < new Date();
                    const isToday = s.due_date === new Date().toISOString().split('T')[0];
                    cumulativePaid += s.total_due;
                    const isActuallyPaid = loan.total_paid >= cumulativePaid;
                    const isOverdue = isPast && !isToday && !isActuallyPaid && loan.status === 'active';
                    const bgClass = isToday ? 'bg-amber-50/50 dark:bg-amber-900/20' : isOverdue ? 'bg-red-50/30 dark:bg-red-900/10' : '';
                    return `
                                <tr class="hover:bg-gray-50 dark:hover:bg-slate-800/30 transition-colors ${bgClass} text-sm">
                                    <td class="py-3 px-4 font-mono text-gray-400 dark:text-slate-500">${s.month_number}</td>
                                    <td class="py-3 px-4 font-medium ${isToday ? 'text-amber-600 dark:text-amber-400' : isOverdue ? 'text-red-500 dark:text-red-400' : 'text-gray-700 dark:text-slate-300'}">
                                        ${UI.formatDate(s.due_date)}
                                    </td>
                                    <td class="py-3 px-4 text-right text-gray-600 dark:text-slate-400">${UI.formatCurrency(s.principal_portion)}</td>
                                    <td class="py-3 px-4 text-right text-gray-600 dark:text-slate-400">${UI.formatCurrency(s.interest_portion)}</td>
                                    <td class="py-3 px-4 text-right font-bold ${isToday ? 'text-amber-600 dark:text-amber-400' : isOverdue ? 'text-red-500 dark:text-red-400' : 'text-gray-900 dark:text-white'}">
                                        ${UI.formatCurrency(s.total_due)}
                                    </td>
                                    <td class="py-3 px-4 text-right text-gray-500 dark:text-slate-400">${UI.formatCurrency(s.balance_remaining)}</td>
                                    <td class="py-3 px-4 text-center">
                                        ${isToday ? `<span class="px-2 py-1 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 rounded-md text-[10px] font-bold uppercase tracking-wider animate-pulse">Today</span>` :
                            isActuallyPaid ? `<i data-lucide="check-circle-2" class="w-4 h-4 mx-auto text-green-500"></i>` :
                                isOverdue ? `<i data-lucide="alert-triangle" class="w-4 h-4 mx-auto text-red-400"></i>` :
                                    `<i data-lucide="clock" class="w-4 h-4 mx-auto text-gray-300 dark:text-slate-600"></i>`}
                                    </td>
                                </tr>
                            `;
                }).join('');
            })()}
                            </tbody>
                        </table>
                </div>
                </div>

                <!-- Payments + Info -->
                <div class="xl:col-span-2 space-y-4">
                    <div class="glass-card p-5">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                                <i data-lucide="receipt" class="w-5 h-5 text-green-500"></i> Payments
                            </h4>
                            ${loan.status === 'active' ? `
                                <button onclick="LoanDetailPage.showPaymentForm()" class="btn btn-success btn-sm">
                                    <i data-lucide="plus" class="w-4 h-4"></i> Record
                                </button>
                            ` : ''}
                        </div>
                        ${loan.payments.length === 0 ? `
                            <p class="text-center text-gray-400 dark:text-slate-500 py-6 text-sm">No payments recorded yet</p>
                        ` : `
                            <div class="space-y-2 max-h-72 overflow-y-auto">
                                ${loan.payments.map(p => `
                                    <div class="flex items-center justify-between p-3 rounded-xl bg-gray-50/50 dark:bg-slate-800/50">
                                        <div class="min-w-0 flex-1">
                                            <p class="font-semibold text-sm text-green-600 dark:text-green-400">+${UI.formatCurrency(p.amount)}</p>
                                            <p class="text-xs text-gray-400 dark:text-slate-500 truncate">${UI.formatDate(p.payment_date)} • ${(p.payment_method || 'cash').replace('_', ' ').toUpperCase()}</p>
                                            ${p.notes ? `<p class="text-xs text-gray-400 dark:text-slate-500 mt-0.5 truncate">${p.notes}</p>` : ''}
                                        </div>
                                        <div class="flex items-center gap-1 flex-shrink-0">
                                            <button onclick="event.stopPropagation(); PrintManager.openReceiptPdf(${p.id})" class="btn btn-ghost btn-sm" title="Prévisualiser reçu PDF">
                                                <i data-lucide="eye" class="w-4 h-4"></i>
                                            </button>
                                            <button onclick="event.stopPropagation(); LoanDetailPage.generateReceipt(${p.id})" class="btn btn-ghost btn-sm" title="Ouvrir dans Aperçu">
                                                <i data-lucide="file-text" class="w-4 h-4"></i>
                                            </button>
                                            <button onclick="event.stopPropagation(); LoanDetailPage.showVoidPaymentModal(${p.id}, ${Number(p.amount || 0)})" class="btn btn-ghost btn-sm text-red-500" title="Void payment">
                                                <i data-lucide="undo-2" class="w-4 h-4"></i>
                                            </button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `}
                    </div>

                    <!-- Loan Info Card -->
                    <div class="glass-card p-5">
                        <h4 class="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
                            <i data-lucide="info" class="w-5 h-5 text-blue-500"></i> Loan Info
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Client</span><a onclick="App.navigate('client_detail', {id:'${loan.client_id}'})" class="text-blue-600 dark:text-blue-400 cursor-pointer hover:underline">${loan.first_name} ${loan.last_name}</a></div>
                            <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Interest Type</span><span class="font-medium">${loan.interest_type === 'fixed' ? 'Fixed Rate' : 'Declining Balance'}</span></div>
                            <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Start Date</span><span class="font-medium">${UI.formatDate(loan.start_date)}</span></div>
                            <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Created</span><span class="font-medium">${UI.formatDate(loan.created_at)}</span></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();
    },

    showPaymentForm() {
        const today = new Date().toISOString().split('T')[0];
        UI.showModal('Record Payment', `
            <form onsubmit="LoanDetailPage.submitPayment(event)" class="space-y-4">
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Amount (₱) *</label>
                    <input name="amount" type="number" class="input" required min="1" step="0.01" placeholder="Enter amount">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Payment Date *</label>
                        <input name="payment_date" type="date" class="input" required value="${today}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Method *</label>
                        <select name="method" class="input select" required>
                            <option value="cash">💵 Cash</option>
                            <option value="gcash">📱 GCash</option>
                            <option value="bank_transfer">🏦 Bank Transfer</option>
                            <option value="check">🧾 Check</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <input name="notes" class="input" placeholder="Optional notes">
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-success"><i data-lucide="check" class="w-4 h-4"></i> Record Payment</button>
                </div>
            </form>
        `, { width: 'max-w-md' });
    },

    async submitPayment(e) {
        e.preventDefault();
        const form = e.target;
        const result = await App.api('record_payment',
            this.loanId,
            parseFloat(form.amount.value),
            form.method.value,
            form.payment_date.value,
            form.notes.value
        );
        if (result && result.success === false) {
            UI.toast(result.error || 'Could not record payment.', 'error');
            return;
        }
        UI.closeModal();
        UI.toast('Payment recorded!', 'success');
        this.render(this.loanId);
    },

    showVoidPaymentModal(paymentId, amount) {
        UI.showModal('Void Payment', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl" style="background:rgba(255,59,48,0.06); border:1px solid rgba(255,59,48,0.2);">
                    <p class="text-sm font-semibold" style="color:var(--apple-red)">This removes ${UI.formatCurrency(amount)} from loan totals without deleting the receipt record.</p>
                    <p class="text-xs mt-1" style="color:var(--text-secondary)">Use this only for entry mistakes or cancelled payments.</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Reason *</label>
                    <input id="void-payment-reason" class="input" placeholder="Example: duplicate entry" autocomplete="off">
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="LoanDetailPage.submitVoidPayment(${paymentId})" class="btn btn-danger">
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
            this.render(this.loanId);
        } else {
            UI.toast(result?.error || 'Could not void payment.', 'error');
        }
    },

    async generateContract() {
        UI.toast('Génération du contrat PDF…', 'info');
        const result = await App.api('generate_contract', this.loanId);
        if (result.success) {
            UI.toast('Contrat PDF ouvert ! Sauvegardé : ' + result.filename, 'success');
        } else {
            UI.toast('Erreur PDF : ' + result.error, 'error');
        }
    },

    async generateReceipt(paymentId) {
        UI.toast('Génération du reçu…', 'info');
        const result = await App.api('generate_receipt', paymentId);
        if (result.success) {
            UI.toast('Reçu PDF ouvert ! Sauvegardé : ' + result.filename, 'success');
        } else {
            UI.toast('Erreur PDF : ' + result.error, 'error');
        }
    },

    markDefaulted() {
        UI.confirm('Are you sure you want to mark this loan as defaulted?', async () => {
            await App.api('update_loan_status', LoanDetailPage.loanId, 'defaulted');
            UI.toast('Loan marked as defaulted', 'warning');
            LoanDetailPage.render(LoanDetailPage.loanId);
        });
    },

    showExtendForm() {
        UI.showModal('Extend Loan Term', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/30">
                    <p class="text-sm text-blue-700 dark:text-blue-400">
                        <i data-lucide="info" class="w-4 h-4 inline mr-1"></i>
                        Adds new payment months after the last scheduled date using the remaining balance.
                    </p>
                </div>
                <form onsubmit="LoanDetailPage.submitExtend(event)" class="space-y-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Additional Months *</label>
                        <input name="months" type="number" class="input" required min="1" max="60" value="3" placeholder="3">
                    </div>
                    <div class="flex gap-3 justify-end pt-2">
                        <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                        <button type="submit" class="btn btn-primary">
                            <i data-lucide="plus-circle" class="w-4 h-4"></i> Extend Loan
                        </button>
                    </div>
                </form>
            </div>
        `, { width: 'max-w-sm' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async submitExtend(e) {
        e.preventDefault();
        const months = parseInt(e.target.months.value);
        UI.toast('Extending loan...', 'info');
        const result = await App.api('extend_loan', this.loanId, months);
        UI.closeModal();
        if (result && result.success) {
            UI.toast(`Loan extended by ${months} months. New term: ${result.new_term} months.`, 'success');
            this.render(this.loanId);
        } else {
            UI.toast('Error: ' + (result?.error || 'Unknown'), 'error');
        }
    },

    printPage() {
        // Redirige vers le menu contextuel PrintManager
        PrintManager.printLoanDetail(this.loanId);
    }
};
