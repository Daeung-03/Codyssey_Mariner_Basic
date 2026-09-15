const setMenuState = (menu, button, isOpen) => {
  menu.classList.toggle('active', isOpen);
  button.setAttribute('aria-expanded', String(isOpen));
  button.setAttribute('aria-label', isOpen ? '메뉴 닫기' : '메뉴 열기');
};

const initializeNavigation = () => {
  const menu = document.querySelector('#primary-navigation');
  const menuButton = document.querySelector('#menu-toggle');

  if (!menu || !menuButton) {
    return;
  }

  menuButton.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    setMenuState(menu, menuButton, !isOpen);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      setMenuState(menu, menuButton, false);
    }
  });

  const desktopMediaQuery = window.matchMedia('(min-width: 768px)');
  desktopMediaQuery.addEventListener('change', ({ matches }) => {
    if (matches) {
      setMenuState(menu, menuButton, false);
    }
  });

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const internalLinks = document.querySelectorAll('a[href^="#"]');

  internalLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const targetSelector = link.getAttribute('href');
      const target = document.querySelector(targetSelector);

      if (!target) {
        return;
      }

      event.preventDefault();
      setMenuState(menu, menuButton, false);
      target.scrollIntoView({
        behavior: prefersReducedMotion.matches ? 'auto' : 'smooth',
        block: 'start',
      });
      window.history.pushState(null, '', targetSelector);
    });
  });
};

const initializeApp = () => {
  initializeNavigation();
  console.log('Q4 portfolio initialized.', CONFIG);
};

initializeApp();
