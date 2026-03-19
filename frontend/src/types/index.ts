// 애플리케이션 타입 정의
export type Tab = "main" | "products";
export type Category = "001" | "002" | "user";

export interface UploadResponse {
  upload_id?: string;
  filename?: string;
  status: string;
}

export interface VitonResponse {
  status: string;
  session_id: string;
  result_url: string;
  result_filename: string;
}

export interface ClothItem {
  id: string;
  name: string;
  src: string;
  isUser?: boolean;
}
