/**
 * PH-Lending Pro — Client Detail Page
 * Full client profile with photo, DTI, penalties, loans, documents, webcam, signature.
 */
const ClientDetailPage = {
    clientId: null,

    async render(clientId) {
        this.clientId = clientId;
        const content = document.getElementById('page-content');
        const client = await App.api('get_client', clientId);

        if (!client) {
            content.innerHTML = UI.emptyState('user-x', 'Client Not Found', 'This client does not exist.');
            return;
        }

        document.getElementById('page-title').textContent = `${client.first_name} ${client.last_name}`;
        document.getElementById('page-subtitle').textContent = client.id;

        const activeLoans = (client.loans || []).filter(l => l.status === 'active');
        const totalDebt = activeLoans.reduce((s, l) => s + (l.principal + l.total_interest - (l.total_paid || 0)), 0);
        const totalMonthlyPayment = activeLoans.reduce((s, l) => s + (l.monthly_payment || 0), 0);
        const income = parseFloat(client.monthly_income || 0);
        const dti = income > 0 ? ((totalMonthlyPayment / income) * 100).toFixed(1) : null;
        const dtiHigh = dti && parseFloat(dti) > 40;

        const pendingPenalties = (client.penalties || []).filter(p => p.status === 'pending');
        const totalPenalties = pendingPenalties.reduce((s, p) => s + p.amount, 0);

        content.innerHTML = `
            <div class="mb-4 flex items-center justify-between gap-3 flex-wrap">
                <button onclick="App.navigate('clients')" class="btn btn-ghost btn-sm">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i> Back to Clients
                </button>
                <button onclick="ClientDetailPage.openPrintCenter()" class="btn btn-outline btn-sm border-blue-200 text-blue-600 dark:border-blue-900 dark:text-blue-400">
                    <i data-lucide="printer" class="w-4 h-4"></i> Print Client Documents
                </button>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <!-- LEFT: Profile Card -->
                <div class="xl:col-span-1 space-y-4">
                    <!-- Profile Photo + Info -->
                    <div class="glass-card p-6 text-center">
                        <!-- Photo -->
                        <div class="relative inline-block mb-4">
                            <div id="profile-photo" class="w-28 h-28 rounded-lg overflow-hidden mx-auto border-4 border-white dark:border-slate-700 shadow-md bg-blue-50 dark:bg-slate-700 flex items-center justify-center">
                                ${client.photo_base64 ?
                `<img src="${client.photo_base64}" class="w-full h-full object-cover" id="profile-img">` :
                `<i data-lucide="user" class="w-12 h-12 text-blue-400 dark:text-slate-400"></i>`
            }
                            </div>
                            <button onclick="ClientDetailPage.takePhoto()" title="Take webcam photo"
                                class="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center shadow-lg transition">
                                <i data-lucide="camera" class="w-4 h-4"></i>
                            </button>
                        </div>

                        <h2 class="text-xl font-bold text-gray-800 dark:text-white">${client.first_name} ${client.last_name}</h2>
                        <p class="text-sm text-gray-500 dark:text-slate-400 font-mono">${client.id}</p>
                        <div class="mt-2">${UI.starRating(client.rating)}</div>

                        ${dti !== null ? `
                        <div class="mt-3 p-3 rounded-xl ${dtiHigh ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40' : 'bg-green-50 dark:bg-green-900/10'}">
                            <p class="text-xs font-medium ${dtiHigh ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}">
                                <i data-lucide="${dtiHigh ? 'alert-triangle' : 'check-circle'}" class="w-3 h-3 inline mr-1"></i>
                                Debt-to-Income: <strong>${dti}%</strong>
                                ${dtiHigh ? ' — HIGH RISK' : ' — Acceptable'}
                            </p>
                            <p class="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">Monthly payments: ${UI.formatCurrency(totalMonthlyPayment)} / income: ${UI.formatCurrency(income)}</p>
                        </div>
                        ` : ''}

                        ${pendingPenalties.length > 0 ? `
                        <div class="mt-3 p-3 rounded-xl bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800/40">
                            <p class="text-xs font-bold text-orange-600 dark:text-orange-400">
                                <i data-lucide="alert-circle" class="w-3 h-3 inline mr-1"></i>
                                ${pendingPenalties.length} Pending Penalt${pendingPenalties.length === 1 ? 'y' : 'ies'}: ${UI.formatCurrency(totalPenalties)}
                            </p>
                        </div>
                        ` : ''}
                    </div>

                    <!-- Contact Info -->
                    <div class="glass-card p-5">
                        <h4 class="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
                            <i data-lucide="contact" class="w-4 h-4 text-blue-500"></i> Contact & Income
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-500 dark:text-slate-300">Phone</span>
                                <div class="flex items-center gap-1.5">
                                    <span class="font-bold text-gray-800 dark:text-gray-100">${client.contact || '—'}</span>
                                    ${client.contact && client.contact.trim().length > 3 ? `
                                    <button onclick="ClientDetailPage.testPhoneNumber('${(client.contact || '').replace(/'/g, "\\'")}')"
                                            class="flex items-center gap-1 px-1.5 py-0.5 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/40 hover:text-blue-600 transition-all duration-150 flex-shrink-0"
                                            title="Envoyer un SMS de test à ce numéro">
                                        <i data-lucide="send" class="w-3 h-3"></i>
                                        <span class="text-[10px] font-semibold">Test</span>
                                    </button>` : ''}
                                </div>
                            </div>
                            ${client.email ? `<div class="flex justify-between items-center"><span class="text-gray-500 dark:text-slate-300">Email</span><a href="mailto:${client.email}" class="font-medium text-blue-600 dark:text-blue-400 hover:underline text-xs truncate max-w-[160px]">${client.email}</a></div>` : ''}
                            <div class="flex items-start justify-between gap-2">
                                <span class="text-gray-500 dark:text-slate-300 flex-shrink-0">Address</span>
                                <div class="flex items-center gap-1 justify-end">
                                    <span class="font-medium text-right text-xs text-gray-700 dark:text-gray-200">${client.address || '—'}</span>
                                    ${client.address ? `
                                    <button onclick="ClientsPage.openMapForAddress('${(client.address || '').replace(/'/g, "\\'")}')"
                                            class="text-blue-500 hover:text-blue-600 flex-shrink-0" title="View on map">
                                        <i data-lucide="map-pin" class="w-3.5 h-3.5"></i>
                                    </button>` : ''}
                                </div>
                            </div>
                            ${client.address_detail ? `<div class="flex justify-between"><span class="text-gray-500 dark:text-slate-300">Details</span><span class="font-medium text-right text-xs text-gray-500 dark:text-gray-400 italic max-w-[160px]">${client.address_detail}</span></div>` : ''}
                            <div class="flex justify-between">
                                <span class="text-gray-500 dark:text-slate-300">Monthly Income</span>
                                <span class="font-bold ${income === 0 ? 'text-gray-400 dark:text-slate-500' : 'text-gray-800 dark:text-gray-100'}">${income > 0 ? UI.formatCurrency(income) : 'Not set'}</span>
                            </div>
                        </div>
                        <button onclick="ClientDetailPage.editClient()" class="btn btn-outline btn-sm w-full mt-3">
                            <i data-lucide="edit-3" class="w-3 h-3"></i> Edit Profile
                        </button>
                    </div>

                    <!-- Notes -->
                    ${client.notes ? `
                    <div class="glass-card p-5">
                        <h4 class="font-bold text-gray-800 dark:text-white mb-2 flex items-center gap-2">
                            <i data-lucide="file-text" class="w-4 h-4 text-purple-500"></i> Notes
                        </h4>
                        <p class="text-sm font-medium text-gray-700 dark:text-gray-200 whitespace-pre-wrap">${client.notes}</p>
                    </div>` : ''}

                    <!-- Referral -->
                    ${client.referrer || client.referrals?.length > 0 ? `
                    <div class="glass-card p-5">
                        <h4 class="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
                            <i data-lucide="network" class="w-4 h-4 text-amber-500"></i> Referral Network
                        </h4>
                        ${client.referrer ? `
                            <p class="text-xs text-gray-400 dark:text-slate-500 mb-1">Referred by:</p>
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-200 block mb-2">
                                <i data-lucide="user" class="w-3 h-3 inline mr-1 text-amber-500"></i>
                                ${client.referrer.first_name} ${client.referrer.last_name}
                                <span class="text-xs text-gray-400 dark:text-slate-500 ml-1">#${client.referrer.id}</span>
                            </span>
                        ` : ''}
                        ${client.referrals?.length > 0 ? `
                            <p class="text-xs text-gray-400 dark:text-slate-500 mb-1">Referred ${client.referrals.length} client(s):</p>
                            ${client.referrals.map(r => `
                                <span class="text-sm font-medium text-gray-700 dark:text-gray-200 block">
                                    <i data-lucide="user" class="w-3 h-3 inline mr-1 text-amber-400"></i>
                                    ${r.first_name} ${r.last_name}
                                    <span class="text-xs text-gray-400 dark:text-slate-500 ml-1">#${r.id}</span>
                                </span>
                            `).join('')}
                        ` : ''}
                    </div>` : ''}

                    <!-- Social Media -->
                    ${(() => {
                let sm = [];
                try { sm = JSON.parse(client.social_media || '[]'); } catch (e) { }
                if (!sm || sm.length === 0) return '';
                return `
                        <div class="glass-card p-5">
                            <h4 class="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
                                <i data-lucide="share-2" class="w-4 h-4 text-pink-500"></i> Réseaux Sociaux
                            </h4>
                            <div class="flex flex-col gap-2">
                                ${sm.map(s => {
                    const net = ClientDetailPage._SOCIAL_NETWORKS.find(n => n.id === s.network);
                    if (!net || !s.handle) return '';
                    const url = net.urlFn(s.handle);
                    return `
                                    <button onclick="ClientDetailPage.openSocialLink('${url.replace(/'/g, "\\'")}')"
                                        class="flex items-center gap-2.5 px-3 py-2 rounded-xl text-left w-full transition hover:scale-[1.02] active:scale-95"
                                        style="background:${net.bg}; color:${net.color};"
                                        title="Ouvrir ${net.label} de ${s.handle}">
                                        <span class="text-base flex-shrink-0">${net.icon}</span>
                                        <div class="min-w-0">
                                            <p class="text-[10px] font-semibold uppercase tracking-wider opacity-75">${net.label}</p>
                                            <p class="text-sm font-bold truncate">${s.handle}</p>
                                        </div>
                                        <i data-lucide="external-link" class="w-3.5 h-3.5 ml-auto opacity-60 flex-shrink-0"></i>
                                    </button>`;
                }).join('')}
                            </div>
                        </div>`;
            })()}

                </div>

                <!-- RIGHT: Loans + Penalties + Documents -->
                <div class="xl:col-span-2 space-y-5">
                    <!-- Loans -->
                    <div class="glass-card p-5">
                        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
                            <h4 class="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                                <i data-lucide="banknote" class="w-5 h-5 text-green-500"></i> Loans (${(client.loans || []).length})
                            </h4>
                            <div class="flex gap-2 flex-wrap">
                                ${activeLoans.length > 0 ? `
                                    <button onclick="ClientDetailPage.showExtendLoanForm(${activeLoans[0].id})" class="btn btn-outline btn-sm">
                                        <i data-lucide="plus-circle" class="w-3 h-3"></i> Extend Loan
                                    </button>
                                    <button onclick="ClientDetailPage.showRefinanceForm('${client.id}', ${activeLoans[0].id})" class="btn btn-outline btn-sm">
                                        <i data-lucide="refresh-cw" class="w-3 h-3"></i> Refinance
                                    </button>
                                ` : `
                                    <button onclick="UI.toast('This client has no active loan.', 'warning')" class="btn btn-outline btn-sm opacity-50 cursor-not-allowed" style="pointer-events: auto;">
                                        <i data-lucide="refresh-cw" class="w-3 h-3"></i> Refinance
                                    </button>
                                `}
                                <button onclick="LoansPage.showCreateForm('${client.id}')" class="btn btn-success btn-sm">
                                    <i data-lucide="plus" class="w-3 h-3"></i> New Loan
                                </button>
                            </div>
                        </div>
                        ${(client.loans || []).length === 0 ? UI.emptyState('banknote', 'No Loans', 'This client has no loans yet.') : `
                            <div class="space-y-3">
                                ${client.loans.map(l => {
                const totalDue = l.principal + l.total_interest;
                const paid = l.total_paid || 0;
                const pct = totalDue > 0 ? Math.min(100, (paid / totalDue * 100)) : 0;
                return `
                                    <div class="p-3 rounded-xl border border-gray-200/50 dark:border-slate-700/30 hover:bg-blue-50/30 dark:hover:bg-slate-800/30 transition">
                                        <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
                                            <div class="flex items-center gap-2 cursor-pointer flex-1 min-w-0" onclick="App.navigate('loan_detail', {id:${l.id}})">
                                                <span class="font-mono text-xs text-gray-400 dark:text-slate-500">#${l.id}</span>
                                                ${UI.badge(l.status)}
                                                <span class="font-bold text-sm">${UI.formatCurrency(l.principal)}</span>
                                            </div>
                                            ${l.status === 'active' ? `
                                            <button onclick="event.stopPropagation(); ClientDetailPage.showQuickPaymentForm(${l.id}, ${l.monthly_payment || 0}, ${Math.max(0, totalDue - paid)})"
                                                class="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-green-500 hover:bg-green-600 active:scale-95 text-white text-xs font-bold transition-all flex-shrink-0 shadow-sm"
                                                title="Record a payment for this loan">
                                                <i data-lucide="plus" class="w-3 h-3"></i> Pay
                                            </button>` : ''}
                                        </div>
                                        <div class="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-1.5 mb-1 cursor-pointer" onclick="App.navigate('loan_detail', {id:${l.id}})">
                                            <div class="h-1.5 rounded-full ${l.status === 'paid' ? 'bg-green-500' : l.status === 'refinanced' ? 'bg-purple-500' : 'bg-blue-500'}" style="width:${pct}%"></div>
                                        </div>
                                        <div class="flex justify-between text-xs text-gray-400 dark:text-slate-500 cursor-pointer" onclick="App.navigate('loan_detail', {id:${l.id}})">
                                            <span>${UI.formatCurrency(paid)} paid</span>
                                            <span>${UI.formatCurrency(l.monthly_payment)}/mo • ${l.term_months}mo</span>
                                        </div>
                                        ${l.rollover_amount > 0 ? `<p class="text-xs text-purple-500 dark:text-purple-400 mt-1">↩ Includes ${UI.formatCurrency(l.rollover_amount)} rollover from Loan #${l.original_loan_id}</p>` : ''}
                                    </div>`;
            }).join('')}
                            </div>
                        `}
                    </div>

                    <!-- Penalties -->
                    <div class="glass-card p-5">
                        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
                            <h4 class="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                                <i data-lucide="alert-circle" class="w-5 h-5 text-orange-500"></i>
                                Penalties ${pendingPenalties.length > 0 ? `<span class="ml-1 px-2 py-0.5 text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-full">${pendingPenalties.length} pending</span>` : ''}
                            </h4>
                            ${activeLoans.length > 0 ? `
                                <button onclick="ClientDetailPage.addPenalty('${client.id}')" class="btn btn-ghost btn-sm text-orange-500">
                                    <i data-lucide="plus" class="w-3 h-3"></i> Add Penalty
                                </button>
                            ` : ''}
                        </div>
                        ${(client.penalties || []).length === 0 ? `<p class="text-sm text-gray-400 dark:text-slate-500 py-2">No penalties recorded.</p>` : `
                            <div class="space-y-2 max-h-56 overflow-y-auto">
                                ${client.penalties.map(p => `
                                    <div class="flex items-center justify-between p-3 rounded-xl ${p.status === 'pending' ? 'bg-orange-50 dark:bg-orange-900/10 border border-orange-200/50 dark:border-orange-800/30' : 'bg-gray-50 dark:bg-slate-800/30'}">
                                        <div class="min-w-0">
                                            <div class="flex items-center gap-2 flex-wrap">
                                                <span class="font-bold text-sm ${p.status === 'pending' ? 'text-orange-600 dark:text-orange-400' : 'text-gray-400'}">${UI.formatCurrency(p.amount)}</span>
                                                <span class="text-xs px-2 py-0.5 rounded-full ${p.status === 'pending' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400' : p.status === 'waived' ? 'bg-gray-100 dark:bg-slate-700 text-gray-500' : 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'}">${p.status}</span>
                                            </div>
                                            <p class="text-xs text-gray-400 dark:text-slate-500">${p.reason.replace('_', ' ')} • Loan #${p.loan_id} • ${UI.formatDate(p.penalty_date)}</p>
                                            ${p.notes ? `<p class="text-xs text-gray-400 mt-0.5">${p.notes}</p>` : ''}
                                        </div>
                                        ${p.status === 'pending' ? `
                                            <div class="flex gap-1 flex-shrink-0">
                                                <button onclick="ClientDetailPage.updatePenalty(${p.id}, 'paid')" class="btn btn-success btn-sm">Paid</button>
                                                <button onclick="ClientDetailPage.updatePenalty(${p.id}, 'waived')" class="btn btn-ghost btn-sm">Waive</button>
                                            </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        `}
                    </div>

                    <!-- Documents & Photos -->
                    <div class="glass-card p-5">
                        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
                            <h4 class="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                                <i data-lucide="paperclip" class="w-5 h-5 text-blue-500"></i> Documents
                            </h4>
                            <div class="flex gap-2 flex-wrap">
                                <button onclick="ClientDetailPage.captureIdPhoto()" class="btn btn-ghost btn-sm">
                                    <i data-lucide="id-card" class="w-3 h-3"></i> ID Photo
                                </button>
                                <button onclick="ClientDetailPage.uploadDocument()" class="btn btn-ghost btn-sm">
                                    <i data-lucide="upload" class="w-3 h-3"></i> Upload
                                </button>
                            </div>
                        </div>
                        ${(client.documents || []).length === 0
                ? `<p class="text-sm text-gray-400 dark:text-slate-500 py-2">No documents uploaded.</p>`
                : `<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                ${client.documents.map(d => `
                                    <div class="relative group cursor-pointer p-2 rounded-lg bg-gray-50 hover:bg-gray-100 dark:bg-slate-800/40 dark:hover:bg-slate-700/60 transition text-xs text-center border border-transparent hover:border-blue-200 dark:hover:border-blue-800/50">
                                        <div class="absolute -top-2 -right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition z-10">
                                            <button onclick="event.stopPropagation(); ClientDetailPage.renameDocument(${d.id}, '${(d.description || d.file_type).replace(/'/g, "\\'")}')" class="p-1.5 bg-blue-500 text-white rounded-full shadow-sm hover:bg-blue-600" title="Rename document">
                                                <i data-lucide="pencil" class="w-3 h-3"></i>
                                            </button>
                                            <button onclick="event.stopPropagation(); ClientDetailPage.deleteDocument(${d.id})" class="p-1.5 bg-red-500 text-white rounded-full shadow-sm hover:bg-red-600 focus:opacity-100" title="Delete document">
                                                <i data-lucide="trash-2" class="w-3 h-3"></i>
                                            </button>
                                        </div>
                                        <div onclick="const path = '${d.file_path}'.replace(/\\\\/g, '\\\\'); App.api('open_file', path)">
                                            <i data-lucide="${d.description === 'photo' || d.description === 'id' ? 'image' : 'file'}" class="w-5 h-5 mx-auto mb-1 text-blue-400 dark:text-blue-500"></i>
                                            <p class="truncate font-medium text-gray-700 dark:text-gray-200">${d.description || d.file_type}</p>
                                            <p class="text-gray-500 dark:text-slate-400 mt-0.5 text-[10px] leading-tight">${UI.formatDateTime(d.created_at)}</p>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>`
            }
                    </div>

                    <!-- Digital Signature / Note -->
                    <div class="glass-card p-5">
                        <h4 class="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
                            <i data-lucide="pen-line" class="w-4 h-4 text-purple-500"></i> Digital Signature / Note
                        </h4>
                        <canvas id="sig-canvas" class="signature-canvas w-full" height="120" style="touch-action: none;"></canvas>
                        <div class="flex gap-2 mt-2">
                            <button onclick="ClientDetailPage.clearSig()" class="btn btn-ghost btn-sm">Clear</button>
                            <button onclick="ClientDetailPage.saveSig()" class="btn btn-primary btn-sm">Save Signature</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Hidden file input for document upload -->
            <input type="file" id="doc-upload-input" class="hidden" onchange="ClientDetailPage.handleDocUpload(event)">
        `;

        lucide.createIcons();
        this._initCanvas();
    },

    _initCanvas() {
        const canvas = document.getElementById('sig-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        let drawing = false;
        const getPos = e => {
            const r = canvas.getBoundingClientRect();
            const src = e.touches ? e.touches[0] : e;
            return [src.clientX - r.left, src.clientY - r.top];
        };
        canvas.onmousedown = canvas.ontouchstart = e => { drawing = true; ctx.beginPath(); const [x, y] = getPos(e); ctx.moveTo(x, y); e.preventDefault(); };
        canvas.onmousemove = canvas.ontouchmove = e => { if (!drawing) return; const [x, y] = getPos(e); ctx.lineTo(x, y); ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2; ctx.stroke(); e.preventDefault(); };
        canvas.onmouseup = canvas.ontouchend = () => drawing = false;
    },

    clearSig() {
        const canvas = document.getElementById('sig-canvas');
        if (canvas) canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    },

    async saveSig() {
        const canvas = document.getElementById('sig-canvas');
        if (!canvas) return;
        const data = canvas.toDataURL('image/png');
        await App.api('save_signature', this.clientId, data);
        UI.toast('Signature saved!', 'success');
    },

    async takePhoto() {
        UI.toast('Ouverture de la caméra...', 'info');
        const result = await App.api('capture_photo_native', this.clientId, 'photo', 'Profile Photo (SPACE = Capture, ESC = Cancel)');
        if (result && result.success) {
            UI.toast(result.message || 'Profile photo updated!', 'success');
            this.render(this.clientId);
        } else if (result && result.error && result.error !== 'Capture cancelled by user.') {
            UI.toast('Error: ' + result.error, 'error');
        }
    },

    async captureIdPhoto() {
        UI.toast('Ouverture de la caméra...', 'info');
        const result = await App.api('capture_photo_native', this.clientId, 'id', 'ID Photo (SPACE = Capture, ESC = Cancel)');
        if (result && result.success) {
            UI.toast(result.message || 'ID photo saved!', 'success');
            this.render(this.clientId);
        } else if (result && result.error && result.error !== 'Capture cancelled by user.') {
            UI.toast('Error: ' + result.error, 'error');
        }
    },

    uploadDocument() {
        document.getElementById('doc-upload-input').click();
    },

    async handleDocUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async () => {
            await App.api('save_document', this.clientId, reader.result, file.name, 'other');
            UI.toast(`Document "${file.name}" uploaded!`, 'success');
            this.render(this.clientId);
        };
        reader.readAsDataURL(file);
    },

    renameDocument(docId, oldName) {
        const newName = prompt("Enter new document name:", oldName);
        if (newName && newName.trim() !== "" && newName !== oldName) {
            App.api('rename_document', docId, newName.trim()).then(res => {
                if (res.success) {
                    UI.toast('Document renamed successfully', 'success');
                    this.render(this.clientId);
                } else {
                    UI.toast('Failed to rename document: ' + res.error, 'error');
                }
            });
        }
    },

    deleteDocument(docId) {
        UI.confirm('Are you sure you want to delete this document permanently?', async () => {
            UI.toast('Deleting document...', 'info');
            const result = await App.api('delete_document', docId);
            if (result.success) {
                UI.toast('Document deleted', 'success');
                this.render(this.clientId);
            } else {
                UI.toast('Failed to delete: ' + result.error, 'error');
            }
        });
    },


    editClient() {
        UI.showModal('Edit Client', `
            <form onsubmit="ClientDetailPage.saveEdit(event)" class="space-y-4">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">First Name *</label>
                        <input name="first_name" class="input" required id="edit-first-name">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Last Name *</label>
                        <input name="last_name" class="input" required id="edit-last-name">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Address</label>
                    <div class="flex gap-2">
                        <div class="relative flex-1">
                            <input name="address" id="cdetail-address-input" class="input w-full" placeholder="Type to search address…"
                                   oninput="ClientsPage.searchAddress(this.value, 'cdetail-addr-results', 'cdetail-address-input')" autocomplete="off">
                            <div id="cdetail-addr-results" class="absolute z-50 w-full mt-1 rounded-xl overflow-hidden shadow-xl border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 hidden max-h-40 overflow-y-auto"></div>
                        </div>
                        <button type="button" title="View on map" class="btn btn-ghost btn-icon flex-shrink-0 text-blue-500"
                                onclick="ClientsPage.openMapFromInput('cdetail-address-input')">
                            <i data-lucide="map-pin" class="w-4 h-4"></i>
                        </button>
                    </div>
                    <div class="mt-1.5">
                        <input name="address_detail" id="edit-address-detail" class="input text-sm" placeholder="Unit / Floor / Landmark / Additional details…">
                        <p class="text-xs text-gray-400 dark:text-slate-500 mt-0.5">Optional: apartment number, landmark, barangay details, etc.</p>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Phone</label>
                        <div class="flex rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-400 transition">
                            <span class="flex items-center px-3 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 font-semibold text-sm border-r border-gray-200 dark:border-slate-600 select-none flex-shrink-0">
                                🇵🇭 +63
                            </span>
                            <input name="contact" type="tel" inputmode="numeric"
                                   class="flex-1 px-3 py-2 bg-transparent text-gray-800 dark:text-white text-sm outline-none placeholder-gray-400"
                                   placeholder="912 345 6789"
                                   id="edit-contact">
                        </div>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Monthly Income (₱)</label>
                        <input name="monthly_income" type="number" step="100" min="0" class="input" placeholder="0" id="edit-income">
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Email</label>
                    <input name="email" type="email" class="input" placeholder="juan@example.com" id="edit-email">
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <textarea name="notes" class="input" rows="3" id="edit-notes"></textarea>
                </div>

                <!-- Social Media Manager -->
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 flex items-center gap-1.5">
                            <i data-lucide="share-2" class="w-3.5 h-3.5 text-pink-500"></i> Réseaux Sociaux
                        </label>
                        <button type="button" onclick="ClientDetailPage._addSocialRow()"
                            class="flex items-center gap-1 text-xs font-semibold text-blue-500 hover:text-blue-600 transition">
                            <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i> Ajouter
                        </button>
                    </div>
                    <div id="social-media-rows" class="space-y-2">
                        <!-- rows injected by JS -->
                    </div>
                    <p class="text-[10px] text-gray-400 dark:text-slate-500 mt-1.5">Entrez le nom d'utilisateur, pas l'URL complète.</p>
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-primary"><i data-lucide="save" class="w-4 h-4"></i> Save Changes</button>
                </div>
            </form>
        `, { width: 'max-w-lg' });
        // Pre-fill form with current data
        App.api('get_client', this.clientId).then(c => {
            document.getElementById('edit-first-name').value = c.first_name || '';
            document.getElementById('edit-last-name').value = c.last_name || '';
            document.getElementById('cdetail-address-input').value = c.address || '';
            document.getElementById('edit-address-detail').value = c.address_detail || '';
            document.getElementById('edit-contact').value = (c.contact || '').replace(/^\+63\s?/, '');
            document.getElementById('edit-income').value = c.monthly_income || '';
            document.getElementById('edit-email').value = c.email || '';
            document.getElementById('edit-notes').value = c.notes || '';
            // Load social media rows
            let sm = [];
            try { sm = JSON.parse(c.social_media || '[]'); } catch (e) { }
            sm.forEach(s => ClientDetailPage._addSocialRow(s.network, s.handle));
            if (sm.length === 0) ClientDetailPage._addSocialRow();
            setTimeout(() => lucide.createIcons(), 50);
        });
    },

    async saveEdit(e) {
        e.preventDefault();
        const form = e.target;
        const rawContact = form.contact.value.trim().replace(/^\+63\s?/, '');

        // Collect social media entries
        const socialMedia = [];
        document.querySelectorAll('.social-row').forEach(row => {
            const network = row.querySelector('.social-network-select')?.value;
            const handle = row.querySelector('.social-handle-input')?.value?.trim();
            if (network && handle) socialMedia.push({ network, handle });
        });

        await App.api('update_client', this.clientId, {
            first_name: form.first_name.value,
            last_name: form.last_name.value,
            address: form.address.value,
            address_detail: form.address_detail?.value || '',
            contact: rawContact ? '+63 ' + rawContact : '',
            email: form.email ? form.email.value : '',
            monthly_income: parseFloat(form.monthly_income.value) || 0,
            notes: form.notes.value,
            social_media: JSON.stringify(socialMedia)
        });
        UI.closeModal();
        UI.toast('Client updated!', 'success');
        this.render(this.clientId);
    },

    showQuickPaymentForm(loanId, monthlyPayment, outstandingBalance) {
        const today = new Date().toISOString().split('T')[0];
        const outstanding = Math.max(0, outstandingBalance || 0);
        const suggestedAmount = Math.min(monthlyPayment || outstanding, outstanding);
        UI.showModal('Record Payment', `
            <form onsubmit="ClientDetailPage.submitQuickPayment(event, ${loanId})" class="space-y-4">
                <div class="p-3 rounded-xl bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/30">
                    <p class="text-xs text-green-700 dark:text-green-400 flex items-center gap-1.5">
                        <i data-lucide="info" class="w-3.5 h-3.5"></i>
                        Recording payment for Loan #${loanId}.
                        ${monthlyPayment > 0 ? `Monthly installment: <strong>${UI.formatCurrency(monthlyPayment)}</strong>` : ''}
                    </p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Amount (₱) *</label>
                    <input name="amount" type="number" class="input" required min="0.01" max="${outstanding}" step="0.01"
                           value="${suggestedAmount}" placeholder="Enter amount">
                    <p class="text-xs mt-1" style="color:var(--text-tertiary)">Outstanding balance: ${UI.formatCurrency(outstanding)}</p>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Payment Date *</label>
                        <input name="payment_date" type="date" class="input" required value="${today}">
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Method *</label>
                        <select name="method" class="input select" required>
                            <option value="cash">Cash</option>
                            <option value="gcash">GCash</option>
                            <option value="bank_transfer">Bank Transfer</option>
                            <option value="check">Check</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                    <input name="notes" class="input" placeholder="Optional notes">
                </div>
                <div class="flex gap-3 justify-end pt-2">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="submit" class="btn btn-success">
                        <i data-lucide="check" class="w-4 h-4"></i> Record Payment
                    </button>
                </div>
            </form>
        `, { width: 'max-w-md' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async submitQuickPayment(e, loanId) {
        e.preventDefault();
        const form = e.target;
        const result = await App.api('record_payment',
            loanId,
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
        this.render(this.clientId);
    },

    showExtendLoanForm(loanId) {
        UI.showModal('Extend Loan Term', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/30">
                    <p class="text-sm text-blue-700 dark:text-blue-400">
                        <i data-lucide="info" class="w-4 h-4 inline mr-1"></i>
                        The remaining balance will be spread over more installments. The contractual total and interest will not increase.
                    </p>
                </div>
                <form onsubmit="ClientDetailPage.submitExtendLoan(event, ${loanId})" class="space-y-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Additional Months *</label>
                        <input name="additional_months" type="number" class="input" required min="1" max="60" value="3" placeholder="3">
                        <p class="text-xs text-gray-400 dark:text-slate-500 mt-1">How many months to add to the loan term</p>
                    </div>
                    <div class="flex gap-3 justify-end pt-2">
                        <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                        <button type="submit" class="btn btn-primary">
                            <i data-lucide="plus-circle" class="w-4 h-4"></i> Extend Loan
                        </button>
                    </div>
                </form>
            </div>
        `, { width: 'max-w-md' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async submitExtendLoan(e, loanId) {
        e.preventDefault();
        const form = e.target;
        const additionalMonths = parseInt(form.additional_months.value);
        UI.toast('Extending loan...', 'info');
        const result = await App.api('extend_loan', loanId, additionalMonths);
        if (result && result.success) {
            UI.closeModal();
            UI.toast(`Term extended to ${result.new_term} months. New installment: ${UI.formatCurrency(result.new_monthly_payment)}.`, 'success');
            this.render(this.clientId);
        } else {
            UI.toast('Error: ' + (result?.error || 'Unknown error'), 'error');
        }
    },

    addPenalty(clientId) {
        const loans = [];
        App.api('get_client_loans', clientId).then(clientLoans => {
            const activeOnes = clientLoans.filter(l => l.status === 'active');
            UI.showModal('Add Penalty', `
                <form onsubmit="ClientDetailPage.submitPenalty(event, '${clientId}')" class="space-y-4">
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Loan *</label>
                        <select name="loan_id" class="input select" required>
                            ${activeOnes.map(l => `<option value="${l.id}">Loan #${l.id} — ${UI.formatCurrency(l.principal)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Amount (₱) *</label>
                            <input name="amount" type="number" step="100" min="0.01" class="input" required placeholder="500">
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Date *</label>
                            <input name="penalty_date" type="date" class="input" value="${new Date().toISOString().split('T')[0]}" required>
                        </div>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Reason *</label>
                        <select name="reason" class="input select" required>
                            <option value="late_payment">Late Payment</option>
                            <option value="missed_payment">Missed Payment</option>
                            <option value="early_termination">Early Termination</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Notes</label>
                        <input name="notes" class="input" placeholder="Optional details">
                    </div>
                    <div class="flex gap-3 justify-end pt-2">
                        <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                        <button type="submit" class="btn btn-danger"><i data-lucide="alert-triangle" class="w-4 h-4"></i> Add Penalty</button>
                    </div>
                </form>
            `, { width: 'max-w-md' });
        });
    },

    async submitPenalty(e, clientId) {
        e.preventDefault();
        const form = e.target;
        await App.api('add_penalty',
            parseInt(form.loan_id.value),
            clientId,
            parseFloat(form.amount.value),
            form.reason.value,
            form.notes.value,
            form.penalty_date.value
        );
        UI.closeModal();
        UI.toast('Penalty added!', 'warning');
        this.render(this.clientId);
    },

    async updatePenalty(penaltyId, status) {
        await App.api('update_penalty_status', penaltyId, status);
        UI.toast(status === 'paid' ? 'Penalty marked as paid' : 'Penalty waived', 'success');
        this.render(this.clientId);
    },

    // ─── Test Phone Number ────────────────────────────────────────
    testPhoneNumber(phone) {
        if (!phone || phone.trim().length < 4) {
            UI.toast('No valid phone number for this client.', 'warning');
            return;
        }

        // Validation basique du format
        const cleaned = phone.replace(/\s/g, '').replace(/-/g, '');
        const validPattern = /^(\+63|0063|09|9)\d{9,10}$|^\+\d{7,15}$/;
        if (!validPattern.test(cleaned)) {
            UI.toast('Format du numéro invalide. Vérifiez le profil du client.', 'warning');
            return;
        }

        // Confirmation avant envoi
        UI.showModal('Test Phone Number', `
            <div class="space-y-4">
                <div class="flex items-center gap-3 p-3 rounded-xl" style="background: var(--surface-2);">
                    <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                        <i data-lucide="smartphone" class="w-5 h-5 text-blue-500"></i>
                    </div>
                    <div>
                        <p class="text-sm font-semibold" style="color:var(--text-primary)">Numéro cible</p>
                        <p class="text-base font-mono font-bold" style="color:var(--accent)">${phone}</p>
                    </div>
                </div>

                <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30">
                    <p class="text-xs text-amber-700 dark:text-amber-400">
                        <i data-lucide="info" class="w-3 h-3 inline mr-1"></i>
                        A test SMS will be sent to this number through your iPhone using Mac Continuity.
                        Assurez-vous que votre iPhone est connecté et que le relais SMS est activé.
                    </p>
                </div>

                <div>
                    <label class="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style="color:var(--text-tertiary)">Message de test</label>
                    <textarea id="test-sms-message" rows="3"
                        class="input w-full font-mono text-sm resize-none"
                        placeholder="Test message">PH-Lending Pro test: this number is configured to receive notifications.</textarea>
                </div>

                <div class="flex gap-3 justify-end pt-2" style="border-top: 0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="ClientDetailPage._doSendTestSms('${phone.replace(/'/g, "\\'")}')"
                        class="btn btn-primary flex items-center gap-2">
                        <i data-lucide="send" class="w-4 h-4"></i>
                        Envoyer le test
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        setTimeout(() => lucide.createIcons(), 50);
    },

    async _doSendTestSms(phone) {
        const message = document.getElementById('test-sms-message')?.value?.trim();
        if (!message) {
            UI.toast('Veuillez écrire un message de test.', 'warning');
            return;
        }
        UI.closeModal();
        UI.toast('Envoi du SMS de test…', 'info');
        const result = await App.api('send_sms_via_phone', phone, message);
        if (result && result.success) {
            if (result.method === 'phone_fallback') {
                UI.toast('AppleScript unavailable. Messages opened via sms://; check your iPhone.', 'warning');
            } else {
                UI.toast(`Test SMS sent successfully to ${phone}.`, 'success');
            }
        } else {
            UI.toast('Failed: ' + (result?.error || 'Unknown error'), 'error');
        }
    },

    showRefinanceForm(clientId, activeLoanId) {
        Promise.all([
            App.api('get_loan_rollover_info', activeLoanId),
            App.api('get_settings')
        ]).then(([info, settings]) => {
            const today = new Date().toISOString().split('T')[0];
            const defaultRate = settings.default_interest_rate || '5.0';
            const defaultType = settings.default_interest_type || 'fixed';

            // ── Verrou : 3 mois minimum requis ─────────────────────
            const monthsPaid = info.months_paid || 0;
            const canRenew = info.can_renew;
            const lockBanner = !canRenew ? `
                <div class="p-3 rounded-xl mb-4 border border-red-200 dark:border-red-800/40 bg-red-50 dark:bg-red-900/15 flex items-start gap-3">
                    <i data-lucide="lock" class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"></i>
                    <div>
                        <p class="text-sm font-bold text-red-600 dark:text-red-400">Renewal not yet allowed</p>
                        <p class="text-xs text-red-500 dark:text-red-400 mt-0.5">
                            The client must have fully paid at least <strong>3 installments</strong> on the current loan before renewing.
                            Currently: <strong>${monthsPaid}</strong> installment${monthsPaid !== 1 ? 's' : ''} completed.
                            <br>${3 - monthsPaid} more installment${(3 - monthsPaid) !== 1 ? 's' : ''} needed.
                        </p>
                    </div>
                </div>` : '';

            // ── Info solde actuel ───────────────────────────────────
            const balanceBanner = `
                <div class="p-3 rounded-xl mb-4 border border-amber-200 dark:border-amber-800/30 bg-amber-50 dark:bg-amber-900/10">
                    <p class="text-xs font-bold text-amber-700 dark:text-amber-400 mb-1.5">
                        Current Loan #${activeLoanId} — Balance Summary
                    </p>
                    <div class="grid grid-cols-3 gap-2 text-center">
                        <div class="bg-white/60 dark:bg-slate-800/40 rounded-lg p-2">
                            <p class="text-[10px] text-gray-500 dark:text-slate-400 uppercase tracking-wider">Total Due</p>
                            <p class="font-bold text-sm text-gray-800 dark:text-white">${UI.formatCurrency(info.total_due)}</p>
                        </div>
                        <div class="bg-white/60 dark:bg-slate-800/40 rounded-lg p-2">
                            <p class="text-[10px] text-gray-500 dark:text-slate-400 uppercase tracking-wider">Paid</p>
                            <p class="font-bold text-sm text-green-600 dark:text-green-400">${UI.formatCurrency(info.already_paid)}</p>
                        </div>
                        <div class="bg-white/60 dark:bg-slate-800/40 rounded-lg p-2">
                            <p class="font-bold text-sm text-red-500 dark:text-red-400 uppercase tracking-wider">Still Owed</p>
                            <p class="font-bold text-sm text-red-500 dark:text-red-400">${UI.formatCurrency(info.remaining)}</p>
                        </div>
                    </div>
                    <p class="text-[10px] text-amber-600 dark:text-amber-400 mt-2">
                        <i data-lucide="info" class="w-3 h-3 inline mr-1"></i>
                        Installments fully paid: <strong>${monthsPaid}</strong> /
                        Monthly installment: <strong>${UI.formatCurrency(info.monthly_payment)}</strong>
                    </p>
                </div>`;

            UI.showModal('Loan Renewal', `
                ${lockBanner}
                ${balanceBanner}
                <form onsubmit="ClientDetailPage.submitRefinance(event, '${clientId}', ${activeLoanId})" class="space-y-4">
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">
                                New Total Credit (₱) *
                                <span class="text-[10px] text-gray-400 font-normal block">Full amount of the new loan</span>
                            </label>
                            <input name="principal" type="number" class="input" required min="${info.remaining}" step="0.01"
                                   placeholder="15000" ${!canRenew ? 'disabled' : ''}
                                   oninput="ClientDetailPage.updateRefinancePreview(this.value, ${info.remaining})">
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">
                                Term (months) *
                            </label>
                            <input name="term" type="number" class="input" required min="1" max="60" value="6" ${!canRenew ? 'disabled' : ''}
                                   oninput="ClientDetailPage.updateRefinancePreview(document.querySelector('[name=principal]')?.value, ${info.remaining})">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Interest Rate (%) *</label>
                            <input name="rate" type="number" class="input" required min="0" step="0.5" value="${defaultRate}" ${!canRenew ? 'disabled' : ''}>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Interest Type *</label>
                            <select name="interest_type" class="input select" ${!canRenew ? 'disabled' : ''}>
                                <option value="fixed" ${defaultType === 'fixed' ? 'selected' : ''}>Fixed</option>
                                <option value="declining" ${defaultType === 'declining' ? 'selected' : ''}>Declining</option>
                            </select>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Rate Duration</label>
                            <select name="rate_duration" class="input select" ${!canRenew ? 'disabled' : ''}>
                                <option value="monthly" selected>Per Month</option>
                                <option value="total">Total for entire term</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Start Date *</label>
                            <input name="start_date" type="date" class="input" value="${today}" required ${!canRenew ? 'disabled' : ''}>
                        </div>
                    </div>

                    <!-- Cash Breakdown Preview -->
                    <div id="refinance-preview" class="hidden">
                        <div class="rounded-xl overflow-hidden border border-blue-200 dark:border-blue-800/40">
                            <div class="bg-blue-500 dark:bg-blue-600 px-4 py-2">
                                <p class="text-white font-bold text-sm">Renewal Breakdown</p>
                            </div>
                            <div class="bg-blue-50 dark:bg-blue-900/10 p-4 space-y-2 text-sm" id="refinance-preview-content"></div>
                        </div>
                    </div>

                    <div class="flex gap-3 justify-end pt-2">
                        <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                        <button type="submit" class="btn btn-primary" ${!canRenew ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>
                            <i data-lucide="refresh-cw" class="w-4 h-4"></i> Create Renewal Loan
                        </button>
                    </div>
                </form>
            `, { width: 'max-w-lg' });
            setTimeout(() => lucide.createIcons(), 50);
        });
    },

    updateRefinancePreview(newCapital, remainingDebt) {
        const principal = parseFloat(newCapital || 0);
        const deduction = parseFloat(remainingDebt || 0);
        const preview = document.getElementById('refinance-preview');
        const content = document.getElementById('refinance-preview-content');
        if (!preview || !content) return;

        if (principal <= 0) {
            preview.classList.add('hidden');
            return;
        }

        const cashToClient = Math.max(0, principal - deduction);
        const insufficient = principal < deduction;
        const termInput = document.querySelector('[name="term"]');
        const term = parseInt(termInput?.value || 6);

        preview.classList.remove('hidden');
        content.innerHTML = `
            <div class="flex justify-between items-center py-1.5">
                <span class="text-gray-600 dark:text-slate-400">New loan total</span>
                <span class="font-bold text-gray-900 dark:text-white">${UI.formatCurrency(principal)}</span>
            </div>
            <div class="flex justify-between items-center py-1.5 border-t border-blue-100 dark:border-blue-800/30">
                <span class="text-gray-600 dark:text-slate-400">
                    <i data-lucide="minus-circle" class="w-3 h-3 inline mr-1 text-red-400"></i>
                    Old loan balance deducted
                </span>
                <span class="font-bold text-red-500 dark:text-red-400">- ${UI.formatCurrency(deduction)}</span>
            </div>
            <div class="flex justify-between items-center py-2 mt-1 rounded-lg px-3 border ${insufficient ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40' : 'bg-green-100 dark:bg-green-900/20 border-green-200 dark:border-green-800/40'}">
                <span class="font-bold ${insufficient ? 'text-red-600 dark:text-red-400' : 'text-green-700 dark:text-green-400'} flex items-center gap-1.5">
                    <i data-lucide="banknote" class="w-4 h-4"></i>
                    ${insufficient ? 'Credit does not cover old balance' : 'Cash to give client'}
                </span>
                <span class="font-bold text-base ${insufficient ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}">${UI.formatCurrency(cashToClient)}</span>
            </div>
            <p class="text-[10px] text-gray-400 dark:text-slate-500 mt-2 text-center">
                New loan: ${UI.formatCurrency(principal)} over ${term} month${term !== 1 ? 's' : ''}, interest applied on full amount
            </p>
        `;
        setTimeout(() => lucide.createIcons(), 20);
    },

    async submitRefinance(e, clientId, activeLoanId) {
        e.preventDefault();
        const form = e.target;

        let finalRate = parseFloat(form.rate.value);
        if (form.rate_duration.value === 'monthly') {
            finalRate = finalRate * parseInt(form.term.value);
        }

        const result = await App.api('create_loan',
            clientId,
            parseFloat(form.principal.value),
            finalRate,
            form.interest_type.value,
            parseInt(form.term.value),
            form.start_date.value,
            activeLoanId,
            true  // renewal_mode = True
        );
        if (result && result.loan_id) {
            UI.closeModal();
            UI.toast(
                `Renewal complete. Cash to client: ${UI.formatCurrency(result.cash_given_to_client)}. New loan: ${UI.formatCurrency(result.total_principal)}.`,
                'success'
            );
            App.navigate('loan_detail', { id: result.loan_id });
        } else {
            UI.toast('Error creating renewal loan: ' + (result?.error || 'Unknown'), 'error');
        }
    },

    async openPrintCenter() {
        if (!this.clientId) return;
        const client = await App.api('get_client', this.clientId);
        if (!client) return;

        let html = '<div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">';
        let itemCount = 0;

        // 1. Documents
        if (client.documents && client.documents.length > 0) {
            const pdfs = client.documents.filter(d => d.file_path && d.file_path.toLowerCase().endsWith('.pdf'));
            if (pdfs.length > 0) {
                html += '<h4 class="font-bold text-gray-800 dark:text-white border-b pb-1">Uploads (PDF)</h4><div class="space-y-2">';
                pdfs.forEach(d => {
                    const desc = d.description || d.file_type;
                    html += `
                        <label class="flex items-center gap-3 p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-800 transition">
                            <input type="checkbox" class="checkbox print-item-check" data-type="document" data-path="${d.file_path.replace(/\\/g, '\\\\')}">
                            <i data-lucide="file-text" class="w-4 h-4 text-blue-500"></i>
                            <span class="text-sm font-medium flex-1 truncate">${desc}</span>
                        </label>
                    `;
                    itemCount++;
                });
                html += '</div>';
            }
        }

        // 2. Loans & Payments (Contracts & Receipts)
        if (client.loans && client.loans.length > 0) {
            html += '<h4 class="font-bold text-gray-800 dark:text-white border-b pb-1 mt-4">Contracts & Receipts</h4><div class="space-y-2">';
            for (const loan of client.loans) {
                html += `
                    <label class="flex items-center gap-3 p-2 bg-blue-50/50 dark:bg-blue-900/10 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition">
                        <input type="checkbox" class="checkbox print-item-check" data-type="contract" data-id="${loan.id}">
                        <i data-lucide="file-signature" class="w-4 h-4 text-purple-500"></i>
                        <span class="text-sm font-bold flex-1">Contract - Loan #${loan.id} (${UI.formatCurrency(loan.principal)})</span>
                    </label>
                `;
                itemCount++;

                const loansPayments = await App.api('get_payments', loan.id);
                if (loansPayments && loansPayments.length > 0) {
                    loansPayments.forEach((p, idx) => {
                        html += `
                            <label class="flex items-center gap-3 p-1.5 ml-6 bg-green-50/30 dark:bg-green-900/10 rounded-lg cursor-pointer hover:bg-green-50 dark:hover:bg-green-900/20 transition">
                                <input type="checkbox" class="checkbox print-item-check" data-type="receipt" data-id="${p.id}">
                                <i data-lucide="receipt" class="w-3 h-3 text-emerald-500"></i>
                                <span class="text-xs font-medium flex-1">Receipt - Payment #${p.id} (${UI.formatDateShort(p.payment_date)})</span>
                            </label>
                        `;
                        itemCount++;
                    });
                }
            }
            html += '</div>';
        }

        if (itemCount === 0) {
            html += '<p class="text-sm text-gray-500 text-center py-4">No printable documents or receipts found for this client.</p>';
        }

        html += '</div>';

        html += `
            <div class="mt-4 pt-3 border-t flex justify-between gap-3 items-center">
                <button onclick="document.querySelectorAll('.print-item-check').forEach(cb => cb.checked = true)" class="btn btn-sm btn-ghost text-xs">Select All</button>
                <div class="flex gap-2">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="ClientDetailPage.submitPrint()" class="btn btn-primary" ${itemCount === 0 ? 'disabled' : ''}>
                        <i data-lucide="printer" class="w-4 h-4"></i> Print Selected
                    </button>
                </div>
            </div>
        `;

        UI.showModal('Print Center', html, { width: 'max-w-xl' });
    },

    async submitPrint() {
        const checkboxes = document.querySelectorAll('.print-item-check:checked');
        if (checkboxes.length === 0) {
            UI.toast('Please select at least one document to print', 'warning');
            return;
        }

        const items = [];
        checkboxes.forEach(cb => {
            const type = cb.getAttribute('data-type');
            if (type === 'document') {
                items.push({ type: 'document', path: cb.getAttribute('data-path') });
            } else {
                items.push({ type: type, id: parseInt(cb.getAttribute('data-id')) });
            }
        });

        UI.toast(`Sending ${items.length} documents to print queue...`, 'info');
        UI.closeModal();

        const result = await App.api('print_multiple_pdfs', items);
        if (result.success) {
            UI.toast(`Opened ${result.count} document(s) for native printing.`, 'success');
        } else {
            UI.toast('Error opening print sequence: ' + result.error, 'error');
        }
    }
};

// ─── Social Networks Config ────────────────────────────────────────────────────
ClientDetailPage._SOCIAL_NETWORKS = [
    {
        id: 'facebook',
        label: 'Facebook',
        icon: 'F',
        placeholder: 'jean.dupont',
        bg: 'rgba(24,119,242,0.12)',
        color: '#1877F2',
        urlFn: h => `https://facebook.com/${h}`
    },
    {
        id: 'messenger',
        label: 'Messenger',
        icon: 'M',
        placeholder: 'jean.dupont',
        bg: 'rgba(0,132,255,0.12)',
        color: '#0084FF',
        urlFn: h => `https://m.me/${h}`
    },
    {
        id: 'instagram',
        label: 'Instagram',
        icon: 'IG',
        placeholder: 'jean_dupont',
        bg: 'rgba(225,48,108,0.12)',
        color: '#E1306C',
        urlFn: h => `https://instagram.com/${h}`
    },
    {
        id: 'tiktok',
        label: 'TikTok',
        icon: 'TT',
        placeholder: 'jean_dupont',
        bg: 'rgba(0,0,0,0.10)',
        color: '#010101',
        urlFn: h => `https://tiktok.com/@${h}`
    },
    {
        id: 'whatsapp',
        label: 'WhatsApp',
        icon: 'WA',
        placeholder: '639171234567',
        bg: 'rgba(37,211,102,0.12)',
        color: '#25D366',
        urlFn: h => `https://wa.me/${h.replace(/[\s+\-()]/g, '')}`
    },
    {
        id: 'viber',
        label: 'Viber',
        icon: 'V',
        placeholder: '639171234567',
        bg: 'rgba(126,58,242,0.12)',
        color: '#7B519D',
        urlFn: h => `viber://chat?number=%2B${h.replace(/[\s+\-()]/g, '')}`
    },
    {
        id: 'twitter',
        label: 'X / Twitter',
        icon: 'X',
        placeholder: 'jean_dupont',
        bg: 'rgba(29,161,242,0.12)',
        color: '#1DA1F2',
        urlFn: h => `https://x.com/${h}`
    },
    {
        id: 'linkedin',
        label: 'LinkedIn',
        icon: 'in',
        placeholder: 'jean-dupont',
        bg: 'rgba(10,102,194,0.12)',
        color: '#0A66C2',
        urlFn: h => `https://linkedin.com/in/${h}`
    },
];

ClientDetailPage._addSocialRow = function (networkId = '', handle = '') {
    const container = document.getElementById('social-media-rows');
    if (!container) return;
    const rowId = 'social-row-' + Date.now() + Math.floor(Math.random() * 1000);
    const options = ClientDetailPage._SOCIAL_NETWORKS.map(n =>
        `<option value="${n.id}" ${n.id === networkId ? 'selected' : ''}>${n.icon} ${n.label}</option>`
    ).join('');
    const net = ClientDetailPage._SOCIAL_NETWORKS.find(n => n.id === networkId);
    const placeholder = net ? net.placeholder : 'Identifiant...';
    const div = document.createElement('div');
    div.className = 'social-row flex items-center gap-2';
    div.id = rowId;
    div.innerHTML = `
        <select class="social-network-select input select flex-shrink-0 text-xs" style="max-width:140px;"
                onchange="ClientDetailPage._updateSocialPlaceholder(this)">
            ${options}
        </select>
        <input class="social-handle-input input flex-1 text-sm" type="text"
               value="${handle.replace(/"/g, '&quot;')}"
               placeholder="${placeholder}">
        <button type="button" onclick="document.getElementById('${rowId}').remove()"
            class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 transition">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;
    container.appendChild(div);
    setTimeout(() => lucide.createIcons(), 20);
};

ClientDetailPage._updateSocialPlaceholder = function (select) {
    const net = ClientDetailPage._SOCIAL_NETWORKS.find(n => n.id === select.value);
    const input = select.closest('.social-row')?.querySelector('.social-handle-input');
    if (input && net) input.placeholder = net.placeholder;
};

ClientDetailPage.openSocialLink = async function (url) {
    if (!url) return;
    // Viber uses a custom scheme — open directly
    if (url.startsWith('viber://')) {
        await App.api('open_file', url);
        return;
    }
    const result = await App.api('open_url', url);
    if (!result || !result.success) {
        UI.toast('Cannot open link: ' + (result?.error || ''), 'error');
    }
};
