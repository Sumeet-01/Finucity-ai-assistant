/* ============================================================
   FINUCITY ADMIN DASHBOARD - WORLD-CLASS JS ENGINE
   Real-time data, command palette, notifications, charts
   Author: Sumeet Sangwan
   ============================================================ */

const AdminDashboard = (() => {
    'use strict';

    // ========== STATE ==========
    const state = {
        stats: {},
        users: [],
        caApplications: [],
        notifications: [],
        isLoading: true,
        refreshInterval: null,
        sidebarCollapsed: localStorage.getItem('admin_sidebar_collapsed') === 'true',
        cmdPaletteOpen: false,
        notifPanelOpen: false,
        charts: {}
    };

    // ========== API ENDPOINTS ==========
    const API = {
        stats: '/api/admin/stats',
        caApplications: '/api/admin/ca-applications',
        approveCa: (id) => `/api/admin/ca-application/${id}/approve`,
        rejectCa: (id) => `/api/admin/ca-application/${id}/reject`,
        updateRole: (id) => `/api/admin/users/${id}/role`,
        suspendCa: '/api/admin/ca/suspend',
        unsuspendCa: '/api/admin/ca/unsuspend',
        banCa: '/api/admin/ca/ban',
        freezeEarnings: '/api/admin/ca/freeze-earnings',
        unfreezeEarnings: '/api/admin/ca/unfreeze-earnings',
        caActions: (id) => `/api/admin/ca/actions/${id}`,
    };

    // ========== UTILITIES ==========
    const $ = (sel, ctx = document) => ctx.querySelector(sel);
    const $$ = (sel, ctx = document) => ctx.querySelectorAll(sel);

    const formatNumber = (n) => {
        if (n === null || n === undefined) return '0';
        if (n >= 10000000) return (n / 10000000).toFixed(1) + 'Cr';
        if (n >= 100000) return (n / 100000).toFixed(1) + 'L';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
        return n?.toLocaleString('en-IN') || '0';
    };

    const formatCurrency = (n) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency', currency: 'INR', maximumFractionDigits: 0
        }).format(n || 0);
    };

    const timeAgo = (date) => {
        if (!date) return 'Unknown';
        const seconds = Math.floor((new Date() - new Date(date)) / 1000);
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';
        return new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    };

    const getInitials = (firstName, lastName) => {
        return ((firstName?.[0] || '') + (lastName?.[0] || '')).toUpperCase() || 'U';
    };

    // ========== API CALLS ==========
    async function apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Request failed');
            return data;
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            showToast(error.message, 'error');
            throw error;
        }
    }

    // ========== TOAST NOTIFICATIONS ==========
    function showToast(message, type = 'info', duration = 4000) {
        let container = $('#admin-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'admin-toast-container';
            container.className = 'admin-toast-container';
            document.body.appendChild(container);
        }

        const icons = {
            success: 'fa-check-circle', error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle', info: 'fa-info-circle'
        };

        const toast = document.createElement('div');
        toast.className = `admin-toast ${type}`;
        toast.style.setProperty('--toast-duration', `${duration}ms`);
        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'toastOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ========== SIDEBAR ==========
    function initSidebar() {
        const layout = $('.admin-layout');
        const toggle = $('#sidebarToggle');

        if (state.sidebarCollapsed) layout?.classList.add('sidebar-collapsed');

        toggle?.addEventListener('click', () => {
            state.sidebarCollapsed = !state.sidebarCollapsed;
            layout?.classList.toggle('sidebar-collapsed');
            localStorage.setItem('admin_sidebar_collapsed', state.sidebarCollapsed);
        });

        // Active link highlighting
        const currentPath = window.location.pathname;
        $$('.sidebar-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                link.classList.add('active');
            }
        });

        // Mobile toggle
        const mobileToggle = $('#mobileSidebarToggle');
        const sidebar = $('.admin-sidebar');
        mobileToggle?.addEventListener('click', () => sidebar?.classList.toggle('mobile-open'));
    }

    // ========== COMMAND PALETTE ==========
    function initCommandPalette() {
        const overlay = $('#cmdPaletteOverlay');
        const input = $('#cmdPaletteInput');
        const results = $('#cmdPaletteResults');

        const commands = [
            { icon: 'fa-chart-pie', label: 'Dashboard Overview', action: () => window.location.href = '/admin/dashboard' },
            { icon: 'fa-users', label: 'Manage Users', action: () => window.location.href = '/admin/users', shortcut: 'G U' },
            { icon: 'fa-user-tie', label: 'CA Applications', action: () => window.location.href = '/admin/ca-applications', shortcut: 'G C' },
            { icon: 'fa-chart-line', label: 'Analytics', action: () => window.location.href = '/admin/analytics' },
            { icon: 'fa-concierge-bell', label: 'Services', action: () => window.location.href = '/admin/services' },
            { icon: 'fa-receipt', label: 'Bookings', action: () => window.location.href = '/admin/bookings' },
            { icon: 'fa-gavel', label: 'Disputes', action: () => window.location.href = '/admin/disputes' },
            { icon: 'fa-tags', label: 'Pricing', action: () => window.location.href = '/admin/pricing' },
            { icon: 'fa-cog', label: 'Settings', action: () => window.location.href = '/admin/settings' },
            { icon: 'fa-sync-alt', label: 'Refresh Data', action: () => { loadAllData(); closePalette(); }, shortcut: 'R' },
            { icon: 'fa-sign-out-alt', label: 'Logout', action: () => window.location.href = '/auth/logout' },
            { icon: 'fa-home', label: 'Main Site', action: () => window.location.href = '/' },
            { icon: 'fa-robot', label: 'AI Chat', action: () => window.location.href = '/chat/' },
        ];

        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); togglePalette(); }
            if (e.key === 'Escape') closePalette();
        });

        $('.cmd-palette-trigger')?.addEventListener('click', togglePalette);

        function togglePalette() {
            state.cmdPaletteOpen = !state.cmdPaletteOpen;
            if (state.cmdPaletteOpen) {
                overlay?.classList.add('open');
                input?.focus();
                renderCommands(commands);
            } else { closePalette(); }
        }

        function closePalette() {
            state.cmdPaletteOpen = false;
            overlay?.classList.remove('open');
            if (input) input.value = '';
        }

        overlay?.addEventListener('click', (e) => { if (e.target === overlay) closePalette(); });

        input?.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            renderCommands(commands.filter(c => c.label.toLowerCase().includes(query)));
        });

        function renderCommands(cmds) {
            if (!results) return;
            results.innerHTML = cmds.map((c, i) => `
                <div class="cmd-palette-item ${i === 0 ? 'selected' : ''}" data-index="${i}">
                    <i class="fas ${c.icon}"></i>
                    <span>${c.label}</span>
                    ${c.shortcut ? `<span class="cmd-shortcut">${c.shortcut}</span>` : ''}
                </div>
            `).join('');

            results.querySelectorAll('.cmd-palette-item').forEach((item, idx) => {
                item.addEventListener('click', () => { cmds[idx].action(); closePalette(); });
            });
        }

        input?.addEventListener('keydown', (e) => {
            const items = results?.querySelectorAll('.cmd-palette-item');
            if (!items?.length) return;
            const current = results.querySelector('.cmd-palette-item.selected');
            let idx = current ? parseInt(current.dataset.index) : 0;

            if (e.key === 'ArrowDown') {
                e.preventDefault(); current?.classList.remove('selected');
                idx = (idx + 1) % items.length;
                items[idx].classList.add('selected');
                items[idx].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'ArrowUp') {
                e.preventDefault(); current?.classList.remove('selected');
                idx = (idx - 1 + items.length) % items.length;
                items[idx].classList.add('selected');
                items[idx].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                e.preventDefault(); current?.click();
            }
        });
    }

    // ========== NOTIFICATION PANEL ==========
    function initNotificationPanel() {
        const panel = $('.notification-panel');
        const overlay = $('.notification-panel-overlay');
        $('#notifBtn')?.addEventListener('click', () => toggleNotif());
        overlay?.addEventListener('click', () => toggleNotif(false));
        $('#closeNotifPanel')?.addEventListener('click', () => toggleNotif(false));

        function toggleNotif(force) {
            state.notifPanelOpen = force !== undefined ? force : !state.notifPanelOpen;
            panel?.classList.toggle('open', state.notifPanelOpen);
            overlay?.classList.toggle('open', state.notifPanelOpen);
        }
    }

    // ========== DATA LOADING ==========
    async function loadStats() {
        try {
            const data = await apiCall(API.stats);
            if (data.success) { state.stats = data.data; renderStats(); }
        } catch (e) { /* silently fail for auto-refresh */ }
    }

    async function loadCAApplications() {
        try {
            const data = await apiCall(API.caApplications);
            if (data.success) { state.caApplications = data.data || []; renderCAApplications(); }
        } catch (e) { /* silently fail */ }
    }

    async function loadAllData() {
        state.isLoading = true;
        await Promise.all([loadStats(), loadCAApplications()]);
        state.isLoading = false;
        updateLastRefresh();
    }

    // ========== RENDERING ==========
    function renderStats() {
        const s = state.stats;
        animateValue('statTotalUsers', s.total_users || 0);
        animateValue('statActiveCAs', s.active_cas || 0);
        animateValue('statPendingApps', s.pending_applications || 0);
        animateValue('statTotalQueries', s.total_queries || 0);

        // Pending badge
        const badge = $('#pendingAppsBadge');
        if (badge) {
            const count = s.pending_applications || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }

        // Update charts if they exist
        updateCharts();
    }

    function animateValue(id, target) {
        const el = document.getElementById(id);
        if (!el) return;
        const start = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
        if (start === target) { el.textContent = formatNumber(target); return; }

        const duration = 600;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = formatNumber(Math.round(start + (target - start) * eased));
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    function renderCAApplications() {
        const container = $('#caAppsList');
        if (!container) return;

        const apps = state.caApplications.slice(0, 5);

        if (apps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle text-success"></i>
                    <h4>All Caught Up</h4>
                    <p>No pending CA applications at the moment</p>
                </div>`;
            return;
        }

        container.innerHTML = `
            <div class="admin-table-wrapper">
                <table class="admin-table">
                    <thead><tr><th>Applicant</th><th>Status</th><th>Applied</th><th>Actions</th></tr></thead>
                    <tbody>
                        ${apps.map(app => `
                            <tr>
                                <td><div class="table-user">
                                    <div class="table-user-avatar">${getInitials(app.first_name, app.last_name)}</div>
                                    <div class="table-user-info">
                                        <h5>${app.first_name || ''} ${app.last_name || ''}</h5>
                                        <span>${app.email || ''}</span>
                                    </div>
                                </div></td>
                                <td><span class="status-badge ca_pending">Pending</span></td>
                                <td>${timeAgo(app.created_at)}</td>
                                <td><div class="d-flex gap-sm">
                                    <button class="btn-admin success sm" onclick="AdminDashboard.approveCA('${app.id}')"><i class="fas fa-check"></i> Approve</button>
                                    <button class="btn-admin danger sm" onclick="AdminDashboard.rejectCA('${app.id}')"><i class="fas fa-times"></i></button>
                                </div></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>`;
    }

    function updateLastRefresh() {
        const el = $('#lastRefresh');
        if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    }

    // ========== CA ACTIONS ==========
    async function approveCA(appId) {
        if (!confirm('Approve this CA application? The user will get CA role.')) return;
        try {
            const data = await apiCall(API.approveCa(appId), { method: 'POST', body: JSON.stringify({}) });
            if (data.success) { showToast('CA approved successfully!', 'success'); await loadAllData(); }
        } catch (e) { /* handled */ }
    }

    async function rejectCA(appId) {
        const reason = prompt('Enter rejection reason:');
        if (!reason) return;
        try {
            const data = await apiCall(API.rejectCa(appId), { method: 'POST', body: JSON.stringify({ reason }) });
            if (data.success) { showToast('Application rejected', 'warning'); await loadAllData(); }
        } catch (e) { /* handled */ }
    }

    // ========== CHARTS ==========
    function initCharts() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.color = '#71717a';
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Inter", sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.plugins.legend.display = false;

        initUserGrowthChart();
        initRoleDistributionChart();
    }

    function initUserGrowthChart() {
        const ctx = document.getElementById('userGrowthChart');
        if (!ctx) return;

        const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const currentMonth = new Date().getMonth();
        const activeLabels = labels.slice(0, currentMonth + 1);
        const baseVal = Math.max((state.stats.total_users || 10) - 50, 2);
        const growthData = activeLabels.map((_, i) => Math.round(baseVal + (i * (state.stats.total_users || 10) / activeLabels.length)));

        state.charts.userGrowth = new Chart(ctx, {
            type: 'line',
            data: {
                labels: activeLabels,
                datasets: [{
                    data: growthData,
                    borderColor: '#fba002',
                    backgroundColor: 'rgba(251, 160, 2, 0.08)',
                    borderWidth: 2, fill: true, tension: 0.4,
                    pointRadius: 0, pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#fba002',
                    pointHoverBorderColor: '#fff', pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    tooltip: {
                        backgroundColor: '#1c1c22', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, padding: 12,
                        callbacks: { label: (ctx) => `Users: ${ctx.parsed.y}` }
                    }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { font: { size: 11 } } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { font: { size: 11 } }, beginAtZero: true }
                }
            }
        });
    }

    function initRoleDistributionChart() {
        const ctx = document.getElementById('roleDistChart');
        if (!ctx) return;

        const s = state.stats;
        const users = Math.max((s.total_users || 1) - (s.active_cas || 0) - (s.pending_applications || 0), 1);

        state.charts.roleDist = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Regular Users', 'Active CAs', 'Pending CAs'],
                datasets: [{
                    data: [users, s.active_cas || 0, s.pending_applications || 0],
                    backgroundColor: ['#06b6d4', '#22c55e', '#f59e0b'],
                    borderWidth: 0, hoverOffset: 6
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '72%',
                plugins: {
                    tooltip: { backgroundColor: '#1c1c22', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, padding: 12 }
                }
            }
        });
    }

    function updateCharts() {
        if (state.charts.roleDist) {
            const s = state.stats;
            const users = Math.max((s.total_users || 1) - (s.active_cas || 0) - (s.pending_applications || 0), 1);
            state.charts.roleDist.data.datasets[0].data = [users, s.active_cas || 0, s.pending_applications || 0];
            state.charts.roleDist.update('none');
        }
    }

    // ========== REAL-TIME REFRESH ==========
    function startAutoRefresh(intervalMs = 30000) {
        state.refreshInterval = setInterval(() => loadStats(), intervalMs);
    }

    function stopAutoRefresh() {
        if (state.refreshInterval) { clearInterval(state.refreshInterval); state.refreshInterval = null; }
    }

    // ========== INIT ==========
    function init() {
        initSidebar();
        initCommandPalette();
        initNotificationPanel();
        loadAllData().then(() => initCharts());
        startAutoRefresh();

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) stopAutoRefresh();
            else { startAutoRefresh(); loadStats(); }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey) { loadAllData(); showToast('Refreshing...', 'info', 1500); }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { approveCA, rejectCA, showToast, loadAllData, state, formatNumber, formatCurrency, timeAgo, getInitials };
})();

window.AdminDashboard = AdminDashboard;
