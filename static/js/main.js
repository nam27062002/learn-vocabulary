/* ==========================================================================
   LearnEnglish App - Main JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // Track all dropdown menus for mutual exclusion
    const dropdownMenus = [];
    
    // Generic dropdown toggle function with mutual exclusion
    const setupDropdown = (toggleId, menuId) => {
        const toggle = document.getElementById(toggleId);
        const menu = document.getElementById(menuId);

        if (toggle && menu) {
            // Add menu to tracking array
            dropdownMenus.push(menu);
            
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Close all other dropdowns first
                dropdownMenus.forEach(otherMenu => {
                    if (otherMenu !== menu) {
                        otherMenu.classList.add('hidden');
                    }
                });
                
                // Toggle current dropdown
                menu.classList.toggle('hidden');
            });

            document.addEventListener('click', (e) => {
                if (!menu.contains(e.target) && !toggle.contains(e.target)) {
                    menu.classList.add('hidden');
                }
            });
        }
    };

    // Setup User and Language dropdowns
    setupDropdown('user-toggle', 'user-menu');
    setupDropdown('lang-toggle', 'lang-menu');

    // ==========================================================================
    // Mobile Navigation
    // ==========================================================================
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            // Close all dropdown menus when mobile menu is toggled
            dropdownMenus.forEach(menu => {
                menu.classList.add('hidden');
            });
            
            mobileMenu.classList.toggle('hidden');
            // Toggle icons inside the button
            const icons = mobileMenuToggle.querySelectorAll('svg');
            icons.forEach(icon => icon.classList.toggle('hidden'));
        });
    }

    // ==========================================================================
    // Language Form Submission
    // ==========================================================================
    const langForm = document.querySelector('.lang-form');
    if (langForm) {
        const langButtons = langForm.querySelectorAll('button');
        langButtons.forEach(button => {
            button.addEventListener('click', function() {
                const nextInput = document.getElementById('nav-next-input');
                if (nextInput) {
                    const currentPath = window.location.pathname;
                    const targetLang = this.value;
                    let newPath = currentPath;

                    // This logic might need adjustment depending on your URL structure
                    if (currentPath.startsWith('/en/')) {
                        newPath = currentPath.substring(3);
                    } else if (currentPath.startsWith('/vi/')) {
                        newPath = currentPath.substring(3);
                    }
                    // Ensure leading slash
                    if (newPath.charAt(0) !== '/') {
                        newPath = '/' + newPath;
                    }

                    nextInput.value = `/${targetLang}${newPath}`;
                }
            });
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

    // ==========================================================================
    // Accessibility Enhancements
    // ==========================================================================
    
    // Keyboard navigation for dropdowns
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close all open dropdowns
            dropdownMenus.forEach(menu => {
                if(menu) menu.classList.add('hidden');
            });
            
            // Close mobile menu if open
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
                // Reset mobile menu icon state
                if (mobileMenuToggle) {
                    const icons = mobileMenuToggle.querySelectorAll('svg');
                    if (icons.length > 1) {
                        icons[0].classList.remove('hidden'); // Show hamburger
                        icons[1].classList.add('hidden');    // Hide close icon
                    }
                }
            }
        }
    });

    // ==========================================================================
    // Favorites Count in Navigation
    // ==========================================================================

    function initializeFavoritesCount() {
        // Check if user is authenticated (favorites count elements exist)
        const navFavoritesCount = document.getElementById('nav-favorites-count');
        const mobileFavoritesCount = document.getElementById('mobile-favorites-count');

        if (!navFavoritesCount && !mobileFavoritesCount) {
            console.log('Favorites count elements not found, user may not be authenticated');
            return;
        }

        // Load favorites count from API
        fetch('/api/favorites/count/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const count = data.count;
                console.log(`Favorites count loaded: ${count}`);

                // Update both desktop and mobile navigation
                if (navFavoritesCount) {
                    navFavoritesCount.textContent = count;
                    navFavoritesCount.style.display = count > 0 ? 'inline' : 'none';
                }

                if (mobileFavoritesCount) {
                    mobileFavoritesCount.textContent = count;
                    mobileFavoritesCount.style.display = count > 0 ? 'inline' : 'none';
                }
            } else {
                console.error('Failed to load favorites count:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading favorites count:', error);
        });
    }

    // Initialize favorites count
    initializeFavoritesCount();

    // Make favorites count function globally available for other scripts
    window.updateFavoritesCount = initializeFavoritesCount;

    // ==========================================================================
    // Console Welcome Message
    // ==========================================================================

    // Get localized text from global context if available
    const consoleTexts = window.manual_texts || {};
    console.log(`%c${consoleTexts.console_welcome || '🎓 LearnEnglish App'}`, 'color: #667eea; font-size: 20px; font-weight: bold;');
    console.log(`%c${consoleTexts.console_subtitle || 'Welcome to the developer console!'}`, 'color: #764ba2; font-size: 14px;');
    console.log(consoleTexts.console_built_with || 'Built with Django + Tailwind CSS + JavaScript ❤️');
});