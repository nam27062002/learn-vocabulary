/**
 * notifications.js — Unified notification system
 *
 * Public API (window.Notify):
 *   Notify.success(message, opts?)   — green toast
 *   Notify.error(message, opts?)     — red toast
 *   Notify.warning(message, opts?)   — yellow toast
 *   Notify.info(message, opts?)      — blue toast
 *   Notify.toast(message, type, opts?) — generic toast
 *   Notify.alert(config)             — Promise<void>    single-button modal
 *   Notify.confirm(config)           — Promise<boolean> two-button modal
 *   Notify.prompt(config)            — Promise<string|null> input modal
 *
 * Toast config opts: { duration: number (ms) }
 *
 * Modal config:
 *   alert:   { type?, title?, message?, html?, confirmText? }
 *   confirm: { type?, title?, message?, html?, confirmText?, cancelText? }
 *   prompt:  { title?, label?, placeholder?, value?, confirmText?, cancelText? }
 *
 * Use `message` for plain text (auto-escaped).
 * Use `html` for rich HTML content (caller's responsibility to sanitize).
 */

const Notify = (() => {
  'use strict';

  // ─────────────────────────────────────────────────────────────
  // Helpers
  // ─────────────────────────────────────────────────────────────

  function _escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  const _ICONS = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };

  // ─────────────────────────────────────────────────────────────
  // ToastManager — transient, stacked, auto-dismiss notifications
  // ─────────────────────────────────────────────────────────────

  class ToastManager {
    constructor() {
      this._container = null;
    }

    /** Lazily create/reuse the fixed container element. */
    _container_el() {
      if (!this._container) {
        this._container = document.createElement('div');
        this._container.id = 'notify-toast-container';
        document.body.appendChild(this._container);
      }
      return this._container;
    }

    /**
     * @param {string} message
     * @param {'success'|'error'|'warning'|'info'} type
     * @param {number} [duration=3500]
     */
    show(message, type = 'info', duration = 3500) {
      if (!document.body) return;

      const icon = _ICONS[type] ?? _ICONS.info;
      const toast = document.createElement('div');
      toast.className = `notify-toast notify-toast--${type}`;
      toast.style.setProperty('--toast-duration', `${duration}ms`);

      // Build structure; use textContent for user message to avoid XSS
      toast.innerHTML = `
        <span class="notify-toast__icon" aria-hidden="true">${icon}</span>
        <span class="notify-toast__message"></span>
        <button class="notify-toast__close" aria-label="Dismiss notification">×</button>
        <span class="notify-toast__progress" aria-hidden="true"></span>
      `;
      toast.querySelector('.notify-toast__message').textContent = message;

      const dismiss = () => {
        clearTimeout(timerId);
        toast.classList.remove('notify-toast--visible');
        setTimeout(() => toast.remove(), 300);
      };

      toast.querySelector('.notify-toast__close').addEventListener('click', dismiss);
      this._container_el().appendChild(toast);

      // Trigger CSS transition on next frame
      requestAnimationFrame(() => toast.classList.add('notify-toast--visible'));

      const timerId = setTimeout(dismiss, duration);
    }
  }

  // ─────────────────────────────────────────────────────────────
  // ModalManager — blocking overlay dialogs (alert/confirm/prompt)
  // ─────────────────────────────────────────────────────────────

  class ModalManager {
    constructor() {
      this._overlay = null;
      this._escHandler = null;
    }

    /** Lazily create/reuse the overlay element. */
    _overlay_el() {
      if (!this._overlay) {
        this._overlay = document.createElement('div');
        this._overlay.id = 'notify-overlay';
        document.body.appendChild(this._overlay);
      }
      return this._overlay;
    }

    /** Mount a dialog into the overlay and show it. */
    _open(dialog, onDismiss) {
      const overlay = this._overlay_el();
      overlay.innerHTML = '';
      overlay.appendChild(dialog);
      overlay.classList.add('notify-overlay--active');
      document.body.classList.add('notify-scroll-lock');

      // Animate dialog in after a frame
      requestAnimationFrame(() => dialog.classList.add('notify-modal--visible'));

      // Backdrop click closes
      overlay.onclick = (e) => { if (e.target === overlay) onDismiss(); };

      // ESC key closes
      this._escHandler = (e) => { if (e.key === 'Escape') onDismiss(); };
      document.addEventListener('keydown', this._escHandler);
    }

    /** Tear down the active modal. */
    _close() {
      const overlay = this._overlay_el();
      overlay.classList.remove('notify-overlay--active');
      document.body.classList.remove('notify-scroll-lock');
      if (this._escHandler) {
        document.removeEventListener('keydown', this._escHandler);
        this._escHandler = null;
      }
      overlay.onclick = null;
    }

    /**
     * Build a base dialog shell.
     * @param {'success'|'error'|'warning'|'info'|'prompt'} type
     * @param {string} title
     * @param {string} bodyContent — raw HTML for the body (pre-sanitized by callers)
     */
    _buildDialog(type, title, bodyContent) {
      const dialog = document.createElement('div');
      dialog.className = `notify-modal notify-modal--${type}`;
      dialog.setAttribute('role', 'dialog');
      dialog.setAttribute('aria-modal', 'true');

      const icon = _ICONS[type];
      const iconHtml = icon
        ? `<div class="notify-modal__icon notify-modal__icon--${type}" aria-hidden="true">${icon}</div>`
        : '';
      const titleHtml = title
        ? `<h2 class="notify-modal__title" id="notify-modal-title"></h2>`
        : '';

      if (title) dialog.setAttribute('aria-labelledby', 'notify-modal-title');

      dialog.innerHTML = `
        ${iconHtml}
        ${titleHtml}
        <div class="notify-modal__body">${bodyContent}</div>
        <div class="notify-modal__footer"></div>
      `;

      if (title) {
        dialog.querySelector('.notify-modal__title').textContent = title;
      }

      return dialog;
    }

    /** Append a button to a footer element. */
    _addBtn(footer, text, variant, handler) {
      const btn = document.createElement('button');
      btn.className = `notify-modal__btn notify-modal__btn--${variant}`;
      btn.textContent = text;
      btn.addEventListener('click', handler);
      footer.appendChild(btn);
      return btn;
    }

    // ── Public modal methods ──────────────────────────────────

    /**
     * Single-action modal (informational).
     * @param {{type?,title?,message?,html?,confirmText?}} config
     * @returns {Promise<void>}
     */
    alert({ type = 'info', title = '', message = '', html = '', confirmText = 'OK' } = {}) {
      return new Promise((resolve) => {
        const bodyContent = html || (message ? `<p class="notify-modal__text">${_escHtml(message)}</p>` : '');
        const dialog = this._buildDialog(type, title, bodyContent);

        const done = () => { this._close(); resolve(); };
        this._addBtn(dialog.querySelector('.notify-modal__footer'), confirmText, 'primary', done);
        this._open(dialog, done);

        requestAnimationFrame(() => dialog.querySelector('.notify-modal__btn')?.focus());
      });
    }

    /**
     * Two-action confirmation modal.
     * @param {{type?,title?,message?,html?,confirmText?,cancelText?}} config
     * @returns {Promise<boolean>}
     */
    confirm({
      type = 'warning',
      title = '',
      message = '',
      html = '',
      confirmText = 'OK',
      cancelText = 'Cancel',
    } = {}) {
      return new Promise((resolve) => {
        const bodyContent = html || (message ? `<p class="notify-modal__text">${_escHtml(message)}</p>` : '');
        const dialog = this._buildDialog(type, title, bodyContent);
        const footer = dialog.querySelector('.notify-modal__footer');

        const cancel  = () => { this._close(); resolve(false); };
        const confirm = () => { this._close(); resolve(true); };

        this._addBtn(footer, cancelText,  'secondary', cancel);
        this._addBtn(footer, confirmText, 'primary',   confirm);
        this._open(dialog, cancel);

        // Focus the confirm button by default
        requestAnimationFrame(() => {
          dialog.querySelectorAll('.notify-modal__btn')[1]?.focus();
        });
      });
    }

    /**
     * Text-input prompt modal.
     * @param {{title?,label?,placeholder?,value?,confirmText?,cancelText?}} config
     * @returns {Promise<string|null>} Trimmed input value, or null if cancelled.
     */
    prompt({
      title = '',
      label = '',
      placeholder = '',
      value = '',
      confirmText = 'OK',
      cancelText = 'Cancel',
    } = {}) {
      return new Promise((resolve) => {
        const dialog = this._buildDialog('prompt', title, '');
        const body   = dialog.querySelector('.notify-modal__body');
        const footer = dialog.querySelector('.notify-modal__footer');

        if (label) {
          const lbl = document.createElement('label');
          lbl.className   = 'notify-modal__label';
          lbl.textContent = label;
          body.appendChild(lbl);
        }

        const input = document.createElement('input');
        input.type        = 'text';
        input.className   = 'notify-modal__input';
        input.placeholder = placeholder;
        input.value       = value;
        body.appendChild(input);

        const dismiss = (val) => { this._close(); resolve(val); };

        const confirmBtn = this._addBtn(footer, confirmText, 'primary', () => {
          const val = input.value.trim();
          if (val) dismiss(val);
        });
        this._addBtn(footer, cancelText, 'secondary', () => dismiss(null));

        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter')  confirmBtn.click();
          if (e.key === 'Escape') dismiss(null);
        });

        this._open(dialog, () => dismiss(null));
        requestAnimationFrame(() => input.focus());
      });
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Instantiate managers (singletons)
  // ─────────────────────────────────────────────────────────────

  const _toast = new ToastManager();
  const _modal = new ModalManager();

  // ─────────────────────────────────────────────────────────────
  // Public Facade
  // ─────────────────────────────────────────────────────────────

  return {
    /** Show a success toast. */
    success: (msg, opts = {}) => _toast.show(msg, 'success', opts.duration),

    /** Show an error toast. */
    error: (msg, opts = {}) => _toast.show(msg, 'error', opts.duration),

    /** Show a warning toast. */
    warning: (msg, opts = {}) => _toast.show(msg, 'warning', opts.duration),

    /** Show an info toast. */
    info: (msg, opts = {}) => _toast.show(msg, 'info', opts.duration),

    /** Show a toast with an explicit type. */
    toast: (msg, type = 'info', opts = {}) => _toast.show(msg, type, opts.duration),

    /** Show an informational modal. Returns Promise<void>. */
    alert: (config) => _modal.alert(config),

    /** Show a confirm modal. Returns Promise<boolean>. */
    confirm: (config) => _modal.confirm(config),

    /** Show a text-input prompt modal. Returns Promise<string|null>. */
    prompt: (config) => _modal.prompt(config),
  };
})();

window.Notify = Notify;
