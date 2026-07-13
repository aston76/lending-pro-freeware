/**
 * PH-Lending Pro — Help & User Guide Page
 * Interactive accordion FAQ / user manual
 */
const HelpPage = {

    sections: [
        {
            icon: 'layout-dashboard',
            color: 'text-blue-500',
            title: 'Dashboard — Overview',
            content: `
                <p class="text-sm text-gray-600 dark:text-slate-400 mb-4">
                    The dashboard is your home screen. It displays the real-time status of your loan portfolio.
                </p>
                <div class="space-y-4">
                    <div>
                        <h5 class="font-semibold text-sm mb-2 text-gray-800 dark:text-white flex items-center gap-2">
                            <i data-lucide="bar-chart-2" class="w-4 h-4 text-blue-500"></i> The 4 Main Statistics
                        </h5>
                        <ul class="space-y-2 text-sm text-gray-600 dark:text-slate-400">
                            <li>• <strong>Active Capital</strong> — Total sum of all active loan principals (status = active)</li>
                            <li>• <strong>Collected Interest</strong> — Interest portion actually covered by recorded payments</li>
                            <li>• <strong>Default Rate</strong> — Percentage of loans marked "defaulted" out of total active</li>
                            <li>• <strong>Total Clients</strong> — Number of clients in the database</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold text-sm mb-2 text-gray-800 dark:text-white flex items-center gap-2">
                            <i data-lucide="calendar-check" class="w-4 h-4 text-amber-500"></i> Today's Collections
                        </h5>
                        <p class="text-sm text-gray-600 dark:text-slate-400">
                            List of all payments due today (based on the amortization schedule).
                            Click a client to go directly to their loan and record a payment.
                        </p>
                        <div class="help-tip mt-2">
                            <strong>Tip:</strong> If a client does not pay, open the loan to add a penalty or mark it as defaulted.
                        </div>
                    </div>
                    <div>
                        <h5 class="font-semibold text-sm mb-2 text-gray-800 dark:text-white flex items-center gap-2">
                            <i data-lucide="trending-up" class="w-4 h-4 text-green-500"></i> Recent Payments
                        </h5>
                        <p class="text-sm text-gray-600 dark:text-slate-400">
                            The last 5 payments recorded in the system with client name, date and amount.
                        </p>
                    </div>
                </div>
            `
        },
        {
            icon: 'users',
            color: 'text-purple-500',
            title: 'Clients — Borrower Management',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Create a Client</h5>
                        <p>Click <strong>"New Client"</strong> (blue button top right). Fill in:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>First Name / Last Name</strong> — required</li>
                            <li>• <strong>Address</strong> — optional</li>
                            <li>• <strong>Phone</strong> — optional but recommended for collections</li>
                            <li>• <strong>Rating</strong> — 1 to 5 stars (your client assessment)</li>
                            <li>• <strong>Referred By</strong> — if this client was referred by another existing client (automatically generates a commission)</li>
                        </ul>
                        <div class="help-tip mt-2">
                            <strong>Tip:</strong> The client ID is generated automatically in the format <code>PH-YYYY-NNN</code> (for example, PH-2026-001).
                        </div>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Detailed Client Profile</h5>
                        <p>Click on any client to open their full profile with:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Profile photo</strong> — captured by webcam or from the filesystem</li>
                            <li>• <strong>DTI (Debt-to-Income)</strong> — monthly installments / monthly income ratio. Above 40% = high risk (shown in red)</li>
                            <li>• <strong>Pending Penalties</strong> — total amount and number of unpaid penalties</li>
                            <li>• <strong>Loan History</strong> — all client loans with their progress</li>
                            <li>• <strong>Documents</strong> — ID photos, contracts, etc.</li>
                            <li>• <strong>Digital Signature</strong> — touch/mouse signature area</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Photo / ID Capture</h5>
                        <p>Two buttons allow you to capture photos:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Camera icon</strong> on the profile photo → Takes profile photo via webcam</li>
                            <li>• <strong>"ID Photo"</strong> in Documents → Photographs the identity document</li>
                            <li>• <strong>"Upload"</strong> → Imports any file from the computer</li>
                        </ul>
                        <div class="help-tip mt-2">
                            <strong>Tip:</strong> If the camera does not work, allow PH-Lending under macOS System Settings, Privacy & Security, Camera.
                        </div>
                    </div>
                </div>
            `
        },
        {
            icon: 'banknote',
            color: 'text-green-500',
            title: 'Loans — Creation and Management',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Create a New Loan</h5>
                        <p>Via <strong>Loans → New Loan</strong> or from the client profile → New Loan. Parameters:</p>
                        <ul class="mt-2 space-y-2 ml-4">
                            <li>• <strong>Principal (₱)</strong> — borrowed amount (capital)</li>
                            <li>• <strong>Interest Rate (%)</strong> — choose whether the entered rate is monthly or for the full term; the contract stores the full-term rate</li>
                            <li>• <strong>Interest Type</strong>:
                                <ul class="ml-4 mt-1 space-y-1">
                                    <li>→ <strong>Fixed Rate</strong>: interest calculated once on the total capital. Equal installments. <em>Ex: ₱10,000 at 3%/month × 6 months = ₱1,800 interest → ₱1,966.67/month</em></li>
                                    <li>→ <strong>Declining Balance</strong>: interest recalculated each month on the remaining capital. Decreasing installments.</li>
                                </ul>
                            </li>
                            <li>• <strong>Rate Duration</strong> (important):
                                <ul class="ml-4 mt-1 space-y-1">
                                    <li>→ <strong>Per Month</strong> (recommended default): you enter the monthly rate (e.g. 3%). The system automatically multiplies by the term.</li>
                                    <li>→ <strong>Total for entire term</strong>: you enter the total rate for the entire loan term.</li>
                                </ul>
                            </li>
                            <li>• <strong>Term (months)</strong> — loan duration (1 to 120 months)</li>
                            <li>• <strong>Start Date</strong> — start date; due dates are calculated automatically (month+1, month+2, etc.)</li>
                        </ul>
                        <div class="help-tip mt-2">
                            The <strong>preview</strong> updates in real time as you type: monthly payment, total interest, and total repayment amount.
                        </div>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Amortization Schedule</h5>
                        <p>In the Loan Detail view, the table shows for each month:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Due Date</strong> — exact due date</li>
                            <li>• <strong>Principal</strong> — capital portion of the installment</li>
                            <li>• <strong>Interest</strong> — interest portion of the installment</li>
                            <li>• <strong>Total Due</strong> — total amount to pay this month</li>
                            <li>• <strong>Balance</strong> — remaining capital after this payment</li>
                            <li>• The <strong>"Today"</strong> row (in orange) marks the current due date</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Loan Statuses</h5>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Active</strong> — loan currently being repaid</li>
                            <li>• <strong>Paid</strong> — fully repaid (automatic when total paid ≥ total due)</li>
                            <li>• <strong>Defaulted</strong> — manually marked as defaulted ("Mark Defaulted" button)</li>
                            <li>• <strong>Refinanced</strong> — loan closed through a refinance</li>
                        </ul>
                    </div>
                </div>
            `
        },
        {
            icon: 'receipt',
            color: 'text-emerald-500',
            title: 'Payments — Recording and Receipts',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Record a Payment</h5>
                        <p>In the Loan Detail view (Active status), click the green <strong>"Record"</strong> button:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Amount (₱)</strong> — amount received (not necessarily equal to the monthly installment)</li>
                            <li>• <strong>Payment Date</strong> — actual payment date (today by default)</li>
                            <li>• <strong>Method</strong> — Cash / GCash / Bank Transfer / Check</li>
                            <li>• <strong>Notes</strong> — reference, transaction number, etc.</li>
                        </ul>
                        <div class="help-tip mt-2">
                            When the total payments reach the total due (principal + interest), the loan automatically switches to <strong>Paid</strong> status.
                        </div>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Partial Payments</h5>
                        <p>You can record multiple partial payments. The system allocates each amount to the oldest unpaid installment first and updates the progress bar. Payments must be greater than zero.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Generate a PDF Receipt</h5>
                        <p>In the loan detail, each payment has a receipt button that generates a professional PDF with:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• Your company logo (if configured)</li>
                            <li>• Client information</li>
                            <li>• Payment details and receipt number</li>
                            <li>• Signature and date</li>
                        </ul>
                        <p class="mt-2">The PDF opens automatically in Preview/Adobe Reader. Files are saved in <code>~/Library/Application Support/PH-Lending/pdfs/</code></p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">"Payments" Page</h5>
                        <p>The Payments page (left menu) shows the complete history of all payments across all loans, with the ability to generate a receipt for each.</p>
                    </div>
                </div>
            `
        },
        {
            icon: 'refresh-cw',
            color: 'text-amber-500',
            title: 'Refinancing / Loan Extension',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div class="p-4 bg-amber-50 dark:bg-amber-900/10 rounded-xl border border-amber-200 dark:border-amber-800/30">
                        <p class="font-semibold text-amber-700 dark:text-amber-400 mb-1">What is refinancing?</p>
                        <p>Refinancing allows a client to obtain a <strong>new loan</strong> before the old one is repaid. The remaining balance of the old loan is automatically <strong>added to the new loan's principal</strong>.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">How it works — step by step</h5>
                        <ol class="space-y-3 ml-4">
                            <li>
                                <strong>1. Initiate refinancing</strong><br>
                                <span class="text-gray-500 dark:text-slate-400">In the client profile → click <em>"Refinance Loan"</em> (visible only if an active loan exists)</span>
                            </li>
                            <li>
                                <strong>2. Remaining balance is calculated</strong><br>
                                <span class="text-gray-500 dark:text-slate-400">The system computes automatically: <code>Total Due - Total Paid = Remaining Balance</code>. This amount will be added to the new principal.</span>
                            </li>
                            <li>
                                <strong>3. Define the new loan</strong><br>
                                <span class="text-gray-500 dark:text-slate-400">
                                    • <strong>New Capital</strong> — new amount lent (without the rollover)<br>
                                    • <strong>Term, Rate, Type</strong> — terms of the new loan<br>
                                    • <strong>Start Date</strong> — start date of the new loan
                                </span>
                            </li>
                            <li>
                                <strong>4. Automatic creation</strong><br>
                                <span class="text-gray-500 dark:text-slate-400">
                                    • The old loan switches to <em>Refinanced</em> status<br>
                                    • A new loan is created with principal: <code>New Capital + Remaining Balance</code><br>
                                    • The new loan shows "↩ Includes ₱X rollover from Loan #Y"
                                </span>
                            </li>
                        </ol>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Concrete Example</h5>
                        <div class="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-4 font-mono text-xs space-y-1">
                            <p>Loan A: Principal ₱10,000 | Total due ₱11,800</p>
                            <p>Already paid: ₱5,000</p>
                            <p class="text-amber-600">Remaining balance: ₱6,800</p>
                            <p class="mt-2">New capital requested: ₱8,000</p>
                            <p class="text-green-600 font-bold">New loan principal: ₱8,000 + ₱6,800 = ₱14,800</p>
                        </div>
                    </div>
                    <div class="help-tip">
                        Refinancing is irreversible. The old loan remains in the client history with "Refinanced" status for traceability.
                    </div>
                </div>
            `
        },
        {
            icon: 'alert-circle',
            color: 'text-orange-500',
            title: 'Penalties — Late Fees',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Add a Penalty</h5>
                        <p>In the client profile → "Penalties" section → <strong>"+ Add Penalty"</strong> button (visible if a loan is active):</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Loan</strong> — select the relevant loan</li>
                            <li>• <strong>Amount</strong> — penalty amount in ₱</li>
                            <li>• <strong>Date</strong> — penalty date</li>
                            <li>• <strong>Reason</strong> — Late Payment / Missed Payment / Early Termination / Other</li>
                            <li>• <strong>Notes</strong> — additional details</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Manage Penalties</h5>
                        <p>Each penalty can be:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Paid</strong> (green button) — marked as paid</li>
                            <li>• <strong>Waived</strong> (grey button) — cancelled / forgiven</li>
                        </ul>
                        <div class="help-tip mt-2">
                            Total pending penalties are shown on the client profile and in the profile summary.
                        </div>
                    </div>
                    <div class="help-tip">
                        Note: penalties are separate fees from the loan. They do not automatically affect the loan balance and are managed manually.
                    </div>
                </div>
            `
        },
        {
            icon: 'calendar',
            color: 'text-blue-400',
            title: 'Collection Calendar',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Calendar View</h5>
                        <p>The calendar visually shows all days when payments are due. Days with collections have an <strong>orange dot</strong> and show the client count on hover.</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>Today</strong> — colored circle (current theme)</li>
                            <li>• <strong>Orange dot</strong> — day with collections due</li>
                            <li>• Click a day → shows the list of clients to collect that day</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Navigation</h5>
                        <p>Use the <strong>◄ ►</strong> arrows to navigate between months. Click a client in the day detail to go directly to their loan.</p>
                    </div>
                    <div class="help-tip">
                        <strong>Tip:</strong> The calendar is based on unpaid amortization installments. Fully paid installments are hidden, and partial payments show only the remaining amount to collect.
                    </div>
                </div>
            `
        },
        {
            icon: 'gift',
            color: 'text-amber-400',
            title: 'Referral Commissions',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">How It Works</h5>
                        <p>When an existing client (the "referrer") recommends a new client (the "referred") who takes a loan, a commission is automatically generated for the referrer.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Configuration</h5>
                        <p>In Settings → Loan Defaults & Commission:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• <strong>% of Principal</strong> — commission calculated as a percentage of the new loan capital</li>
                            <li>• <strong>Fixed Amount ₱</strong> — fixed amount per referral</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Managing Commissions</h5>
                        <p>The "Referral Commissions" page (left menu) shows all commissions with:</p>
                        <ul class="mt-2 space-y-1 ml-4">
                            <li>• The referrer and referred client names</li>
                            <li>• The relevant loan and commission amount</li>
                            <li>• <strong>"Pay"</strong> button to mark as paid</li>
                        </ul>
                    </div>
                    <div class="help-tip">
                        <strong>Tip:</strong> To create a referral link, select "Referred By" when creating the referred client.
                    </div>
                </div>
            `
        },
        {
            icon: 'settings',
            color: 'text-gray-500',
            title: 'Settings — Configuration and Backup',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Company Information</h5>
                        <p>Configure your company name, contact, and address. This information appears on all PDFs (contracts and receipts). The <strong>logo</strong> appears in the sidebar and on PDFs.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Loan Default Values</h5>
                        <ul class="mt-1 space-y-1 ml-4">
                            <li>• <strong>Default Interest Rate</strong> — pre-filled rate in the loan creation form</li>
                            <li>• <strong>Interest Type</strong> — Fixed or Declining pre-selected</li>
                            <li>• <strong>Commission Type/Rate</strong> — settings for referral commissions</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Excel Export</h5>
                        <p>Generates a <code>.xlsx</code> file with 4 tabs: Clients, Loans, Payments, Referral Commissions. The file opens automatically and is saved in <code>~/Library/Application Support/PH-Lending/exports/</code></p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Local Backup</h5>
                        <p>Creates 3 files in <code>~/Library/Application Support/PH-Lending/backups/</code>:</p>
                        <ul class="mt-1 space-y-1 ml-4">
                            <li>• <code>.db</code> — copy of the SQLite database</li>
                            <li>• <code>.xlsx</code> — full Excel export</li>
                            <li>• <code>.json</code> — raw export of all data</li>
                        </ul>
                        <p class="mt-2">Use <strong>Restore</strong> to restore a local backup. The app creates a fresh safety backup before replacing the current profile database.</p>
                        <div class="help-tip mt-2">
                            A backup is created automatically every time the application closes.
                        </div>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Google Drive (Cloud Sync)</h5>
                        <p>To enable Google Drive sync:</p>
                        <ol class="mt-1 space-y-1 ml-4 list-decimal list-inside">
                            <li>Create a project in <a href="https://console.cloud.google.com" class="text-blue-500 underline" onclick="App.api && App.api('open_url', 'https://console.cloud.google.com')">Google Cloud Console</a></li>
                            <li>Enable the Google Drive API</li>
                            <li>Download the <code>credentials.json</code> file</li>
                            <li>Place it in the "Data" folder ("Open Data Folder" button)</li>
                            <li>Click "Sync to Drive" — an authorization window will open</li>
                        </ol>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Demo Mode</h5>
                        <p>Activates a separate database with fictitious data to test the application. Disable it to return to your real data. <strong>Your real data is never affected.</strong></p>
                    </div>
                </div>
            `
        },
        {
            icon: 'calculator',
            color: 'text-indigo-500',
            title: 'Floating Calculator',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <p>The calculator is accessible from the calculator icon in the header and opens above the current view.</p>
                    <ul class="space-y-1 ml-4">
                        <li>• <strong>Move</strong> — click and drag on the top bar</li>
                        <li>• <strong>Close</strong> — ✕ button top right</li>
                        <li>• Supports standard operations: +, −, ×, ÷</li>
                    </ul>
                    <div class="help-tip">
                        <strong>Tip:</strong> Use the calculator to check amounts while entering data without leaving the current screen.
                    </div>
                </div>
            `
        },
        {
            icon: 'file-text',
            color: 'text-rose-500',
            title: 'PDF Generation — Contracts & Receipts',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Loan Contract</h5>
                        <p>In the Loan Detail → <strong>"PDF Contract"</strong> button. The contract includes:</p>
                        <ul class="mt-1 space-y-1 ml-4">
                            <li>• Header with logo and company info</li>
                            <li>• Client and loan information</li>
                            <li>• Full amortization schedule</li>
                            <li>• Signature area</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Payment Receipt</h5>
                        <p>Use the receipt icon on a payment to generate payment details, remaining balance, and loan information.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Print Center</h5>
                        <p>In the client profile → <strong>"Print Client Documents"</strong> button. Allows you to:</p>
                        <ul class="mt-1 space-y-1 ml-4">
                            <li>• Select multiple documents to print as a batch</li>
                            <li>• Contracts for all loans + payment receipts</li>
                            <li>• Click "Print Selected" to open all PDFs at once</li>
                        </ul>
                    </div>
                    <p class="text-xs text-gray-400 dark:text-slate-500">All PDFs are saved in: <code>~/Library/Application Support/PH-Lending/pdfs/</code></p>
                </div>
            `
        },
        {
            icon: 'palette',
            color: 'text-pink-500',
            title: 'Color Themes and Interface',
            content: `
                <div class="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Dark / Light Mode</h5>
                        <p><i data-lucide="moon" class="w-3 h-3 inline"></i> / <i data-lucide="sun" class="w-3 h-3 inline"></i> button in the top bar. Preference saved automatically.</p>
                    </div>
                    <div>
                        <h5 class="font-semibold mb-2 text-gray-800 dark:text-white">Color Themes</h5>
                        <p>5 themes available in Settings → Appearance:</p>
                        <div class="flex items-center gap-3 mt-2 flex-wrap">
                            <div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-blue-500 inline-block"></span> Blue (default)</div>
                            <div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-purple-500 inline-block"></span> Purple</div>
                            <div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-emerald-500 inline-block"></span> Emerald</div>
                            <div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-rose-500 inline-block"></span> Rose</div>
                            <div class="flex items-center gap-2"><span class="w-5 h-5 rounded-full bg-amber-500 inline-block"></span> Amber</div>
                        </div>
                        <p class="mt-2">The theme instantly changes the color of buttons, sidebar, calendar and focused inputs.</p>
                    </div>
                </div>
            `
        },
    ],

    render() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="max-w-3xl mx-auto pb-8">

                <!-- Hero Banner -->
                <div class="glass-card p-6 mb-6 border border-blue-100 dark:border-blue-900/30">
                    <div class="flex items-center gap-4">
                        <div class="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
                             style="background:var(--accent);">
                            <i data-lucide="book-open" class="w-7 h-7 text-white"></i>
                        </div>
                        <div>
                            <h2 class="text-xl font-bold text-gray-800 dark:text-white">PH-Lending Pro — Complete Guide</h2>
                            <p class="text-sm text-gray-500 dark:text-slate-400 mt-0.5">
                                Everything you need to know to use the application like a pro. Click each section to expand.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Search -->
                <div class="relative mb-5">
                    <i data-lucide="search" class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
                    <input type="text" id="help-search" class="input pl-11" placeholder="Search help..."
                           oninput="HelpPage.search(this.value)">
                </div>

                <!-- Accordion Sections -->
                <div id="help-sections" class="space-y-2">
                    ${this.sections.map((s, i) => `
                        <div class="help-section glass-card" id="help-sec-${i}">
                            <div class="help-section-header" aria-expanded="false"
                                 onclick="HelpPage.toggle(${i})">
                                <div class="flex items-center gap-3">
                                    <div class="w-9 h-9 rounded-xl flex items-center justify-center bg-gray-50 dark:bg-slate-800/80 flex-shrink-0">
                                        <i data-lucide="${s.icon}" class="w-5 h-5 ${s.color}"></i>
                                    </div>
                                    <span class="font-semibold text-gray-800 dark:text-white text-sm">${s.title}</span>
                                </div>
                                <i data-lucide="chevron-down" class="w-5 h-5 text-gray-400 help-chevron flex-shrink-0"></i>
                            </div>
                            <div class="help-section-body" id="help-body-${i}">
                                <div class="px-5 pb-5 pt-1 border-t border-gray-100 dark:border-slate-700/50">
                                    ${s.content}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Footer tip -->
                <div class="mt-6 p-4 rounded-xl bg-gray-50 dark:bg-slate-800/40 text-center">
                    <p class="text-xs text-gray-400 dark:text-slate-500">
                        <i data-lucide="info" class="w-3 h-3 inline mr-1"></i>
                        Need more help? Check the source code or contact the developer.
                        Version ${new Date().getFullYear()} · PH-Lending Pro
                    </p>
                </div>
            </div>
        `;
        lucide.createIcons();
    },

    toggle(index) {
        const header = document.querySelector(`#help-sec-${index} .help-section-header`);
        const body = document.getElementById(`help-body-${index}`);
        const isOpen = body.classList.contains('open');

        body.classList.toggle('open', !isOpen);
        header.setAttribute('aria-expanded', !isOpen);
        lucide.createIcons();
    },

    search(query) {
        const q = query.toLowerCase().trim();
        this.sections.forEach((s, i) => {
            const sec = document.getElementById(`help-sec-${i}`);
            if (!sec) return;
            const text = (s.title + ' ' + s.content).toLowerCase();
            const match = !q || text.includes(q);
            sec.style.display = match ? '' : 'none';

            // Auto-open matching sections when searching
            if (q && match) {
                const body = document.getElementById(`help-body-${i}`);
                const header = document.querySelector(`#help-sec-${i} .help-section-header`);
                body.classList.add('open');
                header.setAttribute('aria-expanded', 'true');
            } else if (!q) {
                const body = document.getElementById(`help-body-${i}`);
                const header = document.querySelector(`#help-sec-${i} .help-section-header`);
                body.classList.remove('open');
                header.setAttribute('aria-expanded', 'false');
            }
        });
    }
};
