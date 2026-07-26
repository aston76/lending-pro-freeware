/**
 * Lending Pro Freeware — Reusable UI Components
 * Modal, Toast, StarRating, DataTable, StatCard, MapOverlay
 */

const UI = {
    // ═══════════════════════════════════════════════════════════
    // MODAL
    // ═══════════════════════════════════════════════════════════
    showModal(title, content, options = {}) {
        const { width = 'max-w-lg', onClose, showClose = true } = options;
        const container = document.getElementById('modal-container');
        container.innerHTML = `
            <div class="modal-overlay fixed inset-0 z-40 flex items-center justify-center p-4">
                <div class="modal-content ${width} w-full max-h-[85vh] flex flex-col z-50" onclick="event.stopPropagation()">
                    <div class="flex items-center justify-between px-5 py-4" style="border-bottom: 0.5px solid var(--surface-2);">
                        <h3 class="text-base font-semibold" style="color:var(--text-primary);">${title}</h3>
                        ${showClose ? `<button onclick="UI.closeModal()" class="btn btn-icon btn-ghost"><i data-lucide="x" class="w-4 h-4"></i></button>` : ''}
                    </div>
                    <div class="px-5 py-4 overflow-y-auto flex-1">${content}</div>
                </div>
            </div>
        `;
        container._onClose = onClose;
        lucide.createIcons();
        if (typeof SoundEngine !== 'undefined') SoundEngine.modalOpen();
    },

    closeModal() {
        const container = document.getElementById('modal-container');
        if (container._onClose) container._onClose();
        if (container.innerHTML && typeof SoundEngine !== 'undefined') SoundEngine.modalClose();
        container.innerHTML = '';
    },

    // Keep for legacy calls but now a no-op — backdrop click no longer closes modal
    closeModalOutside(e) {
        // Intentionally disabled: users must use the X button or Cancel
    },

    // ═══════════════════════════════════════════════════════════
    // MAP OVERLAY (Leaflet + OpenStreetMap — overlay SEPARE du modal formulaire)
    // S'ouvre PAR-DESSUS le formulaire sans l'effacer.
    // L'epingle est draggable + reverse geocoding au release.
    // ═══════════════════════════════════════════════════════════
    showMapModal(address, lat, lon, inputId) {
        // Supprimer tout overlay existant proprement
        const existing = document.getElementById('map-overlay');
        if (existing) existing.remove();

        const hasCoords = !!(lat && lon);
        const displayLat = hasCoords ? lat : 10.3157;
        const displayLon = hasCoords ? lon : 123.8854;
        const coordText = hasCoords
            ? (parseFloat(lat).toFixed(5) + ', ' + parseFloat(lon).toFixed(5))
            : 'Deplacez l\'epingle pour preciser la position';

        const confirmBtnHtml = inputId
            ? '<button id="map-overlay-confirm" style="padding:6px 16px;border-radius:10px;border:none;cursor:pointer;background:#007AFF;color:#fff;font-size:13px;font-weight:600;">&#10003; Confirmer</button>'
            : '';

        const overlay = document.createElement('div');
        overlay.id = 'map-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,0.7);backdrop-filter:blur(6px);';

        overlay.innerHTML =
            '<div style="width:100%;max-width:720px;background:var(--surface-2,#1c1c1e);border-radius:20px;overflow:hidden;box-shadow:0 24px 64px rgba(0,0,0,0.6);display:flex;flex-direction:column;">' +
            '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:0.5px solid rgba(255,255,255,0.08);">' +
            '<div style="display:flex;align-items:center;gap:8px;">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>' +
            '<span id="map-overlay-title" style="font-size:14px;font-weight:600;color:var(--text-primary,#fff);max-width:500px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + address + '</span>' +
            '</div>' +
            '<button id="map-overlay-close" style="width:28px;height:28px;border-radius:50%;border:none;cursor:pointer;background:rgba(255,255,255,0.1);color:var(--text-primary,#fff);font-size:18px;line-height:1;display:flex;align-items:center;justify-content:center;">&times;</button>' +
            '</div>' +
            '<div id="map-overlay-leaflet" style="height:420px;background:#e8e4e0;"></div>' +
            '<div style="padding:10px 18px;display:flex;align-items:center;justify-content:space-between;border-top:0.5px solid rgba(255,255,255,0.08);">' +
            '<p id="map-overlay-coords" style="font-size:11px;color:var(--text-tertiary,#888);font-family:monospace;">' + coordText + '</p>' +
            '<div style="display:flex;gap:8px;">' +
            confirmBtnHtml +
            '<button id="map-overlay-close2" style="padding:6px 14px;border-radius:8px;border:none;cursor:pointer;background:rgba(255,255,255,0.1);color:var(--text-primary,#fff);font-size:13px;">Close</button>' +
            '</div>' +
            '</div>' +
            '</div>';

        document.body.appendChild(overlay);

        document.getElementById('map-overlay-close').onclick = function () { UI.closeMapOverlay(); };
        document.getElementById('map-overlay-close2').onclick = function () { UI.closeMapOverlay(); };

        // Initialiser Leaflet
        UI._initLeafletMapOverlay(displayLat, displayLon, address, inputId, hasCoords);
    },

    closeMapOverlay() {
        const overlay = document.getElementById('map-overlay');
        if (overlay) overlay.remove();
    },

    _initLeafletMapOverlay(lat, lon, address, inputId, hasCoords) {
        // Charger Leaflet CSS si necessaire
        if (!document.getElementById('leaflet-css')) {
            const css = document.createElement('link');
            css.id = 'leaflet-css';
            css.rel = 'stylesheet';
            css.href = 'vendor/leaflet.css';
            document.head.appendChild(css);
        }

        const initMap = function () {
            const mapEl = document.getElementById('map-overlay-leaflet');
            if (!mapEl) return;

            const zoom = hasCoords ? 17 : 13;
            const map = L.map('map-overlay-leaflet', { zoomControl: true, scrollWheelZoom: true })
                .setView([lat, lon], zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 19
            }).addTo(map);

            // Icone epingle personnalisee
            const pinIcon = L.divIcon({
                className: '',
                html: '<div style="width:32px;height:32px;background:var(--accent);border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid white;box-shadow:0 3px 8px rgba(0,0,0,0.24);cursor:grab;"></div>',
                iconSize: [32, 32],
                iconAnchor: [16, 32]
            });

            // Marqueur DRAGGABLE
            const marker = L.marker([lat, lon], { icon: pinIcon, draggable: true })
                .addTo(map)
                .bindPopup('<strong>' + address + '</strong><br><span style="font-size:11px;color:#888">Deplacez l\'epingle pour preciser</span>')
                .openPopup();

            // Mise a jour coords + reverse geocoding apres deplacement
            marker.on('dragend', function (e) {
                const newLat = e.target.getLatLng().lat;
                const newLon = e.target.getLatLng().lng;

                const coordsEl = document.getElementById('map-overlay-coords');
                if (coordsEl) coordsEl.textContent = newLat.toFixed(5) + ', ' + newLon.toFixed(5);

                if (inputId && typeof ClientsPage !== 'undefined') {
                    if (!ClientsPage._addrCoords) ClientsPage._addrCoords = {};
                    // Stocker immediatement les coords brutes
                    ClientsPage._addrCoords[inputId] = { lat: newLat, lon: newLon, label: address };

                    // Reverse geocoding pour obtenir le label de la nouvelle position
                    fetch(
                        'https://nominatim.openstreetmap.org/reverse?lat=' + newLat + '&lon=' + newLon + '&format=json',
                        { headers: { 'Accept-Language': 'en', 'User-Agent': 'Lending-Pro-Freeware/1.0' } }
                    )
                        .then(function (r) { return r.json(); })
                        .then(function (data) {
                            const a = data.address || {};
                            const parts = [
                                (a.house_number && a.road) ? (a.house_number + ' ' + a.road) : (a.road || ''),
                                a.suburb || a.neighbourhood || a.village || a.hamlet || '',
                                a.city || a.town || a.municipality || a.county || '',
                                a.state || ''
                            ].filter(Boolean);
                            const newLabel = parts.length
                                ? parts.join(', ')
                                : ((data.display_name || '').split(',').slice(0, 3).join(',').trim());

                            // Mettre a jour le stockage avec le label reverse-geocode
                            ClientsPage._addrCoords[inputId] = { lat: newLat, lon: newLon, label: newLabel };

                            // Mettre a jour le popup du marqueur
                            marker.setPopupContent('<strong>' + newLabel + '</strong><br><span style="font-size:11px;color:#888">' + newLat.toFixed(5) + ', ' + newLon.toFixed(5) + '</span>');
                            marker.openPopup();

                            // Mettre a jour le titre de l'overlay
                            const titleEl = document.getElementById('map-overlay-title');
                            if (titleEl) titleEl.textContent = newLabel;

                            // Mettre a jour le bouton Confirmer
                            UI._bindMapConfirmBtn(inputId, marker);
                        })
                        .catch(function () {
                            // Echec reverse geocoding — garder coords sans label mis a jour
                            UI._bindMapConfirmBtn(inputId, marker);
                        });
                }
            });

            // Bouton Confirmer — utilise la derniere position du marqueur
            UI._bindMapConfirmBtn(inputId, marker);

            setTimeout(function () { map.invalidateSize(); }, 150);
        };

        if (typeof L !== 'undefined') {
            initMap();
        } else {
            const script = document.createElement('script');
            script.id = 'leaflet-js';
            script.src = 'vendor/leaflet.js';
            script.onload = initMap;
            document.head.appendChild(script);
        }
    },

    _bindMapConfirmBtn(inputId, marker) {
        const confirmBtn = document.getElementById('map-overlay-confirm');
        if (!confirmBtn || !inputId) return;
        // Retirer l'ancien listener en clonant le bouton
        const fresh = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(fresh, confirmBtn);
        fresh.onclick = function () {
            const pos = marker.getLatLng();
            const stored = ClientsPage._addrCoords && ClientsPage._addrCoords[inputId];
            const label = (stored && stored.label) ? stored.label : '';
            const inp = document.getElementById(inputId);
            if (inp && label) inp.value = label;
            // S'assurer que les coords finales sont enregistrees
            if (typeof ClientsPage !== 'undefined') {
                if (!ClientsPage._addrCoords) ClientsPage._addrCoords = {};
                ClientsPage._addrCoords[inputId] = {
                    lat: pos.lat,
                    lon: pos.lng,
                    label: label || (inp ? inp.value : '')
                };
            }
            // Fermer la carte ET le dropdown d'adresse qui pourrait etre encore ouvert
            UI.closeMapOverlay();
            if (typeof ClientsPage !== 'undefined') ClientsPage._closeAllAddrDropdowns();
            if (typeof SoundEngine !== 'undefined') SoundEngine.click();
        };
    },

    // ═══════════════════════════════════════════════════════════
    // TOAST NOTIFICATIONS
    // ═══════════════════════════════════════════════════════════
    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const icons = { success: 'check-circle', error: 'alert-circle', warning: 'alert-triangle', info: 'info' };
        const id = 'toast-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = `toast toast-${type}`;
        div.innerHTML = `<i data-lucide="${icons[type]}" class="w-5 h-5 flex-shrink-0"></i><span>${message}</span>`;
        container.appendChild(div);
        lucide.createIcons({ node: div });
        setTimeout(() => div.remove(), 4000);
        if (typeof SoundEngine !== 'undefined') {
            if (type === 'success') SoundEngine.success();
            else if (type === 'error') SoundEngine.error();
        }
    },

    // ═══════════════════════════════════════════════════════════
    // STAR RATING
    // ═══════════════════════════════════════════════════════════
    starRating(rating, editable = false, onChange = null, size = 'w-5 h-5') {
        let html = '<div class="flex items-center gap-0.5">';
        for (let i = 1; i <= 5; i++) {
            const filled = i <= rating;
            if (editable) {
                html += `<span class="star ${filled ? 'filled' : 'empty'}" onclick="${onChange}(${i})">
                    <i data-lucide="star" class="${size} ${filled ? 'fill-current' : ''}"></i>
                </span>`;
            } else {
                html += `<i data-lucide="star" class="${size} ${filled ? 'text-amber-400 fill-amber-400' : 'text-gray-300 dark:text-slate-600'}"></i>`;
            }
        }
        html += '</div>';
        return html;
    },

    // ═══════════════════════════════════════════════════════════
    // STATUS BADGE
    // ═══════════════════════════════════════════════════════════
    badge(status) {
        const map = {
            active: { class: 'badge-active', icon: 'activity', label: 'Active' },
            paid: { class: 'badge-paid', icon: 'check-circle', label: 'Paid' },
            defaulted: { class: 'badge-defaulted', icon: 'alert-circle', label: 'Defaulted' },
            refinanced: { class: 'badge-pending', icon: 'refresh-cw', label: 'Refinanced' },
            pending: { class: 'badge-pending', icon: 'clock', label: 'Pending' },
        };
        const s = map[status] || { class: 'badge-active', icon: 'circle', label: status };
        return `<span class="badge ${s.class}"><i data-lucide="${s.icon}" class="w-3 h-3"></i>${s.label}</span>`;
    },

    // ═══════════════════════════════════════════════════════════
    // STAT CARD
    // ═══════════════════════════════════════════════════════════
    statCard(icon, label, value, color = 'blue', extra = '') {
        const tones = ['blue', 'green', 'red', 'amber', 'purple', 'cyan'];
        const tone = tones.includes(color) ? color : 'blue';
        return `
            <div class="stat-card stat-card-${tone} animate-slide-up">
                <div class="flex items-start justify-between">
                    <div class="min-w-0">
                        <p class="stat-label">${label}</p>
                        <p class="stat-value animate-count">${value}</p>
                        ${extra ? `<p class="stat-extra">${extra}</p>` : ''}
                    </div>
                    <div class="stat-icon">
                        <i data-lucide="${icon}" class="w-4 h-4"></i>
                    </div>
                </div>
            </div>
        `;
    },

    // ═══════════════════════════════════════════════════════════
    // EMPTY STATE
    // ═══════════════════════════════════════════════════════════
    emptyState(icon, title, desc, action = '') {
        return `
            <div class="flex flex-col items-center justify-center py-16 text-center">
                <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                    <i data-lucide="${icon}" class="w-8 h-8 text-gray-400 dark:text-slate-500"></i>
                </div>
                <h3 class="text-lg font-semibold text-gray-600 dark:text-slate-400">${title}</h3>
                <p class="text-sm text-gray-400 dark:text-slate-500 mt-1 max-w-sm">${desc}</p>
                ${action ? `<div class="mt-4">${action}</div>` : ''}
            </div>
        `;
    },

    // ═══════════════════════════════════════════════════════════
    // LOADING SKELETON
    // ═══════════════════════════════════════════════════════════
    skeleton(lines = 3) {
        let html = '<div class="animate-pulse space-y-3 p-4">';
        const widths = ['100%', '72%', '52%'];
        for (let i = 0; i < lines; i++) {
            html += `<div class="h-4 rounded-lg" style="width:${widths[i % 3]}; background:var(--surface-2);"></div>`;
        }
        html += '</div>';
        return html;
    },

    // ═══════════════════════════════════════════════════════════
    // PAGINATION
    // ═══════════════════════════════════════════════════════════
    pagination(page, totalPages, onPageChange) {
        if (totalPages <= 1) return '';
        let html = '<div class="flex items-center justify-center gap-2 mt-4">';
        html += `<button onclick="${onPageChange}(${page - 1})" class="btn btn-sm btn-ghost" ${page <= 1 ? 'disabled' : ''}><i data-lucide="chevron-left" class="w-4 h-4"></i></button>`;

        const start = Math.max(1, page - 2);
        const end = Math.min(totalPages, page + 2);

        if (start > 1) html += `<button onclick="${onPageChange}(1)" class="btn btn-sm btn-ghost">1</button>`;
        if (start > 2) html += '<span class="text-gray-400">…</span>';

        for (let i = start; i <= end; i++) {
            html += `<button onclick="${onPageChange}(${i})" class="btn btn-sm ${i === page ? 'btn-primary' : 'btn-ghost'}">${i}</button>`;
        }

        if (end < totalPages - 1) html += '<span class="text-gray-400">…</span>';
        if (end < totalPages) html += `<button onclick="${onPageChange}(${totalPages})" class="btn btn-sm btn-ghost">${totalPages}</button>`;

        html += `<button onclick="${onPageChange}(${page + 1})" class="btn btn-sm btn-ghost" ${page >= totalPages ? 'disabled' : ''}><i data-lucide="chevron-right" class="w-4 h-4"></i></button>`;
        html += '</div>';
        return html;
    },

    // ═══════════════════════════════════════════════════════════
    // CONFIRM DIALOG
    // ═══════════════════════════════════════════════════════════
    confirm(message, onConfirm) {
        UI._currentConfirmCall = onConfirm;
        UI.showModal('Confirm', `
            <p class="text-gray-600 dark:text-slate-300 mb-6">${message}</p>
            <div class="flex gap-3 justify-end">
                <button onclick="UI.closeModal()" class="btn btn-ghost">Cancel</button>
                <button onclick="if(UI._currentConfirmCall) UI._currentConfirmCall(); UI.closeModal();" class="btn btn-danger">Confirm</button>
            </div>
        `, { width: 'max-w-sm' });
    },

    // ═══════════════════════════════════════════════════════════
    // FORMAT HELPERS
    // ═══════════════════════════════════════════════════════════
    formatCurrency(amount) {
        if (amount == null || isNaN(amount)) return '₱ 0.00';
        return '₱ ' + Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    formatDate(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },

    formatDateShort(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) + ' ' +
            d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    }
};
