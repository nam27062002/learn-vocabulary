/* ==========================================================================
   LearnEnglish App - Main JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================================
    // Mobile Navigation
    // ==========================================================================
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        // Mobile menu toggle
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navMenu.contains(event.target) && !mobileMenuToggle.contains(event.target)) {
                navMenu.classList.remove('active');
            }
        });

        // Close mobile menu when window is resized to desktop
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navMenu.classList.remove('active');
            }
        });
    }

    // ==========================================================================
    // Language Switcher
    // ==========================================================================
    const langToggle = document.getElementById('lang-toggle');
    const langMenu = document.getElementById('lang-menu');
    
    if (langToggle && langMenu) {
        const dropdownArrow = langToggle.querySelector('.dropdown-arrow');
        
        langToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const isOpen = langMenu.classList.contains('show');

            if (isOpen) {
                langMenu.classList.remove('show');
                if (dropdownArrow) dropdownArrow.style.transform = 'rotate(0deg)';
            } else {
                langMenu.classList.add('show');
                if (dropdownArrow) dropdownArrow.style.transform = 'rotate(180deg)';
            }
        });

        // Close language menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!langToggle.contains(event.target) && !langMenu.contains(event.target)) {
                langMenu.classList.remove('show');
                if (dropdownArrow) dropdownArrow.style.transform = 'rotate(0deg)';
            }
        });

        // Language form submission handling
        const langForm = document.querySelector('.lang-form');
        const langButtons = document.querySelectorAll('.lang-option');
        
        if (langForm && langButtons.length > 0) {
            langButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    console.log('Language button clicked:', this.value);
                    // Form will submit naturally
                });
            });
            
            langForm.addEventListener('submit', function(e) {
                console.log('Language form submitted');
                // Form will submit naturally
            });
            
            // Update next URL for navigation language switching
            langButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const targetLang = this.value;
                    const currentPath = window.location.pathname;
                    const nextInput = document.getElementById('nav-next-input');
                    
                    if (nextInput) {
                        // Remove current language prefix and add target language
                        let newPath = currentPath;
                        if (currentPath.startsWith('/vi/')) {
                            newPath = currentPath.substring(3);
                        } else if (currentPath.startsWith('/en/')) {
                            newPath = currentPath.substring(3);
                        }
                        
                        nextInput.value = '/' + targetLang + newPath;
                        console.log('Nav language switch to:', targetLang, 'Next URL:', nextInput.value);
                    }
                });
            });
        }
    }

    // ==========================================================================
    // User Dropdown
    // ==========================================================================
    const userToggle = document.getElementById('user-toggle');
    const userMenu = document.getElementById('user-menu');
    
    if (userToggle && userMenu) {
        const userDropdownArrow = userToggle.querySelector('.dropdown-arrow');
        
        userToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const isOpen = userMenu.classList.contains('show');

            if (isOpen) {
                userMenu.classList.remove('show');
                if (userDropdownArrow) userDropdownArrow.style.transform = 'rotate(0deg)';
            } else {
                userMenu.classList.add('show');
                if (userDropdownArrow) userDropdownArrow.style.transform = 'rotate(180deg)';
            }
        });

        // Close user menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!userToggle.contains(event.target) && !userMenu.contains(event.target)) {
                userMenu.classList.remove('show');
                if (userDropdownArrow) userDropdownArrow.style.transform = 'rotate(0deg)';
            }
        });
    }

    // ==========================================================================
    // Form Enhancements
    // ==========================================================================
    
    // Auto-focus first input in forms
    const firstInput = document.querySelector('form input:not([type="hidden"]):first-of-type');
    if (firstInput && !firstInput.hasAttribute('readonly')) {
        firstInput.focus();
    }

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                // Clear validation styles on input
                this.classList.remove('error', 'success');
            });
        });
    });

    function validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        // Reset classes
        field.classList.remove('error', 'success');
        
        if (required && !value) {
            field.classList.add('error');
            return false;
        }
        
        if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                field.classList.add('error');
                return false;
            }
        }
        
        if (value) {
            field.classList.add('success');
        }
        
        return true;
    }

    // ==========================================================================
    // Smooth Animations & Interactions
    // ==========================================================================
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.button, .action-btn, .nav-link');
    buttons.forEach(button => {
        button.addEventListener('click', createRipple);
    });

    function createRipple(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        // Add ripple styles if not already defined
        if (!document.querySelector('#ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                .ripple {
                    position: absolute;
                    border-radius: 50%;
                    background-color: rgba(255, 255, 255, 0.3);
                    transform: scale(0);
                    animation: ripple-animation 0.6s linear;
                    pointer-events: none;
                }
                @keyframes ripple-animation {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
                .button, .action-btn {
                    position: relative;
                    overflow: hidden;
                }
            `;
            document.head.appendChild(style);
        }
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // ==========================================================================
    // Page Loading Animation
    // ==========================================================================
    
    // Add fade-in animation to content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(20px)';
        mainContent.style.transition = 'all 0.5s ease';
        
        setTimeout(() => {
            mainContent.style.opacity = '1';
            mainContent.style.transform = 'translateY(0)';
        }, 100);
    }

    // ==========================================================================
    // Accessibility Enhancements
    // ==========================================================================
    
    // Keyboard navigation for dropdowns
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close all open dropdowns
            const openDropdowns = document.querySelectorAll('.lang-menu.show');
            openDropdowns.forEach(dropdown => {
                dropdown.classList.remove('show');
            });
            
            // Close mobile menu
            if (navMenu) {
                navMenu.classList.remove('active');
            }
        }
    });

    // ==========================================================================
    // Console Welcome Message
    // ==========================================================================
    
    console.log('%c🎓 LearnEnglish App', 'color: #667eea; font-size: 20px; font-weight: bold;');
    console.log('%cWelcome to the developer console!', 'color: #764ba2; font-size: 14px;');
    console.log('Built with Django + JavaScript ❤️');
}); 