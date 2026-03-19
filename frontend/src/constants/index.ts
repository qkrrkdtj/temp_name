// 애플리케이션 상수
export const API_BASE = "http://localhost:8001";

export const UPLOAD_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'],
} as const;

export const VITON_CONFIG = {
  TIMEOUT: 60000, // 1분 (단순 합성이므로 시간 단축)
  MAX_RETRIES: 2,
} as const;

export const CATEGORIES = {
  TOP: "001" as const,
  OUTER: "002" as const,
  USER: "user" as const,
} as const;
