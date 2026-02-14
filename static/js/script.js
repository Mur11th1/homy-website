// Global variables
let currentUser = null;
let selectedService = null;
let servicesData = [];

// ============ CURRENCY UTILITIES ============
const CURRENCY = {
    symbol: 'KES',
    convenienceFee: 300, // KES 300 convenience fee (was $2.99 ≈ KES 300)
    format: function(amount) {
        // Format number with commas and currency symbol
        return `${this.symbol} ${parseFloat(amount).toLocaleString('en-KE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;
    },
    parse: function(currencyString) {
        // Remove currency symbol and commas, convert to number
        return parseFloat(currencyString.replace(/[^0-9.-]+/g, ''));
    }
};

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Logo interaction - UPDATED FOR CURRENT HTML STRUCTURE
    const logo = document.querySelector('.logo');
    const logoImage = document.querySelector('.logo img');
    const logoText = document.querySelector('.logo-text');
    
    if (logo) {
        console.log('Logo element found');
        
        // Mouse enter effect
        logo.addEventListener('mouseenter', function() {
            if (logoImage) {
                logoImage.style.transform = 'scale(1.15) rotate(5deg)';
                logoImage.style.filter = 'drop-shadow(0 0 20px rgba(255, 255, 255, 0.8)) brightness(1.1)';
            }
            if (logoText) {
                logoText.style.transform = 'scale(1.05)';
                logoText.style.textShadow = '0 0 30px rgba(255, 255, 255, 0.7)';
            }
        });
        
        // Mouse leave effect
        logo.addEventListener('mouseleave', function() {
            if (logoImage) {
                logoImage.style.transform = 'scale(1) rotate(0deg)';
                logoImage.style.filter = 'drop-shadow(0 0 10px rgba(255, 255, 255, 0.5)) brightness(1)';
            }
            if (logoText) {
                logoText.style.transform = 'scale(1)';
                logoText.style.textShadow = '0 0 20px rgba(255, 255, 255, 0.3)';
            }
        });
        
        // Click effect
        logo.addEventListener('click', function() {
            console.log('Logo clicked');
            if (logoImage) {
                logoImage.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    logoImage.style.transform = 'scale(1)';
                }, 200);
            }
            // Navigate to home page
            setTimeout(() => {
                window.location.href = '/';
            }, 300);
        });
    } else {
        console.log('Logo element not found on this page');
    }
    
    // Add click event to Enter button if it exists
    const enterBtn = document.querySelector('.enter-btn');
    if (enterBtn) {
        console.log('Enter button found, adding click handler');
        enterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Enter button clicked');
            enterWebsite();
        });
    }
    
    // Load services if on services page
    if (document.getElementById('servicesGrid')) {
        console.log('Loading services for services page...');
        loadServices();
    }
    
    // Load services for checkout page
    if (document.getElementById('servicesCategories')) {
        console.log('Loading services for checkout page...');
        loadServicesForCheckout();
    }
    
    // Initialize auth forms
    initializeAuthForms();
    
    // Check if user is logged in
    checkLoginStatus();
});

// Navigation
function enterWebsite() {
    console.log('enterWebsite function called');
    const btn = document.querySelector('.enter-btn');
    if (btn) {
        btn.style.transform = 'scale(0.95)';
        btn.textContent = 'Entering...';
        
        setTimeout(() => {
            window.location.href = '/services';
        }, 500);
    } else {
        window.location.href = '/services';
    }
}

// Make enterWebsite available globally
window.enterWebsite = enterWebsite;

// Load services for services page
async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        if (data.success) {
            servicesData = data.services;
            displayServices(servicesData);
        }
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

// UPDATED: Display services with KES currency
function displayServices(services) {
    const servicesGrid = document.getElementById('servicesGrid');
    if (!servicesGrid) return;
    
    servicesGrid.innerHTML = '';
    
    services.forEach(service => {
        const serviceCard = document.createElement('div');
        serviceCard.className = 'service-card';
        serviceCard.onclick = () => selectService(service);
        
        // Generate stars for rating
        const stars = '★'.repeat(Math.floor(service.rating)) + '☆'.repeat(5 - Math.floor(service.rating));
        
        serviceCard.innerHTML = `
            <div class="service-icon">
                <i class="fas fa-${getServiceIcon(service.category)}"></i>
            </div>
            <h3>${service.name}</h3>
            <p>${service.description}</p>
            <div class="service-price">${CURRENCY.format(service.price)}</div>
            <div class="service-rating">${stars} (${service.rating})</div>
            <div class="service-duration">Duration: ${service.duration} minutes</div>
        `;
        
        servicesGrid.appendChild(serviceCard);
    });
}

function getServiceIcon(category) {
    const icons = {
        'AC Repair': 'snowflake',
        'Beauty': 'spa',
        'Plumbing': 'wrench',
        'Electrician': 'bolt',
        'Carpentry': 'hammer',
        'Cleaning': 'broom',
        'Washing': 'tshirt'
    };
    return icons[category] || 'tools';
}

function searchServices() {
    const searchTerm = document.getElementById('serviceSearch').value.toLowerCase();
    const filteredServices = servicesData.filter(service => 
        service.name.toLowerCase().includes(searchTerm) ||
        service.description.toLowerCase().includes(searchTerm) ||
        service.category.toLowerCase().includes(searchTerm)
    );
    displayServices(filteredServices);
}

// Auth functionality
function switchTab(tab) {
    // Update tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(tab)) {
            btn.classList.add('active');
        }
    });
    
    // Show selected form
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    
    document.getElementById(`${tab}Form`).classList.add('active');
}

function initializeAuthForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            // Show loading state
            const submitBtn = this.querySelector('.auth-submit-btn');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Signing in...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Login successful!');
                    window.location.href = '/checkout';
                } else {
                    alert('Login failed: ' + data.message);
                }
            } catch (error) {
                alert('Error during login: ' + error.message);
            } finally {
                // Restore button state
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const name = document.getElementById('registerName').value;
            const email = document.getElementById('registerEmail').value;
            const phone = document.getElementById('registerPhone').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('registerConfirmPassword').value;
            
            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        full_name: name,
                        email,
                        phone,
                        password
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Registration successful! Please login.');
                    switchTab('login');
                } else {
                    alert('Registration failed: ' + data.message);
                }
            } catch (error) {
                alert('Error during registration');
            }
        });
    }
}

// Checkout page functions
async function loadServicesForCheckout() {
    console.log('=== Loading Services for Checkout ===');
    
    const servicesCategories = document.getElementById('servicesCategories');
    const fixNotice = document.getElementById('fixServicesNotice');
    
    if (!servicesCategories) {
        console.error('servicesCategories element not found');
        return;
    }
    
    // Hide fix notice initially
    if (fixNotice) {
        fixNotice.style.display = 'none';
    }
    
    // Show loading state
    servicesCategories.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading services...</p>
        </div>
    `;
    
    try {
        console.log('Fetching services from API...');
        const response = await fetch('/api/services');
        const data = await response.json();
        
        console.log('API Response:', data);
        
        if (data.success && data.services && data.services.length > 0) {
            servicesData = data.services;
            console.log(`Loaded ${servicesData.length} services`);
            
            displayServicesByCategory(servicesData);
            populateServiceSelect(servicesData);
            
            // Hide fix notice if services loaded successfully
            if (fixNotice) {
                fixNotice.style.display = 'none';
            }
            
        } else {
            console.error('No services loaded:', data.message);
            servicesCategories.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>No Services Available</h3>
                    <p>${data.message || 'Could not load services'}</p>
                    <button onclick="loadServicesForCheckout()" class="btn" style="margin-top: 10px;">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
            
            // Show fix notice
            if (fixNotice) {
                fixNotice.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error loading services:', error);
        servicesCategories.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Connection Error</h3>
                <p>Unable to connect to server.</p>
                <button onclick="loadServicesForCheckout()" class="btn" style="margin-top: 10px;">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>
            </div>
        `;
        
        // Show fix notice
        if (fixNotice) {
            fixNotice.style.display = 'block';
        }
    }
}

// UPDATED: Display services by category with KES currency
function displayServicesByCategory(services) {
    const servicesCategories = document.getElementById('servicesCategories');
    if (!servicesCategories) {
        console.error('servicesCategories element not found');
        return;
    }
    
    console.log('Displaying services by category:', services);
    
    if (!services || services.length === 0) {
        servicesCategories.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>No Services Found</h3>
                <p>No services are currently available.</p>
            </div>
        `;
        return;
    }
    
    // Group services by category
    const categories = {};
    
    services.forEach(service => {
        if (!service.category) {
            console.warn('Service missing category:', service);
            service.category = 'Other';
        }
        
        if (!categories[service.category]) {
            categories[service.category] = [];
        }
        categories[service.category].push(service);
    });
    
    console.log('Grouped categories:', Object.keys(categories));
    
    // Build HTML
    let html = '';
    
    Object.entries(categories).forEach(([category, categoryServices]) => {
        html += `
            <div class="category">
                <h4>${category}</h4>
        `;
        
        categoryServices.forEach(service => {
            html += `
                <div class="service-item" onclick="selectServiceForBooking('${service.id}')">
                    <div class="service-info">
                        <strong>${service.name || 'Unnamed Service'}</strong>
                        <p class="service-description">${service.description || 'No description available'}</p>
                        <div class="service-rating">
                            ${'★'.repeat(Math.floor(service.rating || 0))}${'☆'.repeat(5 - Math.floor(service.rating || 0))}
                            <span class="rating-text">(${service.rating || 0})</span>
                        </div>
                    </div>
                    <div class="service-price">
                        ${CURRENCY.format(service.price || 0)}
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    servicesCategories.innerHTML = html;
    
    // Add event listeners to service items
    setTimeout(() => {
        document.querySelectorAll('.service-item').forEach(item => {
            item.addEventListener('click', function() {
                document.querySelectorAll('.service-item').forEach(i => {
                    i.classList.remove('selected');
                });
                this.classList.add('selected');
            });
        });
    }, 100);
}

// UPDATED: Populate service select dropdown with KES
function populateServiceSelect(services) {
    const serviceSelect = document.getElementById('serviceSelect');
    if (!serviceSelect) {
        console.error('serviceSelect element not found');
        return;
    }
    
    console.log('Populating service select dropdown with', services.length, 'services');
    
    // Clear existing options except the first one
    serviceSelect.innerHTML = '<option value="">Choose a service</option>';
    
    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service.id;
        option.textContent = `${service.name} - ${CURRENCY.format(service.price)}`;
        option.setAttribute('data-price', service.price);
        option.setAttribute('data-category', service.category);
        serviceSelect.appendChild(option);
    });
    
    // Add change event listener
    serviceSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.value) {
            const price = parseFloat(selectedOption.getAttribute('data-price'));
            updatePrice(price);
            
            // Highlight corresponding service item
            document.querySelectorAll('.service-item').forEach(item => {
                item.classList.remove('selected');
            });
        } else {
            updatePrice(0);
        }
    });
    
    console.log('Service select populated with', serviceSelect.options.length - 1, 'options');
}

function selectServiceForBooking(serviceId) {
    const serviceSelect = document.getElementById('serviceSelect');
    if (serviceSelect) {
        // Find the option with this serviceId
        for (let option of serviceSelect.options) {
            if (option.value === serviceId) {
                serviceSelect.value = serviceId;
                // Trigger change event to update price
                const event = new Event('change');
                serviceSelect.dispatchEvent(event);
                break;
            }
        }
    }
}

function selectService(service) {
    selectedService = service;
    // Store selected service in sessionStorage for checkout page
    sessionStorage.setItem('selectedService', JSON.stringify(service));
    window.location.href = '/checkout';
}

// UPDATED: Update price with KES
function updatePrice(servicePrice) {
    const serviceFee = document.getElementById('serviceFee');
    const totalPrice = document.getElementById('totalPrice');
    
    if (serviceFee && totalPrice) {
        const total = servicePrice + CURRENCY.convenienceFee;
        
        serviceFee.textContent = CURRENCY.format(servicePrice);
        totalPrice.textContent = CURRENCY.format(total);
    }
}

function searchCheckoutServices() {
    const searchTerm = document.getElementById('checkoutSearch').value.toLowerCase();
    const serviceItems = document.querySelectorAll('.service-item');
    
    serviceItems.forEach(item => {
        const serviceText = item.textContent.toLowerCase();
        if (serviceText.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function selectPayment(method) {
    document.querySelectorAll('.payment-method').forEach(el => {
        el.classList.remove('active');
    });
    
    const selected = document.querySelector(`[onclick*="${method}"]`);
    if (selected) {
        selected.classList.add('active');
    }
}

// UPDATED: Process booking with KES
async function processBooking() {
    console.log('=== Starting Booking Process ===');
    
    // Get all form elements
    const serviceSelect = document.getElementById('serviceSelect');
    const serviceDate = document.getElementById('serviceDate');
    const address = document.getElementById('address');
    const termsAgree = document.getElementById('termsAgree');
    const cardNumber = document.getElementById('cardNumber');
    const expiryDate = document.getElementById('expiryDate');
    const cvv = document.getElementById('cvv');
    const cardName = document.getElementById('cardName');
    
    // Debug logging
    console.log('Form values:');
    console.log('- Service:', serviceSelect ? serviceSelect.value : 'N/A');
    console.log('- Service Date:', serviceDate ? serviceDate.value : 'N/A');
    console.log('- Address:', address ? address.value : 'N/A');
    console.log('- Terms Agreed:', termsAgree ? termsAgree.checked : 'N/A');
    console.log('- Card Number:', cardNumber ? cardNumber.value : 'N/A');
    console.log('- Expiry Date:', expiryDate ? expiryDate.value : 'N/A');
    console.log('- CVV:', cvv ? '***' : 'N/A');
    console.log('- Card Name:', cardName ? cardName.value : 'N/A');
    
    // Validation
    const errors = [];
    
    if (!serviceSelect || !serviceSelect.value) {
        errors.push('Please select a service');
    }
    
    if (!serviceDate || !serviceDate.value) {
        errors.push('Please select a date and time');
    }
    
    if (!address || !address.value.trim()) {
        errors.push('Please enter your address');
    }
    
    if (!termsAgree || !termsAgree.checked) {
        errors.push('Please agree to the Terms & Conditions');
    }
    
    // Payment validation
    if (!cardNumber || !cardNumber.value.trim()) {
        errors.push('Please enter card number');
    } else if (cardNumber.value.replace(/\s/g, '').length < 12) {
        errors.push('Please enter a valid card number (12-16 digits)');
    }
    
    if (!expiryDate || !expiryDate.value.trim()) {
        errors.push('Please enter expiry date');
    }
    
    if (!cvv || !cvv.value.trim()) {
        errors.push('Please enter CVV');
    } else if (cvv.value.length < 3) {
        errors.push('Please enter a valid CVV (3-4 digits)');
    }
    
    if (!cardName || !cardName.value.trim()) {
        errors.push('Please enter name on card');
    }
    
    if (errors.length > 0) {
        alert('❌ Please fix the following errors:\n\n• ' + errors.join('\n• '));
        return;
    }
    
    // Show loading
    const bookBtn = document.querySelector('.book-btn');
    const originalText = bookBtn ? bookBtn.innerHTML : 'Book Now & Pay';
    if (bookBtn) {
        bookBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        bookBtn.disabled = true;
    }
    
    try {
        // Check if user is logged in
        console.log('Checking user session...');
        const sessionCheck = await fetch('/api/check-session');
        const sessionData = await sessionCheck.json();
        
        if (!sessionData.logged_in) {
            alert('Please login first to book a service');
            window.location.href = '/auth';
            return;
        }
        
        console.log('User logged in:', sessionData);
        
        // Get price
        const serviceFee = document.getElementById('serviceFee');
        const totalPrice = document.getElementById('totalPrice');
        
        let serviceFeeValue = 0;
        let totalPriceValue = 0;
        
        if (serviceFee) {
            serviceFeeValue = CURRENCY.parse(serviceFee.textContent);
        }
        
        if (totalPrice) {
            totalPriceValue = CURRENCY.parse(totalPrice.textContent);
        }
        
        console.log('Prices - Service Fee:', serviceFeeValue, 'Total:', totalPriceValue);
        
        // Prepare booking data
        const bookingData = {
            user_id: sessionData.user_id,
            service_id: serviceSelect.value,
            service_date: serviceDate.value.replace('T', ' '), // Fix datetime-local format
            address: address.value.trim(),
            total_price: totalPriceValue
        };
        
        console.log('Sending booking data:', bookingData);
        
        // Send booking request
        const response = await fetch('/api/book', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bookingData)
        });
        
        const data = await response.json();
        console.log('Booking response:', data);
        
        if (data.success) {
            // Simulate payment processing
            setTimeout(() => {
                alert(`✅ ${data.message}\n\n📋 Booking ID: ${data.booking_id}\n💰 Amount Paid: ${CURRENCY.format(totalPriceValue)}\n📅 Service Date: ${serviceDate.value}\n📍 Address: ${address.value}`);
                
                // Redirect to services page
                window.location.href = '/services';
            }, 1000);
            
        } else {
            alert(`❌ Booking failed:\n\n${data.message}`);
            
            // Restore button
            if (bookBtn) {
                bookBtn.innerHTML = originalText;
                bookBtn.disabled = false;
            }
        }
        
    } catch (error) {
        console.error('Booking process error:', error);
        alert('❌ An error occurred while processing your booking. Please try again.');
        
        // Restore button
        if (bookBtn) {
            bookBtn.innerHTML = originalText;
            bookBtn.disabled = false;
        }
    }
}

// ============ FIX FUNCTIONS ============

async function fixServicesTable() {
    if (!confirm('This will recreate the services table with fresh data. Continue?')) {
        return;
    }
    
    const servicesCategories = document.getElementById('servicesCategories');
    if (servicesCategories) {
        servicesCategories.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Fixing services table...</p>
            </div>
        `;
    }
    
    try {
        const response = await fetch('/api/fix-services', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ ${data.message}`);
            // Reload services
            loadServicesForCheckout();
        } else {
            alert(`❌ Failed to fix services: ${data.message}`);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Add this helper function for the "Retry" button
function forceReloadServices() {
    loadServicesForCheckout();
}

// Add this debug function
async function debugCheckout() {
    console.log('=== DEBUG CHECKOUT ===');
    
    // Check if elements exist
    console.log('servicesCategories exists:', !!document.getElementById('servicesCategories'));
    console.log('serviceSelect exists:', !!document.getElementById('serviceSelect'));
    
    // Check API endpoints
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        console.log('/api/services response:', data);
    } catch (error) {
        console.error('Debug error:', error);
    }
}

// ============ UTILITY FUNCTIONS ============

// Add UUID validation function
function isValidUUID(uuid) {
    if (!uuid) return false;
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
}

async function checkLoginStatus() {
    try {
        const response = await fetch('/api/check-session');
        const data = await response.json();
        
        if (data.logged_in) {
            currentUser = {
                id: data.user_id,
                email: data.email,
                name: data.name
            };
            console.log('User logged in:', currentUser);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error checking login status:', error);
        return false;
    }
}

// Force reload services (alternative version)
async function forceReloadServicesAlt() {
    try {
        const response = await fetch('/api/db/sample-data', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Sample services created! Loading...');
            loadServicesForCheckout();
        } else {
            alert('Failed to create services: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Test UUID function
function testUUID() {
    const serviceSelect = document.getElementById('serviceSelect');
    if (!serviceSelect || !serviceSelect.value) {
        alert('Please select a service first');
        return;
    }
    
    const uuid = serviceSelect.value;
    const isValid = isValidUUID(uuid);
    alert(`UUID "${uuid}" is ${isValid ? 'VALID' : 'INVALID'}`);
    
    if (!isValid) {
        console.error('Invalid UUID in service select:', uuid);
    }
}

// Make functions available globally
window.fixServicesTable = fixServicesTable;
window.forceReloadServices = forceReloadServices;
window.debugCheckout = debugCheckout;
window.testUUID = testUUID;
window.searchCheckoutServices = searchCheckoutServices;
window.selectPayment = selectPayment;
window.processBooking = processBooking;
window.switchTab = switchTab;
window.selectServiceForBooking = selectServiceForBooking;