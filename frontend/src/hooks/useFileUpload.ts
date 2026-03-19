import { useCallback, useState } from 'react';
import { API_BASE, UPLOAD_CONFIG } from '../constants';

export const useFileUpload = () => {
  const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
  const [selectedCloth, setSelectedCloth] = useState<string | null>(null);
  const [userClothFile, setUserClothFile] = useState<File | null>(null);

  const handleUserImageUpload = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드할 수 있습니다.');
      return false;
    }
    
    if (file.size > UPLOAD_CONFIG.MAX_SIZE) {
      alert('파일 크기가 10MB를 초과할 수 없습니다.');
      return false;
    }

    if (userImageUrl) URL.revokeObjectURL(userImageUrl);
    setUserImageUrl(URL.createObjectURL(file));
    return true;
  }, [userImageUrl]);

  const handleClothUpload = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드할 수 있습니다.');
      return false;
    }
    
    if (file.size > UPLOAD_CONFIG.MAX_SIZE) {
      alert('파일 크기가 10MB를 초과할 수 없습니다.');
      return false;
    }

    setUserClothFile(file);
    setSelectedCloth(null);
    const imageUrl = URL.createObjectURL(file);
    setSelectedCloth(imageUrl);
    return true;
  }, []);

  const handleClothSelect = useCallback((clothPath: string) => {
    setSelectedCloth(clothPath);
    setUserClothFile(null);
  }, []);

  const clearFiles = useCallback(() => {
    if (userImageUrl) URL.revokeObjectURL(userImageUrl);
    setUserImageUrl(null);
    setSelectedCloth(null);
    setUserClothFile(null);
  }, [userImageUrl]);

  return {
    userImageUrl,
    selectedCloth,
    userClothFile,
    handleUserImageUpload,
    handleClothUpload,
    handleClothSelect,
    clearFiles,
  };
};
