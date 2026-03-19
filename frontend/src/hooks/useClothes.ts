import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { API_BASE, CATEGORIES } from '../constants';

export const useClothes = (category: string) => {
  const [clothList, setClothList] = useState<string[]>([]);
  const [clothLoading, setClothLoading] = useState(false);

  const fetchClothes = useCallback(async () => {
    try {
      setClothLoading(true);
      
      if (category === CATEGORIES.USER) {
        const response = await axios.get<string[]>(`${API_BASE}/uploads/user-clothes`);
        setClothList(response.data);
      } else {
        const response = await axios.get<string[]>(`${API_BASE}/clothing/list`, {
          params: { category, limit: 200 }
        });
        setClothList(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch clothes:', error);
      setClothList([]);
    } finally {
      setClothLoading(false);
    }
  }, [category]);

  const refreshClothes = useCallback(async () => {
    await fetchClothes();
  }, [fetchClothes]);

  useEffect(() => {
    fetchClothes();
  }, [fetchClothes]);

  return {
    clothList,
    clothLoading,
    refreshClothes,
  };
};
