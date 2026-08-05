// Shared modal behavior: open/close, backdrop click, Escape, focus trap,
// and focus restore. Supports stacked modals (item modal over person modal).

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface ModalController {
  open: (initialFocus?: HTMLElement) => void;
  close: () => void;
}

const stack: ModalController[] = [];

export function createModalController(
  backdrop: HTMLElement,
  modal: HTMLElement
): ModalController {
  let lastFocused: HTMLElement | null = null;

  function focusables(): HTMLElement[] {
    return Array.from(modal.querySelectorAll<HTMLElement>(FOCUSABLE));
  }

  function onKeydown(e: KeyboardEvent) {
    if (stack[stack.length - 1] !== controller) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
      return;
    }
    if (e.key !== 'Tab') return;
    const els = focusables();
    if (!els.length) return;
    const first = els[0];
    const last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function open(initialFocus?: HTMLElement) {
    lastFocused = document.activeElement as HTMLElement | null;
    stack.push(controller);
    backdrop.classList.add('open');
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKeydown);
    (initialFocus ?? focusables()[0])?.focus();
  }

  function close() {
    const idx = stack.indexOf(controller);
    if (idx !== -1) stack.splice(idx, 1);
    backdrop.classList.remove('open');
    backdrop.setAttribute('aria-hidden', 'true');
    if (!stack.length) document.body.style.overflow = '';
    document.removeEventListener('keydown', onKeydown);
    lastFocused?.focus();
    lastFocused = null;
  }

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) close();
  });

  const controller: ModalController = { open, close };
  return controller;
}
