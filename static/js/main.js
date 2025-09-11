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

    // Avatar upload handler
    const avatarInput = document.getElementById('avatarInput');
    if (avatarInput) {
        avatarInput.addEventListener('change', function() {
            const file = this.files && this.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('avatar', file);

            // Show loading overlay on avatars
            const desktopLoading = document.getElementById('avatarLoading');
            const mobileLoading = document.getElementById('mobileAvatarLoading');
            if (desktopLoading) desktopLoading.classList.remove('hidden');
            if (mobileLoading) mobileLoading.classList.remove('hidden');

            fetch('/profile/avatar/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.avatar_url) {
                    // Update avatar images on the page if present
                    const desktopAvatar = document.querySelector('#user-toggle img');
                    if (desktopAvatar) desktopAvatar.src = data.avatar_url;
                    const mobileAvatar = document.querySelector('#mobile-menu img');
                    if (mobileAvatar) mobileAvatar.src = data.avatar_url;
                } else {
                    console.error('Upload avatar failed:', data.error);
                }
            })
            .catch(err => console.error('Upload avatar error:', err))
            .finally(() => {
                if (desktopLoading) desktopLoading.classList.add('hidden');
                if (mobileLoading) mobileLoading.classList.add('hidden');
                this.value = '';
            });
        });
    }

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
    // Language menu buttons (manual language switch without Django i18n)
    const langMenu = document.getElementById('lang-menu');
    if (langMenu) {
        const langButtons = langMenu.querySelectorAll('button[data-lang]');
        langButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-lang');
                fetch('/api/set-language/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({ language: target })
                })
                .then(res => res.json())
                .then(data => {
                    if (data && data.success) {
                        // Close menu and reload to apply
                        langMenu.classList.add('hidden');
                        window.location.reload();
                    } else {
                        console.error('Set language failed:', data);
                    }
                })
                .catch(err => console.error('Set language error:', err));
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