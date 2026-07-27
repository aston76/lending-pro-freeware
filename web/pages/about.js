/**
 * Lending Pro Freeware — About
 * Product information and contact for custom development requests.
 */
const AboutPage = {
    async render() {
        const content = document.getElementById('page-content');

        let version = '1.5.0';
        let appName = 'Lending Pro Freeware';
        try {
            const info = await App.api('get_app_info');
            if (info) {
                version = info.version || version;
                appName = info.name || appName;
            }
        } catch (e) { }

        const contactEmail = 'alain.eric@ik.me';

        content.innerHTML = `
            <!-- Hero -->
            <div class="glass-card p-6 sm:p-8 mb-6 stagger">
                <div class="flex flex-col sm:flex-row items-center sm:items-start gap-5">
                    <div class="w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 overflow-hidden"
                         style="background:#071b3a; box-shadow: 0 6px 18px rgba(0,0,0,0.18);">
                        <img src="assets/lending-pro-mark.png" class="w-full h-full object-cover" alt="Lending Pro logo">
                    </div>
                    <div class="text-center sm:text-left min-w-0">
                        <h2 class="text-xl font-bold" style="color: var(--text-primary);">${appName}</h2>
                        <p class="text-sm mt-1" style="color: var(--text-secondary);">
                            Private, offline management of clients, loans, repayments and collections.
                        </p>
                        <div class="flex flex-wrap items-center gap-2 mt-3 justify-center sm:justify-start">
                            <span class="badge badge-active">Version ${version}</span>
                            <span class="badge badge-pending">100% offline</span>
                            <span class="badge" style="background:rgba(52,199,89,0.12); color:#1A8F3A;">No subscription</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Sur mesure / Personnalisation -->
            <div class="glass-card p-6 sm:p-8 mb-6 stagger"
                 style="border: 1px solid rgba(0,122,255,0.18); background: linear-gradient(135deg, rgba(0,122,255,0.05), rgba(88,86,214,0.05));">
                <div class="flex items-center gap-3 mb-4">
                    <div class="p-2.5 rounded-xl" style="background: rgba(0,122,255,0.12);">
                        <i data-lucide="wrench" class="w-5 h-5" style="color: var(--accent);"></i>
                    </div>
                    <div>
                        <h3 class="font-bold text-base" style="color: var(--text-primary);">Tailored to your business</h3>
                        <p class="text-xs" style="color: var(--text-tertiary);">Professional software customization</p>
                    </div>
                </div>
                <p class="text-sm mb-5" style="color: var(--text-secondary);">
                    Every lending business has its own rules. If you need a specific field,
                    a different interest calculation, a custom document or a workflow tailored
                    to the way you work, the software can be adapted for you.
                </p>

                <!-- Carte de contact -->
                <div class="rounded-2xl p-5" style="background: var(--surface-1); border: 1px solid rgba(0,0,0,0.08);">
                    <div class="flex flex-col sm:flex-row items-center gap-4">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
                             style="background: rgba(0,122,255,0.12);">
                            <i data-lucide="mail" class="w-6 h-6" style="color: var(--accent);"></i>
                        </div>
                        <div class="flex-1 min-w-0 text-center sm:text-left">
                            <p class="text-xs font-semibold uppercase tracking-wider mb-0.5" style="color: var(--text-tertiary);">Contact</p>
                            <p class="font-semibold text-sm break-all" style="color: var(--text-primary);">${contactEmail}</p>
                            <p class="text-xs mt-1" style="color: var(--text-secondary);">
                                Describe your requirements to receive a response and customization quote.
                            </p>
                        </div>
                        <button onclick="AboutPage.contact('${contactEmail}')"
                                class="btn btn-primary flex items-center gap-2 flex-shrink-0">
                            <i data-lucide="send" class="w-4 h-4"></i>
                            <span>Send a message</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Détails de l'application -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 stagger">
                ${AboutPage._featureCard('shield-check', 'Complete privacy',
                    'Your data stays on your computer. No uploads, no cloud account and no telemetry.',
                    'rgba(52,199,89,0.12)', '#1A8F3A')}
                ${AboutPage._featureCard('calculator', 'Accurate accounting',
                    'Cent-exact calculations, reconciled schedules and multiple currencies.',
                    'rgba(255,149,0,0.12)', '#B86700')}
                ${AboutPage._featureCard('file-text', "Professional documents",
                    "Contracts, receipts and amortization schedules generated in one click.",
                    'rgba(88,86,214,0.12)', '#5856D6')}
            </div>

            <!-- Footer -->
            <div class="mt-6 text-center">
                <p class="text-xs" style="color: var(--text-tertiary);">
                    ${appName} · Version ${version} · Developed by Alain
                </p>
            </div>
        `;
        lucide.createIcons();
    },

    _featureCard(icon, title, text, bg, color) {
        return `
            <div class="glass-card p-5">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3" style="background: ${bg};">
                    <i data-lucide="${icon}" class="w-5 h-5" style="color: ${color};"></i>
                </div>
                <h4 class="font-semibold text-sm mb-1.5" style="color: var(--text-primary);">${title}</h4>
                <p class="text-xs leading-relaxed" style="color: var(--text-secondary);">${text}</p>
            </div>
        `;
    },

    async contact(email) {
        const subject = encodeURIComponent('Customization request — Lending Pro Freeware');
        const body = encodeURIComponent(
            'Hello,\n\n' +
            'I would like to adapt the software to my business.\n\n' +
            'My requirements:\n' +
            '— \n\n' +
            'Kind regards,'
        );
        const mailto = `mailto:${email}?subject=${subject}&body=${body}`;
        try {
            const res = await App.api('open_url', mailto);
            if (res && res.success === false) {
                UI.toast('Could not open your email app. Write to: ' + email, 'warning');
            }
        } catch (e) {
            UI.toast('Write to: ' + email, 'info');
        }
    }
};
