/**
 * PH-Lending Pro — Settings Page
 * Company settings with logo, loan defaults, export, backup, and Google Drive sync.
 */
const SettingsPage = {
    async render() {
        const content = document.getElementById('page-content');
        const settings = await App.api('get_settings');
        const backupInfo = await App.api('get_backup_info');
        const backups = await App.api('get_backups_list');
        const driveSetup = await App.api('is_drive_setup');
        const appInfo = await App.api('get_app_info');
        const logo = await App.api('get_logo_base64');
        const profiles = await App.api('get_profiles');
        const activeProfile = profiles.find(p => p.is_active) || profiles[0];

        content.innerHTML = `
            <div class="max-w-3xl mx-auto space-y-6">

                <!-- ═══ Profiles ═══ -->
                <div class="glass-card p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-base font-semibold flex items-center gap-2" style="color:var(--text-primary)">
                            <i data-lucide="users-round" class="w-4 h-4" style="color:var(--accent)"></i> Profiles
                        </h3>
                        <button onclick="SettingsPage.showCreateProfileModal()" class="btn btn-primary btn-sm">
                            <i data-lucide="plus" class="w-3.5 h-3.5"></i> New Profile
                        </button>
                    </div>

                    <!-- Active profile badge -->
                    <div class="flex items-center gap-3 mb-4 px-4 py-3 rounded-xl" style="background:var(--surface-2); border:0.5px solid var(--surface-1);">
                        <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                             style="background:${activeProfile.color || 'var(--accent)'}20;">
                            <i data-lucide="shield-check" class="w-5 h-5" style="color:${activeProfile.color || 'var(--accent)'}"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-semibold truncate" style="color:var(--text-primary)">${activeProfile.name}</p>
                            <p class="text-xs" style="color:var(--text-tertiary)">${activeProfile.description || 'Active profile'} · ${activeProfile.client_count || 0} clients · ${activeProfile.loan_count || 0} loans</p>
                        </div>
                        <span class="text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider"
                              style="background:rgba(52,199,89,0.12); color:#1A8F3A;">ACTIVE</span>
                    </div>

                    <!-- Profile list -->
                    <div class="rounded-xl overflow-hidden" style="border:0.5px solid var(--surface-2);" id="profiles-list">
                        ${profiles.map((p, i) => `
                            <div class="flex items-center gap-3 px-4 py-3 ${i < profiles.length - 1 ? '' : ''}"
                                 style="background:var(--surface-0); ${i < profiles.length - 1 ? 'border-bottom:0.5px solid var(--surface-2);' : ''}">
                                <div class="w-3 h-3 rounded-full flex-shrink-0" style="background:${p.color || '#007AFF'}"></div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm font-medium truncate" style="color:var(--text-primary)">${p.name}</p>
                                    <p class="text-[11px]" style="color:var(--text-tertiary)">
                                        ${p.client_count || 0} clients · ${p.loan_count || 0} loans · ${p.size ? (p.size / 1024).toFixed(0) + ' KB' : '—'}
                                    </p>
                                </div>
                                <div class="flex items-center gap-1.5">
                                    ${p.is_active ? `
                                        <span class="text-[10px] px-1.5 py-0.5 rounded font-semibold"
                                              style="background:rgba(52,199,89,0.12); color:#1A8F3A;">✓</span>
                                    ` : `
                                        <button onclick="SettingsPage.switchProfile('${p.id}')" class="btn btn-ghost btn-sm text-xs" title="Switch to this profile">
                                            <i data-lucide="arrow-right-left" class="w-3 h-3"></i> Switch
                                        </button>
                                    `}
                                    <button onclick="SettingsPage.showEditProfileModal('${p.id}')" class="btn btn-icon btn-ghost btn-sm" title="Edit">
                                        <i data-lucide="pencil" class="w-3 h-3" style="color:var(--text-tertiary)"></i>
                                    </button>
                                    ${p.id !== 'default' ? `
                                        <button onclick="SettingsPage.deleteProfile('${p.id}', '${p.name.replace(/'/g, "\\'")}')" class="btn btn-icon btn-ghost btn-sm" title="Delete">
                                            <i data-lucide="trash-2" class="w-3 h-3" style="color:var(--apple-red)"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Security & Reset -->
                    <div class="mt-4 pt-3 space-y-3" style="border-top:0.5px solid var(--surface-2);">

                        <!-- Password toggle row -->
                        <div class="rounded-xl overflow-hidden" style="border:0.5px solid var(--surface-2);">
                            <div class="flex items-center justify-between px-4 py-3" style="background:var(--surface-0);">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                                         style="background:linear-gradient(135deg,#FF9500,#FF6B00);">
                                        <i data-lucide="lock" class="w-4 h-4 text-white"></i>
                                    </div>
                                    <div>
                                        <p class="text-sm font-medium" style="color:var(--text-primary)">Password Protection</p>
                                        <p class="text-xs" style="color:var(--text-tertiary)">Require password for reset, delete & switch</p>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button onclick="SettingsPage.showPasswordSetup()" class="btn btn-ghost btn-sm" title="Configure password"
                                            id="password-config-btn" style="display:none">
                                        <i data-lucide="settings" class="w-3.5 h-3.5" style="color:var(--accent)"></i>
                                    </button>
                                    <label class="apple-toggle">
                                        <input type="checkbox" id="password-toggle" onchange="SettingsPage.togglePassword(this.checked)">
                                        <div class="apple-toggle-track"></div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Reset button -->
                        <button onclick="SettingsPage.resetProfileData()" class="btn btn-sm flex items-center gap-1.5"
                                style="background:rgba(255,59,48,0.08); color:var(--apple-red); border:1px solid rgba(255,59,48,0.2);">
                            <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                            Reset Current Profile (erase all data)
                        </button>
                        <p class="text-[11px]" style="color:var(--text-tertiary)">
                            ⚠️ Permanently deletes all data in <strong>${activeProfile.name}</strong>. Backup auto-created. You must type <code style="background:var(--surface-2); padding:1px 4px; border-radius:4px;">RESET</code> to confirm.
                        </p>
                    </div>
                </div>

                <!-- Company Settings + Logo -->
                <div class="glass-card p-6">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                        <i data-lucide="building-2" class="w-5 h-5 text-blue-500"></i> Company Settings
                    </h3>
                    <form id="company-form" onsubmit="SettingsPage.saveCompany(event)" class="space-y-4">
                        <!-- Logo Upload -->
                        <div class="flex items-start gap-5 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl">
                            ${(() => {
                const sz = localStorage.getItem('ph-logo-size') || 'M';
                const sizes = { S: 'w-20 h-20', M: 'w-28 h-28', L: 'w-36 h-36' };
                const cls = sizes[sz] || sizes.M;
                return `
                                <div id="logo-preview-container"
                                     class="${cls} rounded-2xl border-2 border-dashed border-gray-300 dark:border-slate-600
                                            flex items-center justify-center overflow-hidden cursor-pointer
                                            hover:border-blue-400 transition flex-shrink-0"
                                     onclick="document.getElementById('logo-input').click()" >
                                    ${logo
                        ? `<img src="${logo}" class="w-full h-full object-cover rounded-2xl" id="logo-preview">`
                        : `<i data-lucide="image-plus" class="w-8 h-8 text-gray-400" id="logo-placeholder"></i>`
                    }
                                </div>`;
            })()}
                            <div class="min-w-0 flex-1">
                                <p class="font-semibold text-sm text-gray-700 dark:text-slate-300 mb-1">Company Logo</p>
                                <p class="text-xs text-gray-400 dark:text-slate-500 mb-3">Fills the square — use a square image for best results. Appears in sidebar and PDFs.</p>
                                <!-- Size picker -->
                                <div class="flex items-center gap-2 mb-3">
                                    <span class="text-xs text-gray-500 dark:text-slate-400 font-medium">Size:</span>
                                    ${['S', 'M', 'L'].map(s => `
                                        <button type="button" id="logo-size-${s}"
                                            onclick="SettingsPage.setLogoSize('${s}')"
                                            class="w-7 h-7 rounded-lg text-xs font-bold transition border-2
                                                ${(localStorage.getItem('ph-logo-size') || 'M') === s
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white dark:bg-slate-800 text-gray-500 border-gray-200 dark:border-slate-600 hover:border-blue-400'}">${s}</button>
                                    `).join('')}
                                </div>
                                <input type="file" id="logo-input" class="hidden" accept="image/*" onchange="SettingsPage.uploadLogo(event)">
                                <button type="button" onclick="document.getElementById('logo-input').click()" class="btn btn-ghost btn-sm">
                                    <i data-lucide="upload" class="w-3 h-3"></i> Upload Logo
                                </button>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Company Name</label>
                                <input name="company_name" class="input" value="${settings.company_name || 'PH-Lending Pro'}">
                            </div>
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Phone Number</label>
                                <div class="flex rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-400 transition">
                                    <span class="flex items-center px-3 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 font-semibold text-sm border-r border-gray-200 dark:border-slate-600 select-none flex-shrink-0">
                                        🇵🇭 +63
                                    </span>
                                    <input name="company_phone"
                                           type="tel"
                                           inputmode="numeric"
                                           class="flex-1 px-3 py-2 bg-transparent text-gray-800 dark:text-white text-sm outline-none placeholder-gray-400"
                                           placeholder="912 345 6789"
                                           value="${(settings.company_phone || '').replace(/^\+63\s?/, '')}">
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Email / Contact</label>
                                <input name="company_contact" class="input" placeholder="info@lending.com" value="${settings.company_contact || ''}">
                            </div>
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Address</label>
                                <input name="company_address" class="input" value="${settings.company_address || ''}">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary btn-sm"><i data-lucide="save" class="w-4 h-4"></i> Save Company Info</button>
                    </form>
                </div>

                <!-- Loan Defaults & Commission -->
                <div class="glass-card p-6">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                        <i data-lucide="sliders" class="w-5 h-5 text-purple-500"></i> Loan Defaults & Commission
                    </h3>
                    <form id="defaults-form" onsubmit="SettingsPage.saveLoanDefaults(event)" class="space-y-4">
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Default Interest Rate (%)</label>
                                <input name="default_interest_rate" type="number" class="input" step="0.1" min="0" 
                                       value="${settings.default_interest_rate || '5.0'}">
                            </div>
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Interest Type</label>
                                <select name="default_interest_type" class="input select">
                                    <option value="fixed" ${settings.default_interest_type === 'fixed' ? 'selected' : ''}>Fixed</option>
                                    <option value="declining" ${settings.default_interest_type === 'declining' ? 'selected' : ''}>Declining</option>
                                </select>
                            </div>
                            <div>
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Commission Type</label>
                                <select name="commission_type" class="input select" onchange="SettingsPage.toggleCommissionField(this.value)">
                                    <option value="percentage" ${(settings.commission_type || 'percentage') === 'percentage' ? 'selected' : ''}>% of Principal</option>
                                    <option value="fixed_amount" ${settings.commission_type === 'fixed_amount' ? 'selected' : ''}>Fixed Amount (₱)</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div id="commission-rate-field" class="${settings.commission_type === 'fixed_amount' ? 'hidden' : ''}">
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Commission Rate (%)</label>
                                <input name="commission_rate" type="number" class="input" step="0.1" min="0" 
                                       value="${settings.commission_rate || '2.0'}">
                            </div>
                            <div id="commission-amount-field" class="${settings.commission_type !== 'fixed_amount' ? 'hidden' : ''}">
                                <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Commission Amount (₱)</label>
                                <input name="commission_amount" type="number" class="input" step="100" min="0" 
                                       value="${settings.commission_amount || '500'}">
                            </div>
                        </div>

                        <!-- Referral Bonus -->
                        <div class="p-4 rounded-xl border border-dashed border-amber-200 dark:border-amber-800/40 bg-amber-50/40 dark:bg-amber-900/10">
                            <div class="flex items-center justify-between mb-3">
                                <div class="flex items-center gap-2">
                                    <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:linear-gradient(135deg,#FF9500,#FF6B00);">
                                        <i data-lucide="gift" class="w-4 h-4 text-white"></i>
                                    </div>
                                    <div>
                                        <p class="text-sm font-semibold text-gray-800 dark:text-white">Referral Bonus (₱)</p>
                                        <p class="text-xs text-gray-400 dark:text-slate-500">Bonus given to a client who refers a new borrower</p>
                                    </div>
                                </div>
                                <label class="apple-toggle">
                                    <input type="checkbox" name="referral_bonus_enabled" id="referral-bonus-toggle"
                                           ${settings.referral_bonus_enabled === 'true' ? 'checked' : ''}
                                           onchange="SettingsPage.toggleReferralBonus(this.checked)">
                                    <div class="apple-toggle-track"></div>
                                </label>
                            </div>
                            <div id="referral-bonus-fields" class="${settings.referral_bonus_enabled === 'true' ? '' : 'hidden'} space-y-3">
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div>
                                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">Bonus Amount (₱)</label>
                                        <div class="flex rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-amber-400/40 transition">
                                            <span class="flex items-center px-3 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 font-semibold text-sm border-r border-gray-200 dark:border-slate-600 flex-shrink-0">
                                                ₱
                                            </span>
                                            <input name="referral_bonus_amount" type="number" class="flex-1 px-3 py-2 bg-transparent text-gray-800 dark:text-white text-sm outline-none" 
                                                   step="50" min="0" placeholder="500"
                                                   value="${settings.referral_bonus_amount || '500'}">
                                        </div>
                                    </div>
                                    <div>
                                        <label class="text-sm font-medium text-gray-600 dark:text-slate-400 mb-1 block">When to Pay Bonus</label>
                                        <select name="referral_bonus_trigger" class="input select">
                                            <option value="on_loan_creation" ${(settings.referral_bonus_trigger || 'on_loan_creation') === 'on_loan_creation' ? 'selected' : ''}>When new loan is created</option>
                                            <option value="on_first_payment" ${settings.referral_bonus_trigger === 'on_first_payment' ? 'selected' : ''}>After 1st payment of new loan</option>
                                            <option value="on_loan_completion" ${settings.referral_bonus_trigger === 'on_loan_completion' ? 'selected' : ''}>When new loan is fully paid</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="p-2.5 rounded-lg bg-amber-100/60 dark:bg-amber-900/20 text-xs text-amber-700 dark:text-amber-300">
                                    <i data-lucide="info" class="w-3.5 h-3.5 inline mr-1"></i>
                                    The referral commission system records this bonus in the <strong>Commissions</strong> tab automatically when the trigger condition is met.
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary btn-sm"><i data-lucide="save" class="w-4 h-4"></i> Save Defaults</button>
                    </form>
                </div>

                <!-- SMS Configuration -->
                <div class="glass-card p-6">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-1 flex items-center gap-2">
                        <i data-lucide="message-square" class="w-5 h-5 text-green-500"></i> SMS & Alerts
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-slate-400 mb-4">
                        Configure automatic SMS sending to overdue clients.
                        Uses the <strong>iPhone connected to the Mac</strong> (Apple Continuity) or an <strong>SMS API</strong>.
                    </p>

                    <!-- Provider tabs -->
                    <div class="rounded-xl overflow-hidden mb-4" style="border: 0.5px solid var(--surface-2);">
                        <!-- iPhone (no config needed) -->
                        <div class="flex items-center gap-3 px-4 py-3" style="background:var(--surface-0); border-bottom: 0.5px solid var(--surface-2);">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                                 style="background: linear-gradient(135deg,#34C759,#30B0C7);">
                                <i data-lucide="smartphone" class="w-4 h-4 text-white"></i>
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-medium" style="color:var(--text-primary)">iPhone (Apple Continuity)</p>
                                <p class="text-xs" style="color:var(--text-tertiary)">Opens Messages.app with a pre-filled message. Requires iPhone + Mac on the same Apple ID with SMS Relay enabled.</p>
                            </div>
                            <span class="text-xs px-2 py-1 rounded-full font-semibold"
                                  style="background: rgba(52,199,89,0.12); color: #1A8F3A;">No setup needed</span>
                        </div>

                        <!-- API config -->
                        <div class="px-4 py-3" style="background:var(--surface-0);">
                            <div class="flex items-center gap-3 mb-3">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                                     style="background: linear-gradient(135deg,#007AFF,#5856D6);">
                                    <i data-lucide="globe" class="w-4 h-4 text-white"></i>
                                </div>
                                <div>
                                    <p class="text-sm font-medium" style="color:var(--text-primary)">SMS API (Semaphore / Twilio)</p>
                                    <p class="text-xs" style="color:var(--text-tertiary)">Direct send without manual steps. Requires an account with the provider.</p>
                                </div>
                            </div>
                            <form id="sms-api-form" onsubmit="SettingsPage.saveSmsConfig(event)" class="space-y-3">
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div>
                                        <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Provider</label>
                                        <select name="sms_provider" class="input select" onchange="SettingsPage.toggleSmsProviderFields(this.value)">
                                            <option value="semaphore" ${(settings.sms_provider || 'semaphore') === 'semaphore' ? 'selected' : ''}>
                                                Semaphore (Philippines)
                                            </option>
                                            <option value="twilio" ${settings.sms_provider === 'twilio' ? 'selected' : ''}>
                                                Twilio (International)
                                            </option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Sender ID / Sender Name</label>
                                        <input name="sms_sender_id" class="input" placeholder="LENDING" value="${settings.sms_sender_id || ''}">
                                    </div>
                                </div>
                                <div>
                                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">API Key</label>
                                    <input name="sms_api_key" type="password" class="input font-mono" placeholder="Your API key" value="${settings.sms_api_key || ''}">
                                </div>
                                <div id="twilio-fields" class="${settings.sms_provider === 'twilio' ? '' : 'hidden'} space-y-3">
                                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        <div>
                                            <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Account SID (Twilio)</label>
                                            <input name="sms_account_sid" class="input font-mono text-xs" placeholder="ACxxxxxxxx" value="${settings.sms_account_sid || ''}">
                                        </div>
                                        <div>
                                            <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">From Number (Twilio)</label>
                                            <input name="sms_from_number" class="input font-mono" placeholder="+1XXXXXXXXXX" value="${settings.sms_from_number || ''}">
                                        </div>
                                    </div>
                                </div>
                                <div class="flex items-center gap-3 pt-1">
                                    <button type="submit" class="btn btn-primary btn-sm">
                                        <i data-lucide="save" class="w-3.5 h-3.5"></i> Save SMS API
                                    </button>
                                    <a href="https://semaphore.co" target="_blank"
                                       class="text-xs text-blue-500 hover:underline">Semaphore →</a>
                                    <a href="https://twilio.com" target="_blank"
                                       class="text-xs text-blue-500 hover:underline">Twilio →</a>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- SMS Templates -->
                    <div>
                        <div class="flex items-center justify-between mb-3">
                            <p class="text-sm font-semibold" style="color:var(--text-primary)">
                                <i data-lucide="file-text" class="w-4 h-4 inline-block mr-1 opacity-60"></i>
                                Message Templates
                            </p>
                            <button onclick="SettingsPage.addSmsTemplate()" class="btn btn-ghost btn-sm">
                                <i data-lucide="plus" class="w-3.5 h-3.5"></i> Add
                            </button>
                        </div>
                        <p class="text-xs mb-3" style="color:var(--text-tertiary)">
                            Available variables:
                            <code class="px-1 rounded" style="background:var(--surface-2)">{name}</code>
                            <code class="px-1 rounded" style="background:var(--surface-2)">{amount}</code>
                            <code class="px-1 rounded" style="background:var(--surface-2)">{date}</code>
                            <code class="px-1 rounded" style="background:var(--surface-2)">{days}</code>
                            <code class="px-1 rounded" style="background:var(--surface-2)">{company}</code>
                            <code class="px-1 rounded" style="background:var(--surface-2)">{phone}</code>
                        </p>
                        <div id="sms-templates-list" class="space-y-3">
                            ${await SettingsPage._renderTemplates()}
                        </div>
                    </div>
                </div>

                <!-- Export -->
                <div class="glass-card p-6">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-2 flex items-center gap-2">
                        <i data-lucide="download" class="w-5 h-5 text-green-500"></i> Export Data
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-slate-400 mb-4">Choose which data to export. Always includes a Summary sheet with KPIs.</p>
                    <div class="flex flex-wrap gap-3">
                        <button onclick="SettingsPage.showExportModal()" class="btn btn-success">
                            <i data-lucide="file-spreadsheet" class="w-4 h-4"></i> Choose & Export (.xlsx)
                        </button>
                        <button onclick="App.api('open_excel_dir')" class="btn btn-ghost" title="Open exports folder in Finder">
                            <i data-lucide="folder-open" class="w-4 h-4"></i> Open Exports Folder
                        </button>
                        <button onclick="App.api('open_pdf_dir')" class="btn btn-ghost" title="Open PDFs folder in Finder">
                            <i data-lucide="folder-open" class="w-4 h-4"></i> Open PDF Folder
                        </button>
                    </div>
                </div>

                <!-- Backup -->
                <div class="glass-card p-6">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                        <i data-lucide="hard-drive" class="w-5 h-5 text-amber-500"></i> Backup & Sync
                    </h3>
                    
                    <div class="flex items-center gap-4 mb-4 p-3 rounded-xl ${backupInfo.online ? 'bg-green-50 dark:bg-green-900/10' : 'bg-amber-50 dark:bg-amber-900/10'}">
                        <div class="w-3 h-3 rounded-full ${backupInfo.online ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}"></div>
                        <span class="text-sm font-medium ${backupInfo.online ? 'text-green-700 dark:text-green-400' : 'text-amber-700 dark:text-amber-400'}">
                            ${backupInfo.online ? 'Online — Cloud sync available' : 'Offline — Local backup only'}
                        </span>
                    </div>

                    ${backupInfo.last_backup ? `
                        <p class="text-xs text-gray-400 dark:text-slate-500 mb-4">Last backup: ${backupInfo.last_backup}</p>
                    ` : ''}

                    <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
                        <button onclick="SettingsPage.backupLocal()" class="btn btn-primary">
                            <i data-lucide="save" class="w-4 h-4"></i> Local Backup
                        </button>
                        <button onclick="SettingsPage.syncDrive()" class="btn ${driveSetup ? 'btn-success' : 'btn-ghost'}">
                            <i data-lucide="cloud-upload" class="w-4 h-4"></i> Sync to Drive
                        </button>
                        <button onclick="SettingsPage.showRestoreModal()" class="btn btn-ghost" ${backups.length === 0 ? 'disabled title="No backup available"' : ''}>
                            <i data-lucide="rotate-ccw" class="w-4 h-4"></i> Restore
                        </button>
                        <button onclick="SettingsPage.openDrive()" class="btn btn-ghost">
                            <i data-lucide="external-link" class="w-4 h-4"></i> ${driveSetup ? 'Open Drive' : 'Setup Drive'}
                        </button>
                    </div>

                    <p class="text-xs text-gray-400 dark:text-slate-500 mt-3">
                        Local backup creates 3 copies: .db (SQLite), .xlsx (Excel), .json (Raw Data)
                    </p>
                    ${!driveSetup ? `
                        <div class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/10 rounded-xl flex items-start gap-3">
                            <i data-lucide="info" class="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5"></i>
                            <div>
                                <p class="text-xs text-blue-600 dark:text-blue-400">
                                    <strong>Google Drive Setup:</strong> Place your <code class="bg-blue-100 dark:bg-blue-800/30 px-1 rounded">google_credentials.json</code> file in the app data folder to enable cloud sync.
                                </p>
                                <button onclick="App.api('open_data_dir')" class="mt-2 btn btn-ghost btn-sm text-blue-600 dark:text-blue-400">
                                    <i data-lucide="folder-open" class="w-3 h-3"></i> Open Data Folder
                                </button>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <!-- Appearance / Color Themes — Apple style -->
                <div class="glass-card p-6">
                    <h3 class="text-base font-semibold flex items-center gap-2 mb-5" style="color:var(--text-primary)">
                        <i data-lucide="paintbrush-2" class="w-4 h-4" style="color:var(--accent)"></i> Appearance
                    </h3>

                    <!-- Settings rows — Apple list style -->
                    <div class="rounded-xl overflow-hidden" style="border: 0.5px solid var(--surface-2);">

                        <!-- Dark / Light mode row -->
                        <div class="flex items-center justify-between px-4 py-3" style="background:var(--surface-0); border-bottom: 0.5px solid var(--surface-2);">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg,#636366,#48484A);">
                                    <i data-lucide="moon" class="w-4 h-4 text-white"></i>
                                </div>
                                <div>
                                    <p class="text-sm font-medium" style="color:var(--text-primary)">Dark Mode</p>
                                    <p class="text-xs" style="color:var(--text-tertiary)">Toggle interface appearance</p>
                                </div>
                            </div>
                            <label class="apple-toggle">
                                <input type="checkbox" ${App.darkMode ? 'checked' : ''} onchange="App.toggleTheme()">
                                <div class="apple-toggle-track"></div>
                            </label>
                        </div>

                        <!-- UI Sounds row -->
                        <div class="flex items-center justify-between px-4 py-3" style="background:var(--surface-0);">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 70%,purple));">
                                    <i data-lucide="volume-2" class="w-4 h-4 text-white"></i>
                                </div>
                                <div>
                                    <p class="text-sm font-medium" style="color:var(--text-primary)">UI Sounds &amp; Effects</p>
                                    <p class="text-xs" style="color:var(--text-tertiary)">Tactile audio feedback on interactions</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                <button onclick="SettingsPage.previewSound()" class="btn btn-ghost btn-sm" title="Play preview">
                                    <i data-lucide="play-circle" class="w-4 h-4" style="color:var(--accent)"></i>
                                </button>
                                <label class="apple-toggle">
                                    <input type="checkbox" id="sounds-toggle"
                                        ${localStorage.getItem('ph-sounds-enabled') !== 'false' ? 'checked' : ''}
                                        onchange="SettingsPage.toggleSounds(this.checked)">
                                    <div class="apple-toggle-track"></div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- Accent Color -->
                    <div class="mt-5">
                        <p class="text-xs font-semibold uppercase tracking-wider mb-3" style="color:var(--text-tertiary)">Accent Color</p>
                        <div class="flex items-center gap-3 flex-wrap">
                            ${[
                { name: 'blue', color: '#007AFF', appleColor: '#007AFF', label: 'Blue' },
                { name: 'purple', color: '#AF52DE', appleColor: '#AF52DE', label: 'Purple' },
                { name: 'emerald', color: '#34C759', appleColor: '#34C759', label: 'Green' },
                { name: 'rose', color: '#FF375F', appleColor: '#FF375F', label: 'Pink' },
                { name: 'amber', color: '#FF9500', appleColor: '#FF9500', label: 'Orange' },
            ].map(t => `
                                <button class="theme-swatch ${App.currentTheme === t.name ? 'active' : ''}"
                                        data-theme="${t.name}" title="${t.label}"
                                        style="background:${t.appleColor}; color:${t.appleColor};"
                                        onclick="App.applyColorTheme('${t.name}'); SoundEngine.toggle();">
                                </button>
                            `).join('')}
                        </div>
                        <div class="flex flex-wrap gap-2 mt-3">
                            ${[
                { name: 'blue', label: 'Blue' }, { name: 'purple', label: 'Purple' },
                { name: 'emerald', label: 'Green' }, { name: 'rose', label: 'Pink' }, { name: 'amber', label: 'Orange' }
            ].map(t => `
                                <button class="btn btn-sm ${App.currentTheme === t.name ? 'btn-primary' : 'btn-ghost'}"
                                        onclick="App.applyColorTheme('${t.name}'); SoundEngine.toggle();">${t.label}</button>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- App Info & Demo Mode -->
                <div class="glass-card p-6 border border-gray-100 dark:border-slate-800">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                            <i data-lucide="info" class="w-5 h-5 text-gray-500"></i> Application Info
                        </h3>
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-semibold text-gray-600 dark:text-slate-400">Demo Mode</span>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" class="sr-only peer" ${App.isDemoMode ? 'checked' : ''} onchange="SettingsPage.toggleDemo(this.checked)">
                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-amber-500"></div>
                            </label>
                        </div>
                    </div>
                    ${App.isDemoMode ? `
                    <div class="mb-4 p-3 rounded-xl border" style="background:rgba(255,149,0,0.06); border-color:rgba(255,149,0,0.25);">
                        <p class="text-xs font-bold mb-2" style="color:#FF9500;">⚠️ Demo Mode Active — test data only</p>
                        <div class="flex flex-wrap gap-2">
                            <button onclick="SettingsPage.resetDemoData()"
                                class="btn btn-sm flex items-center gap-1.5"
                                style="background:linear-gradient(135deg,#FF9500,#FF6B00); color:white;">
                                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                                Regenerate Demo Data
                            </button>
                            <button onclick="SettingsPage.toggleDemo(false)"
                                class="btn btn-sm btn-ghost">
                                Disable Demo
                            </button>
                        </div>
                    </div>` : ''}
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Version</span><span class="font-mono">${appInfo.version}</span></div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-500 dark:text-slate-400">Data Directory</span>
                            <button onclick="App.api('open_data_dir')" class="flex items-center gap-1 text-blue-600 dark:text-blue-400 text-xs hover:underline">
                                <i data-lucide="folder-open" class="w-3 h-3"></i> Open
                            </button>
                        </div>
                        <div class="flex justify-between"><span class="text-gray-500 dark:text-slate-400">Database</span><span class="font-mono text-xs truncate max-w-[200px]">${appInfo.db_path}</span></div>
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();

        // Init password toggle state
        App.api('is_password_protected').then(enabled => {
            const toggle = document.getElementById('password-toggle');
            const configBtn = document.getElementById('password-config-btn');
            if (toggle) toggle.checked = enabled;
            if (configBtn) configBtn.style.display = enabled ? '' : 'none';
        });

        // Attach AutoSave
        AutoSave.attach(document.getElementById('company-form'), async () => {
            const form = document.getElementById('company-form');
            await App.api('save_settings', {
                company_name: form.company_name.value,
                company_contact: form.company_contact.value,
                company_address: form.company_address.value
            });
            const nameEl = document.getElementById('sidebar-company-name');
            if (nameEl) nameEl.textContent = form.company_name.value || 'PH-Lending';
        });

        AutoSave.attach(document.getElementById('defaults-form'), async () => {
            const form = document.getElementById('defaults-form');
            await App.api('save_settings', {
                default_interest_rate: form.default_interest_rate.value,
                default_interest_type: form.default_interest_type.value,
                commission_type: form.commission_type.value,
                commission_rate: form.commission_rate.value,
                commission_amount: form.commission_amount.value,
                referral_bonus_enabled: String(form.referral_bonus_enabled?.checked || false),
                referral_bonus_amount: form.referral_bonus_amount?.value || '500',
                referral_bonus_trigger: form.referral_bonus_trigger?.value || 'on_loan_creation'
            });
        });
    },

    async toggleDemo(enabled) {
        if (enabled) {
            UI.toast('Activating Demo Mode, generating data...', 'info');
        }
        await App.api('toggle_demo_mode', enabled);
        App.isDemoMode = enabled;
        App.updateDemoBadge();
        App.navigate('dashboard');
        UI.toast(enabled ? 'Demo Mode Activated' : 'Demo Mode Disabled', 'success');
    },

    async resetDemoData() {
        UI.confirm(
            '🔄 Regenerate demo data?\n\nAll current demo data will be erased and replaced with new scenarios including overdue clients (4 severity levels).',
            async () => {
                // Show loading toast
                UI.toast('Regenerating demo data…', 'info');

                // Disable the button while loading
                const btn = document.querySelector('[onclick="SettingsPage.resetDemoData()"]');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> In progress…';
                    lucide.createIcons({ nodes: [btn] });
                }

                const result = await App.api('reset_demo_data');

                if (result.success) {
                    // Refresh the alert badge
                    await App.refreshAlertsBadge();
                    // Navigate to alerts to see the result
                    UI.toast('✅ Demo data regenerated! 10 overdue clients created.', 'success');
                    SoundEngine.success();
                    setTimeout(() => App.navigate('alerts'), 600);
                } else {
                    UI.toast('❌ Error: ' + (result.error || 'Unknown'), 'error');
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = '<i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Regenerate Demo Data';
                        lucide.createIcons({ nodes: [btn] });
                    }
                }
            }
        );
    },

    toggleCommissionField(type) {
        document.getElementById('commission-rate-field').classList.toggle('hidden', type === 'fixed_amount');
        document.getElementById('commission-amount-field').classList.toggle('hidden', type !== 'fixed_amount');
    },

    toggleReferralBonus(enabled) {
        const fields = document.getElementById('referral-bonus-fields');
        if (fields) fields.classList.toggle('hidden', !enabled);
        // Auto-save immediately
        const form = document.getElementById('defaults-form');
        if (form) App.api('save_settings', { referral_bonus_enabled: String(enabled) });
    },

    async uploadLogo(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async () => {
            const result = await App.api('save_logo', reader.result);
            if (result.success) {
                UI.toast('Logo uploaded! It will appear in the sidebar.', 'success');
                App.loadLogo();
                // Update preview with object-cover
                const container = document.getElementById('logo-preview-container');
                if (container) container.innerHTML = `<img src="${reader.result}" class="w-full h-full object-cover rounded-2xl">`;
            } else {
                UI.toast('Logo upload failed: ' + result.error, 'error');
            }
        };
        reader.readAsDataURL(file);
    },

    async saveCompany(e) {
        e.preventDefault();
        const form = e.target;
        const rawPhone = form.company_phone.value.trim().replace(/^\+63\s?/, '');
        await App.api('save_settings', {
            company_name: form.company_name.value,
            company_phone: rawPhone ? '+63 ' + rawPhone : '',
            company_contact: form.company_contact.value,
            company_address: form.company_address.value
        });
        // Update sidebar company name immediately
        const nameEl = document.getElementById('sidebar-company-name');
        if (nameEl) nameEl.textContent = form.company_name.value || 'PH-Lending';
        UI.toast('Company settings saved!', 'success');
    },

    async saveLoanDefaults(e) {
        e.preventDefault();
        const form = e.target;
        await App.api('save_settings', {
            default_interest_rate: form.default_interest_rate.value,
            default_interest_type: form.default_interest_type.value,
            commission_type: form.commission_type.value,
            commission_rate: form.commission_rate.value,
            commission_amount: form.commission_amount.value
        });
        UI.toast('Loan defaults saved!', 'success');
    },

    async exportExcel() {
        UI.toast('Generating Excel file…', 'info');
        const result = await App.api('export_excel');
        if (result.success) {
            UI.toast('Excel exported and opened! ✓', 'success');
        } else {
            UI.toast('Export failed: ' + result.error, 'error');
        }
    },

    showExportModal() {
        const allSheets = [
            { id: 'clients', label: 'Clients', icon: 'users', desc: 'All client profiles (name, contact, income, referrals)' },
            { id: 'loans', label: 'Loans', icon: 'banknote', desc: 'All loans with principal, interest, remaining balance' },
            { id: 'payments', label: 'Payments', icon: 'receipt', desc: 'All payment transactions' },
            { id: 'amortization', label: 'Amortization Schedule', icon: 'calendar-range', desc: 'Monthly schedule for every loan' },
            { id: 'penalties', label: 'Penalties', icon: 'alert-circle', desc: 'All penalties (pending + resolved)' },
            { id: 'commissions', label: 'Commissions', icon: 'gift', desc: 'Referral commission records' },
        ];

        UI.showModal('Export to Excel', `
            <div class="space-y-5">
                <!-- Quick presets -->
                <div>
                    <p class="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">Quick Presets</p>
                    <div class="flex flex-wrap gap-2">
                        <button type="button" onclick="SettingsPage._selectAllSheets(true)" class="btn btn-outline btn-sm">✓ Select All</button>
                        <button type="button" onclick="SettingsPage._selectAllSheets(false)" class="btn btn-ghost btn-sm">✕ Deselect All</button>
                        <button type="button" onclick="SettingsPage._presetFinancial()" class="btn btn-ghost btn-sm">💰 Financial Only</button>
                        <button type="button" onclick="SettingsPage._presetClients()" class="btn btn-ghost btn-sm">👥 Clients Only</button>
                    </div>
                </div>

                <!-- Sheet checkboxes -->
                <div>
                    <p class="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">Sheets to Include</p>
                    <div class="space-y-2">
                        ${allSheets.map(s => `
                            <label class="flex items-start gap-3 p-3 rounded-xl border border-gray-100 dark:border-slate-700/50
                                          bg-gray-50/50 dark:bg-slate-800/30 cursor-pointer
                                          hover:bg-blue-50/50 dark:hover:bg-blue-900/10 hover:border-blue-200 dark:hover:border-blue-800/40 transition">
                                <input type="checkbox" class="export-sheet-check mt-0.5 accent-blue-500" value="${s.id}" checked>
                                <div>
                                    <p class="text-sm font-semibold text-gray-800 dark:text-white flex items-center gap-1.5">
                                        <i data-lucide="${s.icon}" class="w-3.5 h-3.5 opacity-60"></i> ${s.label}
                                    </p>
                                    <p class="text-xs text-gray-400 dark:text-slate-500 mt-0.5">${s.desc}</p>
                                </div>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <!-- Date filter -->
                <div>
                    <p class="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">Date Range Filter <span class="normal-case font-normal text-gray-400">(optional)</span></p>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs text-gray-500 dark:text-slate-400 mb-1 block">From</label>
                            <input type="date" id="export-date-from" class="input text-sm">
                        </div>
                        <div>
                            <label class="text-xs text-gray-500 dark:text-slate-400 mb-1 block">To</label>
                            <input type="date" id="export-date-to" class="input text-sm" value="${new Date().toISOString().split('T')[0]}">
                        </div>
                    </div>
                    <p class="text-xs text-gray-400 dark:text-slate-500 mt-1">⚠️ Leave blank to export all data regardless of date.</p>
                </div>

                <div class="flex gap-3 justify-end pt-2 border-t border-gray-100 dark:border-slate-700/50">
                    <button type="button" onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button type="button" onclick="SettingsPage.runSelectiveExport()" class="btn btn-success">
                        <i data-lucide="file-spreadsheet" class="w-4 h-4"></i> Generate Excel
                    </button>
                </div>
            </div>
        `, { width: 'max-w-lg' });
        lucide.createIcons();
    },

    _selectAllSheets(checked) {
        document.querySelectorAll('.export-sheet-check').forEach(cb => cb.checked = checked);
    },
    _presetFinancial() {
        const fin = ['loans', 'payments', 'amortization', 'penalties', 'commissions'];
        document.querySelectorAll('.export-sheet-check').forEach(cb => {
            cb.checked = fin.includes(cb.value);
        });
    },
    _presetClients() {
        document.querySelectorAll('.export-sheet-check').forEach(cb => {
            cb.checked = cb.value === 'clients';
        });
    },

    async runSelectiveExport() {
        const sheets = [...document.querySelectorAll('.export-sheet-check:checked')].map(cb => cb.value);
        if (sheets.length === 0) {
            UI.toast('Please select at least one sheet to export.', 'warning');
            return;
        }
        const dateFrom = document.getElementById('export-date-from').value || null;
        const dateTo = document.getElementById('export-date-to').value || null;
        UI.closeModal();
        UI.toast(`Generating Excel (${sheets.length} sheet${sheets.length > 1 ? 's' : ''})…`, 'info');
        const result = await App.api('export_excel_selective', sheets, dateFrom, dateTo);
        if (result.success) {
            UI.toast(`Excel exported and opened! ✓ (${sheets.length} sheet${sheets.length > 1 ? 's' : ''})`, 'success');
        } else {
            UI.toast('Export failed: ' + result.error, 'error');
        }
    },

    setLogoSize(size) {
        localStorage.setItem('ph-logo-size', size);
        const sizes = { S: 'w-20 h-20', M: 'w-28 h-28', L: 'w-36 h-36' };
        const container = document.getElementById('logo-preview-container');
        if (container) {
            // Toggle size classes
            container.classList.remove('w-20', 'h-20', 'w-28', 'h-28', 'w-36', 'h-36');
            const [w, h] = sizes[size].split(' ');
            container.classList.add(w, h);
        }
        // Update button active state
        ['S', 'M', 'L'].forEach(s => {
            const btn = document.getElementById(`logo-size-${s}`);
            if (!btn) return;
            if (s === size) {
                btn.className = btn.className.replace(/bg-white.*?hover:border-blue-400/s, 'bg-blue-500 text-white border-blue-500');
            } else {
                btn.className = btn.className.replace('bg-blue-500 text-white border-blue-500',
                    'bg-white dark:bg-slate-800 text-gray-500 border-gray-200 dark:border-slate-600 hover:border-blue-400');
            }
        });
        // Update sidebar logo container size too
        App.loadLogo();
    },

    async backupLocal() {
        UI.toast('Creating backup…', 'info');
        const result = await App.api('do_backup_local');
        if (result.success) {
            UI.toast(`Backup saved! (${result.files.length} files)`, 'success');
        } else {
            UI.toast('Backup had errors: ' + result.errors.join(', '), 'warning');
        }
    },

    async showRestoreModal() {
        const backups = await App.api('get_backups_list');
        if (!backups || backups.length === 0) {
            UI.toast('No local backup available.', 'warning');
            return;
        }

        UI.showModal('Restore Backup', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl" style="background:rgba(255,149,0,0.08); border:1px solid rgba(255,149,0,0.22);">
                    <p class="text-sm font-semibold" style="color:var(--apple-orange)">This replaces the current profile database.</p>
                    <p class="text-xs mt-1" style="color:var(--text-secondary)">A fresh safety backup is created automatically before restore. Media files are not changed.</p>
                </div>
                <div>
                    <label class="text-xs font-medium mb-1.5 block" style="color:var(--text-secondary)">Backup</label>
                    <select id="restore-backup-select" class="input select">
                        ${backups.map(b => `
                            <option value="${b.name}">${b.timestamp} · ${b.size_mb} MB</option>
                        `).join('')}
                    </select>
                </div>
                <div>
                    <label class="text-xs font-medium mb-1.5 block" style="color:var(--text-secondary)">
                        Type <code style="background:var(--surface-2); padding:2px 6px; border-radius:4px; font-weight:700; color:var(--apple-orange)">RESTORE</code> to confirm
                    </label>
                    <input id="restore-confirm-input" class="input font-mono text-center text-lg tracking-widest"
                           placeholder="Type RESTORE here" autocomplete="off" spellcheck="false">
                </div>
                <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button id="restore-confirm-btn" disabled onclick="SettingsPage._executeRestore()" class="btn"
                            style="background:var(--apple-orange); color:white; opacity:0.5;">
                        <i data-lucide="rotate-ccw" class="w-4 h-4"></i> Restore Backup
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        lucide.createIcons();

        const input = document.getElementById('restore-confirm-input');
        const btn = document.getElementById('restore-confirm-btn');
        if (input && btn) {
            input.addEventListener('input', () => {
                btn.disabled = input.value !== 'RESTORE';
                btn.style.opacity = input.value === 'RESTORE' ? '0.9' : '0.5';
            });
            input.focus();
        }
    },

    async _executeRestore() {
        const select = document.getElementById('restore-backup-select');
        const input = document.getElementById('restore-confirm-input');
        if (!select || !input || input.value !== 'RESTORE') {
            UI.toast('You must type RESTORE to confirm.', 'warning');
            return;
        }

        UI.closeModal();
        UI.toast('Restoring backup…', 'info');
        const result = await App.api('restore_backup', select.value);
        if (result.success) {
            SoundEngine.success();
            UI.toast('Backup restored. Reloading dashboard…', 'success');
            await App.refreshAlertsBadge();
            App.navigate('dashboard');
        } else {
            UI.toast('Restore failed: ' + (result.error || 'Unknown error'), 'error');
        }
    },

    async syncDrive() {
        UI.toast('Syncing to Google Drive…', 'info');
        const result = await App.api('do_sync_drive');
        if (result.success) {
            UI.toast(`Synced to Drive! (${result.uploaded_files.length} files)`, 'success');
        } else {
            UI.toast('Drive sync failed: ' + result.error, 'error');
        }
    },

    async openDrive() {
        const result = await App.api('open_drive');
        if (result.success) {
            UI.toast('Google Drive folder opened in browser', 'success');
        } else if (result.opened_folder) {
            UI.toast('Google Drive not set up. Data folder opened — place your credentials.json there.', 'info');
        } else {
            UI.toast('Could not open Drive folder', 'warning');
        }
    },

    toggleSounds(enabled) {
        SoundEngine.setEnabled(enabled);
        SoundEngine.toggle();
        UI.toast(enabled ? '🔊 UI Sounds enabled' : '🔇 UI Sounds disabled', 'info');
    },

    previewSound() {
        const prev = SoundEngine.enabled;
        SoundEngine.enabled = true;
        SoundEngine.success();
        setTimeout(() => SoundEngine.click(), 300);
        setTimeout(() => { SoundEngine.enabled = prev; }, 600);
    },

    // ─── SMS Config ───────────────────────────────────────────
    toggleSmsProviderFields(provider) {
        const twilioFields = document.getElementById('twilio-fields');
        if (twilioFields) twilioFields.classList.toggle('hidden', provider !== 'twilio');
    },

    async saveSmsConfig(e) {
        e.preventDefault();
        const form = e.target;
        await App.api('save_settings', {
            sms_provider: form.sms_provider.value,
            sms_api_key: form.sms_api_key.value,
            sms_sender_id: form.sms_sender_id.value,
            sms_account_sid: form.sms_account_sid?.value || '',
            sms_from_number: form.sms_from_number?.value || '',
        });
        UI.toast('✅ SMS API configuration saved!', 'success');
        SoundEngine.save();
    },

    // ─── SMS Templates ────────────────────────────────────────
    async _renderTemplates() {
        const templates = await App.api('get_sms_templates');
        this._smsTemplates = templates;
        return templates.map((t, i) => `
            <div class="rounded-xl p-3 space-y-2" id="tpl-card-${i}"
                 style="background:var(--surface-2); border: 0.5px solid var(--surface-1);">
                <div class="flex items-center gap-2">
                    <input type="text" class="input flex-1 text-sm font-semibold" value="${t.name}"
                           id="tpl-name-${i}" placeholder="Template name">
                    <button onclick="SettingsPage.deleteSmsTemplate(${i})"
                        class="btn btn-icon btn-ghost btn-sm" title="Delete">
                        <i data-lucide="trash-2" class="w-3.5 h-3.5" style="color:var(--apple-red)"></i>
                    </button>
                </div>
                <textarea class="input w-full text-sm font-mono leading-relaxed resize-none" rows="3"
                          id="tpl-text-${i}" placeholder="Message text…">${t.text}</textarea>
                <button onclick="SettingsPage.saveSmsTemplate(${i})" class="btn btn-primary btn-sm">
                    <i data-lucide="save" class="w-3.5 h-3.5"></i> Save
                </button>
            </div>
        `).join('');
    },

    async saveSmsTemplate(index) {
        const name = document.getElementById(`tpl-name-${index}`)?.value?.trim();
        const text = document.getElementById(`tpl-text-${index}`)?.value?.trim();
        if (!name || !text) { UI.toast('Name and text are required.', 'warning'); return; }

        const templates = await App.api('get_sms_templates');
        if (templates[index]) {
            templates[index].name = name;
            templates[index].text = text;
        }
        await App.api('save_sms_templates', templates);
        UI.toast('✅ Template saved!', 'success');
        SoundEngine.save();
    },

    async addSmsTemplate() {
        const templates = await App.api('get_sms_templates');
        templates.push({
            id: 'custom_' + Date.now(),
            name: 'New Template',
            text: 'Hello {name}, your payment of {amount} is {days} days overdue. Please contact us. — {company}'
        });
        await App.api('save_sms_templates', templates);

        // Re-render the templates list
        const list = document.getElementById('sms-templates-list');
        if (list) {
            list.innerHTML = await this._renderTemplates();
            lucide.createIcons();
        }
        UI.toast('New template added!', 'success');
    },

    async deleteSmsTemplate(index) {
        const templates = await App.api('get_sms_templates');
        if (templates.length <= 1) {
            UI.toast('Cannot delete the last template.', 'warning');
            return;
        }
        templates.splice(index, 1);
        await App.api('save_sms_templates', templates);

        const list = document.getElementById('sms-templates-list');
        if (list) {
            list.innerHTML = await this._renderTemplates();
            lucide.createIcons();
        }
        UI.toast('Template deleted.', 'info');
    },

    // ═══════════════════════════════════════════════════════════════
    // PROFILE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════

    _profileColors: [
        { value: '#007AFF', label: 'Blue' },
        { value: '#AF52DE', label: 'Purple' },
        { value: '#34C759', label: 'Green' },
        { value: '#FF375F', label: 'Pink' },
        { value: '#FF9500', label: 'Orange' },
        { value: '#5856D6', label: 'Indigo' },
        { value: '#FF6482', label: 'Coral' },
        { value: '#30B0C7', label: 'Teal' },
    ],

    showCreateProfileModal() {
        const colorPicker = this._profileColors.map(c => `
            <button type="button" class="profile-color-btn w-7 h-7 rounded-full border-2 border-transparent transition hover:scale-110"
                    style="background:${c.value}" data-color="${c.value}" title="${c.label}"
                    onclick="document.querySelectorAll('.profile-color-btn').forEach(b=>b.style.borderColor='transparent'); this.style.borderColor='white'; document.getElementById('new-profile-color').value='${c.value}'">
            </button>
        `).join('');

        UI.showModal('Create New Profile', `
            <div class="space-y-4">
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Profile Name *</label>
                    <input id="new-profile-name" class="input" placeholder="e.g. Branch 2, Test, Partner..." autofocus>
                </div>
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Description</label>
                    <input id="new-profile-desc" class="input" placeholder="Optional description...">
                </div>
                <div>
                    <label class="text-xs font-medium mb-1.5 block" style="color:var(--text-secondary)">Color</label>
                    <div class="flex items-center gap-2 flex-wrap">${colorPicker}</div>
                    <input type="hidden" id="new-profile-color" value="#007AFF">
                </div>
                <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="SettingsPage.createProfile()" class="btn btn-primary">
                        <i data-lucide="plus" class="w-4 h-4"></i> Create Profile
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        lucide.createIcons();
        // Auto-select first color
        setTimeout(() => {
            const first = document.querySelector('.profile-color-btn');
            if (first) first.style.borderColor = 'white';
        }, 50);
    },

    async createProfile() {
        const name = document.getElementById('new-profile-name')?.value?.trim();
        const desc = document.getElementById('new-profile-desc')?.value?.trim() || '';
        const color = document.getElementById('new-profile-color')?.value || '#007AFF';

        if (!name) {
            UI.toast('Profile name is required.', 'warning');
            return;
        }

        UI.closeModal();
        UI.toast('Creating profile...', 'info');
        const result = await App.api('create_new_profile', name, desc, color);
        if (result.success) {
            SoundEngine.success();
            UI.toast(`Profile "${name}" created! ✓`, 'success');
            App.navigate('settings');
        } else {
            UI.toast('Error: ' + (result.error || 'Unknown'), 'error');
        }
    },

    async showEditProfileModal(profileId) {
        const profiles = await App.api('get_profiles');
        const profile = profiles.find(p => p.id === profileId);
        if (!profile) return;

        const colorPicker = this._profileColors.map(c => `
            <button type="button" class="edit-profile-color-btn w-7 h-7 rounded-full border-2 transition hover:scale-110"
                    style="background:${c.value}; border-color:${c.value === profile.color ? 'white' : 'transparent'}"
                    data-color="${c.value}" title="${c.label}"
                    onclick="document.querySelectorAll('.edit-profile-color-btn').forEach(b=>b.style.borderColor='transparent'); this.style.borderColor='white'; document.getElementById('edit-profile-color').value='${c.value}'">
            </button>
        `).join('');

        UI.showModal('Edit Profile', `
            <div class="space-y-4">
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Profile Name</label>
                    <input id="edit-profile-name" class="input" value="${profile.name}">
                </div>
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Description</label>
                    <input id="edit-profile-desc" class="input" value="${profile.description || ''}">
                </div>
                <div>
                    <label class="text-xs font-medium mb-1.5 block" style="color:var(--text-secondary)">Color</label>
                    <div class="flex items-center gap-2 flex-wrap">${colorPicker}</div>
                    <input type="hidden" id="edit-profile-color" value="${profile.color || '#007AFF'}">
                </div>
                <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button onclick="SettingsPage.saveEditProfile('${profileId}')" class="btn btn-primary">
                        <i data-lucide="save" class="w-4 h-4"></i> Save
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        lucide.createIcons();
    },

    async saveEditProfile(profileId) {
        const name = document.getElementById('edit-profile-name')?.value?.trim();
        const desc = document.getElementById('edit-profile-desc')?.value?.trim() || '';
        const color = document.getElementById('edit-profile-color')?.value || '#007AFF';

        if (!name) {
            UI.toast('Profile name is required.', 'warning');
            return;
        }

        UI.closeModal();
        const result = await App.api('rename_existing_profile', profileId, name, desc, color);
        if (result.success) {
            SoundEngine.save();
            UI.toast('Profile updated ✓', 'success');
            App.navigate('settings');
        } else {
            UI.toast('Error: ' + (result.error || 'Unknown'), 'error');
        }
    },

    async switchProfile(profileId) {
        const profiles = await App.api('get_profiles');
        const target = profiles.find(p => p.id === profileId);
        if (!target) return;

        // Password gate
        const allowed = await this._requirePassword('switch profile');
        if (!allowed) return;

        UI.confirm(
            `Switch to profile "${target.name}"?\n\nThe app will reload with data from this profile.`,
            async () => {
                UI.toast('Switching profile...', 'info');
                const result = await App.api('switch_active_profile', profileId);
                if (result.success) {
                    SoundEngine.success();
                    UI.toast(`Switched to "${target.name}" ✓`, 'success');
                    await App.refreshAlertsBadge();
                    App.navigate('dashboard');
                } else {
                    UI.toast('Error: ' + (result.error || 'Unknown'), 'error');
                }
            }
        );
    },

    async deleteProfile(profileId, profileName) {
        // Password gate
        const allowed = await this._requirePassword('delete profile');
        if (!allowed) return;

        UI.confirm(
            `🗑️ Delete profile "${profileName}"?\n\nThis will permanently delete its database and all data. This cannot be undone.`,
            async () => {
                UI.toast('Deleting profile...', 'info');
                const result = await App.api('delete_existing_profile', profileId);
                if (result.success) {
                    SoundEngine.success();
                    UI.toast(`Profile "${profileName}" deleted.`, 'success');
                    App.navigate('settings');
                } else {
                    UI.toast('Error: ' + (result.error || 'Unknown'), 'error');
                }
            }
        );
    },

    async resetProfileData() {
        // Password gate
        const allowed = await this._requirePassword('reset profile');
        if (!allowed) return;

        const profiles = await App.api('get_profiles');
        const active = profiles.find(p => p.is_active);
        const name = active ? active.name : 'Current Profile';

        // Show "type RESET" confirmation modal
        UI.showModal('⚠️ Reset Profile Data', `
            <div class="space-y-4">
                <div class="p-3 rounded-xl" style="background:rgba(255,59,48,0.06); border:1px solid rgba(255,59,48,0.2);">
                    <p class="text-sm font-semibold" style="color:var(--apple-red)">
                        This will permanently erase ALL data in "${name}":
                    </p>
                    <ul class="text-xs mt-2 space-y-1" style="color:var(--text-secondary)">
                        <li>• All clients and their documents</li>
                        <li>• All loans and amortization schedules</li>
                        <li>• All payments and penalties</li>
                        <li>• All commissions</li>
                    </ul>
                </div>
                <div class="p-3 rounded-xl" style="background:rgba(52,199,89,0.06); border:1px solid rgba(52,199,89,0.2);">
                    <p class="text-xs" style="color:#1A8F3A">
                        ✅ A backup will be created automatically before reset.<br>
                        ✅ Company settings, SMS config, and preferences are preserved.
                    </p>
                </div>
                <div>
                    <label class="text-xs font-medium mb-1.5 block" style="color:var(--text-secondary)">
                        Type <code style="background:var(--surface-2); padding:2px 6px; border-radius:4px; font-weight:700; color:var(--apple-red)">RESET</code> to confirm
                    </label>
                    <input id="reset-confirm-input" class="input font-mono text-center text-lg tracking-widest"
                           placeholder="Type RESET here" autocomplete="off" spellcheck="false"
                           oninput="document.getElementById('reset-confirm-btn').disabled = this.value !== 'RESET'">
                </div>
                <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                    <button id="reset-confirm-btn" disabled onclick="SettingsPage._executeReset()" class="btn"
                            style="background:var(--apple-red); color:white; opacity:0.5;"
                            onmouseenter="if(!this.disabled) this.style.opacity='1'"
                            onmouseleave="if(!this.disabled) this.style.opacity='0.85'">
                        <i data-lucide="alert-triangle" class="w-4 h-4"></i> Erase All Data
                    </button>
                </div>
            </div>
        `, { width: 'max-w-md' });
        lucide.createIcons();

        // Enable button styling when RESET is typed
        const input = document.getElementById('reset-confirm-input');
        if (input) {
            input.addEventListener('input', () => {
                const btn = document.getElementById('reset-confirm-btn');
                if (btn) {
                    btn.disabled = input.value !== 'RESET';
                    btn.style.opacity = input.value === 'RESET' ? '0.85' : '0.5';
                }
            });
            input.focus();
        }
    },

    async _executeReset() {
        const input = document.getElementById('reset-confirm-input');
        if (!input || input.value !== 'RESET') {
            UI.toast('You must type RESET to confirm.', 'warning');
            return;
        }
        UI.closeModal();
        UI.toast('🔄 Creating backup and resetting...', 'info');
        const result = await App.api('reset_current_profile');
        if (result.success) {
            SoundEngine.success();
            UI.toast('✅ Profile reset complete! All data erased.', 'success');
            await App.refreshAlertsBadge();
            App.navigate('dashboard');
        } else {
            UI.toast('❌ Error: ' + (result.error || 'Unknown'), 'error');
        }
    },

    // ═══════════════════════════════════════════════════════════════
    // PASSWORD PROTECTION
    // ═══════════════════════════════════════════════════════════════

    /**
     * Check if password is required, and prompt for it.
     * Returns true if action is allowed, false if cancelled/wrong.
     */
    async _requirePassword(actionName) {
        const isProtected = await App.api('is_password_protected');
        if (!isProtected) return true; // No password set, allow

        return new Promise(resolve => {
            UI.showModal('🔒 Password Required', `
                <div class="space-y-4">
                    <p class="text-sm" style="color:var(--text-secondary)">
                        Enter your password to <strong>${actionName}</strong>.
                    </p>
                    <input id="password-check-input" type="password" class="input text-center text-lg"
                           placeholder="Enter password" autocomplete="off"
                           onkeydown="if(event.key==='Enter') document.getElementById('password-check-btn').click()">
                    <p id="password-check-error" class="text-xs text-center hidden" style="color:var(--apple-red)">
                        ❌ Wrong password. Try again.
                    </p>
                    <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                        <button onclick="UI.closeModal(); SettingsPage._pwResolve && SettingsPage._pwResolve(false);" class="btn btn-ghost">Cancel</button>
                        <button id="password-check-btn" onclick="SettingsPage._checkPassword()" class="btn btn-primary">
                            <i data-lucide="unlock" class="w-4 h-4"></i> Unlock
                        </button>
                    </div>
                </div>
            `, { width: 'max-w-sm', onClose: () => resolve(false) });
            lucide.createIcons();
            this._pwResolve = resolve;
            setTimeout(() => document.getElementById('password-check-input')?.focus(), 100);
        });
    },

    async _checkPassword() {
        const input = document.getElementById('password-check-input');
        if (!input || !input.value) return;
        const result = await App.api('verify_profile_password', input.value);
        if (result.valid) {
            // Clear the onClose callback BEFORE closing the modal
            // to prevent it from resolving the promise with false
            const container = document.getElementById('modal-container');
            if (container) container._onClose = null;
            UI.closeModal();
            if (this._pwResolve) { this._pwResolve(true); this._pwResolve = null; }
        } else {
            const err = document.getElementById('password-check-error');
            if (err) err.classList.remove('hidden');
            input.value = '';
            input.focus();
            SoundEngine.error();
        }
    },

    async togglePassword(enabled) {
        if (enabled) {
            // Show password setup modal
            this.showPasswordSetup();
        } else {
            // Ask current password before disabling
            const isProtected = await App.api('is_password_protected');
            if (isProtected) {
                const allowed = await this._requirePassword('disable password');
                if (!allowed) {
                    // Re-check the toggle
                    const toggle = document.getElementById('password-toggle');
                    if (toggle) toggle.checked = true;
                    return;
                }
            }
            await App.api('remove_profile_password');
            const configBtn = document.getElementById('password-config-btn');
            if (configBtn) configBtn.style.display = 'none';
            UI.toast('🔓 Password protection disabled.', 'info');
            SoundEngine.toggle();
        }
    },

    showPasswordSetup() {
        UI.showModal('🔒 Set Password', `
            <div class="space-y-4">
                <p class="text-sm" style="color:var(--text-secondary)">
                    This password will be required for dangerous actions: reset data, delete profile, switch profile.
                </p>
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">New Password</label>
                    <input id="new-pw-input" type="password" class="input" placeholder="Enter password" autocomplete="new-password">
                </div>
                <div>
                    <label class="text-xs font-medium mb-1 block" style="color:var(--text-secondary)">Confirm Password</label>
                    <input id="new-pw-confirm" type="password" class="input" placeholder="Confirm password" autocomplete="new-password"
                           onkeydown="if(event.key==='Enter') SettingsPage._savePassword()">
                </div>
                <div class="flex gap-3 justify-end pt-2" style="border-top:0.5px solid var(--surface-2);">
                    <button onclick="UI.closeModal(); SettingsPage._cancelPasswordSetup();" class="btn btn-ghost">Cancel</button>
                    <button onclick="SettingsPage._savePassword()" class="btn btn-primary">
                        <i data-lucide="lock" class="w-4 h-4"></i> Set Password
                    </button>
                </div>
            </div>
        `, { width: 'max-w-sm', onClose: () => this._cancelPasswordSetup() });
        lucide.createIcons();
        setTimeout(() => document.getElementById('new-pw-input')?.focus(), 100);
    },

    _cancelPasswordSetup() {
        // If we were trying to enable and user cancels, uncheck toggle
        App.api('is_password_protected').then(enabled => {
            const toggle = document.getElementById('password-toggle');
            if (toggle) toggle.checked = enabled;
            const configBtn = document.getElementById('password-config-btn');
            if (configBtn) configBtn.style.display = enabled ? '' : 'none';
        });
    },

    async _savePassword() {
        const pw = document.getElementById('new-pw-input')?.value;
        const confirm = document.getElementById('new-pw-confirm')?.value;
        if (!pw || pw.length < 8) {
            UI.toast('Password must be at least 8 characters.', 'warning');
            return;
        }
        if (pw !== confirm) {
            UI.toast('Passwords do not match.', 'warning');
            return;
        }
        UI.closeModal();
        const result = await App.api('set_profile_password', pw);
        if (result.success) {
            const toggle = document.getElementById('password-toggle');
            if (toggle) toggle.checked = true;
            const configBtn = document.getElementById('password-config-btn');
            if (configBtn) configBtn.style.display = '';
            SoundEngine.success();
            UI.toast('🔒 Password protection enabled!', 'success');
        } else {
            UI.toast('Error: ' + (result.error || 'Unknown'), 'error');
        }
    },
};
