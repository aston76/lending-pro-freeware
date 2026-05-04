/**
 * PH-Lending Pro — Referral Commissions Page
 */
const CommissionsPage = {
    async render() {
        const content = document.getElementById('page-content');
        const commissions = await App.api('get_referral_commissions');

        content.innerHTML = `
            <div class="flex items-center justify-between mb-5">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-xl">
                        <i data-lucide="gift" class="w-5 h-5 text-amber-600 dark:text-amber-400"></i>
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-800 dark:text-white">Referral Commissions</h3>
                        <p class="text-xs text-gray-400 dark:text-slate-500">${commissions.length} commissions tracked</p>
                    </div>
                </div>
            </div>

            ${commissions.length === 0 ? UI.emptyState('gift', 'No Referral Commissions', 'Commissions are automatically generated when a referred client takes a loan.') : `
                <!-- Summary -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 stagger">
                    ${UI.statCard('gift', 'Total Commissions',
            UI.formatCurrency(commissions.reduce((s, c) => s + c.commission_amount, 0)), 'amber')}
                    ${UI.statCard('check-circle', 'Paid Out',
                UI.formatCurrency(commissions.filter(c => c.status === 'paid').reduce((s, c) => s + c.commission_amount, 0)), 'green')}
                    ${UI.statCard('clock', 'Pending',
                    UI.formatCurrency(commissions.filter(c => c.status === 'pending').reduce((s, c) => s + c.commission_amount, 0)), 'blue')}
                </div>

                <div class="glass-card overflow-hidden">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Referrer</th>
                                <th>Referred</th>
                                <th>Loan</th>
                                <th>Commission</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${commissions.map(c => `
                                <tr style="cursor:default">
                                    <td>
                                        <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
                                            <i data-lucide="user" class="w-3 h-3 inline mr-1 text-amber-500"></i>
                                            ${c.referrer_first} ${c.referrer_last}
                                            <span class="text-xs text-gray-400 dark:text-slate-500 ml-1">#${c.referrer_id}</span>
                                        </span>
                                    </td>
                                    <td>
                                        <span class="text-sm text-gray-700 dark:text-gray-300">
                                            <i data-lucide="user" class="w-3 h-3 inline mr-1 text-gray-400"></i>
                                            ${c.referred_first} ${c.referred_last}
                                            <span class="text-xs text-gray-400 dark:text-slate-500 ml-1">#${c.referred_id}</span>
                                        </span>
                                    </td>
                                    <td>
                                        <a onclick="App.navigate('loan_detail', {id:${c.loan_id}})" class="text-sm font-mono cursor-pointer hover:underline text-blue-600 dark:text-blue-400">
                                            #${c.loan_id}
                                        </a>
                                    </td>
                                    <td><span class="font-semibold text-sm">${UI.formatCurrency(c.commission_amount)}</span></td>
                                    <td>${UI.badge(c.status)}</td>
                                    <td><span class="text-sm text-gray-400 dark:text-slate-500">${UI.formatDate(c.created_at)}</span></td>
                                    <td>
                                        ${c.status === 'pending' ? `
                                            <button onclick="CommissionsPage.markPaid(${c.id})" class="btn btn-success btn-sm">
                                                <i data-lucide="check" class="w-3 h-3"></i> Pay
                                            </button>
                                        ` : '<span class="text-xs text-green-500">✓ Paid</span>'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        `;
        lucide.createIcons();
    },

    async markPaid(id) {
        await App.api('mark_commission_paid', id);
        UI.toast('Commission marked as paid!', 'success');
        this.render();
    }
};
