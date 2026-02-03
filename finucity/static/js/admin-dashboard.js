/**
 * Admin Dashboard JavaScript
 * Production-grade CA ecosystem management interface
 * Author: Sumeet Sangwan (Fintech-grade implementation)
 */

// ==================== GLOBAL VARIABLES ====================
let currentTab = 'overview';
let dashboardData = {
    statistics: {},
    applications: [],
    verifiedCAs: [],
    complaints: [],
    auditLogs: [],
    settings: {}
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    loadInitialData();
});

function initializeDashboard() {
    // Set up tab navigation
    const tabs = document.querySelectorAll('.admin-nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
    
    // Set up filter listeners
    setupFilterListeners();
    
    // Set up form submissions
    setupFormListeners();
}

function setupEventListeners() {
    // Modal close handlers
    document.querySelectorAll('.admin-modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.admin-modal');
            modal.classList.remove('active');
        });
    });
    
    // Close modal on background click
    document.querySelectorAll('.admin-modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
    
    // Search functionality
    const caSearch = document.getElementById('caSearch');
    if (caSearch) {
        caSearch.addEventListener('input', debounce(filterVerifiedCAs, 300));
    }
}

function setupFilterListeners() {
    // Application filter
    const appFilter = document.getElementById('applicationFilter');
    if (appFilter) {
        appFilter.addEventListener('change', filterApplications);
    }
    
    // Complaint filter
    const complaintFilter = document.getElementById('complaintFilter');
    if (complaintFilter) {
        complaintFilter.addEventListener('change', filterComplaints);
    }
    
    // Audit log filter
    const logFilter = document.getElementById('logActionFilter');
    if (logFilter) {
        logFilter.addEventListener('change', filterAuditLogs);
    }
}

function setupFormListeners() {
    // Settings form
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings();
        });
    }
}

// ==================== TAB MANAGEMENT ====================
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.admin-tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all nav tabs
    document.querySelectorAll('.admin-nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to nav tab
    const navTab = document.querySelector(`[data-tab="${tabName}"]`);
    if (navTab) {
        navTab.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'applications':
            loadApplications();
            break;
        case 'verified-cas':
            loadVerifiedCAs();
            break;
        case 'complaints':
            loadComplaints();
            break;
        case 'audit-logs':
            loadAuditLogs();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ==================== DATA LOADING ====================
async function loadInitialData() {
    try {
        await Promise.all([
            loadStatistics(),
            loadOverviewData()
        ]);
    } catch (error) {
        console.error('Error loading initial data:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/ca-ecosystem/statistics');
        const data = await response.json();
        
        if (data.success) {
            dashboardData.statistics = data.statistics;
            updateStatisticsDisplay();
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

function updateStatisticsDisplay() {
    const stats = dashboardData.statistics;
    
    // Update header stats
    updateElement('totalCas', stats.total_cas || 0);
    updateElement('pendingApps', stats.pending_applications || 0);
    updateElement('activeComplaints', stats.complaints_count || 0);
    
    // Update overview stats
    updateElement('verifiedCasCount', stats.verified_cas || 0);
    updateElement('pendingAppsCount', stats.pending_applications || 0);
    updateElement('complaintsCount', stats.complaints_count || 0);
    updateElement('suspendedCasCount', stats.suspended_cas || 0);
    
    // Update badges
    updateBadge('pendingBadge', stats.pending_applications || 0);
    updateBadge('complaintBadge', stats.complaints_count || 0);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value.toLocaleString();
    }
}

function updateBadge(id, value) {
    const badge = document.getElementById(id);
    if (badge) {
        if (value > 0) {
            badge.textContent = value > 99 ? '99+' : value;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

async function loadOverviewData() {
    try {
        const response = await fetch('/api/ca-ecosystem/statistics');
        const data = await response.json();
        
        if (data.success) {
            displayRecentActivity(data.statistics.recent_applications || []);
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
        document.getElementById('recentActivity').innerHTML = '<div class="admin-empty">No recent activity</div>';
    }
}

function displayRecentActivity(applications) {
    const container = document.getElementById('recentActivity');
    
    if (!applications || applications.length === 0) {
        container.innerHTML = '<div class="admin-empty">No recent activity</div>';
        return;
    }
    
    const html = applications.map(app => `
        <div class="admin-table-container">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Application</th>
                        <th>ICAI Number</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${app.full_name || 'N/A'}</td>
                        <td>${app.icai_number || 'N/A'}</td>
                        <td>${createStatusBadge(app.status)}</td>
                        <td>${formatDate(app.created_at)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// ==================== APPLICATIONS MANAGEMENT ====================
async function loadApplications() {
    const container = document.getElementById('applicationsList');
    container.innerHTML = '<div class="admin-loading"><div class="admin-spinner"></div>Loading applications...</div>';
    
    try {
        const status = document.getElementById('applicationFilter').value;
        const url = status ? `/api/ca-ecosystem/applications?status=${status}` : '/api/ca-ecosystem/applications';
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            dashboardData.applications = data.applications;
            displayApplications(data.applications);
        } else {
            throw new Error(data.error || 'Failed to load applications');
        }
    } catch (error) {
        console.error('Error loading applications:', error);
        container.innerHTML = '<div class="admin-empty">Error loading applications</div>';
    }
}

function displayApplications(applications) {
    const container = document.getElementById('applicationsList');
    
    if (!applications || applications.length === 0) {
        container.innerHTML = '<div class="admin-empty">No applications found</div>';
        return;
    }
    
    const html = `
        <div class="admin-table-container">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Applicant</th>
                        <th>ICAI Number</th>
                        <th>Experience</th>
                        <th>Status</th>
                        <th>Applied</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${applications.map(app => `
                        <tr>
                            <td>
                                <div>
                                    <strong>${app.full_name || 'N/A'}</strong><br>
                                    <small style="color: #94a3b8;">${app.email || 'N/A'}</small>
                                </div>
                            </td>
                            <td>${app.icai_number || 'N/A'}</td>
                            <td>${app.experience_years || 0} years</td>
                            <td>${createStatusBadge(app.status)}</td>
                            <td>${formatDate(app.created_at)}</td>
                            <td>
                                <div class="admin-card-actions">
                                    <button class="admin-btn admin-btn-sm" onclick="viewApplication('${app.id}')">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                    ${app.status === 'pending' ? `
                                        <button class="admin-btn admin-btn-primary admin-btn-sm" onclick="approveApplication('${app.id}')">
                                            <i class="fas fa-check"></i> Approve
                                        </button>
                                        <button class="admin-btn admin-btn-danger admin-btn-sm" onclick="rejectApplication('${app.id}')">
                                            <i class="fas fa-times"></i> Reject
                                        </button>
                                    ` : ''}
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

async function viewApplication(applicationId) {
    try {
        const response = await fetch(`/api/ca-ecosystem/applications/${applicationId}`);
        const data = await response.json();
        
        if (data.success) {
            showApplicationModal(data.application);
        } else {
            throw new Error(data.error || 'Failed to load application');
        }
    } catch (error) {
        console.error('Error viewing application:', error);
        showNotification('Error loading application details', 'error');
    }
}

function showApplicationModal(application) {
    const modal = document.getElementById('applicationModal');
    const body = document.getElementById('applicationModalBody');
    
    body.innerHTML = `
        <div class="admin-form">
            <div class="admin-form-group">
                <label class="admin-form-label">Applicant Information</label>
                <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                    <p><strong>Name:</strong> ${application.full_name || 'N/A'}</p>
                    <p><strong>Email:</strong> ${application.email || 'N/A'}</p>
                    <p><strong>Phone:</strong> ${application.phone || 'N/A'}</p>
                </div>
            </div>
            
            <div class="admin-form-group">
                <label class="admin-form-label">Professional Details</label>
                <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                    <p><strong>ICAI Number:</strong> ${application.icai_number || 'N/A'}</p>
                    <p><strong>Registration Year:</strong> ${application.registration_year || 'N/A'}</p>
                    <p><strong>Experience:</strong> ${application.experience_years || 0} years</p>
                    <p><strong>CA Type:</strong> ${application.ca_type || 'N/A'}</p>
                    <p><strong>Firm Name:</strong> ${application.firm_name || 'N/A'}</p>
                </div>
            </div>
            
            <div class="admin-form-group">
                <label class="admin-form-label">Practice Address</label>
                <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                    <p>${application.practice_address || 'N/A'}</p>
                </div>
            </div>
            
            <div class="admin-form-group">
                <label class="admin-form-label">Specializations</label>
                <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                    ${(application.specializations || []).map(spec => `<span class="status-badge status-verified">${spec}</span>`).join(' ')}
                </div>
            </div>
            
            <div class="admin-form-group">
                <label class="admin-form-label">Application Status</label>
                <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                    ${createStatusBadge(application.status)}
                    <p style="margin-top: 0.5rem; color: #94a3b8; font-size: 0.875rem;">
                        Applied: ${formatDate(application.created_at)}
                    </p>
                </div>
            </div>
            
            ${application.admin_notes ? `
                <div class="admin-form-group">
                    <label class="admin-form-label">Admin Notes</label>
                    <div style="background: var(--glass-bg); padding: 1rem; border-radius: 8px;">
                        <p>${application.admin_notes}</p>
                    </div>
                </div>
            ` : ''}
            
            <div class="admin-form-actions">
                ${application.status === 'pending' ? `
                    <button type="button" class="admin-btn admin-btn-primary" onclick="approveApplication('${application.id}')">
                        <i class="fas fa-check"></i> Approve Application
                    </button>
                    <button type="button" class="admin-btn admin-btn-danger" onclick="rejectApplication('${application.id}')">
                        <i class="fas fa-times"></i> Reject Application
                    </button>
                ` : ''}
                <button type="button" class="admin-btn" onclick="closeModal('applicationModal')">Close</button>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

async function approveApplication(applicationId) {
    if (!confirm('Are you sure you want to approve this CA application?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/ca-ecosystem/applications/${applicationId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                notes: 'Approved by admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Application approved successfully', 'success');
            closeModal('applicationModal');
            loadApplications();
            loadStatistics();
        } else {
            throw new Error(data.error || 'Failed to approve application');
        }
    } catch (error) {
        console.error('Error approving application:', error);
        showNotification('Error approving application', 'error');
    }
}

async function rejectApplication(applicationId) {
    const reason = prompt('Please provide rejection reason:');
    if (!reason) {
        return;
    }
    
    try {
        const response = await fetch(`/api/ca-ecosystem/applications/${applicationId}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Application rejected successfully', 'success');
            closeModal('applicationModal');
            loadApplications();
            loadStatistics();
        } else {
            throw new Error(data.error || 'Failed to reject application');
        }
    } catch (error) {
        console.error('Error rejecting application:', error);
        showNotification('Error rejecting application', 'error');
    }
}

// ==================== VERIFIED CAS MANAGEMENT ====================
async function loadVerifiedCAs() {
    const container = document.getElementById('verifiedCasList');
    container.innerHTML = '<div class="admin-loading"><div class="admin-spinner"></div>Loading verified CAs...</div>';
    
    try {
        const response = await fetch('/api/ca-ecosystem/verified-cas');
        const data = await response.json();
        
        if (data.success) {
            dashboardData.verifiedCAs = data.cas;
            displayVerifiedCAs(data.cas);
        } else {
            throw new Error(data.error || 'Failed to load verified CAs');
        }
    } catch (error) {
        console.error('Error loading verified CAs:', error);
        container.innerHTML = '<div class="admin-empty">Error loading verified CAs</div>';
    }
}

function displayVerifiedCAs(cas) {
    const container = document.getElementById('verifiedCasList');
    
    if (!cas || cas.length === 0) {
        container.innerHTML = '<div class="admin-empty">No verified CAs found</div>';
        return;
    }
    
    const html = `
        <div class="admin-table-container">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>CA Name</th>
                        <th>Email</th>
                        <th>Trust Score</th>
                        <th>Status</th>
                        <th>Joined</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${cas.map(ca => `
                        <tr>
                            <td>
                                <div>
                                    <strong>${ca.first_name || ''} ${ca.last_name || ''}</strong><br>
                                    <small style="color: #94a3b8;">${ca.icai_number || 'N/A'}</small>
                                </div>
                            </td>
                            <td>${ca.email || 'N/A'}</td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <div style="width: 100px; height: 4px; background: linear-gradient(90deg, #10b981, #059669); border-radius: 2px;"></div>
                                    <span>${ca.trust_score || 0}</span>
                                </div>
                            </td>
                            <td>${ca.is_suspended ? createStatusBadge('suspended') : createStatusBadge('verified')}</td>
                            <td>${formatDate(ca.created_at)}</td>
                            <td>
                                <div class="admin-card-actions">
                                    ${ca.is_suspended ? `
                                        <button class="admin-btn admin-btn-primary admin-btn-sm" onclick="reinstateCA('${ca.id}')">
                                            <i class="fas fa-check"></i> Reinstate
                                        </button>
                                    ` : `
                                        <button class="admin-btn admin-btn-danger admin-btn-sm" onclick="suspendCA('${ca.id}')">
                                            <i class="fas fa-pause"></i> Suspend
                                        </button>
                                    `}
                                    <button class="admin-btn admin-btn-danger admin-btn-sm" onclick="blacklistCA('${ca.id}')">
                                        <i class="fas fa-ban"></i> Blacklist
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// ==================== COMPLAINTS MANAGEMENT ====================
async function loadComplaints() {
    const container = document.getElementById('complaintsList');
    container.innerHTML = '<div class="admin-loading"><div class="admin-spinner"></div>Loading complaints...</div>';
    
    try {
        const status = document.getElementById('complaintFilter').value;
        const priority = null; // Can add priority filter later
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        
        const response = await fetch(`/api/ca-ecosystem/complaints?${params}`);
        const data = await response.json();
        
        if (data.success) {
            dashboardData.complaints = data.complaints;
            displayComplaints(data.complaints);
        } else {
            throw new Error(data.error || 'Failed to load complaints');
        }
    } catch (error) {
        console.error('Error loading complaints:', error);
        container.innerHTML = '<div class="admin-empty">Error loading complaints</div>';
    }
}

function displayComplaints(complaints) {
    const container = document.getElementById('complaintsList');
    
    if (!complaints || complaints.length === 0) {
        container.innerHTML = '<div class="admin-empty">No complaints found</div>';
        return;
    }
    
    const html = `
        <div class="admin-table-container">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Complaint</th>
                        <th>Against</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${complaints.map(complaint => `
                        <tr>
                            <td>
                                <div>
                                    <strong>${complaint.title || 'N/A'}</strong><br>
                                    <small style="color: #94a3b8;">By: ${complaint.reporter?.first_name || 'N/A'} ${complaint.reporter?.last_name || ''}</small>
                                </div>
                            </td>
                            <td>${complaint.accused?.first_name || 'N/A'} ${complaint.accused?.last_name || ''}</td>
                            <td>${formatComplaintType(complaint.complaint_type)}</td>
                            <td>${createPriorityBadge(complaint.priority)}</td>
                            <td>${createStatusBadge(complaint.status)}</td>
                            <td>${formatDate(complaint.created_at)}</td>
                            <td>
                                <div class="admin-card-actions">
                                    <button class="admin-btn admin-btn-sm" onclick="viewComplaint('${complaint.id}')">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// ==================== AUDIT LOGS ====================
async function loadAuditLogs() {
    const container = document.getElementById('auditLogsList');
    container.innerHTML = '<div class="admin-loading"><div class="admin-spinner"></div>Loading audit logs...</div>';
    
    try {
        const actionType = document.getElementById('logActionFilter').value;
        const params = new URLSearchParams();
        if (actionType) params.append('action_type', actionType);
        
        const response = await fetch(`/api/ca-ecosystem/audit-logs?${params}`);
        const data = await response.json();
        
        if (data.success) {
            dashboardData.auditLogs = data.logs;
            displayAuditLogs(data.logs);
        } else {
            throw new Error(data.error || 'Failed to load audit logs');
        }
    } catch (error) {
        console.error('Error loading audit logs:', error);
        container.innerHTML = '<div class="admin-empty">Error loading audit logs</div>';
    }
}

function displayAuditLogs(logs) {
    const container = document.getElementById('auditLogsList');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = '<div class="admin-empty">No audit logs found</div>';
        return;
    }
    
    const html = `
        <div class="admin-table-container">
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Admin</th>
                        <th>Action</th>
                        <th>Target</th>
                        <th>Description</th>
                        <th>IP Address</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${logs.map(log => `
                        <tr>
                            <td>${log.profiles?.first_name || 'N/A'} ${log.profiles?.last_name || ''}</td>
                            <td>${formatActionType(log.action_type)}</td>
                            <td>${log.target_profiles?.first_name || 'N/A'} ${log.target_profiles?.last_name || ''}</td>
                            <td>${log.description || 'N/A'}</td>
                            <td>${log.ip_address || 'N/A'}</td>
                            <td>${formatDate(log.created_at)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// ==================== SETTINGS MANAGEMENT ====================
async function loadSettings() {
    try {
        const response = await fetch('/api/ca-ecosystem/settings');
        const data = await response.json();
        
        if (data.success) {
            dashboardData.settings = data.settings;
            populateSettingsForm(data.settings);
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function populateSettingsForm(settings) {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    
    Object.keys(settings).forEach(key => {
        const input = form.elements[key];
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = settings[key] === 'true';
            } else {
                input.value = settings[key];
            }
        }
    });
}

async function saveSettings() {
    const form = document.getElementById('settingsForm');
    const formData = new FormData(form);
    
    const settings = {};
    for (const [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    try {
        const response = await fetch('/api/ca-ecosystem/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Settings saved successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings', 'error');
    }
}

// ==================== UTILITY FUNCTIONS ====================
function createStatusBadge(status) {
    const statusClasses = {
        'pending': 'status-pending',
        'approved': 'status-approved',
        'rejected': 'status-rejected',
        'suspended': 'status-suspended',
        'blacklisted': 'status-blacklisted',
        'verified': 'status-verified',
        'under_review': 'status-pending',
        'more_info_required': 'status-pending'
    };
    
    const statusClass = statusClasses[status] || 'status-pending';
    return `<span class="status-badge ${statusClass}">${status.replace('_', ' ').toUpperCase()}</span>`;
}

function createPriorityBadge(priority) {
    const priorityClasses = {
        'low': 'status-approved',
        'medium': 'status-pending',
        'high': 'status-rejected',
        'critical': 'status-blacklisted'
    };
    
    const priorityClass = priorityClasses[priority] || 'status-pending';
    return `<span class="status-badge ${priorityClass}">${priority.toUpperCase()}</span>`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatComplaintType(type) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatActionType(actionType) {
    return actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `admin-notification admin-notification-${type}`;
    notification.innerHTML = `
        <div class="admin-notification-content">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}"></i>
            <span>${message}</span>
        </div>
        <button class="admin-notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .admin-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--glass-bg-strong);
                backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                padding: 1rem 1.5rem;
                box-shadow: var(--glass-shadow);
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 1rem;
                min-width: 300px;
                animation: slideIn 0.3s ease;
            }
            
            .admin-notification-success {
                border-color: rgba(16, 185, 129, 0.3);
                color: #10b981;
            }
            
            .admin-notification-error {
                border-color: rgba(239, 68, 68, 0.3);
                color: #ef4444;
            }
            
            .admin-notification-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                flex: 1;
            }
            
            .admin-notification-close {
                background: transparent;
                border: none;
                color: #94a3b8;
                cursor: pointer;
                padding: 0.25rem;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// ==================== REFRESH FUNCTIONS ====================
function refreshActivity() {
    loadOverviewData();
}

function refreshApplications() {
    loadApplications();
}

function refreshVerifiedCAs() {
    loadVerifiedCAs();
}

function refreshComplaints() {
    loadComplaints();
}

function refreshAuditLogs() {
    loadAuditLogs();
}

// ==================== FILTER FUNCTIONS ====================
function filterApplications() {
    loadApplications();
}

function filterComplaints() {
    loadComplaints();
}

function filterAuditLogs() {
    loadAuditLogs();
}

function filterVerifiedCAs() {
    const searchTerm = document.getElementById('caSearch').value.toLowerCase();
    const filteredCAs = dashboardData.verifiedCAs.filter(ca => {
        const fullName = `${ca.first_name || ''} ${ca.last_name || ''}`.toLowerCase();
        const email = (ca.email || '').toLowerCase();
        return fullName.includes(searchTerm) || email.includes(searchTerm);
    });
    displayVerifiedCAs(filteredCAs);
}

// ==================== CA ACTIONS ====================
async function suspendCA(caId) {
    const reason = prompt('Please provide suspension reason:');
    if (!reason) return;
    
    try {
        const response = await fetch(`/api/ca-ecosystem/cas/${caId}/suspend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('CA suspended successfully', 'success');
            loadVerifiedCAs();
            loadStatistics();
        } else {
            throw new Error(data.error || 'Failed to suspend CA');
        }
    } catch (error) {
        console.error('Error suspending CA:', error);
        showNotification('Error suspending CA', 'error');
    }
}

async function reinstateCA(caId) {
    const reason = prompt('Please provide reinstatement reason:');
    if (!reason) return;
    
    try {
        const response = await fetch(`/api/ca-ecosystem/cas/${caId}/reinstate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('CA reinstated successfully', 'success');
            loadVerifiedCAs();
            loadStatistics();
        } else {
            throw new Error(data.error || 'Failed to reinstate CA');
        }
    } catch (error) {
        console.error('Error reinstating CA:', error);
        showNotification('Error reinstating CA', 'error');
    }
}

async function blacklistCA(caId) {
    if (!confirm('Are you sure you want to blacklist this CA? This action cannot be undone.')) {
        return;
    }
    
    const reason = prompt('Please provide blacklist reason (required):');
    if (!reason) return;
    
    try {
        const response = await fetch(`/api/ca-ecosystem/cas/${caId}/blacklist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('CA blacklisted successfully', 'success');
            loadVerifiedCAs();
            loadStatistics();
        } else {
            throw new Error(data.error || 'Failed to blacklist CA');
        }
    } catch (error) {
        console.error('Error blacklisting CA:', error);
        showNotification('Error blacklisting CA', 'error');
    }
}

async function viewComplaint(complaintId) {
    // Implementation for viewing complaint details
    showNotification('Complaint details view coming soon', 'info');
}
