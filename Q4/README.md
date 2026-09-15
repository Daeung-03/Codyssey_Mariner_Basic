# 반응형 포트폴리오 웹사이트

순수 HTML/CSS/JavaScript만으로 구현한 반응형 포트폴리오 사이트.
외부 라이브러리(React/Vue/jQuery/Bootstrap/Tailwind) 없이 DOM 조작, 이벤트 처리,
GitHub API 비동기 연동을 직접 구현한다.

> 상세 설계는 [`docs/PLAN.md`](docs/PLAN.md) 참고.

---

## 과제 요약

| 항목 | 내용 |
|------|------|
| 목표 | "이벤트 → 상태 변경 → DOM 렌더링" 흐름 체득 (React 학습 기반) |
| 핵심 제약 | 외부 라이브러리 금지 / 인라인 스타일·`onclick` 금지 / `var` 금지 |
| 허용 | Google Fonts, Font Awesome 아이콘 |
| 실행 환경 | 최신 Chrome (정적 파일, VS Code + Live Server) |
| 배포 | GitHub Pages |

---

## 폴더 구조 (최소 모듈)

```
Q4/
├── index.html          ← 단일 페이지, 시맨틱 마크업
├── css/
│   └── style.css       ← 변수/레이아웃/반응형/다크모드/애니메이션
├── js/
│   ├── config.js       ← 설정값 (GitHub username, 임계값)
│   └── main.js         ← 인터랙션 + API 연동 로직
├── images/             ← 프로필 이미지 등
├── README.md
└── docs/
    ├── PROBLEM.md
    └── PLAN.md
```

---

## 구현 기능

- **반응형 레이아웃**: 모바일 퍼스트, 768px(태블릿)/1024px(데스크톱) 브레이크포인트
- **섹션**: Hero, About, Skills, Projects, Contact, Footer
- **네비게이션**: Flexbox 기반, 모바일 햄버거 메뉴 토글
- **다크 모드**: 토글 + localStorage 영속
- **부드러운 스크롤**: 앵커 클릭 시 섹션 이동
- **스크롤 인터랙션**: 스크롤 탑 버튼, 네비 스타일 변경, 등장 애니메이션
- **Contact 폼**: 필수값 + 이메일 형식 검증, 에러/성공 메시지
- **GitHub API 연동**: 저장소 목록을 카드로 렌더, 로딩/성공/에러/빈 상태 처리

---

## 상태 → 렌더링 흐름

1. 다크 모드 토글 → theme 상태 변경 → 전체 스타일 변경
2. API 호출 → loading/success/error/empty 상태 → Projects 렌더 분기
3. 폼 입력/제출 → 유효성 상태 변경 → 에러/성공 메시지 표시

---

## 동작 기준값 (임계값)

| 항목 | 기준값 |
|------|--------|
| 스크롤 탑 버튼 노출 | scrollY ≥ 300px |
| 네비게이션 배경 변경 | scrollY ≥ 60px |
| 스크롤 애니메이션 (IntersectionObserver threshold) | 0.2 |

> 기준값은 변경 가능하며, 변경 시 이 표를 갱신한다.

---

## 실행 방법

```bash
# VS Code Live Server 또는 정적 서버로 실행
cd Q4
# 예: python 간이 서버
python3 -m http.server 5500
# http://localhost:5500 접속
```

---

## GitHub API 주의사항

- 엔드포인트: `https://api.github.com/users/{username}/repos`
- 인증 없이 호출 시 시간당 60회 제한. 짧은 시간 반복 새로고침 지양.
- 403(레이트 리밋) 응답 시 에러 상태 UI + 재시도 버튼 표시.

---

## 배포

- 배포 URL: `(배포 후 기재)`
- 스크린샷: 데스크톱 / 모바일 / 다크모드 `(추후 첨부)`

---

## 사용 기술

HTML5(시맨틱 태그), CSS3(Flexbox, Grid, CSS 변수, 미디어 쿼리),
JavaScript(ES6+, DOM API, addEventListener, fetch/async-await, IntersectionObserver, localStorage)
