// form.js - Contact form validation and submission handler
// Handles client-side validation, accessibility, and success message display

// Select form and associated elements
const form = document.querySelector('form');
const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const messageInput = document.getElementById('message');
const nameError = document.getElementById('name-error');
const emailError = document.getElementById('email-error');
const messageError = document.getElementById('message-error');
const successMessage = document.getElementById('success-message');

// Email validation regex pattern
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Form submission handler
form.addEventListener('submit', function(event) {
    // Prevent default form submission
    event.preventDefault();
    
    // Reset error messages and success state
    nameError.textContent = '';
    emailError.textContent = '';
    messageError.textContent = '';
    successMessage.style.display = 'none';
    
    // Flag to track form validity
    let isValid = true;

    // Validate name field
    if (nameInput.value.trim() === '') {
        nameError.textContent = 'Name is required';
        nameError.setAttribute('aria-live', 'polite');
        isValid = false;
    }

    // Validate email field
    if (!emailRegex.test(emailInput.value)) {
        emailError.textContent = 'Please enter a valid email address';
        emailError.setAttribute('aria-live', 'polite');
        isValid = false;
    }

    // Validate message field
    if (messageInput.value.trim() === '') {
        messageError.textContent = 'Message is required';
        messageError.setAttribute('aria-live', 'polite');
        isValid = false;
    }

    // If form is valid, show success message
    if (isValid) {
        successMessage.style.display = 'block';
        successMessage.setAttribute('aria-live', 'assertive');
        // Reset form fields
        form.reset();
    }
});

// Keyboard navigation support: focus management
form.addEventListener('keydown', function(event) {
    // Allow tab navigation to work as expected
    if (event.key === 'Tab') {
        // Ensure focusable elements are properly managed
        // This is primarily handled by browser default behavior
    }
});

// Accessibility: Add ARIA attributes to form elements
nameInput.setAttribute('aria-required', 'true');
emailInput.setAttribute('aria-required', 'true');
messageInput.setAttribute('aria-required', 'true');

// Ensure error messages are announced by screen readers
nameError.setAttribute('role', 'alert');
emailError.setAttribute('role', 'alert');
messageError.setAttribute('role', 'alert');
successMessage.setAttribute('role', 'status');