/**
 * PH-Lending Pro — PrintManager
 * Système d'impression contextuel intelligent.
 * - Bouton d'impression dans le header — adapte son action selon la page active
 * - Visualisateur PDF grand format (plein écran) intégré à l'app
 * - Génère les bons PDFs selon le contexte (amortissement, client, reçu…)
 */

const PrintManager = {

    _currentPdfPath: null,
    _currentPdfTitle: null,

    // ─── Point d'entrée principal (bouton header) ──────────────────
    async smartPrint() {
        const page = App.currentPage;
        const params = App.currentParams || {};

        SoundEngine.click();

        switch (page) {
            case 'loan_detail':
                await this.printLoanDetail(params.id);
                break;

            case 'client_detail':
                // Ouvre le Print Center du client
                if (window.ClientDetailPage && ClientDetailPage.clientId) {
                    ClientDetailPage.openPrintCenter();
                } else {
                    UI.toast('Open a client profile to print client documents.', 'info');
                }
                break;

            case 'dashboard':
                await this.printDashboard();
                break;

            case 'clients':
                await this.printClientsList();
                break;

            case 'loans':
                await this.printLoansList();
                break;

            case 'payments':
                await this.printPaymentsList();
                break;

            case 'calendar':
                await this.printCalendar();
                break;

            case 'alerts':
                await this.printAlerts();
                break;

            default:
                // Impression HTML générique de la page
                window.print();
                break;
        }
    },

    // ─── Loan Detail : menu choix impression ─────────────────────
    async printLoanDetail(loanId) {
        if (!loanId) { UI.toast('No loan selected.', 'warning'); return; }

        // Petit menu contextuel
        const menuHtml = `
            <div class="space-y-2 py-1">
                <button onclick="UI.closeModal(); PrintManager.openAmortizationPdf(${loanId})"
                        class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-800/60 transition text-left">
                    <div class="w-9 h-9 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                        <i data-lucide="calendar-range" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>
                    </div>
                    <div>
                        <p class="font-semibold text-sm text-gray-800 dark:text-white">Amortization Schedule</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Complete installment schedule</p>
                    </div>
                    <i data-lucide="chevron-right" class="w-4 h-4 text-gray-300 ml-auto"></i>
                </button>
                <button onclick="UI.closeModal(); PrintManager.openContractPdf(${loanId})"
                        class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-800/60 transition text-left">
                    <div class="w-9 h-9 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
                        <i data-lucide="file-signature" class="w-4 h-4 text-purple-600 dark:text-purple-400"></i>
                    </div>
                    <div>
                        <p class="font-semibold text-sm text-gray-800 dark:text-white">Loan Contract</p>
                        <p class="text-xs text-gray-400 dark:text-slate-500">Official contract ready for signature</p>
                    </div>
                    <i data-lucide="chevron-right" class="w-4 h-4 text-gray-300 ml-auto"></i>
                </button>
            </div>
        `;
        UI.showModal('Print Loan #' + loanId, menuHtml, { width: 'max-w-sm' });
    },

    // ─── Générer + Prévisualiser : Tableau d'amortissement ────────
    async openAmortizationPdf(loanId) {
        this._showPdfViewer(`Amortization — Loan #${loanId}`, 'Installment Schedule');
        try {
            const result = await App.api('generate_amortization_pdf', loanId);
            if (result.success) {
                this._loadPdfInViewer(result.path, result.b64);
            } else {
                this._pdfError(result.error);
            }
        } catch (e) {
            this._pdfError(String(e));
        }
    },

    // ─── Générer + Prévisualiser : Contrat ───────────────────────
    async openContractPdf(loanId) {
        this._showPdfViewer(`Contract — Loan #${loanId}`, 'Loan Contract');
        try {
            const result = await App.api('generate_contract_preview', loanId);
            if (result.success) {
                this._loadPdfInViewer(result.path, result.b64);
            } else {
                this._pdfError(result.error);
            }
        } catch (e) {
            this._pdfError(String(e));
        }
    },

    // ─── Générer + Prévisualiser : Reçu de paiement ──────────────
    async openReceiptPdf(paymentId, loanId) {
        this._showPdfViewer(`Receipt — Payment #${paymentId}`, 'Payment Receipt');
        try {
            const result = await App.api('generate_receipt_preview', paymentId);
            if (result.success) {
                this._loadPdfInViewer(result.path, result.b64);
            } else {
                this._pdfError(result.error);
            }
        } catch (e) {
            this._pdfError(String(e));
        }
    },

    // ─── Dashboard : impression HTML ─────────────────────────────
    async printDashboard() {
        UI.toast('Preparing dashboard print view...', 'info');
        window.print();
    },

    // ─── Listes : impression HTML de la vue ──────────────────────
    async printClientsList() {
        UI.toast('Preparing client list print view...', 'info');
        window.print();
    },

    async printLoansList() {
        UI.toast('Preparing loan list print view...', 'info');
        window.print();
    },

    async printPaymentsList() {
        UI.toast('Preparing payment print view...', 'info');
        window.print();
    },

    async printCalendar() {
        UI.toast('Preparing collection calendar print view...', 'info');
        window.print();
    },

    async printAlerts() {
        UI.toast('Preparing alerts print view...', 'info');
        window.print();
    },

    // ─── Viewer : affiche l'overlay avec spinner ──────────────────
    _showPdfViewer(title, subtitle) {
        this._currentPdfPath = null;
        this._currentPdfTitle = title;

        document.getElementById('pdf-viewer-title').textContent = title;
        document.getElementById('pdf-viewer-subtitle').textContent = subtitle;

        const overlay = document.getElementById('pdf-viewer-overlay');
        const loading = document.getElementById('pdf-viewer-loading');
        const frame = document.getElementById('pdf-viewer-frame');

        overlay.classList.remove('hidden');
        overlay.classList.add('pdf-viewer-visible');
        loading.classList.remove('hidden');
        frame.classList.add('hidden');
        frame.src = '';

        // Escape key to close
        this._escHandler = (e) => { if (e.key === 'Escape') this.closePdfViewer(); };
        document.addEventListener('keydown', this._escHandler);

        lucide.createIcons();
    },

    // ─── Viewer : charge le PDF dans l'iframe ─────────────────────
    _loadPdfInViewer(path, b64) {
        this._currentPdfPath = path;

        const loading = document.getElementById('pdf-viewer-loading');
        const frame = document.getElementById('pdf-viewer-frame');

        // Utilise la data URI base64 si disponible (compatible pywebview)
        // Sinon on essaye le chemin file://
        if (b64) {
            frame.src = b64; // data:application/pdf;base64,...
        } else if (path) {
            // Convertit le chemin macOS en file:// URI
            const fileUri = 'file://' + path.replace(/\\/g, '/');
            frame.src = fileUri;
        }

        frame.onload = () => {
            loading.classList.add('hidden');
            frame.classList.remove('hidden');
        };

        // Fallback : si l'iframe ne charge pas en 3s (pywebview peut bloquer PDF inline)
        setTimeout(() => {
            if (!frame.classList.contains('hidden')) return; // déjà chargé
            loading.classList.add('hidden');
            frame.classList.remove('hidden');
        }, 2500);
    },

    // ─── Viewer : erreur ──────────────────────────────────────────
    _pdfError(msg) {
        const loading = document.getElementById('pdf-viewer-loading');
        loading.innerHTML = `
            <i data-lucide="alert-circle" class="w-12 h-12 text-red-400 mb-3"></i>
            <p class="text-white font-semibold">PDF Generation Error</p>
            <p class="text-white/60 text-sm mt-1">${msg || 'Unknown error'}</p>
            <button onclick="PrintManager.closePdfViewer()" class="mt-4 px-4 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/20 transition">Close</button>
        `;
        lucide.createIcons();
    },

    // ─── Fermer le viewer ─────────────────────────────────────────
    closePdfViewer() {
        const overlay = document.getElementById('pdf-viewer-overlay');
        overlay.classList.add('pdf-viewer-closing');
        setTimeout(() => {
            overlay.classList.add('hidden');
            overlay.classList.remove('pdf-viewer-visible', 'pdf-viewer-closing');
            const frame = document.getElementById('pdf-viewer-frame');
            frame.src = '';
        }, 280);
        if (this._escHandler) {
            document.removeEventListener('keydown', this._escHandler);
        }
    },

    // ─── Imprimer le PDF actuellement affiché ─────────────────────
    printCurrentPdf() {
        if (this._currentPdfPath) {
            App.api('open_and_print_pdf', this._currentPdfPath).then(() => {
                SoundEngine.success();
            });
        } else {
            // Fallback: imprimer via l'iframe
            const frame = document.getElementById('pdf-viewer-frame');
            if (frame && frame.contentWindow) {
                try { frame.contentWindow.print(); } catch (e) {
                    // Si cross-origin bloqué, ouvre le fichier natif
                    if (this._currentPdfPath) {
                        App.api('open_file', this._currentPdfPath);
                    }
                }
            }
        }
        SoundEngine.click();
    },

    // ─── Ouvrir le PDF dans Preview ───────────────────────────────
    downloadCurrentPdf() {
        if (this._currentPdfPath) {
            App.api('open_file', this._currentPdfPath);
            UI.toast('PDF opened in Preview.', 'success');
            SoundEngine.success();
        }
    },
};
