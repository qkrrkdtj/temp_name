# Frontend React Application

## 🎨 React 웹 인터페이스

### 📋 개요
NT Fit 가상 피팅 시스템의 프론트엔드 React 애플리케이션입니다. 사용자 친화적인 인터페이스를 통해 이미지 업로드, 가상 피팅, 결과 관리 등 모든 기능을 제공합니다.

---

## 🏗️ 구조

```
frontend/
├── src/
│   ├── App.tsx              # 메인 애플리케이션 컴포넌트
│   ├── main.tsx             # 애플리케이션 진입점
│   ├── style.css            # 전역 스타일시트
│   ├── constants/           # 상수 및 설정
│   │   └── index.ts         # API URL, 설정 값
│   ├── hooks/               # 커스텀 React Hooks
│   │   └── useVitonAPI.ts   # API 통신 Hook
│   └── types/               # TypeScript 타입 정의
│       └── index.ts         # 데이터 타입
├── public/
│   └── index.html           # HTML 템플릿
├── package.json             # npm 의존성 및 스크립트
├── vite.config.ts           # Vite 빌드 설정
└── README_FRONTEND.md       # 프론트엔드 상세 문서
```

---

## 🔧 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.x | UI 프레임워크 |
| TypeScript | 5.x | 타입 안전성 |
| Vite | 5.x | 빌드 도구 |
| Axios | 1.x | HTTP 클라이언트 |
| CSS3 | - | 스타일링 |

---

## 🚀 실행 방법

### 개발 환경
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 프로덕션 빌드
```bash
# 빌드
npm run build

# 미리보기
npm run preview

# 린트
npm run lint
```

---

## 🎮 주요 기능

### 📸 이미지 업로드
- **드래그 앤 드롭**: 직관적인 파일 업로드
- **클릭 업로드**: 파일 선택기 통한 업로드
- **파일 검증**: 이미지 타입 및 크기 확인
- **미리보기**: 업로드된 이미지 즉시 확인

### 🎭 가상 피팅
- **실시간 처리**: 플레이스홀더 10-30초 내 완료
- **진행 상태**: 처리 상태 표시
- **결과 갤러리**: 생성된 결과 이미지 관리
- **세션 관리**: 여러 세션 결과 저장

### 🗂️ 의류 관리
- **카테고리**: 상의/아우터/내 옷 분류
- **검색**: 번호로 빠른 의류 검색
- **삭제**: 불필요한 의류 이미지 삭제
- **업로드**: 새로운 의류 이미지 추가

### 📱 사용자 인터페이스
- **반응형 디자인**: 모든 화면 크기 지원
- **탭 네비게이션**: 메인/상품 페이지 구분
- **모달 다이얼로그**: 옷 추가 기능
- **스무스 스크롤**: 결과 섹션으로 자동 이동

---

## 🧩 컴포넌트 구조

### 메인 컴포넌트 (App.tsx)
```typescript
function App() {
  // 상태 관리
  const [tab, setTab] = useState<Tab>("main");
  const [virtualTryOnAPI] = useVirtualTryOnAPI();
  const [fileUpload] = useFileUpload();
  
  // 핵심 기능
  const handleUserDrop = async (e: React.DragEvent) => { /* ... */ };
  const handleClothDrop = async (e: React.DragEvent) => { /* ... */ };
  const onPickUserImage = async (e: React.ChangeEvent) => { /* ... */ };
  
  return (
    // JSX 렌더링
  );
}
```

### 커스텀 Hooks

#### useFileUpload Hook
```typescript
const useFileUpload = () => {
  const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
  const [selectedCloth, setSelectedCloth] = useState<string | null>(null);
  
  const handleUserImageUpload = useCallback((file: File) => { /* ... */ });
  const handleClothUpload = useCallback((file: File) => { /* ... */ });
  
  return {
    userImageUrl,
    selectedCloth,
    handleUserImageUpload,
    handleClothUpload,
    // ...
  };
};
```

#### useVirtualTryOnAPI Hook
```typescript
const useVirtualTryOnAPI = () => {
  const [running, setRunning] = useState(false);
  const [resultFiles, setResultFiles] = useState<string[]>([]);
  
  const uploadUserImage = useCallback(async (file: File) => { /* ... */ });
  const runVirtualTryOn = useCallback(async (clothId: string) => { /* ... */ };
  
  return {
    running,
    resultFiles,
    uploadUserImage,
    runVirtualTryOn,
    // ...
  };
};
```

---

## 🎨 스타일링

### CSS 구조
```css
/* 레이아웃 */
.app-container { /* 전체 컨테이너 */ }
.nav-container { /* 네비게이션 */ }
.main-container { /* 메인 콘텐츠 */ }

/* 컴포넌트 */
.upload-area { /* 업로드 영역 */ }
.result-section { /* 결과 섹션 */ }
.cloth-grid { /* 의류 그리드 */ }

/* 버튼 */
.btn { /* 기본 버튼 */ }
.btn.primary { /* 주요 버튼 */ }
.btn.ghost { /* 고스트 버튼 */ }

/* 반응형 */
@media (max-width: 768px) { /* 모바일 */ }
@media (max-width: 480px) { /* 소형 모바일 */ }
```

### 테마 색상
```css
:root {
  --primary-color: #3b82f6;
  --secondary-color: #64748b;
  --success-color: #10b981;
  --error-color: #ef4444;
  --background-color: #f8fafc;
  --border-color: #e2e8f0;
}
```

---

## 📡 API 통신

### API 설정
```typescript
// constants/index.ts
export const API_BASE = "http://localhost:8001";
export const VITON_CONFIG = {
  TIMEOUT: 60000,
  MAX_RETRIES: 2,
};
```

### Axios 인스턴스
```typescript
// 기본 설정
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: VITON_CONFIG.TIMEOUT,
});

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

### API 호출 예제
```typescript
// 이미지 업로드
const uploadUserImage = async (file: File): Promise<string | null> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post<UploadResponse>(
    '/upload/user-image', 
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  
  return response.data.upload_id;
};

// 가상 피팅 실행
const runVirtualTryOn = async (clothId: string): Promise<boolean> => {
  const response = await apiClient.post<VitonResponse>(
    '/viton/tryon', 
    null,
    { params: { upload_id: userUploadId, cloth_id: clothId } }
  );
  
  // 결과 처리
  const sessionId = response.data.session_id;
  // ...
};
```

---

## 🔄 상태 관리

### 로컬 상태
```typescript
// 사용자 상태
const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
const [selectedCloth, setSelectedCloth] = useState<string | null>(null);

// API 상태
const [running, setRunning] = useState(false);
const [resultFiles, setResultFiles] = useState<string[]>([]);

// UI 상태
const [tab, setTab] = useState<Tab>("main");
const [showModal, setShowModal] = useState(false);
```

### 상태 업데이트 패턴
```typescript
// 비동기 상태 업데이트
const handleAsyncAction = useCallback(async () => {
  try {
    setRunning(true);
    const result = await apiCall();
    setResultFiles(prev => [...prev, result]);
  } catch (error) {
    console.error(error);
    alert('오류가 발생했습니다.');
  } finally {
    setRunning(false);
  }
}, []);
```

---

## 🛡️ 에러 처리

### 사용자 에러 처리
```typescript
const handleError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.detail || '네트워크 오류';
    alert(message);
  } else if (error instanceof Error) {
    alert(error.message);
  } else {
    alert('알 수 없는 오류가 발생했습니다.');
  }
};
```

### 유효성 검사
```typescript
// 파일 유효성 검사
const validateFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  const maxSize = 10 * 1024 * 1024; // 10MB
  
  return allowedTypes.includes(file.type) && file.size <= maxSize;
};

// 입력 유효성 검사
const validateInputs = (): boolean => {
  if (!userImageUrl) {
    alert('먼저 사용자 사진을 업로드해주세요.');
    return false;
  }
  if (!selectedCloth) {
    alert('옷을 선택해주세요.');
    return false;
  }
  return true;
};
```

---

## 🎯 사용자 경험 최적화

### 로딩 상태
```typescript
// 버튼 로딩 상태
<button 
  className="btn primary" 
  onClick={handleTryOn}
  disabled={running}
>
  {running ? "생성 중..." : "입어보기"}
</button>

// 스켈레톽 로딩
{running && (
  <div className="loading-skeleton">
    <div className="skeleton-line"></div>
    <div className="skeleton-line"></div>
  </div>
)}
```

### 사용자 피드백
```typescript
// 성공 피드백
const showSuccess = (message: string) => {
  alert(message); // 실제로는 toast/notification 사용 권장
};

// 자동 스크롤
const scrollToResults = () => {
  document.getElementById("result-section")?.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
};
```

---

## 📱 반응형 디자인

### 브레이크포인트
```css
/* 데스크톱 */
@media (min-width: 1024px) {
  .cloth-grid { grid-template-columns: repeat(4, 1fr); }
}

/* 태블릿 */
@media (max-width: 1023px) and (min-width: 768px) {
  .cloth-grid { grid-template-columns: repeat(3, 1fr); }
}

/* 모바일 */
@media (max-width: 767px) {
  .cloth-grid { grid-template-columns: repeat(2, 1fr); }
  .upload-area { min-height: 200px; }
}
```

### 모바일 최적화
```css
/* 터치 타겟 크기 */
.btn { 
  min-height: 44px; 
  min-width: 44px;
  padding: 12px 24px;
}

/* 모바일 네비게이션 */
.nav-container {
  flex-direction: column;
  gap: 8px;
}
```

---

## 🔧 개발 가이드

### 새로운 컴포넌트 추가
```typescript
// components/NewComponent.tsx
interface NewComponentProps {
  title: string;
  onAction: () => void;
}

const NewComponent: React.FC<NewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="new-component">
      <h3>{title}</h3>
      <button onClick={onAction}>액션</button>
    </div>
  );
};

export default NewComponent;
```

### 새로운 Hook 추가
```typescript
// hooks/useNewFeature.ts
export const useNewFeature = () => {
  const [state, setState] = useState(initialState);
  
  const action = useCallback(() => {
    // 로직 구현
  }, []);
  
  return { state, action };
};
```

---

## 📊 성능 최적화

### 이미지 최적화
```typescript
// 이미지 미리보기 최적화
const createImagePreview = (file: File): string => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();
  
  img.onload = () => {
    // 이미지 리사이즈 로직
    canvas.width = 300;
    canvas.height = (img.height / img.width) * 300;
    ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
  };
  
  return URL.createObjectURL(file);
};
```

### 메모리 관리
```typescript
// URL 객체 정리
useEffect(() => {
  return () => {
    if (userImageUrl) {
      URL.revokeObjectURL(userImageUrl);
    }
  };
}, [userImageUrl]);

// 컴포넌트 언마운트 시 정리
useEffect(() => {
  return () => {
    // 구독 해제, 타이머 정리 등
  };
}, []);
```

---

## 📖 추가 문서

- **🚀 배포 가이드**: 상위 디렉토리 `DEPLOYMENT.md`
- **🔧 백엔드**: `../backend/README_BACKEND.md`
- **🤖 AI 업그레이드**: `../backend/README_AI_UPGRADE.md`

---

## 🎯 향후 개발 계획

1. **UI/UX 개선**: 더 나은 사용자 경험
2. **애니메이션**: 처리 상태 시각화
3. **PWA 지원**: 오프라인 기능
4. **다국어**: i18n 지원
5. **테마**: 다크/라이트 모드

---

> 🎨 **현재 상태**: 모든 웹 기능 완벽 동작 ✅  
> 📱 **사용자 경험**: 직관적이고 반응적인 인터페이스 ✅
