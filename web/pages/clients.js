/**
 * Lending Pro Freeware — Clients Page
 */
const ClientsPage = {
    currentPage: 1,
    searchQuery: '',

    async render() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="flex items-center justify-between mb-5">
                <div class="flex items-center gap-3 flex-1 max-w-md">
                    <div class="relative flex-1">
                        <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" id="client-search" class="input pl-10" placeholder="Search clients..." 
                               value="${this.searchQuery}" oninput="ClientsPage.onSearch(this.value)">
                    </div>
                </div>
                <button onclick="ClientsPage.showCreateForm()" class="btn btn-primary">
                    <i data-lucide="user-plus" class="w-4 h-4"></i> New Client
                </button>
            </div>
            <div id="clients-table-container">
                ${UI.skeleton(5)}
            </div>
        `;
        lucide.createIcons();
        await this.loadClients();
    },

    async loadClients() {
        const data = await App.api('get_clients', this.searchQuery, 'created_at', 'DESC', this.currentPage, 15);
        const container = document.getElementById('clients-table-container');

        if (data.clients.length === 0) {
            container.innerHTML = UI.emptyState('users', 'No Clients Yet',
                'Start by adding your first borrower to the system.',
                '<button onclick="ClientsPage.showCreateForm()" class="btn btn-primary"><i data-lucide="user-plus" class="w-4 h-4"></i> Add First Client</button>'
            );
            lucide.createIcons();
            return;
        }

        container.innerHTML = `
            <div class="glass-card overflow-hidden">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Contact</th>
                            <th>Rating</th>
                            <th>Created</th>
                            <th class="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.clients.map(c => `
                            <tr onclick="App.navigate('client_detail', {id: '${c.id}'})">
                                <td>
                                    <span class="text-xs font-mono font-medium text-blue-600 dark:text-blue-400">${c.id}</span>
                                </td>
                                <td>
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                            ${c.first_name[0]}${c.last_name[0]}
                                        </div>
                                        <div>
                                            <p class="font-semibold text-sm">${c.first_name} ${c.last_name}</p>
                                            ${c.address ? `<p class="text-xs text-gray-400 dark:text-slate-500 truncate max-w-[200px]">${c.address}</p>` : ''}
                                        </div>
                                    </div>
                                </td>
                                <td><span class="text-sm">${c.contact || '—'}</span></td>
                                <td>${UI.starRating(c.rating)}</td>
                                <td><span class="text-sm text-gray-400 dark:text-slate-500">${UI.formatDate(c.created_at)}</span></td>
                                <td class="text-right">
                                    <button onclick="event.stopPropagation(); ClientsPage.showEditForm('${c.id}')" class="btn btn-sm btn-ghost">
                                        <i data-lucide="edit-2" class="w-4 h-4"></i>
                                    </button>
                                    <button onclick="event.stopPropagation(); ClientsPage.deleteClient('${c.id}')" class="btn btn-sm btn-ghost text-red-500">
                                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${UI.pagination(data.page, data.total_pages, 'ClientsPage.goToPage')}
        `;
        lucide.createIcons();
    },

    onSearch(val) {
        this.searchQuery = val;
        this.currentPage = 1;
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(() => this.loadClients(), 300);
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadClients();
    },

    async showCreateForm() {
        const allClients = await App.api('get_all_clients_simple');
        const referralOptions = allClients.map(c =>
            `<option value="${c.id}">${c.first_name} ${c.last_name} (${c.id})</option>`
        ).join('');

        UI.showModal('New Client', `
            <form onsubmit="ClientsPage.submitCreate(event)" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">First Name *</label>
                        <input name="first_name" class="input" required placeholder="Juan">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Last Name *</label>
                        <input name="last_name" class="input" required placeholder="Dela Cruz">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">ID Number</label>
                        <input name="id_number" class="input" placeholder="Passport / UMID / SSS">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Date of Birth</label>
                        <input name="date_of_birth" type="date" class="input" max="${new Date().toISOString().split('T')[0]}">
                    </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Employer</label>
                        <input name="employer" class="input" placeholder="Company name">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Occupation</label>
                        <input name="occupation" class="input" placeholder="Job title">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Gender</label>
                        <select name="gender" class="input select">
                            <option value="">— Not specified —</option>
                            <option value="female">Female</option>
                            <option value="male">Male</option>
                            <option value="non_binary">Non-binary</option>
                            <option value="prefer_not_to_say">Prefer not to say</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Address</label>
                    <div class="flex gap-2">
                        <div class="relative flex-1">
                            <input name="address" id="create-address-input" class="input w-full" placeholder="Type to search address…"
                                   oninput="if(ClientsPage._addrCoords) delete ClientsPage._addrCoords['create-address-input']; ClientsPage.searchAddress(this.value, 'create-addr-results', 'create-address-input')" autocomplete="off">
                            <div id="create-addr-results" class="absolute z-50 w-full mt-1 rounded-xl overflow-hidden shadow-xl border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 hidden max-h-48 overflow-y-auto"></div>
                        </div>
                        <button type="button" title="View on map" class="btn btn-ghost btn-icon flex-shrink-0 text-blue-500"
                                onclick="ClientsPage.openMapFromInput('create-address-input')">
                            <i data-lucide="map-pin" class="w-4 h-4"></i>
                        </button>
                    </div>
                    <div class="mt-1.5">
                        <input name="address_detail" class="input text-sm" placeholder="Unit / Floor / Landmark / Additional details…">
                        <p class="text-xs text-gray-400 dark:text-slate-500 mt-0.5">Optional: apartment number, landmark, barangay details, etc.</p>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Contact Number</label>
                        <input name="contact" type="tel" class="input" placeholder="+41 79 123 45 67">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Rating</label>
                        <select name="rating" class="input select">
                            <option value="1">⭐ 1 Star</option>
                            <option value="2">⭐⭐ 2 Stars</option>
                            <option value="3">⭐⭐⭐ 3 Stars</option>
                            <option value="4">⭐⭐⭐⭐ 4 Stars</option>
                            <option value="5" selected>⭐⭐⭐⭐⭐ 5 Stars</option>
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Email</label>
                        <input name="email" type="email" class="input" placeholder="juan@example.com">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Monthly Income (${UI.currencyCode()})</label>
                        <input name="monthly_income" type="number" class="input" min="0" step="0.01" inputmode="decimal" placeholder="0">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Referred By</label>
                    <select name="referred_by" class="input select">
                        <option value="">— None —</option>
                        ${referralOptions}
                    </select>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <textarea name="notes" class="input" rows="2" placeholder="Additional notes..."></textarea>
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-primary"><i data-lucide="check" class="w-4 h-4"></i> Create Client</button>
                </div>
            </form>
        `, { width: 'max-w-xl' });
        // Activer le clic-outside pour fermer le dropdown adresse
        setTimeout(function () { ClientsPage._setupOutsideClick(); }, 100);
    },

    async submitCreate(e) {
        e.preventDefault();
        const form = e.target;
        const data = {
            first_name: form.first_name.value,
            last_name: form.last_name.value,
            address: form.address.value,
            address_detail: form.address_detail?.value || '',
            contact: form.contact.value.trim(),
            email: form.email.value || '',
            monthly_income: parseFloat(form.monthly_income.value) || 0,
            id_number: form.id_number?.value || '',
            date_of_birth: form.date_of_birth?.value || '',
            employer: form.employer?.value || '',
            occupation: form.occupation?.value || '',
            gender: form.gender?.value || '',
            rating: parseInt(form.rating.value),
            referred_by: form.referred_by.value || null,
            notes: form.notes.value
        };
        const id = await App.api('create_client', data);
        if (!id || id.success === false) {
            UI.toast(id?.error || 'Could not create client.', 'error');
            return;
        }
        UI.closeModal();
        UI.toast(`Client ${id} created successfully!`, 'success');
        if (App.currentPage === 'clients') await this.loadClients();
        else App.navigate('clients');
    },

    async showEditForm(clientId) {
        const client = await App.api('get_client', clientId);
        const allClients = await App.api('get_all_clients_simple');
        const referralOptions = allClients.filter(c => c.id !== clientId).map(c =>
            `<option value="${c.id}" ${client.referred_by === c.id ? 'selected' : ''}>${c.first_name} ${c.last_name} (${c.id})</option>`
        ).join('');

        UI.showModal('Edit Client', `
            <form onsubmit="ClientsPage.submitEdit(event, '${clientId}')" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">First Name *</label>
                        <input name="first_name" class="input" required value="${client.first_name}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Last Name *</label>
                        <input name="last_name" class="input" required value="${client.last_name}">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">ID Number</label>
                        <input name="id_number" class="input" value="${client.id_number || ''}" placeholder="Passport / UMID / SSS">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Date of Birth</label>
                        <input name="date_of_birth" type="date" class="input" value="${client.date_of_birth || ''}" max="${new Date().toISOString().split('T')[0]}">
                    </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Employer</label>
                        <input name="employer" class="input" value="${client.employer || ''}" placeholder="Company name">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Occupation</label>
                        <input name="occupation" class="input" value="${client.occupation || ''}" placeholder="Job title">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Gender</label>
                        <select name="gender" class="input select">
                            ${[['','— Not specified —'],['female','Female'],['male','Male'],['non_binary','Non-binary'],['prefer_not_to_say','Prefer not to say']].map(([value,label]) => `<option value="${value}" ${client.gender === value ? 'selected' : ''}>${label}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Address</label>
                    <div class="flex gap-2">
                        <div class="relative flex-1">
                            <input name="address" id="edit-address-input" class="input w-full" placeholder="Type to search address…"
                                   value="${client.address || ''}"
                                   oninput="if(ClientsPage._addrCoords) delete ClientsPage._addrCoords['edit-address-input']; ClientsPage.searchAddress(this.value, 'edit-addr-results', 'edit-address-input')" autocomplete="off">
                            <div id="edit-addr-results" class="absolute z-50 w-full mt-1 rounded-xl overflow-hidden shadow-xl border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 hidden max-h-48 overflow-y-auto"></div>
                        </div>
                        <button type="button" title="View on map" class="btn btn-ghost btn-icon flex-shrink-0 text-blue-500"
                                onclick="ClientsPage.openMapFromInput('edit-address-input')">
                            <i data-lucide="map-pin" class="w-4 h-4"></i>
                        </button>
                    </div>
                    <div class="mt-1.5">
                        <input name="address_detail" class="input text-sm" placeholder="Unit / Floor / Landmark / Additional details…" value="${client.address_detail || ''}">
                        <p class="text-xs text-gray-400 dark:text-slate-500 mt-0.5">Optional: apartment number, landmark, barangay details, etc.</p>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Contact Number</label>
                        <input name="contact" type="tel" class="input" placeholder="+41 79 123 45 67" value="${client.contact || ''}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Rating</label>
                        <select name="rating" class="input select">
                            ${[1, 2, 3, 4, 5].map(i => `<option value="${i}" ${client.rating === i ? 'selected' : ''}>${'⭐'.repeat(i)} ${i} Star${i > 1 ? 's' : ''}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Email</label>
                        <input name="email" type="email" class="input" placeholder="juan@example.com" value="${client.email || ''}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Monthly Income (${UI.currencyCode()})</label>
                        <input name="monthly_income" type="number" class="input" min="0" step="0.01" inputmode="decimal" value="${client.monthly_income || ''}" placeholder="0">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Referred By</label>
                    <select name="referred_by" class="input select">
                        <option value="">— None —</option>
                        ${referralOptions}
                    </select>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <textarea name="notes" class="input" rows="2">${client.notes || ''}</textarea>
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-primary"><i data-lucide="save" class="w-4 h-4"></i> Save Changes</button>
                </div>
            </form>
        `, { width: 'max-w-xl' });
        // Activer le clic-outside pour fermer le dropdown adresse
        setTimeout(function () { ClientsPage._setupOutsideClick(); }, 100);
    },

    async submitEdit(e, clientId) {
        e.preventDefault();
        const form = e.target;
        const data = {
            first_name: form.first_name.value,
            last_name: form.last_name.value,
            address: form.address.value,
            address_detail: form.address_detail?.value || '',
            contact: form.contact.value.trim(),
            email: form.email.value || '',
            monthly_income: parseFloat(form.monthly_income.value) || 0,
            id_number: form.id_number?.value || '',
            date_of_birth: form.date_of_birth?.value || '',
            employer: form.employer?.value || '',
            occupation: form.occupation?.value || '',
            gender: form.gender?.value || '',
            rating: parseInt(form.rating.value),
            referred_by: form.referred_by.value || null,
            notes: form.notes.value
        };
        const result = await App.api('update_client', clientId, data);
        if (result?.success === false) {
            UI.toast(result.error || 'Could not update client.', 'error');
            return;
        }
        UI.closeModal();
        UI.toast('Client updated successfully!', 'success');
        this.loadClients();
    },

    deleteClient(clientId) {
        UI.confirm(`Are you sure you want to delete client ${clientId}? This will also delete all their loans and payments.`,
            async () => {
                await App.api('delete_client', clientId);
                UI.toast('Client deleted', 'success');
                ClientsPage.loadClients();
            }
        );
    },

    // ─── Address Autocomplete (OpenStreetMap Nominatim — free, no API key) ─────
    _addrTimer: null,
    _addrCoords: {},  // { inputId -> { lat, lon } }
    _outsideClickBound: null,  // reference au listener de clic-outside

    // Ferme tous les dropdowns d'adresse ouverts
    _closeAllAddrDropdowns() {
        ['create-addr-results', 'edit-addr-results', 'cdetail-addr-results'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('hidden');
        });
    },

    // Installe (ou reinstalle) le listener de clic-outside
    _setupOutsideClick() {
        // Retirer l'ancien listener s'il existe
        if (ClientsPage._outsideClickBound) {
            document.removeEventListener('click', ClientsPage._outsideClickBound, true);
        }
        ClientsPage._outsideClickBound = function (e) {
            const addrContainers = [
                document.getElementById('create-addr-results'),
                document.getElementById('edit-addr-results'),
                document.getElementById('cdetail-addr-results'),
                document.getElementById('create-address-input'),
                document.getElementById('edit-address-input'),
                document.getElementById('cdetail-address-input')
            ].filter(Boolean);
            const clickedInsideAddr = addrContainers.some(function (el) { return el.contains(e.target); });
            if (!clickedInsideAddr) {
                ClientsPage._closeAllAddrDropdowns();
            }
        };
        document.addEventListener('click', ClientsPage._outsideClickBound, true);
    },

    searchAddress(query, resultsId, inputId) {
        clearTimeout(this._addrTimer);
        const results = document.getElementById(resultsId);
        if (!results) return;

        if (!query || query.length < 3) {
            results.classList.add('hidden');
            return;
        }

        this._addrTimer = setTimeout(async () => {
            results.innerHTML = '<div class="px-4 py-3 text-xs text-gray-400 dark:text-slate-500 flex items-center gap-2"><div class="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div> Searching…</div>';
            results.classList.remove('hidden');
            try {
                const url = `https://nominatim.openstreetmap.org/search?` +
                    `q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=7`;
                const resp = await fetch(url, {
                    headers: { 'Accept-Language': 'en', 'User-Agent': 'Lending-Pro-Freeware/1.0' }
                });
                const places = await resp.json();

                if (!places.length) {
                    results.innerHTML = '<div class="px-4 py-3 text-xs text-gray-400 dark:text-slate-500">No addresses found. Try more details.</div>';
                    return;
                }

                results.innerHTML = '';
                places.forEach(p => {
                    const a = p.address || {};
                    const parts = [
                        a.house_number && a.road ? `${a.house_number} ${a.road}` : (a.road || ''),
                        a.suburb || a.neighbourhood || a.village || a.hamlet || '',
                        a.city || a.town || a.municipality || a.county || '',
                        a.state || ''
                    ].filter(Boolean);
                    const label = parts.length ? parts.join(', ') : p.display_name.split(',').slice(0, 3).join(',');

                    const item = document.createElement('div');
                    item.className = 'px-4 py-2.5 cursor-pointer hover:bg-blue-50 dark:hover:bg-slate-700 transition border-b border-gray-100 dark:border-slate-700/50 last:border-0';
                    item.setAttribute('data-label', label);
                    item.setAttribute('data-lat', p.lat);
                    item.setAttribute('data-lon', p.lon);
                    item.setAttribute('data-input', inputId);
                    item.setAttribute('data-results', resultsId);
                    item.innerHTML = `
                        <p class="font-medium text-sm text-gray-800 dark:text-white">${label}</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500 truncate">${p.display_name}</p>
                    `;
                    item.addEventListener('click', (e) => {
                        const el = e.currentTarget;
                        ClientsPage._pickAddress(
                            el.getAttribute('data-input'),
                            el.getAttribute('data-results'),
                            el.getAttribute('data-label'),
                            el.getAttribute('data-lat'),
                            el.getAttribute('data-lon')
                        );
                    });
                    results.appendChild(item);
                });

            } catch (err) {
                results.innerHTML = '<div class="px-4 py-3 text-xs text-red-400">Could not reach OpenStreetMap. Check your internet connection.</div>';
            }
        }, 450);
    },

    _pickAddress(inputId, resultsId, label, lat, lon) {
        // IMPORTANT: annuler le timer en cours pour eviter que la liste re-apparaisse
        clearTimeout(ClientsPage._addrTimer);
        const input = document.getElementById(inputId);
        const results = document.getElementById(resultsId);
        if (input) input.value = label;
        if (results) results.classList.add('hidden');
        // Store coords for map button
        if (!ClientsPage._addrCoords) ClientsPage._addrCoords = {};
        ClientsPage._addrCoords[inputId] = { lat: parseFloat(lat), lon: parseFloat(lon), label };
        if (typeof SoundEngine !== 'undefined') SoundEngine.click();
    },

    // Legacy alias kept for client_detail.js which still calls selectAddress
    selectAddress(resultsId, label) {
        const inputId = resultsId === 'create-addr-results' ? 'create-address-input'
            : resultsId === 'edit-addr-results' ? 'edit-address-input'
                : 'cdetail-address-input';
        ClientsPage._pickAddress(inputId, resultsId, label, null, null);
    },

    openMapFromInput(inputId) {
        const input = document.getElementById(inputId);
        const address = input ? input.value.trim() : '';
        if (!address) { UI.toast('Please enter or select an address first.', 'warning'); return; }

        // Fermer le dropdown avant d'ouvrir la carte
        clearTimeout(ClientsPage._addrTimer);
        ClientsPage._closeAllAddrDropdowns();

        const coords = ClientsPage._addrCoords && ClientsPage._addrCoords[inputId];
        if (coords && coords.lat) {
            // On a deja des coords stockees (selection depuis dropdown ou drag precedent)
            UI.showMapModal(address, coords.lat, coords.lon, inputId);
        } else {
            // Pas de coords : geocoder le texte saisi
            UI.toast('Locating address…', 'info');
            fetch('https://nominatim.openstreetmap.org/search?q=' + encodeURIComponent(address) + '&format=json&limit=1',
                { headers: { 'Accept-Language': 'en', 'User-Agent': 'Lending-Pro-Freeware/1.0' } })
                .then(function (r) { return r.json(); })
                .then(function (results) {
                    if (results.length) {
                        const lat = parseFloat(results[0].lat);
                        const lon = parseFloat(results[0].lon);
                        // Stocker les coords geocodees
                        if (!ClientsPage._addrCoords) ClientsPage._addrCoords = {};
                        ClientsPage._addrCoords[inputId] = { lat: lat, lon: lon, label: address };
                        UI.showMapModal(address, lat, lon, inputId);
                    } else {
                        UI.showMapModal(address, null, null, inputId);
                    }
                })
                .catch(function () { UI.showMapModal(address, null, null, inputId); });
        }
    },

    // Called from client profile view (no input field — just an address string)
    openMapForAddress(address) {
        if (!address) return;
        UI.toast('Locating on map…', 'info');
        fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`,
            { headers: { 'Accept-Language': 'en', 'User-Agent': 'Lending-Pro-Freeware/1.0' } })
            .then(r => r.json())
            .then(results => {
                if (results.length) {
                    UI.showMapModal(address, parseFloat(results[0].lat), parseFloat(results[0].lon));
                } else {
                    UI.showMapModal(address, null, null);
                }
            })
            .catch(() => UI.showMapModal(address, null, null));
    }
};
