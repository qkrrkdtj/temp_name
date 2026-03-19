import { useCallback, useState } from 'react';
import axios from 'axios';
import { API_BASE, VITON_CONFIG } from '../constants';
import { UploadResponse, VitonResponse } from '../types';

export const useVitonAPI = () => {
  const [running, setRunning] = useState(false);
  const [resultFiles, setResultFiles] = useState<string[]>([]);
  const [lastResultFile, setLastResultFile] = useState<string | null>(null);
  const [userUploadId, setUserUploadId] = useState<string | null>(null);
  const [uploadedClothFilename, setUploadedClothFilename] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<string | null>(null);

  const uploadUserImage = useCallback(async (file: File): Promise<string | null> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post<UploadResponse>(`${API_BASE}/upload/user-image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: VITON_CONFIG.TIMEOUT,
      });
      
      if (response.data.upload_id) {
        setUserUploadId(response.data.upload_id);
        return response.data.upload_id;
      }
      return null;
    } catch (error) {
      console.error('User image upload failed:', error);
      alert("사용자 이미지 업로드 중 오류가 발생했습니다.");
      return null;
    }
  }, []);

  const uploadClothImage = useCallback(async (file: File): Promise<string | null> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post<UploadResponse>(`${API_BASE}/upload/cloth`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: VITON_CONFIG.TIMEOUT,
      });
      
      if (response.data.filename) {
        setUploadedClothFilename(response.data.filename);
        return response.data.filename;
      }
      return null;
    } catch (error) {
      console.error('Cloth image upload failed:', error);
      alert("옷 이미지 업로드 중 오류가 발생했습니다.");
      return null;
    }
  }, []);

  const runViton = useCallback(async (clothId: string): Promise<boolean> => {
    if (!userUploadId) {
      alert("먼저 사용자 사진을 업로드해주세요.");
      return false;
    }
    
    try {
      setRunning(true);
      
      const response = await axios.post<VitonResponse>(`${API_BASE}/viton/tryon`, null, {
        params: { upload_id: userUploadId, cloth_id: clothId },
        timeout: VITON_CONFIG.TIMEOUT,
      });
      
      const sessionId = response.data.session_id;
      setCurrentSession(sessionId);
      
      const resultsResponse = await axios.get<string[]>(`${API_BASE}/viton/results`, {
        params: { name: sessionId },
      });
      
      setResultFiles(resultsResponse.data);
      setLastResultFile(resultsResponse.data.length ? resultsResponse.data[resultsResponse.data.length - 1] : null);
      
      document.getElementById("result-section")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
      
      return true;
    } catch (error) {
      console.error('Virtual try-on execution failed:', error);
      alert("가상 피팅 실행 중 오류가 발생했습니다.");
      return false;
    } finally {
      setRunning(false);
    }
  }, [userUploadId]);

  const deleteUserCloth = useCallback(async (filename: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_BASE}/uploads/cloth/${filename}`);
      if (uploadedClothFilename === filename) {
        setUploadedClothFilename(null);
      }
      return true;
    } catch (error) {
      console.error('Cloth deletion failed:', error);
      alert("옷 삭제 중 오류가 발생했습니다.");
      return false;
    }
  }, [uploadedClothFilename]);

  const clearResults = useCallback(() => {
    setResultFiles([]);
    setLastResultFile(null);
    setCurrentSession(null);
  }, []);

  return {
    running,
    resultFiles,
    lastResultFile,
    userUploadId,
    uploadedClothFilename,
    currentSession,
    uploadUserImage,
    uploadClothImage,
    runViton,
    deleteUserCloth,
    clearResults,
  };
};
