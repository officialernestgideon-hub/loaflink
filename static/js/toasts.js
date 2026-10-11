/**
 * LoafLink — Toast system
 *
 * Auto-initializes on page load. Reads Django messages rendered by
 * the {% include 'partials/_toasts.html' %} template snippet.
 *
 * Usage in any template:
 *   {% include 'partials/_toasts.html' %}
 *
 * Then any Django message (from `messages.success(...)`, `messages.error(...)`,
 * etc.) renders as a slide-in toast that auto-dismisses.
 */

(function () {
  'use strict';

  const TOAST_DURATION = 4500;       // ms before auto-dismiss
  const ANIMATION_DURATION = 320;    // ms for slide in/out

  function createToast({ type, message }) {
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');

    const icons = {
      success: 'fa-check-circle',
      error: 'fa-circle-exclamation',
      warning: 'fa-triangle-exclamation',
      info: 'fa-circle-info',
    };
    const icon = icons[type] || icons.info;

    el.innerHTML = `
      <i class="fa-solid ${icon} toast__icon"></i>
      <div class="toast__body">${escapeHtml(message)}</div>
      <button class="toast__close" aria-label="Dismiss">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;

    const close = () => dismiss(el);
    el.querySelector('.toast__close').addEventListener('click', close);

    return el;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function mountContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-container';
      c.className = 'toast-container';
      document.body.appendChild(c);
    }
    return c;
  }

  function show(opts) {
    const container = mountContainer();
    const toast = createToast(opts);
    container.appendChild(toast);

    // Trigger enter animation
    requestAnimationFrame(() => {
      toast.classList.add('toast--visible');
    });

    // Auto-dismiss
    setTimeout(() => dismiss(toast), TOAST_DURATION);
  }

  function dismiss(toast) {
    if (!toast || toast.dataset.dismissed === 'true') return;
    toast.dataset.dismissed = 'true';
    toast.classList.remove('toast--visible');
    toast.classList.add('toast--leaving');
    setTimeout(() => toast.remove(), ANIMATION_DURATION);
  }

  // Expose globally for programmatic calls
  window.LoafToast = { show };

  // Auto-load Django messages from a hidden JSON payload
  document.addEventListener('DOMContentLoaded', () => {
    const payload = document.getElementById('django-toast-payload');
    if (!payload) return;

    try {
      const messages = JSON.parse(payload.textContent);
      messages.forEach((m, i) => {
        setTimeout(() => show(m), i * 150);
      });
    } catch (e) {
      console.warn('Toast payload parse error', e);
    }
  });
})();