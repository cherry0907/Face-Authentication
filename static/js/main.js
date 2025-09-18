// Global utility functions

// Toast notification system
function showToast(type, message) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => {
        toast.style.animation = 'slideOutRight 0.3s ease-in-out';
        setTimeout(() => toast.remove(), 300);
    });

    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="closeToast(this)">&times;</button>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            closeToast(toast.querySelector('.toast-close'));
        }
    }, 5000);
}

function closeToast(button) {
    const toast = button ? button.closest('.toast') : document.getElementById('toast');
    if (toast) {
        toast.style.animation = 'slideOutRight 0.3s ease-in-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
}

// OTP Modal functions
function showOtpModal() {
    const modal = document.getElementById('otpModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Focus on OTP input
        setTimeout(() => {
            const otpInput = document.getElementById('otp');
            if (otpInput) {
                otpInput.focus();
            }
        }, 100);
    }
}

function closeOtpModal() {
    const modal = document.getElementById('otpModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Clear form
        const form = document.getElementById('otpForm');
        if (form) {
            form.reset();
        }
        
        // Clear message
        const message = document.getElementById('otpMessage');
        if (message) {
            message.innerHTML = '';
            message.className = 'message';
        }
    }
}

// OTP form submission
document.addEventListener('DOMContentLoaded', function() {
    const otpForm = document.getElementById('otpForm');
    
    if (otpForm) {
        otpForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(otpForm);
            const messageDiv = document.getElementById('otpMessage');
            
            try {
                const response = await fetch('/verify-otp', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    messageDiv.innerHTML = result.message;
                    messageDiv.className = 'message success';
                    
                    // Close modal and redirect after success
                    setTimeout(() => {
                        closeOtpModal();
                        showToast('success', 'Account verified successfully! You can now log in.');
                        setTimeout(() => {
                            window.location.href = '/login';
                        }, 1500);
                    }, 1500);
                } else {
                    messageDiv.innerHTML = result.message;
                    messageDiv.className = 'message error';
                }
            } catch (error) {
                messageDiv.innerHTML = 'Network error. Please try again.';
                messageDiv.className = 'message error';
            }
        });
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('otpModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeOtpModal();
            }
        });
    }
    
    // OTP input formatting (only numbers, max 6 digits)
    const otpInput = document.getElementById('otp');
    if (otpInput) {
        otpInput.addEventListener('input', function(e) {
            // Remove non-digits
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            
            // Limit to 6 digits
            if (e.target.value.length > 6) {
                e.target.value = e.target.value.slice(0, 6);
            }
        });
        
        // Auto-submit when 6 digits are entered
        otpInput.addEventListener('input', function(e) {
            if (e.target.value.length === 6) {
                setTimeout(() => {
                    otpForm.dispatchEvent(new Event('submit'));
                }, 500);
            }
        });
    }
});

// Utility function to format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters
    return password.length >= 8;
}

// Add loading state to buttons
function setButtonLoading(button, loading = true) {
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');
    
    if (loading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoading) btnLoading.style.display = 'inline';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoading) btnLoading.style.display = 'none';
    }
}

// Handle network errors gracefully
function handleNetworkError(error) {
    console.error('Network error:', error);
    showToast('error', 'Network error. Please check your connection and try again.');
}

// Show confirmation dialogs
function showConfirmation(message, callback) {
    if (confirm(message)) {
        callback();
    }
}