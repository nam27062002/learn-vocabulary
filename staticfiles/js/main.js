// ============================================
// MODERN UX/UI JAVASCRIPT SYSTEM
// ============================================

class VocabularyApp {
  constructor() {
    this.theme = localStorage.getItem('theme') || 'dark';
    this.isAnimationsEnabled = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.toastContainer = null;
    this.init();
  }

  init() {
    this.initTheme();
    this.initToastContainer();
    this.initEventListeners();
    this.initAnimations();
    this.initIntersectionObserver();
    this.initProgressBars();
    console.log('🚀 Vocabulary App initialized with modern UX/UI');
  }

  // ============================================
  // THEME SYSTEM
  // ============================================

  initTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateThemeToggle();
  }

  toggleTheme() {
    this.theme = this.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', this.theme);
    localStorage.setItem('theme', this.theme);
    this.updateThemeToggle();
    this.showToast('success', `Switched to ${this.theme} mode`, 2000);
  }

  updateThemeToggle() {
    const toggles = document.querySelectorAll('.theme-toggle');
    toggles.forEach(toggle => {
      toggle.setAttribute('aria-label', `Switch to ${this.theme === 'dark' ? 'light' : 'dark'} mode`);
    });
  }

  // ============================================
  // TOAST SYSTEM
  // ============================================

  initToastContainer() {
    if (!document.querySelector('.toast-container')) {
      this.toastContainer = document.createElement('div');
      this.toastContainer.className = 'toast-container';
      document.body.appendChild(this.toastContainer);
    } else {
      this.toastContainer = document.querySelector('.toast-container');
    }
  }

  showToast(type = 'info', message, duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="toast-icon">${this.getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;

    this.toastContainer.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto remove
    if (duration > 0) {
      setTimeout(() => {
        this.removeToast(toast);
      }, duration);
    }

    return toast;
  }

  removeToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
    }, 300);
  }

  getToastIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  // ============================================
  // ANIMATION SYSTEM
  // ============================================

  initAnimations() {
    if (!this.isAnimationsEnabled) return;

    // Stagger animations for lists
    this.animateStaggeredElements();
    
    // Button ripple effects
    this.initRippleEffects();
    
    // Smooth page transitions
    this.initPageTransitions();
  }

  animateStaggeredElements() {
    const staggerContainers = document.querySelectorAll('.stagger');
    staggerContainers.forEach(container => {
      const children = container.children;
      Array.from(children).forEach((child, index) => {
        child.style.animationDelay = `${index * 0.1}s`;
      });
    });
  }

  initRippleEffects() {
    document.addEventListener('click', (e) => {
      const button = e.target.closest('.btn');
      if (!button || button.disabled) return;

      const ripple = document.createElement('span');
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple 0.6s linear;
        left: ${x}px;
        top: ${y}px;
        width: ${size}px;
        height: ${size}px;
      `;

      button.style.position = 'relative';
      button.style.overflow = 'hidden';
      button.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    });

    // Add ripple animation CSS
    if (!document.querySelector('#ripple-styles')) {
      const style = document.createElement('style');
      style.id = 'ripple-styles';
      style.textContent = `
        @keyframes ripple {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  initPageTransitions() {
    // Add page transition effects for navigation
    const links = document.querySelectorAll('a[href^="/"], a[href^="' + window.location.origin + '"]');
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
        
        const href = link.getAttribute('href');
        if (href && href !== '#' && !href.startsWith('javascript:')) {
          document.body.style.opacity = '0.8';
          document.body.style.transform = 'scale(0.98)';
          document.body.style.transition = 'all 0.2s ease';
        }
      });
    });
  }

  // ============================================
  // INTERSECTION OBSERVER
  // ============================================

  initIntersectionObserver() {
    if (!window.IntersectionObserver) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fadeInUp');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '50px'
    });

    // Observe cards and other animated elements
    const animatedElements = document.querySelectorAll('.card, .flashcard-item, .stat-card');
    animatedElements.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px)';
      observer.observe(el);
    });
  }

  // ============================================
  // PROGRESS BARS
  // ============================================

  initProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
      const width = bar.getAttribute('data-width') || bar.style.width || '0%';
      bar.style.width = '0%';
      
      setTimeout(() => {
        bar.style.width = width;
      }, 500);
    });
  }

  // ============================================
  // MODAL SYSTEM
  // ============================================

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus trap
    const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }

    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        this.closeModal(modalId);
      }
    });

    // Close on escape key
    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        this.closeModal(modalId);
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.remove('show');
    document.body.style.overflow = '';
  }

  // ============================================
  // DROPDOWN SYSTEM
  // ============================================

  initDropdowns() {
    document.addEventListener('click', (e) => {
      const dropdown = e.target.closest('.dropdown');
      const trigger = e.target.closest('[data-dropdown-trigger]');
      
      if (trigger) {
        e.preventDefault();
        const targetId = trigger.getAttribute('data-dropdown-trigger');
        const targetDropdown = document.querySelector(`[data-dropdown="${targetId}"]`);
        
        if (targetDropdown) {
          // Close other dropdowns
          document.querySelectorAll('.dropdown.show').forEach(d => {
            if (d !== targetDropdown.closest('.dropdown')) {
              d.classList.remove('show');
            }
          });
          
          targetDropdown.closest('.dropdown').classList.toggle('show');
        }
      } else if (!dropdown) {
        // Click outside - close all dropdowns
        document.querySelectorAll('.dropdown.show').forEach(d => {
          d.classList.remove('show');
        });
      }
    });
  }

  // ============================================
  // FORM ENHANCEMENTS
  // ============================================

  initFormEnhancements() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
      textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
      });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      const inputs = form.querySelectorAll('input, textarea, select');
      inputs.forEach(input => {
        input.addEventListener('blur', () => this.validateField(input));
        input.addEventListener('input', () => this.clearFieldError(input));
      });
    });

    // Auto-save drafts
    this.initAutoSave();
  }

  validateField(field) {
    const isValid = field.checkValidity();
    const errorElement = field.parentElement.querySelector('.form-error');
    
    if (!isValid) {
      field.classList.add('error');
      if (errorElement) {
        errorElement.textContent = field.validationMessage;
      }
    } else {
      field.classList.remove('error');
      if (errorElement) {
        errorElement.textContent = '';
      }
    }
    
    return isValid;
  }

  clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentElement.querySelector('.form-error');
    if (errorElement) {
      errorElement.textContent = '';
    }
  }

  initAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
      const formId = form.getAttribute('data-auto-save');
      let saveTimeout;

      form.addEventListener('input', (e) => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
          this.autoSaveForm(form, formId);
        }, 2000);
      });

      // Load saved data
      this.loadAutoSavedData(form, formId);
    });
  }

  autoSaveForm(form, formId) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
      data[key] = value;
    }

    localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
    this.showToast('info', 'Draft saved automatically', 1500);
  }

  loadAutoSavedData(form, formId) {
    const savedData = localStorage.getItem(`autosave_${formId}`);
    if (!savedData) return;

    try {
      const data = JSON.parse(savedData);
      Object.keys(data).forEach(key => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field && field.type !== 'file') {
          field.value = data[key];
        }
      });
      
      this.showToast('info', 'Draft restored', 2000);
    } catch (e) {
      console.warn('Failed to load auto-saved data:', e);
    }
  }

  // ============================================
  // SEARCH & FILTER
  // ============================================

  initSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
      let searchTimeout;
      
      input.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.performSearch(e.target.value, e.target);
        }, 300);
      });
    });
  }

  performSearch(query, input) {
    const target = input.getAttribute('data-search-target');
    const items = document.querySelectorAll(target || '.searchable-item');
    
    items.forEach(item => {
      const text = item.textContent.toLowerCase();
      const matches = text.includes(query.toLowerCase());
      
      item.style.display = matches ? '' : 'none';
      
      if (matches && query) {
        this.highlightText(item, query);
      } else {
        this.removeHighlight(item);
      }
    });

    // Update results count
    const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
    const countElement = document.querySelector('.search-results-count');
    if (countElement) {
      countElement.textContent = `${visibleItems.length} results found`;
    }
  }

  highlightText(element, query) {
    if (!query) return;
    
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );

    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
      textNodes.push(node);
    }

    textNodes.forEach(textNode => {
      const text = textNode.textContent;
      const regex = new RegExp(`(${query})`, 'gi');
      
      if (regex.test(text)) {
        const highlighted = text.replace(regex, '<mark>$1</mark>');
        const span = document.createElement('span');
        span.innerHTML = highlighted;
        textNode.parentNode.replaceChild(span, textNode);
      }
    });
  }

  removeHighlight(element) {
    const marks = element.querySelectorAll('mark');
    marks.forEach(mark => {
      mark.replaceWith(mark.textContent);
    });
  }

  // ============================================
  // MOBILE NAVIGATION
  // ============================================

  initMobileNavigation() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-nav');
    
    if (mobileToggle && mobileMenu) {
      mobileToggle.addEventListener('click', () => {
        mobileMenu.classList.toggle('show');
        mobileToggle.setAttribute('aria-expanded', 
          mobileToggle.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
        );
      });

      // Close on link click
      mobileMenu.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
          mobileMenu.classList.remove('show');
          mobileToggle.setAttribute('aria-expanded', 'false');
        }
      });

      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!mobileToggle.contains(e.target) && !mobileMenu.contains(e.target)) {
          mobileMenu.classList.remove('show');
          mobileToggle.setAttribute('aria-expanded', 'false');
        }
      });
    }
  }

  // ============================================
  // EVENT LISTENERS
  // ============================================

  initEventListeners() {
    // Theme toggle
    document.addEventListener('click', (e) => {
      if (e.target.matches('.theme-toggle')) {
        this.toggleTheme();
      }
    });

    // Initialize all interactive components
    this.initDropdowns();
    this.initFormEnhancements();
    this.initSearch();
    this.initMobileNavigation();

    // Handle escape key globally
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        // Close modals
        document.querySelectorAll('.modal.show').forEach(modal => {
          modal.classList.remove('show');
        });
        
        // Close dropdowns
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
          dropdown.classList.remove('show');
        });
      }
    });

    // Smooth scrolling for anchor links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (link) {
        e.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });

    // Loading states for forms
    document.addEventListener('submit', (e) => {
      const form = e.target;
      const submitButton = form.querySelector('button[type="submit"]');
      
      if (submitButton && !submitButton.disabled) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
          <span class="loading-spinner"></span>
          <span>Loading...</span>
        `;
        
        // Re-enable after 5 seconds (fallback)
        setTimeout(() => {
          submitButton.disabled = false;
          submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
        }, 5000);
      }
    });
  }

  // ============================================
  // UTILITY METHODS
  // ============================================

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // ============================================
  // VOCABULARY APP SPECIFIC FEATURES
  // ============================================

  initFlashcardInteractions() {
    const flashcards = document.querySelectorAll('.flashcard-item');
    flashcards.forEach(card => {
      card.addEventListener('click', () => {
        card.classList.toggle('flipped');
      });

      // Audio playback
      const audioButton = card.querySelector('.play-audio');
      if (audioButton) {
        audioButton.addEventListener('click', (e) => {
          e.stopPropagation();
          const audioUrl = audioButton.getAttribute('data-audio');
          if (audioUrl) {
            const audio = new Audio(audioUrl);
            audio.play().catch(e => {
              this.showToast('error', 'Could not play audio');
            });
          }
        });
      }

      // Delete functionality
      const deleteButton = card.querySelector('.delete-flashcard-btn');
      if (deleteButton) {
        deleteButton.addEventListener('click', (e) => {
          e.stopPropagation();
          this.deleteFlashcard(deleteButton.getAttribute('data-id'), card);
        });
      }
    });
  }

  deleteFlashcard(cardId, cardElement) {
    if (!confirm('Are you sure you want to delete this flashcard?')) {
      return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/api/delete-flashcard/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ id: cardId })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        cardElement.style.transform = 'scale(0)';
        cardElement.style.opacity = '0';
        setTimeout(() => {
          cardElement.remove();
        }, 300);
        this.showToast('success', 'Flashcard deleted successfully');
      } else {
        this.showToast('error', data.error || 'Failed to delete flashcard');
      }
    })
    .catch(error => {
      this.showToast('error', 'Network error occurred');
    });
  }

  initStudyMode() {
    const studyCards = document.querySelectorAll('.study-card');
    let currentCardIndex = 0;

    const showCard = (index) => {
      studyCards.forEach((card, i) => {
        card.style.display = i === index ? 'flex' : 'none';
      });
    };

    const nextCard = () => {
      currentCardIndex = (currentCardIndex + 1) % studyCards.length;
      showCard(currentCardIndex);
    };

    const prevCard = () => {
      currentCardIndex = (currentCardIndex - 1 + studyCards.length) % studyCards.length;
      showCard(currentCardIndex);
    };

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (studyCards.length === 0) return;
      
      switch(e.key) {
        case 'ArrowRight':
        case ' ':
          e.preventDefault();
          nextCard();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          prevCard();
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          studyCards[currentCardIndex].classList.toggle('flipped');
          break;
      }
    });

    if (studyCards.length > 0) {
      showCard(0);
    }
  }

  // Initialize vocabulary-specific features
  initVocabularyFeatures() {
    this.initFlashcardInteractions();
    this.initStudyMode();
  }
}

// ============================================
// GLOBAL INITIALIZATION
// ============================================

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.vocabularyApp = new VocabularyApp();
    window.vocabularyApp.initVocabularyFeatures();
  });
} else {
  window.vocabularyApp = new VocabularyApp();
  window.vocabularyApp.initVocabularyFeatures();
}

// Global utility functions for backward compatibility
window.showToast = (type, message, duration) => {
  if (window.vocabularyApp) {
    return window.vocabularyApp.showToast(type, message, duration);
  }
};

window.openModal = (modalId) => {
  if (window.vocabularyApp) {
    return window.vocabularyApp.openModal(modalId);
  }
};

window.closeModal = (modalId) => {
  if (window.vocabularyApp) {
    return window.vocabularyApp.closeModal(modalId);
  }
};

// Performance monitoring
window.addEventListener('load', () => {
  const loadTime = performance.now();
  console.log(`🚀 Page loaded in ${Math.round(loadTime)}ms`);
});

// Error handling
window.addEventListener('error', (e) => {
  console.error('Global error:', e.error);
  if (window.vocabularyApp) {
    window.vocabularyApp.showToast('error', 'An unexpected error occurred');
  }
});

// Service Worker registration (future enhancement)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // navigator.serviceWorker.register('/sw.js')
    //   .then(registration => console.log('SW registered:', registration))
    //   .catch(error => console.log('SW registration failed:', error));
  });
} 