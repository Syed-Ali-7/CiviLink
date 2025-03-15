// Main JavaScript for BBMP Ward Issues Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(message => {
            const bsAlert = new bootstrap.Alert(message);
            bsAlert.close();
        });
    }, 5000);

    // Add animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Enable tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // File input preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewContainer = document.getElementById(this.id + 'Preview');
            if (previewContainer && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewContainer.innerHTML = `<img src="${e.target.result}" class="img-preview img-fluid rounded">`;
                    previewContainer.classList.remove('d-none');
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Handle Back Button Cache Issues
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            window.location.reload();
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// Function to confirm actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Function for handling loading states
function setLoading(button, isLoading) {
    if (isLoading) {
        const originalText = button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Loading...';
        button.disabled = true;
    } else {
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
        button.disabled = false;
    }
}

// Add loading state to forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                setLoading(submitBtn, true);
            }
        });
    });
    
    // Handle status radios for issue resolution
    const statusRadios = document.querySelectorAll('.status-radio');
    if (statusRadios.length > 0) {
        statusRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                const resolvedPhotoSection = document.getElementById('resolvedPhotoSection');
                const resolvedPhotoInput = document.getElementById('resolvedPhoto');
                
                if (this.value === 'resolved') {
                    resolvedPhotoSection.style.display = 'block';
                    resolvedPhotoInput.disabled = false;
                    resolvedPhotoInput.required = true;
                    
                    // Show the preview container
                    const previewContainer = document.getElementById('resolvedPhotoPreviewContainer');
                    if (previewContainer) {
                        previewContainer.style.display = 'block';
                    }
                } else {
                    resolvedPhotoSection.style.display = 'none';
                    resolvedPhotoInput.disabled = true;
                    resolvedPhotoInput.required = false;
                }
            });
        });
    }
    
    // Handle resolved photo preview
    const resolvedPhotoInput = document.getElementById('resolvedPhoto');
    if (resolvedPhotoInput) {
        resolvedPhotoInput.addEventListener('change', function() {
            const previewContainer = document.getElementById('resolvedPhotoPreviewContainer');
            const previewElement = document.getElementById('resolvedPhotoPreview');
            
            if (previewContainer && previewElement && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewElement.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="mb-0">New Resolved Photo:</h6>
                        </div>
                        <img src="${e.target.result}" class="img-fluid rounded" alt="Resolved issue preview" style="max-height: 200px;">
                    `;
                    previewElement.style.display = 'block';
                    previewContainer.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
});
