/**
 * CA Onboarding JavaScript
 * Production-grade multi-step application form
 * Author: Sumeet Sangwan (Fintech-grade implementation)
 */

// ==================== GLOBAL VARIABLES ====================
let currentStep = 1;
const totalSteps = 4;
let applicationData = {
    basicInfo: {},
    professional: {},
    documents: {},
    files: {}
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeOnboarding();
    setupEventListeners();
    loadSavedDraft();
});

function initializeOnboarding() {
    updateProgressBar();
    setupFileUpload();
    setupFormValidation();
}

function setupEventListeners() {
    // Form submissions
    document.getElementById('basicInfoForm').addEventListener('submit', handleBasicInfoSubmit);
    document.getElementById('professionalForm').addEventListener('submit', handleProfessionalSubmit);
    document.getElementById('documentsForm').addEventListener('submit', handleDocumentsSubmit);
    
    // File upload drag and drop
    setupDragAndDrop();
    
    // Auto-save draft
    setupAutoSave();
}

// ==================== STEP NAVIGATION ====================
function goToStep(stepNumber) {
    if (stepNumber < 1 || stepNumber > totalSteps) return;
    
    // Hide current step
    document.getElementById(`step${currentStep}`).style.display = 'none';
    document.querySelector(`.progress-step[data-step="${currentStep}"]`).classList.remove('active');
    
    // Show new step
    currentStep = stepNumber;
    document.getElementById(`step${currentStep}`).style.display = 'block';
    document.querySelector(`.progress-step[data-step="${currentStep}"]`).classList.add('active');
    
    // Update progress bar
    updateProgressBar();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Load step data if needed
    if (stepNumber === 4) {
        loadReviewStep();
    }
}

function updateProgressBar() {
    const progressFill = document.getElementById('progressFill');
    const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
    progressFill.style.width = `${progressPercentage}%`;
    
    // Update step indicators
    for (let i = 1; i <= totalSteps; i++) {
        const stepElement = document.querySelector(`.progress-step[data-step="${i}"]`);
        const iconElement = stepElement.querySelector('.progress-step-icon');
        
        stepElement.classList.remove('completed', 'active');
        
        if (i < currentStep) {
            stepElement.classList.add('completed');
            iconElement.innerHTML = '<i class="fas fa-check"></i>';
        } else if (i === currentStep) {
            stepElement.classList.add('active');
        } else {
            iconElement.innerHTML = `<span>${i}</span>`;
        }
    }
}

// ==================== FORM HANDLERS ====================
async function handleBasicInfoSubmit(e) {
    e.preventDefault();
    
    if (!validateBasicInfo()) {
        return;
    }
    
    const formData = new FormData(e.target);
    applicationData.basicInfo = Object.fromEntries(formData);
    
    // Save draft
    saveDraft();
    
    // Proceed to next step
    goToStep(2);
}

function validateBasicInfo() {
    const form = document.getElementById('basicInfoForm');
    let isValid = true;
    
    // Clear previous errors
    form.querySelectorAll('.form-group').forEach(group => {
        group.classList.remove('error');
        group.querySelector('.error-message').style.display = 'none';
    });
    
    // Validate full name
    const fullName = form.querySelector('[name="full_name"]');
    if (!fullName.value.trim()) {
        showFieldError(fullName, 'Full name is required');
        isValid = false;
    }
    
    // Validate phone
    const phone = form.querySelector('[name="phone"]');
    const phoneRegex = /^[+]?[0-9]{10,15}$/;
    if (!phoneRegex.test(phone.value.replace(/\s/g, ''))) {
        showFieldError(phone, 'Please enter a valid phone number');
        isValid = false;
    }
    
    // Validate ICAI number
    const icaiNumber = form.querySelector('[name="icai_number"]');
    const icaiRegex = /^[A-Z]{3}[0-9]{6}$/;
    if (!icaiRegex.test(icaiNumber.value.toUpperCase())) {
        showFieldError(icaiNumber, 'ICAI number must be 3 letters followed by 6 digits (e.g., ABC123456)');
        isValid = false;
    }
    
    // Validate city and state
    const city = form.querySelector('[name="city"]');
    const state = form.querySelector('[name="state"]');
    
    if (!city.value.trim()) {
        showFieldError(city, 'City is required');
        isValid = false;
    }
    
    if (!state.value) {
        showFieldError(state, 'State is required');
        isValid = false;
    }
    
    return isValid;
}

async function handleProfessionalSubmit(e) {
    e.preventDefault();
    
    if (!validateProfessional()) {
        return;
    }
    
    const formData = new FormData(e.target);
    const professionalData = Object.fromEntries(formData);
    
    // Handle checkboxes
    professionalData.specializations = getCheckedValues('specializations');
    professionalData.client_types = getCheckedValues('client_types');
    
    applicationData.professional = professionalData;
    
    // Save draft
    saveDraft();
    
    // Proceed to next step
    goToStep(3);
}

function validateProfessional() {
    const form = document.getElementById('professionalForm');
    let isValid = true;
    
    // Clear previous errors
    form.querySelectorAll('.form-group').forEach(group => {
        group.classList.remove('error');
        const errorMsg = group.querySelector('.error-message');
        if (errorMsg) errorMsg.style.display = 'none';
    });
    
    // Validate registration year
    const regYear = form.querySelector('[name="registration_year"]');
    const currentYear = new Date().getFullYear();
    if (!regYear.value || regYear.value < 1950 || regYear.value > currentYear) {
        showFieldError(regYear, `Please enter a valid year between 1950 and ${currentYear}`);
        isValid = false;
    }
    
    // Validate experience
    const experience = form.querySelector('[name="experience_years"]');
    if (!experience.value || experience.value < 0 || experience.value > 50) {
        showFieldError(experience, 'Experience must be between 0 and 50 years');
        isValid = false;
    }
    
    // Validate CA type
    const caType = form.querySelector('[name="ca_type"]');
    if (!caType.value) {
        showFieldError(caType, 'Please select your CA type');
        isValid = false;
    }
    
    // Validate practice address
    const practiceAddress = form.querySelector('[name="practice_address"]');
    if (!practiceAddress.value.trim()) {
        showFieldError(practiceAddress, 'Practice address is required');
        isValid = false;
    }
    
    // Validate specializations
    const specializations = getCheckedValues('specializations');
    if (specializations.length === 0) {
        const container = form.querySelector('[name="specializations"]').closest('.form-group');
        container.classList.add('error');
        container.querySelector('.error-message').style.display = 'flex';
        isValid = false;
    }
    
    return isValid;
}

async function handleDocumentsSubmit(e) {
    e.preventDefault();
    
    if (!validateDocuments()) {
        return;
    }
    
    // Save draft
    saveDraft();
    
    // Proceed to review step
    goToStep(4);
}

function validateDocuments() {
    const requiredDocuments = ['icai_certificate', 'government_id', 'practice_certificate', 'profile_photo'];
    let isValid = true;
    
    requiredDocuments.forEach(docType => {
        const files = applicationData.files[docType] || [];
        const container = document.querySelector(`[data-document-type="${docType}"]`).closest('.form-group');
        
        container.classList.remove('error');
        const errorMsg = container.querySelector('.error-message');
        if (errorMsg) errorMsg.style.display = 'none';
        
        if (files.length === 0) {
            container.classList.add('error');
            if (errorMsg) {
                errorMsg.style.display = 'flex';
                errorMsg.querySelector('span').textContent = 'This document is required';
            }
            isValid = false;
        }
    });
    
    return isValid;
}

// ==================== FILE UPLOAD ====================
function setupFileUpload() {
    document.querySelectorAll('.file-upload-area').forEach(area => {
        const input = area.querySelector('.file-upload-input');
        
        area.addEventListener('click', () => input.click());
        
        input.addEventListener('change', (e) => {
            handleFileSelect(e.target.files, area.dataset.documentType);
        });
    });
}

function setupDragAndDrop() {
    document.querySelectorAll('.file-upload-area').forEach(area => {
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            handleFileSelect(e.dataTransfer.files, area.dataset.documentType);
        });
    });
}

function handleFileSelect(files, documentType) {
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    Array.from(files).forEach(file => {
        // Validate file type
        if (!validTypes.includes(file.type)) {
            showNotification('Invalid file type. Only PDF, JPG, and PNG are allowed.', 'error');
            return;
        }
        
        // Validate file size
        if (file.size > maxSize) {
            showNotification('File too large. Maximum size is 10MB.', 'error');
            return;
        }
        
        // Add to files list
        if (!applicationData.files[documentType]) {
            applicationData.files[documentType] = [];
        }
        
        // Remove existing file of same type (only allow one file per document type)
        applicationData.files[documentType] = [{
            name: file.name,
            size: file.size,
            type: file.type,
            file: file
        }];
        
        // Update UI
        updateFileList(documentType);
    });
}

function updateFileList(documentType) {
    const fileList = document.getElementById(`${documentType}_files`);
    const files = applicationData.files[documentType] || [];
    
    if (files.length === 0) {
        fileList.innerHTML = '';
        return;
    }
    
    const file = files[0];
    const fileIcon = getFileIcon(file.type);
    const fileSize = formatFileSize(file.size);
    
    fileList.innerHTML = `
        <div class="file-item">
            <div class="file-info">
                <i class="fas ${fileIcon} file-icon"></i>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${fileSize}</div>
                </div>
            </div>
            <button type="button" class="file-remove" onclick="removeFile('${documentType}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
}

function removeFile(documentType) {
    delete applicationData.files[documentType];
    updateFileList(documentType);
}

function getFileIcon(fileType) {
    if (fileType === 'application/pdf') return 'fa-file-pdf';
    if (fileType.startsWith('image/')) return 'fa-file-image';
    return 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ==================== REVIEW STEP ====================
function loadReviewStep() {
    const reviewContainer = document.getElementById('applicationReview');
    
    const reviewHTML = `
        <div class="review-section">
            <h3 class="form-section-title">
                <i class="fas fa-user"></i>
                Personal Information
            </h3>
            <div class="review-grid">
                <div class="review-item">
                    <label>Full Name:</label>
                    <span>${applicationData.basicInfo.full_name || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>Email:</label>
                    <span>${applicationData.basicInfo.email || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>Phone:</label>
                    <span>${applicationData.basicInfo.phone || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>ICAI Number:</label>
                    <span>${applicationData.basicInfo.icai_number?.toUpperCase() || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>City:</label>
                    <span>${applicationData.basicInfo.city || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>State:</label>
                    <span>${applicationData.basicInfo.state || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <div class="review-section">
            <h3 class="form-section-title">
                <i class="fas fa-briefcase"></i>
                Professional Details
            </h3>
            <div class="review-grid">
                <div class="review-item">
                    <label>Registration Year:</label>
                    <span>${applicationData.professional.registration_year || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>Experience:</label>
                    <span>${applicationData.professional.experience_years || 0} years</span>
                </div>
                <div class="review-item">
                    <label>CA Type:</label>
                    <span>${applicationData.professional.ca_type || 'N/A'}</span>
                </div>
                <div class="review-item">
                    <label>Firm Name:</label>
                    <span>${applicationData.professional.firm_name || 'N/A'}</span>
                </div>
                <div class="review-item full-width">
                    <label>Practice Address:</label>
                    <span>${applicationData.professional.practice_address || 'N/A'}</span>
                </div>
                <div class="review-item full-width">
                    <label>Specializations:</label>
                    <span>${(applicationData.professional.specializations || []).join(', ') || 'N/A'}</span>
                </div>
                <div class="review-item full-width">
                    <label>Client Types:</label>
                    <span>${(applicationData.professional.client_types || []).join(', ') || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <div class="review-section">
            <h3 class="form-section-title">
                <i class="fas fa-file-alt"></i>
                Uploaded Documents
            </h3>
            <div class="documents-review">
                ${generateDocumentsReview()}
            </div>
        </div>
        
        <div class="review-section">
            <h3 class="form-section-title">
                <i class="fas fa-check-circle"></i>
                Declaration
            </h3>
            <div class="declaration">
                <label class="checkbox-item">
                    <input type="checkbox" id="declarationCheck" required>
                    <span class="checkbox-label">
                        I hereby declare that all information provided is true and accurate to the best of my knowledge. 
                        I understand that any false information may lead to rejection of my application and potential legal action.
                    </span>
                </label>
            </div>
        </div>
    `;
    
    reviewContainer.innerHTML = reviewHTML;
    
    // Add review styles
    if (!document.querySelector('#review-styles')) {
        const style = document.createElement('style');
        style.id = 'review-styles';
        style.textContent = `
            .review-section {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }
            
            .review-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
            
            .review-item {
                display: flex;
                flex-direction: column;
                gap: 0.25rem;
            }
            
            .review-item.full-width {
                grid-column: 1 / -1;
            }
            
            .review-item label {
                font-size: 0.875rem;
                color: #94a3b8;
                font-weight: 500;
            }
            
            .review-item span {
                font-size: 0.875rem;
                color: #f1f5f9;
                font-weight: 500;
            }
            
            .documents-review {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }
            
            .document-review-item {
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            }
            
            .document-review-item i {
                font-size: 2rem;
                color: #10b981;
                margin-bottom: 0.5rem;
            }
            
            .document-review-item .document-name {
                font-size: 0.875rem;
                color: #f1f5f9;
                font-weight: 500;
                margin-bottom: 0.25rem;
            }
            
            .document-review-item .document-size {
                font-size: 0.75rem;
                color: #94a3b8;
            }
            
            .declaration {
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                padding: 1rem;
            }
            
            .declaration .checkbox-label {
                color: #f1f5f9;
                line-height: 1.6;
            }
        `;
        document.head.appendChild(style);
    }
}

function generateDocumentsReview() {
    const documentTypes = {
        'icai_certificate': 'ICAI Certificate',
        'government_id': 'Government ID',
        'practice_certificate': 'Practice Certificate',
        'profile_photo': 'Profile Photo',
        'office_proof': 'Office Proof',
        'degree_certificate': 'Degree Certificate'
    };
    
    let html = '';
    
    Object.entries(documentTypes).forEach(([type, label]) => {
        const files = applicationData.files[type] || [];
        
        if (files.length > 0) {
            const file = files[0];
            const fileIcon = getFileIcon(file.type);
            
            html += `
                <div class="document-review-item">
                    <i class="fas ${fileIcon}"></i>
                    <div class="document-name">${label}</div>
                    <div class="document-size">${file.name}</div>
                </div>
            `;
        }
    });
    
    return html || '<p>No documents uploaded</p>';
}

// ==================== APPLICATION SUBMISSION ====================
async function submitApplication() {
    // Check declaration
    const declarationCheck = document.getElementById('declarationCheck');
    if (!declarationCheck.checked) {
        showNotification('Please accept the declaration to continue.', 'error');
        return;
    }
    
    // Show loading
    showLoading(true);
    
    try {
        // Prepare application data
        const applicationDataPayload = {
            ...applicationData.basicInfo,
            ...applicationData.professional,
            specializations: applicationData.professional.specializations || [],
            services: applicationData.professional.specializations || [], // Same as specializations for now
            client_types: applicationData.professional.client_types || [],
            documents: {} // Will be populated after file uploads
        };
        
        // Upload files first
        const uploadedDocuments = {};
        for (const [docType, files] of Object.entries(applicationData.files)) {
            if (files.length > 0) {
                const file = files[0].file;
                // In a real implementation, you would upload the file to your backend
                // For now, we'll just store the file info
                uploadedDocuments[docType] = {
                    name: file.name,
                    size: file.size,
                    type: file.type
                };
            }
        }
        
        applicationDataPayload.documents = uploadedDocuments;
        
        // Submit application
        const response = await fetch('/api/ca-ecosystem/applications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(applicationDataPayload)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Clear saved draft
            clearDraft();
            
            // Show success status with message
            showApplicationStatus('submitted', result.message);
        } else {
            // Handle different error types
            let errorMessage = result.error || 'Failed to submit application';
            
            // Add specific guidance for common errors
            if (response.status === 503) {
                errorMessage += '\n\nPlease contact support at support@finucity.com';
            } else if (response.status === 400) {
                errorMessage = 'Please check your form data: ' + errorMessage;
            }
            
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Error submitting application:', error);
        
        // Show user-friendly error message
        showNotification(
            error.message || 'Error submitting application. Please try again or contact support.',
            'error',
            10000 // Show for 10 seconds
        );
    } finally {
        showLoading(false);
    }
}

function showApplicationStatus(status) {
    // Hide all steps
    document.querySelectorAll('.onboarding-step').forEach(step => {
        step.style.display = 'none';
    });
    
    // Show status step
    const statusStep = document.getElementById('statusStep');
    statusStep.style.display = 'block';
    
    // Update status content based on status
    const statusIcon = document.getElementById('statusIcon');
    const statusTitle = document.getElementById('statusTitle');
    const statusDescription = document.getElementById('statusDescription');
    
    switch (status) {
        case 'submitted':
            statusIcon.className = 'status-icon pending';
            statusIcon.innerHTML = '<i class="fas fa-clock"></i>';
            statusTitle.textContent = 'Application Submitted Successfully';
            statusDescription.textContent = 'Your CA application has been successfully submitted. Our verification team will review your application within 7 business days. You will receive updates via email.';
            break;
        case 'error':
            statusIcon.className = 'status-icon rejected';
            statusIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            statusTitle.textContent = 'Submission Failed';
            statusDescription.textContent = 'There was an error submitting your application. Please try again or contact support if the problem persists.';
            break;
    }
}

// ==================== UTILITY FUNCTIONS ====================
function showFieldError(field, message) {
    const formGroup = field.closest('.form-group');
    formGroup.classList.add('error');
    const errorMsg = formGroup.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.querySelector('span').textContent = message;
        errorMsg.style.display = 'flex';
    }
}

function getCheckedValues(name) {
    const checkboxes = document.querySelectorAll(`input[name="${name}"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = show ? 'flex' : 'none';
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

// ==================== DRAFT MANAGEMENT ====================
function saveDraft() {
    const draft = {
        step: currentStep,
        data: applicationData,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('caApplicationDraft', JSON.stringify(draft));
}

function loadSavedDraft() {
    const draftData = localStorage.getItem('caApplicationDraft');
    if (!draftData) return;
    
    try {
        const draft = JSON.parse(draftData);
        
        // Check if draft is recent (less than 7 days)
        const draftDate = new Date(draft.timestamp);
        const now = new Date();
        const daysDiff = (now - draftDate) / (1000 * 60 * 60 * 24);
        
        if (daysDiff > 7) {
            clearDraft();
            return;
        }
        
        // Load draft data
        applicationData = draft.data;
        currentStep = draft.step || 1;
        
        // Populate forms with draft data
        populateFormsWithDraft();
        
        // Update UI
        goToStep(currentStep);
        
        // Show notification
        showNotification('Draft restored from previous session', 'info');
        
    } catch (error) {
        console.error('Error loading draft:', error);
        clearDraft();
    }
}

function populateFormsWithDraft() {
    // Populate basic info form
    if (applicationData.basicInfo) {
        const basicForm = document.getElementById('basicInfoForm');
        Object.entries(applicationData.basicInfo).forEach(([key, value]) => {
            const field = basicForm.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = value;
            }
        });
    }
    
    // Populate professional form
    if (applicationData.professional) {
        const professionalForm = document.getElementById('professionalForm');
        Object.entries(applicationData.professional).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                // Handle checkboxes
                value.forEach(val => {
                    const checkbox = professionalForm.querySelector(`[name="${key}"][value="${val}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            } else {
                const field = professionalForm.querySelector(`[name="${key}"]`);
                if (field) {
                    field.value = value;
                }
            }
        });
    }
    
    // Update file lists
    Object.entries(applicationData.files).forEach(([docType, files]) => {
        updateFileList(docType);
    });
}

function clearDraft() {
    localStorage.removeItem('caApplicationDraft');
}

function saveDraft() {
    const draft = {
        step: currentStep,
        data: applicationData,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('caApplicationDraft', JSON.stringify(draft));
}

function setupAutoSave() {
    // Auto-save every 30 seconds
    setInterval(() => {
        if (currentStep < 4) { // Don't save after submission
            saveDraft();
        }
    }, 30000);
    
    // Save on page unload
    window.addEventListener('beforeunload', () => {
        if (currentStep < 4) {
            saveDraft();
        }
    });
}

// ==================== FORM VALIDATION SETUP ====================
function setupFormValidation() {
    // Real-time validation
    document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(field => {
        field.addEventListener('blur', () => {
            validateField(field);
        });
        
        field.addEventListener('input', () => {
            // Clear error on input
            const formGroup = field.closest('.form-group');
            if (formGroup.classList.contains('error')) {
                formGroup.classList.remove('error');
                const errorMsg = formGroup.querySelector('.error-message');
                if (errorMsg) errorMsg.style.display = 'none';
            }
        });
    });
}

function validateField(field) {
    const formGroup = field.closest('.form-group');
    const isRequired = field.hasAttribute('required') || 
                     field.closest('.form-group').querySelector('.form-label.required');
    
    if (isRequired && !field.value.trim()) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Specific validations
    if (field.name === 'phone') {
        const phoneRegex = /^[+]?[0-9]{10,15}$/;
        if (!phoneRegex.test(field.value.replace(/\s/g, ''))) {
            showFieldError(field, 'Please enter a valid phone number');
            return false;
        }
    }
    
    if (field.name === 'icai_number') {
        const icaiRegex = /^[A-Z]{3}[0-9]{6}$/;
        if (!icaiRegex.test(field.value.toUpperCase())) {
            showFieldError(field, 'ICAI number must be 3 letters followed by 6 digits');
            return false;
        }
    }
    
    if (field.name === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            return false;
        }
    }
    
    // Clear error if valid
    formGroup.classList.remove('error');
    const errorMsg = formGroup.querySelector('.error-message');
    if (errorMsg) errorMsg.style.display = 'none';
    
    return true;
}
