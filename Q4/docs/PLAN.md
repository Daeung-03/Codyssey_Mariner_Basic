# Q4 반응형 포트폴리오 — 구현 계획 (PLAN)

순수 HTML/CSS/JavaScript만으로 반응형 포트폴리오 웹사이트를 구현한다.
외부 라이브러리는 금지이며, "이벤트 → 상태 변경 → DOM 렌더링" 흐름 이해를 최우선 목표로 한다.

---

## 1. 설계 원칙

- **최소 모듈 (Minimal Modules)**: 파일을 잘게 쪼개지 않고, 역할이 명확한 최소 단위로만 분리한다.
- **관심사 분리**: 구조(HTML) / 표현(CSS) / 동작(JS)을 파일 단위로 분리한다.
- **상태 중심**: 각 기능은 `상태(state) → 렌더(render)` 흐름을 따른다. DOM을 직접 여기저기서 바꾸지 않고, 상태 변경 후 렌더 함수가 화면을 갱신한다.
- **의존성 없음**: 프레임워크/빌드 도구 없이 브라우저가 바로 실행하는 정적 파일로 구성한다.

---

## 2. 아키텍처 (최소 모듈 구성)

과제 요구사항(`index.html`, `css/`, `js/`, `images/`)을 만족하면서 모듈을 최소화한 구성이다.

```
Q4/
├── index.html              ← 단일 페이지, 시맨틱 마크업 + 섹션 전체
├── css/
│   └── style.css           ← CSS 변수, 레이아웃, 반응형, 다크모드, 애니메이션
├── js/
│   ├── config.js           ← 설정값 (GitHub username, 스크롤 임계값, 정적 데이터)
│   └── main.js             ← 모든 인터랙션 + API 연동 (기능별 함수로 구획)
├── images/                 ← 프로필 이미지, 파비콘 등
├── README.md
└── docs/
    ├── PROBLEM.md
    └── PLAN.md
```

### 모듈을 이렇게 나눈 이유

| 파일 | 역할 | 왜 분리했나 |
|------|------|-------------|
| `index.html` | 문서 구조, 섹션, 폼 마크업 | 페이지가 하나뿐이라 단일 HTML로 충분 |
| `css/style.css` | 모든 스타일 | 규모가 작아 파일 분리보다 섹션 주석 구획이 관리에 유리 |
| `js/config.js` | 변경 가능한 설정/데이터 | 소스 코드와 "바꿀 값"을 분리 (username, 임계값 등) |
| `js/main.js` | 동작 로직 전체 | 기능별 함수로 나누되, 한 파일에서 초기화 흐름을 한눈에 보이게 |

> `main.js`는 하나의 파일이지만 내부를 **기능 단위 함수 블록**으로 구획한다.
> 각 함수는 `초기화(init) → 이벤트 바인딩 → 상태 → 렌더` 구조를 따른다.

---

## 3. HTML 구조 계획

시맨틱 태그로 섹션을 구성한다.

```
<header>
  <nav> (로고 + 메뉴 앵커 + 다크모드 토글 + 햄버거 버튼)
<main>
  <section id="hero">      인사말, CTA 버튼 2개
  <section id="about">     프로필 이미지 + 자기소개
  <section id="skills">    기술 스택 목록
  <section id="projects">  GitHub API 카드 (상태별 UI 컨테이너)
  <section id="contact">   문의 폼 (name/email/message + 에러 영역)
<footer>                   저작권 + 소셜 링크
<button id="scroll-top">   스크롤 탑 버튼
```

체크 포인트:
- 모든 `<img>`에 의미 있는 `alt`
- 폼 `<label for>` ↔ input `id` 매칭
- 네비 앵커 링크(`#hero`, `#about`...)로 섹션 이동
- 인라인 스타일/`onclick` 금지

---

## 4. CSS 계획

- `:root`에 색상/폰트/간격 변수 정의
- `[data-theme="dark"]`에 다크모드 변수 오버라이드
- **모바일 퍼스트** 작성 후 `@media (min-width: 768px)`, `(min-width: 1024px)`로 확장
- 네비게이션: **Flexbox** (로고 좌 / 메뉴 우)
- Projects 카드: **Grid** `repeat(auto-fit, minmax(...))`
- 버튼/카드에 `transition` + `hover` 효과, 카드 `box-shadow`
- 모바일에서 메뉴 숨김 + 햄버거 노출, `.active` 클래스로 표시 제어

---

## 5. JavaScript 기능 계획 (상태 → 렌더 흐름)

`main.js`는 `DOMContentLoaded` 시점에 각 기능의 `init`을 호출한다.

| 기능 | 이벤트 | 상태 | 렌더 |
|------|--------|------|------|
| 햄버거 메뉴 | `click` | isMenuOpen | 메뉴 `.active` 토글 |
| 부드러운 스크롤 | 앵커 `click` | — | `scrollInto.View({behavior:'smooth'})` |
| 스크롤 탑 버튼 | `scroll` | scrollY > 300 | 버튼 표시/숨김 + 클릭 시 top |
| 네비 스타일 변경 | `scroll` | scrollY > 60 | nav `.scrolled` 클래스 |
| 다크 모드 | 토글 `click` | theme(localStorage) | `data-theme` 속성 변경 |
| 스크롤 애니메이션 | IntersectionObserver | isVisible (th 0.2) | `.visible` 클래스 부여 |
| Contact 폼 | `submit`, `input` | 유효성 상태 | 에러 메시지 + 성공 메시지 |
| GitHub Projects | `init` / 재시도 `click` | loading/success/error/empty | Projects 섹션 렌더 분기 |

### 상태 → 렌더 필수 흐름 (요구 3개 이상 충족)

1. 다크 모드 토글 → theme 상태 변경 → 전체 스타일 변경
2. API 호출 → loading/success/error/empty 상태 → Projects 렌더 분기
3. 폼 입력/제출 → 유효성 상태 → 에러/성공 메시지 표시

### GitHub API 연동 계획

- 엔드포인트: `https://api.github.com/users/{username}/repos`
- `fetch` + `async/await` + `try/catch`
- 4가지 상태 UI: 로딩 스피너 / 카드 리스트 / 에러+재시도 / 빈 상태
- 응답을 `map`으로 카드 HTML(템플릿 리터럴)로 변환, 구조분해로 필드 추출
- 403(레이트 리밋) 발생 시 에러 상태 UI 표시

---

## 6. 구현 순서 (권장 단계)

1. `index.html` 시맨틱 골격 + 섹션 배치
2. `css/style.css` 변수/레이아웃/반응형 기본
3. 네비게이션 + 햄버거 + 부드러운 스크롤
4. 다크 모드 (localStorage 영속)
5. 스크롤 탑 / 네비 스타일 / 스크롤 애니메이션
6. Contact 폼 유효성 검사
7. GitHub API 연동 + 상태별 UI
8. 반응형 QA (모바일/태블릿/데스크톱) + 다크모드 QA
9. GitHub Pages 배포 + README 스크린샷/URL 정리

---

## 7. 보너스 (선택, 여력 시)

- 언어별 프로젝트 필터링 (`filter`)
- Hero 타이핑 효과
- `prefers-color-scheme` 시스템 다크모드 감지
- Formspree/EmailJS 실제 폼 전송

---

## 8. 배포 & 제출

- GitHub Pages로 배포, 배포 URL에서 전 기능 동작 확인
- README에 프로젝트 설명 / 사용 기술 / 배포 URL / 스크린샷(데스크톱·모바일·다크모드) 포함
- 스크롤 임계값(300px), 네비 변경 임계값(60px), IO threshold(0.2)는 README에 명시
