const THEME_STORAGE_KEY = 'portfolio-theme';

const getStoredTheme = () => {
  try {
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return storedTheme === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
};

const storeTheme = (theme) => {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // 저장소 접근이 제한되어도 현재 페이지의 테마 전환은 유지한다.
  }
};

const renderTheme = (theme, button) => {
  const isDark = theme === 'dark';

  document.documentElement.dataset.theme = theme;
  button.textContent = isDark ? 'Light' : 'Dark';
  button.setAttribute('aria-pressed', String(isDark));
  button.setAttribute('aria-label', isDark ? '라이트 모드로 전환' : '다크 모드로 전환');
};

const initializeTheme = () => {
  const themeButton = document.querySelector('#theme-toggle');

  if (!themeButton) {
    return;
  }

  let currentTheme = getStoredTheme();
  renderTheme(currentTheme, themeButton);

  themeButton.addEventListener('click', () => {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    storeTheme(currentTheme);
    renderTheme(currentTheme, themeButton);
  });
};

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
  initializeTheme();
  initializeNavigation();
  console.log('Q4 portfolio initialized.', CONFIG);
};

initializeApp();
