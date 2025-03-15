// Authentication related JavaScript for BBMP Ward Issues Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Phone number validation with Indian format
    const phoneInputs = document.querySelectorAll('input[name="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/[^0-9+]/g, '');
            
            // Format as Indian phone number - optional +91 followed by 10 digits
            if (this.value.startsWith('+91') && this.value.length > 13) {
                this.value = this.value.substring(0, 13);
            } else if (!this.value.startsWith('+91') && this.value.length > 10) {
                this.value = this.value.substring(0, 10);
            }
            
            // Validate the phone number
            validatePhoneNumber(this);
        });
        
        // Initial validation
        validatePhoneNumber(input);
    });
    
    // OTP input validation - only allow numbers and limit to 6 digits
    const otpInputs = document.querySelectorAll('input[name="otp"]');
    otpInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Limit to 6 digits
            if (this.value.length > 6) {
                this.value = this.value.substring(0, 6);
            }
            
            // Validate OTP
            validateOTP(this);
        });
        
        // Initial validation
        validateOTP(input);
    });
    
    // Timer for OTP resend
    startOTPTimer();
});

// Function to validate phone number
function validatePhoneNumber(input) {
    const phoneNumber = input.value;
    const isValid = /^(\+91)?[6-9]\d{9}$/.test(phoneNumber);
    
    // Set validation UI
    if (phoneNumber.length > 0) {
        if (isValid) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
    } else {
        input.classList.remove('is-valid');
        input.classList.remove('is-invalid');
    }
    
    // Find the submit button in the same form
    const submitBtn = input.closest('form').querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = !isValid && phoneNumber.length > 0;
    }
}

// Function to validate OTP
function validateOTP(input) {
    const otp = input.value;
    const isValid = otp.length === 6;
    
    // Set validation UI
    if (otp.length > 0) {
        if (isValid) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
    } else {
        input.classList.remove('is-valid');
        input.classList.remove('is-invalid');
    }
    
    // Find the submit button in the same form
    const submitBtn = input.closest('form').querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = !isValid && otp.length > 0;
    }
}

// Function to start OTP timer (for future implementation of resend functionality)
function startOTPTimer() {
    const timerElement = document.getElementById('otpTimer');
    if (!timerElement) return;
    
    let timeLeft = 60; // 60 seconds countdown
    
    const resendButton = document.getElementById('resendOtpButton');
    if (resendButton) {
        resendButton.disabled = true;
    }
    
    const interval = setInterval(function() {
        timeLeft--;
        timerElement.textContent = timeLeft;
        
        if (timeLeft <= 0) {
            clearInterval(interval);
            timerElement.textContent = '0';
            
            if (resendButton) {
                resendButton.disabled = false;
            }
        }
    }, 1000);
}

// Function to handle OTP resend (for future implementation)
function resendOTP() {
    // In a real app, this would make an API call to resend the OTP
    // For hackathon, we'll just restart the timer
    
    // Disable the resend button
    const resendButton = document.getElementById('resendOtpButton');
    if (resendButton) {
        resendButton.disabled = true;
    }
    
    // Get the phone number
    const phoneInput = document.querySelector('input[name="phone"]');
    if (!phoneInput) return;
    
    const phoneNumber = phoneInput.value;
    
    // Display a message to the user
    const messageElement = document.createElement('div');
    messageElement.className = 'alert alert-info mt-2';
    messageElement.textContent = `A new OTP has been sent to ${phoneNumber}`;
    
    const form = document.querySelector('form');
    form.insertBefore(messageElement, form.firstChild);
    
    // Start the timer again
    startOTPTimer();
    
    // Auto-dismiss the message after 5 seconds
    setTimeout(function() {
        messageElement.remove();
    }, 5000);
}
