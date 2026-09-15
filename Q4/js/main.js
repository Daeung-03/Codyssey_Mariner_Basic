const THEME_STORAGE_KEY = 'portfolio-theme';

const getPreferredScrollBehavior = () => (
  window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
);

const getSystemTheme = () => (
  window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
);

const getStoredTheme = () => {
  try {
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);

    if (storedTheme === 'light' || storedTheme === 'dark') {
      return storedTheme;
    }
  } catch {
    // 저장소 접근이 제한되면 시스템 테마를 초기값으로 사용한다.
  }

  return getSystemTheme();
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

const closeMenu = (menu, button) => {
  menu.classList.remove('active');
  button.setAttribute('aria-expanded', 'false');
  button.setAttribute('aria-label', '메뉴 열기');
};

const focusSection = (section) => {
  section.setAttribute('tabindex', '-1');
  section.focus({ preventScroll: true });
  section.addEventListener('blur', () => {
    section.removeAttribute('tabindex');
  }, { once: true });
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
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';

    if (event.key === 'Escape' && isOpen) {
      closeMenu(menu, menuButton);
      menuButton.focus();
    }
  });

  const desktopMediaQuery = window.matchMedia('(min-width: 768px)');
  desktopMediaQuery.addEventListener('change', ({ matches }) => {
    if (matches) {
      closeMenu(menu, menuButton);
    }
  });

  const internalLinks = document.querySelectorAll('a[href^="#"]');

  internalLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const targetSelector = link.getAttribute('href');
      const target = document.querySelector(targetSelector);

      if (!target) {
        return;
      }

      event.preventDefault();
      closeMenu(menu, menuButton);
      target.scrollIntoView({
        behavior: getPreferredScrollBehavior(),
        block: 'start',
      });
      focusSection(target);
      window.history.pushState(null, '', targetSelector);
    });
  });
};

const initializeScrollUI = () => {
  const header = document.querySelector('.site-header');
  const scrollTopButton = document.querySelector('#scroll-top');

  if (!header || !scrollTopButton) {
    return;
  }

  const renderScrollUI = () => {
    const showScrollTop = window.scrollY >= CONFIG.scrollTopThreshold;
    const highlightHeader = window.scrollY >= CONFIG.navScrollThreshold;

    scrollTopButton.hidden = !showScrollTop;
    header.classList.toggle('scrolled', highlightHeader);
  };

  window.addEventListener('scroll', renderScrollUI, { passive: true });
  scrollTopButton.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: getPreferredScrollBehavior(),
    });
  });

  renderScrollUI();
};

const initializeScrollAnimations = () => {
  const animatedSections = document.querySelectorAll('main section');

  if (!('IntersectionObserver' in window)) {
    animatedSections.forEach((section) => section.classList.add('visible'));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(({ isIntersecting, target }) => {
      if (!isIntersecting) {
        return;
      }

      target.classList.add('visible');
      observer.unobserve(target);
    });
  }, {
    threshold: CONFIG.observerThreshold,
  });

  animatedSections.forEach((section) => {
    section.classList.add('reveal');
    observer.observe(section);
  });
};

const REQUIRED_FIELD_MESSAGES = Object.freeze({
  name: '이름을 입력해 주세요.',
  email: '이메일을 입력해 주세요.',
  message: '메시지를 입력해 주세요.',
});

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const getContactFieldError = ({ name, type, value }) => {
  const normalizedValue = value.trim();

  if (!normalizedValue) {
    return REQUIRED_FIELD_MESSAGES[name] ?? '필수 항목을 입력해 주세요.';
  }

  if (type === 'email' && !EMAIL_PATTERN.test(normalizedValue)) {
    return '올바른 이메일 형식을 입력해 주세요.';
  }

  return '';
};

const renderContactField = ({ field, errorElement }, errorMessage) => {
  const hasError = Boolean(errorMessage);

  field.classList.toggle('invalid', hasError);
  field.setAttribute('aria-invalid', String(hasError));
  errorElement.textContent = errorMessage;
};

const initializeContactForm = () => {
  const form = document.querySelector('#contact-form');
  const formStatus = document.querySelector('#form-status');

  if (!form || !formStatus) {
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  const endpoint = form.getAttribute('action');

  if (!submitButton || !endpoint) {
    return;
  }

  const controls = [...form.querySelectorAll('input, textarea')]
    .map((field) => ({
      field,
      errorElement: document.querySelector(`#${field.id}-error`),
    }))
    .filter(({ errorElement }) => errorElement);

  const validationState = Object.fromEntries(
    controls.map(({ field }) => [field.name, '']),
  );
  const defaultSubmitLabel = submitButton.textContent;
  let isSubmitting = false;

  const validateControl = (control) => {
    const errorMessage = getContactFieldError(control.field);
    validationState[control.field.name] = errorMessage;
    renderContactField(control, errorMessage);
    return !errorMessage;
  };

  const clearFormStatus = () => {
    if (isSubmitting) {
      return;
    }

    formStatus.textContent = '';
    formStatus.dataset.state = '';
  };

  const setSubmitting = (submitting) => {
    isSubmitting = submitting;
    form.setAttribute('aria-busy', String(submitting));
    submitButton.disabled = submitting;
    submitButton.textContent = submitting ? '전송 중...' : defaultSubmitLabel;
  };

  controls.forEach((control) => {
    control.field.addEventListener('input', () => {
      validateControl(control);
      clearFormStatus();
    });
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const isValid = controls.map(validateControl).every(Boolean);

    if (!isValid) {
      formStatus.textContent = '입력 내용을 다시 확인해 주세요.';
      formStatus.dataset.state = 'error';
      controls.find(({ field }) => field.getAttribute('aria-invalid') === 'true')?.field.focus();
      return;
    }

    const formData = new FormData(form);
    setSubmitting(true);
    formStatus.textContent = '메시지를 전송하는 중입니다...';
    formStatus.dataset.state = 'sending';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('form-submit-failed');
      }

      formStatus.textContent = '메시지가 성공적으로 전송되었습니다.';
      formStatus.dataset.state = 'success';
      form.reset();

      controls.forEach((control) => {
        validationState[control.field.name] = '';
        renderContactField(control, '');
      });
    } catch {
      formStatus.textContent = '메시지를 전송하지 못했습니다. 잠시 후 다시 시도해 주세요.';
      formStatus.dataset.state = 'error';
    } finally {
      setSubmitting(false);
    }
  });
};

const PROJECT_STATUS = Object.freeze({
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
  EMPTY: 'empty',
});

const HTML_ESCAPE_CHARACTERS = Object.freeze({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#039;',
});

const escapeHTML = (value) => String(value).replace(
  /[&<>"']/g,
  (character) => HTML_ESCAPE_CHARACTERS[character],
);

const getSafeGitHubUrl = (value) => {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'github.com' ? url.href : '';
  } catch {
    return '';
  }
};

const renderProjectCard = ({
  name,
  description,
  html_url: repositoryUrl,
  language,
  stargazers_count: stars,
  forks_count: forks,
}) => {
  const safeRepositoryUrl = getSafeGitHubUrl(repositoryUrl);
  const repositoryLink = safeRepositoryUrl
    ? `<a href="${escapeHTML(safeRepositoryUrl)}" target="_blank" rel="noopener noreferrer">
        GitHub에서 보기
      </a>`
    : '<span class="project-card__unavailable">저장소 링크 없음</span>';

  return `
    <article class="project-card">
      <h3>${escapeHTML(name)}</h3>
      <p class="project-card__description">
        ${escapeHTML(description || '저장소 설명이 없습니다.')}
      </p>
      <ul class="project-card__meta" aria-label="저장소 정보">
        <li>${escapeHTML(language || '기타')}</li>
        <li>Stars ${escapeHTML(stars)}</li>
        <li>Forks ${escapeHTML(forks)}</li>
      </ul>
      ${repositoryLink}
    </article>
  `;
};

const ALL_LANGUAGES = 'all';

const getProjectLanguage = ({ language }) => language || '기타';

const renderProjectFilters = (container, state) => {
  if (state.status !== PROJECT_STATUS.SUCCESS) {
    container.hidden = true;
    container.innerHTML = '';
    return;
  }

  const languages = [...new Set(state.projects.map(getProjectLanguage))]
    .sort((first, second) => first.localeCompare(second));
  const filterOptions = [ALL_LANGUAGES, ...languages];

  container.hidden = false;
  container.innerHTML = filterOptions.map((language) => {
    const isSelected = state.selectedLanguage === language;
    const label = language === ALL_LANGUAGES ? '전체' : language;

    return `
      <button
        type="button"
        data-language="${encodeURIComponent(language)}"
        aria-pressed="${String(isSelected)}"
      >
        ${escapeHTML(label)}
      </button>
    `;
  }).join('');
};

const renderProjects = (container, state) => {
  if (state.status === PROJECT_STATUS.LOADING) {
    container.innerHTML = `
      <div class="projects-status" role="status">
        <span class="projects-spinner" aria-hidden="true"></span>
        <p>프로젝트를 불러오는 중...</p>
      </div>
    `;
    return;
  }

  if (state.status === PROJECT_STATUS.ERROR) {
    container.innerHTML = `
      <div class="projects-status projects-status--error" role="alert">
        <p>${escapeHTML(state.errorMessage)}</p>
        <button type="button" data-action="retry-projects">다시 시도</button>
      </div>
    `;
    return;
  }

  if (state.status === PROJECT_STATUS.EMPTY) {
    container.innerHTML = `
      <div class="projects-status" role="status">
        <p>표시할 프로젝트가 없습니다.</p>
      </div>
    `;
    return;
  }

  const visibleProjects = state.selectedLanguage === ALL_LANGUAGES
    ? state.projects
    : state.projects.filter(
      (project) => getProjectLanguage(project) === state.selectedLanguage,
    );

  if (visibleProjects.length === 0) {
    container.innerHTML = `
      <div class="projects-status" role="status">
        <p>선택한 언어의 프로젝트가 없습니다.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = visibleProjects.map(renderProjectCard).join('');
};

const initializeProjects = () => {
  const projectsContainer = document.querySelector('#projects-content');
  const filtersContainer = document.querySelector('#project-filters');

  if (!projectsContainer || !filtersContainer) {
    return;
  }

  const projectsState = {
    status: PROJECT_STATUS.LOADING,
    projects: [],
    errorMessage: '',
    selectedLanguage: ALL_LANGUAGES,
  };

  const renderProjectUI = () => {
    renderProjectFilters(filtersContainer, projectsState);
    renderProjects(projectsContainer, projectsState);
  };

  const loadProjects = async () => {
    projectsState.status = PROJECT_STATUS.LOADING;
    projectsState.errorMessage = '';
    projectsState.selectedLanguage = ALL_LANGUAGES;
    renderProjectUI();

    try {
      const username = CONFIG.githubUsername.trim();

      if (!username) {
        throw new Error('missing-username');
      }

      const endpoint = `https://api.github.com/users/${encodeURIComponent(username)}/repos?sort=updated&per_page=12`;
      const response = await fetch(endpoint);

      if (!response.ok) {
        throw new Error(response.status === 403 ? 'rate-limit' : 'request-failed');
      }

      const repositories = await response.json();

      if (!Array.isArray(repositories)) {
        throw new Error('invalid-response');
      }

      projectsState.projects = repositories.filter(({ archived }) => !archived);
      projectsState.status = projectsState.projects.length > 0
        ? PROJECT_STATUS.SUCCESS
        : PROJECT_STATUS.EMPTY;
    } catch (error) {
      projectsState.status = PROJECT_STATUS.ERROR;
      projectsState.projects = [];
      projectsState.errorMessage = error.message === 'rate-limit'
        ? '프로젝트를 불러올 수 없습니다. GitHub API 요청 한도를 초과했습니다.'
        : '프로젝트를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.';
    }

    renderProjectUI();
  };

  projectsContainer.addEventListener('click', (event) => {
    const retryButton = event.target.closest('[data-action="retry-projects"]');

    if (retryButton) {
      loadProjects();
    }
  });

  filtersContainer.addEventListener('click', (event) => {
    const filterButton = event.target.closest('[data-language]');

    if (!filterButton) {
      return;
    }

    const selectedLanguage = decodeURIComponent(filterButton.dataset.language);
    const isAvailable = selectedLanguage === ALL_LANGUAGES
      || projectsState.projects.some(
        (project) => getProjectLanguage(project) === selectedLanguage,
      );

    if (!isAvailable) {
      return;
    }

    projectsState.selectedLanguage = selectedLanguage;
    renderProjectUI();
  });

  loadProjects();
};

const initializeTypingEffect = () => {
  const heroTitle = document.querySelector('#hero-title');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!heroTitle || prefersReducedMotion) {
    return;
  }

  const fullText = heroTitle.textContent.trim();
  let characterIndex = 0;

  heroTitle.textContent = '';
  heroTitle.setAttribute('aria-label', fullText);
  heroTitle.classList.add('typing');

  const typingTimer = window.setInterval(() => {
    characterIndex += 1;
    heroTitle.textContent = fullText.slice(0, characterIndex);

    if (characterIndex >= fullText.length) {
      window.clearInterval(typingTimer);
      heroTitle.classList.remove('typing');
    }
  }, 65);
};

const initializeApp = () => {
  initializeTheme();
  initializeNavigation();
  initializeScrollUI();
  initializeScrollAnimations();
  initializeContactForm();
  initializeProjects();
  initializeTypingEffect();
  console.log('Q4 portfolio initialized.', CONFIG);
};

initializeApp();
