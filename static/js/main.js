// Main JavaScript file for Apparel Inventory System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Confirm delete actions
    document.querySelectorAll('.btn-danger').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Handle sidebar toggle on mobile
    var sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }
});

// Function to format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Function to validate email format
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Function to validate phone number format
function validatePhone(phone) {
    const re = /^$$?([0-9]{3})$$?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
    return re.test(String(phone));
}

// Form validation for customer form
const customerForm = document.getElementById('customerForm');
if (customerForm) {
    customerForm.addEventListener('submit', function(e) {
        const emailInput = document.getElementById('email');
        const phoneInput = document.getElementById('phone');
        
        let isValid = true;
        
        // Validate email
        if (emailInput && !validateEmail(emailInput.value)) {
            alert('Please enter a valid email address');
            emailInput.focus();
            isValid = false;
        }
        
        // Validate phone if provided
        if (phoneInput && phoneInput.value && !validatePhone(phoneInput.value)) {
            alert('Please enter a valid phone number');
            phoneInput.focus();
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
        }
    });
}

// Form validation for product form
const productForm = document.getElementById('productForm');
if (productForm) {
    productForm.addEventListener('submit', function(e) {
        const priceInput = document.getElementById('price');
        const quantityInput = document.getElementById('quantity');
        
        let isValid = true;
        
        // Validate price
        if (priceInput && (isNaN(priceInput.value) || parseFloat(priceInput.value) <= 0)) {
            alert('Please enter a valid price greater than zero');
            priceInput.focus();
            isValid = false;
        }
        
        // Validate quantity
        if (quantityInput && (isNaN(quantityInput.value) || parseInt(quantityInput.value) < 0)) {
            alert('Please enter a valid quantity (zero or greater)');
            quantityInput.focus();
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
        }
    });
}