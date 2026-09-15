# Vanilla JavaScript 반응형 포트폴리오

외부 UI 프레임워크 없이 HTML, CSS, JavaScript가 브라우저에서 어떻게 연결되는지 직접 확인하기 위해 만든 단일 페이지 포트폴리오다. 핵심 구현 기준은 화면의 완성도보다 **사용자 이벤트 → 상태 변경 → DOM 렌더링** 흐름을 코드로 설명할 수 있게 만드는 것이었다.

- 원본 요구사항: [`docs/PROBLEM.md`](docs/PROBLEM.md)
- 구현 계획: [`docs/PLAN.md`](docs/PLAN.md)
- GitHub 사용자 설정 및 임계값: [`js/config.js`](js/config.js)
- GitHub 저장소: <https://github.com/Daeung-03/Codyssey_Mariner_Basic>
- 배포 URL: GitHub Pages 설정 후 기재

---

## 실행 방법

```bash
cd Q4
python3 -m http.server 5500
```

브라우저에서 <http://localhost:5500>으로 접속한다. `file://`로 직접 열기보다 정적 서버를 사용하는 이유는 실제 배포 환경과 비슷하게 외부 CSS/JS, `fetch`, Formspree 요청을 확인하기 위해서다.

```text
Q4/
├── index.html              # 문서 구조와 접근성 마크업
├── css/style.css           # 디자인 토큰, 레이아웃, 반응형, 상태 스타일
├── js/config.js            # GitHub 사용자명과 스크롤 임계값
├── js/main.js              # 상태, 이벤트, DOM 렌더링, API 연동
├── images/                 # 로컬 이미지
├── docs/PROBLEM.md         # 원본 문제
├── docs/PLAN.md            # 단계별 구현 계획
└── README.md
```

파일을 분리한 기준은 **구조(HTML), 표현(CSS), 동작(JavaScript), 변경 가능한 설정(config)**이다. 페이지는 하나이므로 파일을 기능별로 과도하게 나누지 않고, 각 파일 내부를 기능 함수와 주석 구역으로 구분했다.

---

## PROBLEM.md 해석 → 구현

### 1. 시맨틱 HTML과 접근성

**문제 해석**

단순히 `div`로 화면을 나누는 것이 아니라 각 영역의 목적을 브라우저와 보조 기술이 이해할 수 있어야 한다. 섹션 이동 링크, 이미지 대체 텍스트, 폼 label 연결도 구조의 일부로 해석했다.

**구현**
- `header/nav/main/section/article/footer`로 페이지 랜드마크와 콘텐츠 단위를 구분했다: [`index.html:13-139`](index.html#L13-L139)
- Hero, About, Skills, Projects, Contact에 고유 `id`와 `aria-labelledby`를 연결했다: [`index.html:44-130`](index.html#L44-L130)
- 프로필 이미지에 의미 있는 `alt`, 폼에 `label for` ↔ control `id`, 오류 영역에 `aria-describedby`를 적용했다: [`index.html:55-72`](index.html#L55-L72), [`index.html:99-129`](index.html#L99-L129)
- 모바일 메뉴는 `aria-controls/aria-expanded`, 테마는 `aria-pressed`, 동적 결과는 `aria-live`와 `role="status/alert"`로 상태를 전달한다.

### 2. CSS 변수와 다크 모드

**문제 해석**

라이트/다크 스타일을 컴포넌트마다 다시 작성하지 않고, 의미 기반 색상 토큰을 교체하는 방식으로 구현해야 한다.

**구현**
- `:root`에 배경, 표면, 텍스트, 강조색, 간격, 반경, 그림자를 정의했다: [`style.css:4-43`](css/style.css#L4-L43)
- `[data-theme="dark"]`는 동일한 변수 이름의 값만 덮어쓴다: [`style.css:44-61`](css/style.css#L44-L61)
- `getSystemTheme/getStoredTheme`가 저장 테마를 우선하고, 저장값이 없으면 `prefers-color-scheme`을 초기값으로 사용한다: [`main.js:7-24`](js/main.js#L7-L24)
- `initializeTheme`의 click 이벤트가 `currentTheme`을 변경하고, `storeTheme`과 `renderTheme`을 호출한다: [`main.js:25-58`](js/main.js#L25-L58)

```text
테마 버튼 click
→ currentTheme: light ↔ dark
→ localStorage 저장
→ <html data-theme="..."> 갱신
→ CSS 변수 전체 교체
```

### 3. 모바일 퍼스트 반응형 레이아웃

**문제 해석**

가장 좁은 화면을 기본 규칙으로 만들고, 공간이 늘어나는 지점에서 필요한 속성만 확장한다. 브레이크포인트는 기기 이름보다 레이아웃이 바뀌어야 하는 너비로 사용했다.

**구현**
- 기본 CSS가 모바일 레이아웃이며 768px, 1024px에서 확장한다: [`style.css:649-710`](css/style.css#L649-L710)
- 네비게이션과 버튼 그룹처럼 **한 방향 정렬**이 중요한 영역에는 Flexbox를 사용했다: [`style.css:127-223`](css/style.css#L127-L223)
- Skills와 Projects처럼 **행과 열 및 자동 카드 배치**가 필요한 영역에는 Grid를 사용했다: [`style.css:355-394`](css/style.css#L355-L394)
- Projects는 `repeat(auto-fit, minmax(16rem, 1fr))`로 카드 수와 화면 폭에 따라 열 개수가 자동 조정된다: [`style.css:388-394`](css/style.css#L388-L394)
- 모바일 메뉴는 기본 숨김, `.active`일 때 표시하며 768px 이상에서는 상시 표시한다: [`style.css:720-816`](css/style.css#L720-L816)

### 4. 햄버거 메뉴와 부드러운 섹션 이동

**문제 해석**

HTML `onclick`이 아니라 JavaScript에서 DOM을 선택하고 이벤트를 연결해야 한다. 메뉴 열림 여부는 클래스와 ARIA 상태가 함께 바뀌어야 한다.

**구현**
- `setMenuState`가 `.active`와 `aria-expanded`를 함께 갱신하고, `closeMenu`는 명시적으로 `classList.remove`를 사용한다: [`main.js:59-70`](js/main.js#L59-L70)
- `initializeNavigation`이 click, keydown, media-query change 이벤트를 등록한다: [`main.js:79-130`](js/main.js#L79-L130)
- 내부 앵커 click에서 기본 점프를 `preventDefault()`로 막고 `scrollIntoView()`로 이동한다.
- 이동 후 섹션에 임시 `tabindex="-1"`을 주어 키보드 포커스를 옮기고, blur 시 제거한다: [`main.js:71-78`](js/main.js#L71-L78)
- Escape로 메뉴를 닫으면 햄버거 버튼으로 포커스를 돌려준다.

### 5. 스크롤 기반 UI와 애니메이션

**문제 해석**

스크롤 좌표 기반 UI와 요소의 화면 진입 감지는 역할이 다르다. 전자는 `scroll` 이벤트, 후자는 `IntersectionObserver`로 분리했다.

**구현**
- `initializeScrollUI`가 `scrollY`와 config 임계값을 비교해 Top 버튼의 `hidden`과 헤더 `.scrolled`를 갱신한다: [`main.js:131-157`](js/main.js#L131-L157)
- `initializeScrollAnimations`가 각 section을 관찰하고 20% 진입 시 `.visible`을 추가한 뒤 `unobserve()`한다: [`main.js:158-184`](js/main.js#L158-L184)
- `.reveal → .reveal.visible`에서 opacity와 transform을 전환한다: [`style.css:824-858`](css/style.css#L824-L858)
- `prefers-reduced-motion` 사용자는 부드러운 이동과 장식 애니메이션을 줄인다.

| 동작 | 기준값 | 설정 위치 |
|---|---:|---|
| Top 버튼 표시 | `scrollY >= 300` | [`config.js:3`](js/config.js#L3) |
| 헤더 배경/그림자 변경 | `scrollY >= 60` | [`config.js:4`](js/config.js#L4) |
| 섹션 등장 Observer | `threshold: 0.2` | [`config.js:5`](js/config.js#L5) |

### 6. Contact 검증과 실제 전송

**문제 해석**

브라우저 기본 경고에만 의존하지 않고 필드 근처에 오류를 표시해야 한다. 실제 전송은 유효성 통과 후에만 수행하고, 서버 응답이 성공해야 성공 UI를 보여야 한다.

**구현**
- `getContactFieldError`가 공백 제거 후 필수값과 이메일 정규식을 검사한다: [`main.js:185-206`](js/main.js#L185-L206)
- `renderContactField`가 `.invalid`, `aria-invalid`, 오류 `textContent`를 동기화한다: [`main.js:207-214`](js/main.js#L207-L214)
- `initializeContactForm` 내부 `validationState`가 필드별 오류 문자열을 보관한다: [`main.js:215-323`](js/main.js#L215-L323)
- `input` 이벤트는 해당 필드를 즉시 다시 검사하고, `submit`은 `preventDefault()` 후 전체 필드를 검사한다.
- 유효하면 `FormData`를 Formspree에 POST한다. 전송 중 `aria-busy`와 버튼 disabled로 중복 전송을 막고, `response.ok`일 때만 reset한다.
- Formspree endpoint는 폼의 `action`에 선언했다: [`index.html:99-129`](index.html#L99-L129)
- 오류/성공 상태 색상과 필드 테두리는 CSS 변수로 표현한다: [`style.css:541-616`](css/style.css#L541-L616)

> Formspree endpoint는 공개 폼 주소이며 비밀 토큰이 아니다. 실제 수신 여부는 Formspree 폼 활성화와 수신 이메일 인증 후 확인해야 한다.

### 7. GitHub API와 상태별 렌더링

**문제 해석**

API 성공 결과만 그리는 것이 아니라 요청 전·성공·실패·빈 배열을 서로 다른 상태로 표현해야 한다. 재시도도 같은 로딩 함수로 돌아가야 한다.

**구현**
- `PROJECT_STATUS`가 `loading/success/error/empty` 상태 이름을 고정한다: [`main.js:324-330`](js/main.js#L324-L330)
- `renderProjects`가 상태에 따라 스피너, 카드, 오류+재시도, 빈 메시지를 렌더한다: [`main.js:416-463`](js/main.js#L416-L463)
- `initializeProjects` 안의 `projectsState`가 API 상태, 원본 프로젝트, 오류 문구, 선택 언어를 함께 보관한다: [`main.js:464-556`](js/main.js#L464-L556)
- `loadProjects`는 `fetch + async/await + try/catch`를 사용한다. HTTP 403은 레이트 리밋 메시지로, 네트워크·형식 오류는 일반 오류로 처리한다.
- 외부 문자열은 `escapeHTML`로 이스케이프하고, 저장소 링크는 HTTPS `github.com`인지 검증한다: [`main.js:331-383`](js/main.js#L331-L383)
- GitHub 사용자명은 config에서 바꿀 수 있다: [`config.js:2`](js/config.js#L2)

```text
loadProjects()
→ status = loading → renderProjectUI()
→ fetch
   ├─ 성공 + 데이터 있음 → success
   ├─ 성공 + 빈 배열     → empty
   └─ HTTP/네트워크 오류 → error
→ renderProjectUI()
```

### 8. ES6+와 배열 메서드

**문제 해석**

문법을 사용했다는 사실보다, 데이터 변환 단계에서 각 배열 메서드의 역할이 분명해야 한다.

**구현**
1. API 배열에서 archived 저장소를 `filter()`로 제거한다: [`main.js:464-556`](js/main.js#L464-L556)
2. 언어 목록은 `map()`과 `Set`으로 중복을 제거한다: [`main.js:388-415`](js/main.js#L388-L415)
3. 선택 언어가 있으면 다시 `filter()`하여 화면에 표시할 배열을 만든다: [`main.js:416-463`](js/main.js#L416-L463)
4. `map(renderProjectCard).join('')`으로 카드 HTML 문자열을 만든다.
5. 카드 함수 인자에서 구조분해 할당과 속성 이름 변경을 사용한다: [`main.js:353-383`](js/main.js#L353-L383)

### 9. 보너스 요구사항

| 보너스 | 문제 해석 및 구현 | 코드 |
|---|---|---|
| 언어별 프로젝트 필터 | `selectedLanguage` 상태 변경 후 `filter()` 결과 재렌더, 버튼 `aria-pressed` 동기화 | [`main.js:384-556`](js/main.js#L384-L556), [`index.html:84-98`](index.html#L84-L98), [`style.css:406-442`](css/style.css#L406-L442) |
| Hero 타이핑 | 65ms마다 문자열 slice 범위를 늘리고 완료 시 timer/커서 제거, reduced-motion이면 생략 | [`main.js:557-582`](js/main.js#L557-L582), [`style.css:306-326`](css/style.css#L306-L326) |
| 실제 폼 전송 | Formspree POST, 전송 중/성공/실패 상태와 중복 방지 | [`main.js:215-323`](js/main.js#L215-L323) |
| 시스템 다크 모드 | 저장 테마가 없을 때 `prefers-color-scheme: dark` 감지 | [`main.js:7-24`](js/main.js#L7-L24) |

---

## 상태 → 렌더링 설계

| 기능 | 이벤트 | 상태 | 렌더 함수/DOM 갱신 |
|---|---|---|---|
| 테마 | 테마 버튼 `click` | `currentTheme` | `renderTheme()` → `data-theme`, 버튼 ARIA |
| 메뉴 | 햄버거 `click`, Escape | 메뉴 열림 여부 | `setMenuState()/closeMenu()` → `.active`, ARIA |
| 스크롤 UI | `scroll` | `scrollY` 임계값 비교 | Top `hidden`, 헤더 `.scrolled` |
| API | 초기 호출, 재시도 | `projectsState.status` | `renderProjects()` |
| 필터 | 언어 버튼 `click` | `selectedLanguage` | `renderProjectFilters()` + `renderProjects()` |
| 폼 | `input`, `submit` | `validationState`, `isSubmitting` | 필드 오류, 상태 메시지, 버튼 disabled |

단순 boolean 하나는 지역 변수로 관리하고, API처럼 서로 연관된 값이 많은 경우 객체로 묶었다. 즉 모든 상태를 무조건 객체로 만든 것이 아니라 **같이 변경되고 같이 렌더링되는 값**을 하나의 상태 단위로 묶었다.

---

## 검증

개발 중 별도 테스트 프레임워크를 추가하지 않고 Node 구문 검사, 정적 요구사항 검사, 가짜 DOM·mock fetch 실행으로 최소 검증했다.

- `node --check`: JavaScript 구문
- HTML: 시맨틱 태그, 앵커 대상, alt, label/id, 인라인 style/onclick 금지
- CSS: 변수, 다크 테마, Flex/Grid, 768/1024px, reduced-motion
- mock GitHub API: 로딩·성공·403·빈 상태·재시도·언어 필터
- mock Formspree: 유효성 실패 시 요청 차단, 중복 제출 방지, 성공 reset, 실패 입력 유지
- mock 브라우저: 시스템 다크 fallback, localStorage 우선순위, 타이핑 완료

실제 Chrome 화면, 실제 GitHub 네트워크 응답, 실제 Formspree 이메일 수신은 로컬 서버 및 배포 URL에서 최종 확인한다.

---

# Interview

## 항목 1 — 구현 확인

### 브라우저 창 크기를 줄였을 때 레이아웃이 모바일에 맞게 변경되는가?

네. 기본 규칙을 모바일로 작성하고 768px에서 About·Skills·Footer를 확장하며, 1024px에서 콘텐츠 폭과 Skills 4열을 적용했다. Projects는 `auto-fit/minmax`라서 고정 열 수 대신 가용 폭에 맞춰 카드가 자동 줄바꿈된다. 확인 위치: [`style.css:355-394`](css/style.css#L355-L394), [`style.css:649-710`](css/style.css#L649-L710).

### 테마 토글 버튼 클릭 시 다크/라이트 모드가 전환되고, 새로고침 후에도 유지되는가?

네. click에서 `currentTheme`을 변경하고 localStorage에 저장한 뒤 `data-theme`을 렌더링한다. 새로고침 시 저장값을 먼저 읽고, 저장값이 없을 때만 시스템 테마를 사용한다. 확인 위치: [`main.js:7-58`](js/main.js#L7-L58), [`style.css:4-61`](css/style.css#L4-L61).

### 햄버거 메뉴, 스크롤 애니메이션, 맨 위로 가기 버튼 등이 정상 동작하는가?

- 햄버거: `.active`와 `aria-expanded` 동기화, Escape 닫기
- 스크롤 애니메이션: section 20% 진입 시 `.visible`
- Top 버튼: 300px 이상에서 표시하고 click 시 `top: 0`

확인 위치: [`main.js:59-184`](js/main.js#L59-L184), [`style.css:720-858`](css/style.css#L720-L858).

### GitHub API에서 데이터를 불러와 화면에 표시되고, 로딩/에러/빈 상태가 구분되는가?

네. `PROJECT_STATUS`와 `projectsState`로 네 상태를 구분하고 `renderProjects`가 상태별 DOM을 만든다. 403은 레이트 리밋 전용 오류이며 오류 UI의 다시 시도 버튼이 같은 `loadProjects()`를 재호출한다. 확인 위치: [`main.js:324-556`](js/main.js#L324-L556).

### 필수 입력값 누락, 이메일 형식 오류 시 즉각적인 피드백이 표시되는가?

네. 각 필드의 `input` 이벤트에서 즉시 재검사하고 필드 근처 `<small>`에 오류를 표시한다. submit 시 전체 검증에 실패하면 첫 오류 필드로 포커스를 이동하며 API 요청은 보내지 않는다. 확인 위치: [`main.js:185-323`](js/main.js#L185-L323), [`index.html:99-129`](index.html#L99-L129).

**판정: ☐ PASS / ☐ FAIL**

## 항목 2 — 구조와 기본 개념

### HTML, CSS, JavaScript가 각각의 파일로 분리되어 있고, 분리한 이유와 각 파일의 역할을 구분하여 답변할 수 있는가?

네. HTML은 의미와 입력 구조, CSS는 표현과 반응형 규칙, JavaScript는 이벤트·상태·DOM 갱신을 담당한다. `config.js`는 사용자명과 임계값처럼 자주 변경되는 값을 로직에서 분리한다. 이렇게 나누면 내용·디자인·동작 변경이 서로 덜 영향을 준다.

### header, nav, main, section, footer 등 시맨틱 태그를 사용했고, 어떤 기준으로 태그를 선택했는지 설명할 수 있는가?

페이지 머리말은 `header`, 주요 이동 링크는 `nav`, 핵심 콘텐츠는 `main`, 독립 주제는 `section`, 자체 콘텐츠 카드는 `article`, 문서 끝 정보는 `footer`를 선택했다. 보이는 모양이 아니라 콘텐츠의 역할을 기준으로 정했다. 확인 위치: [`index.html:13-139`](index.html#L13-L139).

### CSS 변수(:root)로 색상, 폰트 등을 정의했고, 변수로 관리하면 어떤 이점이 있는지 구체적으로 답변할 수 있는가?

반복 값을 한곳에서 바꿀 수 있고, `--color-surface`처럼 값이 아닌 의미로 스타일을 읽을 수 있다. 다크모드는 컴포넌트를 다시 작성하지 않고 같은 변수 이름의 값만 교체할 수 있다. 확인 위치: [`style.css:4-61`](css/style.css#L4-L61).

### onclick 인라인 속성 대신 addEventListener를 사용한 이유를 두 방식의 차이와 비교하여 제시할 수 있는가?

`onclick`은 HTML 구조와 동작을 섞고 한 속성에 하나의 핸들러만 직접 표현한다. `addEventListener`는 JavaScript에 동작을 모으고 동일 요소에 여러 이벤트 리스너를 추가하거나 조건별 초기화하기 쉽다. 이 프로젝트는 메뉴, 스크롤, 폼, 필터 모두 `addEventListener`로 연결했다: [`main.js:79-323`](js/main.js#L79-L323), [`main.js:464-556`](js/main.js#L464-L556).

**판정: ☐ PASS / ☐ FAIL**

## 항목 3 — 상태, 비동기, 배열, 레이아웃

### 다크 모드, API 호출, 폼 유효성 검사 중 하나를 예시로 들어, 이벤트 → 상태 변경 → 화면 업데이트 흐름이 코드에서 어떻게 이어지는지 따라가며 짚어줄 수 있는가?

다크 모드를 예로 들면 다음 순서다.

1. `initializeTheme`이 테마 버튼 click을 수신한다.
2. `currentTheme`을 light/dark 반대 값으로 바꾼다.
3. `storeTheme`으로 localStorage에 저장한다.
4. `renderTheme`이 `<html data-theme>`과 버튼 텍스트·ARIA를 갱신한다.
5. CSS의 `[data-theme="dark"]` 변수가 전체 컴포넌트 색을 바꾼다.

코드: [`main.js:25-58`](js/main.js#L25-L58), [`style.css:44-61`](css/style.css#L44-L61).

### async/await와 try/catch를 사용하여 API 호출 성공과 실패를 어떻게 분기 처리했는지 코드 흐름을 따라 답변할 수 있는가?

`loadProjects`는 먼저 상태를 loading으로 바꾸고 렌더한다. `await fetch` 후 `response.ok`와 JSON 배열 여부를 검사하며, 정상 데이터는 success 또는 empty로 변경한다. HTTP·네트워크·파싱 오류는 catch에서 error 상태로 변경한다. 마지막에는 성공/실패와 관계없이 같은 `renderProjectUI`를 호출한다. 코드: [`main.js:464-556`](js/main.js#L464-L556).

### map, filter 등 배열 메서드를 활용하여 GitHub 데이터를 카드 UI로 변환하는 과정을 단계별로 정리할 수 있는가?

1. API 저장소에서 `filter(({ archived }) => !archived)`로 보관 저장소를 제외한다.
2. 언어 값은 `map(getProjectLanguage)` 후 `Set`으로 중복 제거한다.
3. 사용자가 언어를 선택하면 다시 `filter()`하여 표시 배열을 만든다.
4. 표시 배열을 `map(renderProjectCard)`로 HTML 카드 문자열로 변환하고 `join('')`한다.

코드: [`main.js:353-463`](js/main.js#L353-L463), [`main.js:464-556`](js/main.js#L464-L556).

### Flexbox와 Grid를 각각 어디에 적용했는지 확인하고, 해당 상황에서 그 방식을 선택한 이유를 비교하여 설명할 수 있는가?

Flexbox는 네비게이션·버튼·메타 정보처럼 한 축을 기준으로 정렬하는 곳에 사용했다. Grid는 Skills와 Projects처럼 행과 열을 함께 다루고 카드 폭에 따라 열 수가 달라지는 곳에 사용했다. 즉 **1차원 정렬은 Flexbox, 2차원 배치는 Grid**를 기준으로 선택했다. 코드: [`style.css:127-223`](css/style.css#L127-L223), [`style.css:355-394`](css/style.css#L355-L394).

**판정: ☐ PASS / ☐ FAIL**

## 항목 4 — 상태 객체와 모바일 퍼스트

### 상태(STATE) 객체를 따로 만들어서 관리한 이유는 무엇이며, 그냥 변수로 처리하면 안 되는지 설명할 수 있는가?

변수로 처리해도 되지만 API 상태처럼 `status`, `projects`, `errorMessage`, `selectedLanguage`가 함께 바뀌면 서로 다른 시점의 값이 섞이기 쉽다. 하나의 `projectsState`로 묶으면 렌더 함수가 한 객체만 받아 일관된 화면을 만들 수 있다. 반대로 테마 문자열이나 `isSubmitting`처럼 단순하고 지역적인 상태는 일반 변수로 두었다. 코드: [`main.js:464-556`](js/main.js#L464-L556).

### 반응형 디자인에서 “모바일 퍼스트”로 작성한 이유를 이야기할 수 있는가?

좁은 화면의 단순한 1열 구조를 기본값으로 두고 공간이 생길 때만 2열·4열 규칙을 추가하면 CSS 재정의가 줄고 작은 화면의 콘텐츠 우선순위가 명확해진다. `min-width: 768px`, `min-width: 1024px` 순으로 기능을 확장했기 때문에 상위 화면은 하위 규칙을 자연스럽게 상속한다. 코드: [`style.css:649-710`](css/style.css#L649-L710).

**판정: ☐ PASS / ☐ FAIL**
