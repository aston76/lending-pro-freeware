/**
 * Lending Pro Freeware — Loans Page
 * List all loans with status filter and create new loans.
 */
const LoansPage = {
    currentPage: 1,
    statusFilter: 'all',
    searchQuery: '',

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
                <div class="flex items-center gap-3">
                    <div class="relative">
                        <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" id="loan-search" class="input pl-10 w-64" placeholder="Search by client..."
                               value="${this.searchQuery}" oninput="LoansPage.onSearch(this.value)">
                    </div>
                    <div class="flex bg-gray-100 dark:bg-slate-800 rounded-xl p-1 gap-1 flex-wrap">
                        ${['all', 'active', 'paid', 'refinanced', 'defaulted'].map(s => `
                            <button onclick="LoansPage.filterStatus('${s}')" 
                                    class="px-3 py-1.5 rounded-lg text-xs font-semibold transition ${this.statusFilter === s ? 'bg-white dark:bg-slate-700 shadow text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'}">
                                ${s.charAt(0).toUpperCase() + s.slice(1)}
                            </button>
                        `).join('')}
                    </div>
                </div>
                <button onclick="LoansPage.showCreateForm()" class="btn btn-primary">
                    <i data-lucide="plus" class="w-4 h-4"></i> New Loan
                </button>
            </div>
            <div id="loans-table-container">${UI.skeleton(5)}</div>
        `;
        lucide.createIcons();
        await this.loadLoans();
    },

    async loadLoans() {
        const data = await App.api('get_all_loans', this.statusFilter, this.searchQuery, this.currentPage, 15);
        const container = document.getElementById('loans-table-container');

        if (data.loans.length === 0) {
            container.innerHTML = UI.emptyState('banknote', 'No Loans Found',
                this.statusFilter !== 'all' ? 'No loans match this filter.' : 'Create your first loan to get started.',
                '<button onclick="LoansPage.showCreateForm()" class="btn btn-primary"><i data-lucide="plus" class="w-4 h-4"></i> New Loan</button>'
            );
            lucide.createIcons();
            return;
        }

        container.innerHTML = `
            <div class="glass-card overflow-hidden">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Client</th>
                            <th>Principal</th>
                            <th>Rate</th>
                            <th>Term</th>
                            <th>Installment</th>
                            <th>Paid</th>
                            <th>Status</th>
                            <th>Start</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.loans.map(l => {
            const totalDue = Number(l.total_repayment || (l.principal + l.total_interest));
            const paidPct = totalDue > 0 ? Math.min(100, (l.total_paid / totalDue * 100)).toFixed(0) : 0;
            return `
                            <tr onclick="App.navigate('loan_detail', {id: ${l.id}})">
                                <td><span class="font-mono text-sm font-medium">${l.id}</span></td>
                                <td>
                                    <div>
                                        <p class="font-semibold text-sm">${l.first_name} ${l.last_name}</p>
                                        <p class="text-xs text-gray-400 dark:text-slate-500 font-mono">${l.client_id}</p>
                                    </div>
                                </td>
                                <td><span class="font-semibold text-sm">${UI.formatCurrency(l.principal)}</span></td>
                                <td>
                                    <div class="flex flex-col gap-0.5">
                                        <span class="text-sm font-semibold">${(l.interest_rate / (l.original_term_months || l.term_months)).toFixed(2)}%<span class="text-xs font-normal text-gray-400 dark:text-slate-500">/mo</span></span>
                                        <span class="text-xs px-1.5 py-0.5 rounded-md inline-block w-fit font-medium ${l.interest_type === 'fixed' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'}">${l.interest_type === 'fixed' ? 'Fixed' : 'Declining'}</span>
                                    </div>
                                </td>
                                <td><span class="text-sm">${l.term_months}mo · ${(l.repayment_frequency || 'monthly').replace('biweekly', '2 weeks')}</span></td>
                                <td><span class="text-sm">${UI.formatCurrency(l.installment_amount || l.monthly_payment)}</span></td>
                                <td>
                                    <div class="flex items-center gap-2">
                                        <div class="flex-1 bg-gray-200 dark:bg-slate-700 rounded-full h-1.5 w-16">
                                            <div class="h-1.5 rounded-full ${l.status === 'paid' ? 'bg-green-500' : l.status === 'defaulted' ? 'bg-red-500' : 'bg-blue-500'}" 
                                                 style="width: ${paidPct}%"></div>
                                        </div>
                                        <span class="text-xs text-gray-400">${paidPct}%</span>
                                    </div>
                                </td>
                                <td>${UI.badge(l.status)}</td>
                                <td><span class="text-sm text-gray-400">${UI.formatDateShort(l.start_date)}</span></td>
                            </tr>`;
        }).join('')}
                    </tbody>
                </table>
            </div>
            ${UI.pagination(data.page, data.total_pages, 'LoansPage.goToPage')}
        `;
        lucide.createIcons();
    },

    searchClient(val) {
        const clients = LoansPage._allClients || [];
        const results = document.getElementById('client-search-results');
        const hiddenInput = document.getElementById('client_id_hidden');
        const display = document.getElementById('client-selected-display');

        // Clear selection if user is typing again
        if (hiddenInput) hiddenInput.value = '';
        if (display) {
            display.textContent = 'No client selected';
            display.className = 'text-xs mt-1 text-gray-400 dark:text-slate-500';
        }

        if (!val || val.length < 3) {
            if (results) results.classList.add('hidden');
            return;
        }

        const query = val.toLowerCase();
        const filtered = clients.filter(c =>
            c.first_name.toLowerCase().includes(query) ||
            c.last_name.toLowerCase().includes(query) ||
            c.id.toLowerCase().includes(query)
        ).slice(0, 10);

        if (!results) return;

        if (filtered.length === 0) {
            results.innerHTML = '<div class="px-4 py-3 text-sm text-gray-400 dark:text-slate-500">No clients found</div>';
            results.classList.remove('hidden');
            return;
        }

        results.innerHTML = filtered.map(c => `
            <div class="px-4 py-2.5 cursor-pointer hover:bg-blue-50 dark:hover:bg-slate-700 transition border-b border-gray-100 dark:border-slate-700/50 last:border-0"
                 onclick="LoansPage.selectClient('${c.id}', '${c.first_name} ${c.last_name}')">
                <p class="font-semibold text-sm text-gray-800 dark:text-white">${c.first_name} ${c.last_name}</p>
                <p class="text-xs text-gray-400 dark:text-slate-500 font-mono">${c.id}</p>
            </div>
        `).join('');
        results.classList.remove('hidden');
    },

    selectClient(id, name) {
        const hiddenInput = document.getElementById('client_id_hidden');
        const display = document.getElementById('client-selected-display');
        const searchInput = document.getElementById('client-search-input');
        const results = document.getElementById('client-search-results');

        if (hiddenInput) hiddenInput.value = id;
        if (searchInput) searchInput.value = name;
        if (results) results.classList.add('hidden');
        if (display) {
            display.textContent = `Selected: ${name} (${id})`;
            display.className = 'text-xs mt-1 text-green-600 dark:text-green-400 font-medium';
        }
        SoundEngine.click();
    },

    filterStatus(status) {
        this.statusFilter = status;
        this.currentPage = 1;
        this.render();
    },

    onSearch(val) {
        this.searchQuery = val;
        this.currentPage = 1;
        clearTimeout(this._t);
        this._t = setTimeout(() => this.loadLoans(), 300);
    },

    goToPage(p) { this.currentPage = p; this.loadLoans(); },

    async showCreateForm(presetClientId = null) {
        const [clients, settings, collectors] = await Promise.all([
            App.api('get_all_clients_simple'),
            App.api('get_settings'),
            App.api('get_collectors', true),
        ]);
        if (clients.length === 0) {
            UI.toast('Please create a client first', 'warning');
            ClientsPage.showCreateForm();
            return;
        }
        const defaultRate = settings.default_interest_rate || '5.0';
        const defaultType = settings.default_interest_type || 'fixed';

        // Si on vient d'une fiche client, on verrouille le client
        const presetClient = presetClientId ? clients.find(c => c.id === presetClientId) : null;
        const clientField = presetClient
            ? `<div class="flex items-center gap-3 p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/40">
                    <i data-lucide="user-check" class="w-5 h-5 text-blue-500 flex-shrink-0"></i>
                    <div class="flex-1 min-w-0">
                        <p class="font-semibold text-sm text-gray-800 dark:text-white truncate">${presetClient.first_name} ${presetClient.last_name}</p>
                        <p class="text-xs text-blue-500 dark:text-blue-400 font-mono">${presetClient.id}</p>
                    </div>
                    <span class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-800/40 text-blue-600 dark:text-blue-300 rounded-lg font-medium flex-shrink-0">Client actuel</span>
                    <input type="hidden" name="client_id" value="${presetClient.id}">
               </div>`
            : `<div class="relative">
                    <input id="client-search-input" class="input" placeholder="Type 3+ letters to search client..."
                           oninput="LoansPage.searchClient(this.value)" autocomplete="off">
                    <div id="client-search-results" class="absolute z-50 w-full mt-1 rounded-xl overflow-hidden shadow-xl border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 hidden max-h-48 overflow-y-auto"></div>
                    <input type="hidden" name="client_id" id="client_id_hidden" required>
                    <p id="client-selected-display" class="text-xs mt-1 text-gray-400 dark:text-slate-500">No client selected</p>
               </div>`;

        // Store clients for local search
        LoansPage._allClients = clients;

        UI.showModal('New Loan', `
            <form onsubmit="LoansPage.submitCreate(event)" class="space-y-4">
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Client *</label>
                    ${clientField}
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Principal (${UI.currencyCode()}) *</label>
                        <input name="principal" type="number" class="input" required min="0.01" step="0.01" inputmode="decimal" placeholder="10000"
                               oninput="LoansPage.previewLoan()">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Interest Rate (%) *</label>
                        <input name="rate" type="number" class="input" required min="0" max="100" step="0.01" inputmode="decimal" value="${defaultRate}"
                               oninput="LoansPage.previewLoan()">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Interest Type</label>
                        <select name="interest_type" class="input select" onchange="LoansPage.previewLoan()">
                            <option value="fixed" ${defaultType === 'fixed' ? 'selected' : ''}>Fixed Rate</option>
                            <option value="declining" ${defaultType === 'declining' ? 'selected' : ''}>Declining Balance</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Term (months) *</label>
                        <input name="term_months" type="number" class="input" required min="1" max="120" value="6"
                               oninput="LoansPage.previewLoan()">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Rate Duration</label>
                    <select name="rate_duration" class="input select" onchange="LoansPage.previewLoan()">
                        <option value="monthly" selected>Per Month</option>
                        <option value="total">Total for entire term</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Repayment Frequency</label>
                        <select name="repayment_frequency" class="input select" onchange="LoansPage.previewLoan()">
                            <option value="monthly">Monthly</option>
                            <option value="biweekly">Every 2 weeks</option>
                            <option value="weekly">Weekly</option>
                            <option value="daily">Daily</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Collector</label>
                        <select name="collector_id" class="input select">
                            <option value="">— Unassigned —</option>
                            ${(collectors || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Processing Fee (${UI.currencyCode()})</label>
                        <input name="processing_fee" type="number" min="0" step="0.01" class="input" value="0" oninput="LoansPage.previewLoan()">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Insurance Fee (${UI.currencyCode()})</label>
                        <input name="insurance_fee" type="number" min="0" step="0.01" class="input" value="0" oninput="LoansPage.previewLoan()">
                    </div>
                </div>
                <label class="flex items-start gap-3 p-3 rounded-xl cursor-pointer" style="background:var(--surface-2);">
                    <input name="interest_deducted_upfront" type="checkbox" class="mt-0.5" onchange="LoansPage.previewLoan()">
                    <span>
                        <span class="block text-sm font-medium">Deduct interest upfront</span>
                        <span class="block text-xs mt-0.5" style="color:var(--text-tertiary)">Interest is withheld from disbursement and is not charged again in installments.</span>
                    </span>
                </label>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Start Date *</label>
                    <input name="start_date" type="date" class="input" required value="${new Date().toISOString().split('T')[0]}" onchange="LoansPage.previewLoan()">
                </div>

                <!-- Loan Preview -->
                <div id="loan-preview" class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800/30 hidden">
                    <p class="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2">LOAN PREVIEW</p>
                    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 text-center">
                        <div>
                            <p class="text-lg font-bold text-gray-800 dark:text-white" id="preview-monthly">—</p>
                            <p class="text-xs text-gray-500 dark:text-slate-400">Installment</p>
                        </div>
                        <div>
                            <p class="text-lg font-bold text-green-600 dark:text-green-400" id="preview-interest">—</p>
                            <p class="text-xs text-gray-500 dark:text-slate-400">Total Interest</p>
                        </div>
                        <div>
                            <p class="text-lg font-bold text-gray-800 dark:text-white" id="preview-total">—</p>
                            <p class="text-xs text-gray-500 dark:text-slate-400">Total Amount</p>
                        </div>
                        <div>
                            <p class="text-lg font-bold text-blue-600 dark:text-blue-400" id="preview-disbursed">—</p>
                            <p class="text-xs text-gray-500 dark:text-slate-400">Net Disbursed</p>
                        </div>
                        <div>
                            <p class="text-lg font-bold text-purple-600 dark:text-purple-400" id="preview-taeg">—</p>
                            <p class="text-xs text-gray-500 dark:text-slate-400">Effective APR</p>
                        </div>
                    </div>
                </div>

                <details class="rounded-xl p-3" style="background:var(--surface-2);">
                    <summary class="cursor-pointer text-sm font-semibold">Optional guarantor / co-maker</summary>
                    <div class="grid grid-cols-2 gap-3 mt-3">
                        <input name="guarantor_name" class="input" placeholder="Full name">
                        <input name="guarantor_contact" class="input" placeholder="Contact number">
                        <input name="guarantor_relation" class="input" placeholder="Relationship">
                        <input name="guarantor_id_number" class="input" placeholder="ID number">
                    </div>
                </details>
                <details class="rounded-xl p-3" style="background:var(--surface-2);">
                    <summary class="cursor-pointer text-sm font-semibold">Optional collateral</summary>
                    <div class="grid grid-cols-2 gap-3 mt-3">
                        <input name="collateral_description" class="input col-span-2" placeholder="Asset description">
                        <select name="collateral_type" class="input select">
                            <option value="vehicle">Vehicle</option><option value="real_estate">Real estate</option>
                            <option value="equipment">Equipment</option><option value="jewelry">Jewelry</option>
                            <option value="electronics">Electronics</option><option value="other">Other</option>
                        </select>
                        <input name="collateral_value" type="number" min="0" step="0.01" class="input" placeholder="Estimated value">
                        <input name="collateral_serial" class="input" placeholder="Serial / title number">
                        <input name="collateral_plate" class="input" placeholder="Plate number">
                    </div>
                </details>

                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-primary"><i data-lucide="check" class="w-4 h-4"></i> Create Loan</button>
                </div>
            </form>
        `, { width: 'max-w-3xl' });
        this.previewLoan();
    },

    async previewLoan() {
        const modal = document.querySelector('.modal-content');
        if (!modal) return;
        const form = modal.querySelector('form');
        const principal = parseFloat(form.principal?.value);
        let rate = parseFloat(form.rate?.value);
        const type = form.interest_type?.value;
        const term = parseInt(form.term_months?.value);
        const rateDuration = form.rate_duration?.value;
        const frequency = form.repayment_frequency?.value || 'monthly';
        const processingFee = parseFloat(form.processing_fee?.value) || 0;
        const insuranceFee = parseFloat(form.insurance_fee?.value) || 0;
        const upfront = Boolean(form.interest_deducted_upfront?.checked);
        const startDate = form.start_date?.value || new Date().toISOString().split('T')[0];

        if (!Number.isFinite(principal) || principal <= 0 || !Number.isFinite(rate) || rate < 0 || !term) {
            document.getElementById('loan-preview')?.classList.add('hidden');
            return;
        }

        if (rateDuration === 'monthly') {
            rate = rate * term;
        }

        try {
            const preview = await App.api('calculate_loan_preview', principal, rate, type, term,
                frequency, processingFee, insuranceFee, upfront, startDate);
            const el = document.getElementById('loan-preview');
            if (!preview || preview.success === false) {
                el?.classList.add('hidden');
                return;
            }
            el.classList.remove('hidden');
            document.getElementById('preview-monthly').textContent = UI.formatCurrency(preview.monthly_payment);
            document.getElementById('preview-interest').textContent = UI.formatCurrency(preview.total_interest);
            document.getElementById('preview-total').textContent = UI.formatCurrency(preview.total_amount);
            document.getElementById('preview-disbursed').textContent = UI.formatCurrency(preview.disbursed_amount);
            document.getElementById('preview-taeg').textContent = `${Number(preview.taeg || 0).toFixed(2)}%`;
        } catch (e) { }
    },

    async submitCreate(e) {
        e.preventDefault();
        const form = e.target;
        const clientId = form.client_id.value.trim();
        if (!clientId) {
            UI.toast('Please select a client from the search results before creating the loan.', 'warning');
            return;
        }

        let finalRate = parseFloat(form.rate.value);
        if (form.rate_duration.value === 'monthly') {
            finalRate = finalRate * parseInt(form.term_months.value);
        }

        const guarantors = form.guarantor_name?.value.trim() ? [{
            name: form.guarantor_name.value,
            contact: form.guarantor_contact?.value || '',
            relation: form.guarantor_relation?.value || '',
            id_number: form.guarantor_id_number?.value || '',
        }] : [];
        const collateral = form.collateral_description?.value.trim() ? [{
            description: form.collateral_description.value,
            collateral_type: form.collateral_type?.value || 'other',
            estimated_value: parseFloat(form.collateral_value?.value) || 0,
            serial_number: form.collateral_serial?.value || '',
            plate_number: form.collateral_plate?.value || '',
        }] : [];

        const result = await App.api('create_loan',
            clientId,
            parseFloat(form.principal.value),
            finalRate,
            form.interest_type.value,
            parseInt(form.term_months.value),
            form.start_date.value,
            null,
            false,
            form.repayment_frequency.value,
            parseFloat(form.processing_fee.value) || 0,
            parseFloat(form.insurance_fee.value) || 0,
            Boolean(form.interest_deducted_upfront.checked),
            form.collector_id.value || null,
            guarantors,
            collateral
        );
        if (!result || result.success === false) {
            UI.toast(result?.error || 'Could not create loan.', 'error');
            return;
        }
        UI.closeModal();
        UI.toast(`Loan #${result.loan_id} created successfully!`, 'success');
        App.navigate('loan_detail', { id: result.loan_id });
    }
};
