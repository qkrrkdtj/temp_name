import React, { useEffect, useMemo, useState, useRef, useCallback } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000";

type Tab = "main" | "products";
type Category = "001" | "002" | "user";

// Custom hook for file handling
const useFileUpload = () => {
  const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
  const [selectedCloth, setSelectedCloth] = useState<string | null>(null);
  const [userClothFile, setUserClothFile] = useState<File | null>(null);

  const handleUserImageUpload = useCallback((file: File) => {
    if (file.type.startsWith('image/')) {
      if (userImageUrl) URL.revokeObjectURL(userImageUrl);
      setUserImageUrl(URL.createObjectURL(file));
    } else {
      alert('이미지 파일만 업로드할 수 있습니다.');
    }
  }, [userImageUrl]);

  const handleClothUpload = useCallback((file: File) => {
    if (file.type.startsWith('image/')) {
      setUserClothFile(file);
      setSelectedCloth(null);
      const imageUrl = URL.createObjectURL(file);
      setSelectedCloth(imageUrl);
    } else {
      alert('이미지 파일만 업로드할 수 있습니다.');
    }
  }, []);

  const handleClothSelect = useCallback((clothPath: string) => {
    setSelectedCloth(clothPath);
    setUserClothFile(null);
  }, []);

  // Cleanup URLs on unmount
  useEffect(() => {
    return () => {
      if (userImageUrl) URL.revokeObjectURL(userImageUrl);
    };
  }, [userImageUrl]);

  return {
    userImageUrl,
    selectedCloth,
    userClothFile,
    handleUserImageUpload,
    handleClothUpload,
    handleClothSelect,
    setUserImageUrl
  };
};

// Custom hook for API calls
const useVirtualTryOnAPI = () => {
  const [running, setRunning] = useState(false);
  const [resultFiles, setResultFiles] = useState<string[]>([]);
  const [lastResultFile, setLastResultFile] = useState<string | null>(null);
  const [userUploadId, setUserUploadId] = useState<string | null>(null);
  const [uploadedClothFilename, setUploadedClothFilename] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<string | null>(null);

  const uploadUserImage = useCallback(async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE}/upload/user-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setUserUploadId(response.data.upload_id);
      return response.data.upload_id;
    } catch (e) {
      console.error(e);
      alert("사용자 이미지 업로드 중 오류가 발생했습니다.");
      throw e;
    }
  }, []);

  const uploadClothImage = useCallback(async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE}/upload/cloth`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setUploadedClothFilename(response.data.filename);
      return response.data.filename;
    } catch (e) {
      console.error(e);
      alert("옷 이미지 업로드 중 오류가 발생했습니다.");
      throw e;
    }
  }, []);

  const deleteUserCloth = useCallback(async (filename: string) => {
    try {
      await axios.delete(`${API_BASE}/uploads/cloth/${filename}`);
      // 목록 새로고침을 위해 상태 업데이트
      if (uploadedClothFilename === filename) {
        setUploadedClothFilename(null);
      }
      return true;
    } catch (e) {
      console.error(e);
      alert("옷 삭제 중 오류가 발생했습니다.");
      return false;
    }
  }, [uploadedClothFilename]);

  const runVirtualTryOn = useCallback(async (session: string, clothId: string) => {
    if (!userUploadId) {
      alert("먼저 사용자 사진을 업로드해주세요.");
      return;
    }
    
    console.log('=== Virtual Try-on 실행 시작 ===');
    console.log('userUploadId:', userUploadId);
    console.log('clothId:', clothId);
    console.log('session:', session);
    
    try {
      setRunning(true);
      const url = `${API_BASE}/viton/tryon`;
      const params = { 
        upload_id: userUploadId,
        cloth_id: clothId
      };
      
      console.log('API URL:', url);
      console.log('API Params:', params);
      
      const response = await axios.post(url, null, { params });
      console.log('API Response:', response.data);
      
      // 응답에서 세션 ID 추출
      const sessionId = response.data.session_id;
      console.log('Session ID:', sessionId);
      setCurrentSession(sessionId);
      
      // Refresh results after running - 세션 ID로 결과 조회
      const res = await axios.get<string[]>(`${API_BASE}/viton/results`, {
        params: { name: sessionId }
      });
      console.log('Results response:', res.data);
      
      setResultFiles(res.data);
      setLastResultFile(res.data.length ? res.data[res.data.length - 1] : null);
      
      // Scroll to results
      document.getElementById("result-section")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    } catch (e) {
      console.error('=== Virtual Try-on 실행 오류 ===');
      console.error('Error:', e);
      if (e instanceof Error) {
        console.error('Error message:', e.message);
        console.error('Error stack:', e.stack);
      }
      alert("가상 피팅 실행 중 오류가 발생했습니다. 백엔드 서버와 콘솔 로그를 확인해 주세요.");
    } finally {
      setRunning(false);
    }
  }, [userUploadId]);

  const refreshResults = useCallback(async (session: string, scroll = false) => {
    try {
      const res = await axios.get<string[]>(`${API_BASE}/viton/results`, {
        params: { name: session }
      });
      setResultFiles(res.data);
      setLastResultFile(res.data.length ? res.data[res.data.length - 1] : null);
      if (scroll) {
        document.getElementById("result-section")?.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
      }
    } catch (e) {
      console.error(e);
      alert("결과 목록을 갱신하지 못했습니다.");
    }
  }, []);

  const clearResults = useCallback(() => {
    setResultFiles([]);
    setLastResultFile(null);
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
    deleteUserCloth,
    runVirtualTryOn,
    refreshResults,
    clearResults
  };
};

function App() {
  const [tab, setTab] = useState<Tab>("main");
  const [showClothUploadModal, setShowClothUploadModal] = useState(false);
  const [resultSession, setResultSession] = useState("web_demo");
  
  // Custom hooks
  const fileUpload = useFileUpload();
  const virtualTryOnAPI = useVirtualTryOnAPI();
  
  const selectedProductId = useMemo(() => {
    if (!fileUpload.selectedCloth) return null;
    const file = fileUpload.selectedCloth.split("/").pop() ?? fileUpload.selectedCloth;
    return file.replace(/\.[^.]+$/, "");
  }, [fileUpload.selectedCloth]);

  const [category, setCategory] = useState<Category>("001");
  const [clothList, setClothList] = useState<string[]>([]);
  const [clothLoading, setClothLoading] = useState(false);
  const [search, setSearch] = useState("");

  // Refs for file inputs
  const userFileInputRef = useRef<HTMLInputElement>(null);
  const clothFileInputRef = useRef<HTMLInputElement>(null);
  const clothFileInputModalRef = useRef<HTMLInputElement>(null);

  const clothSrc = useMemo(() => {
    if (!fileUpload.selectedCloth) return null;
    
    // 사용자가 직접 업로드한 옷인 경우 (blob URL)
    if (fileUpload.selectedCloth.startsWith('blob:')) {
      return fileUpload.selectedCloth;
    }
    
    // 사용자 업로드 옷인 경우 (파일명)
    if (fileUpload.userClothFile) {
      return fileUpload.selectedCloth; // blob URL
    }
    
    // 기존 카테고리 옷인 경우
    return `${API_BASE}/static/clothing_only/${fileUpload.selectedCloth}`;
  }, [fileUpload.selectedCloth, fileUpload.userClothFile]);

  const resultImageSrc = useMemo(() => {
    if (!virtualTryOnAPI.currentSession || virtualTryOnAPI.resultFiles.length === 0) return null;
    const last = virtualTryOnAPI.resultFiles[virtualTryOnAPI.resultFiles.length - 1];
    return `${API_BASE}/static/app_results/${virtualTryOnAPI.currentSession}/${last}`;
  }, [virtualTryOnAPI.resultFiles, virtualTryOnAPI.currentSession]);

  const filteredClothes = useMemo(() => {
    const q = search.trim();
    if (!q) return clothList;
    return clothList.filter((rel) => {
      const file = rel.split("/").pop() ?? rel;
      const id = file.replace(/\.[^.]+$/, "");
      return id.includes(q);
    });
  }, [clothList, search]);

  // Fetch clothes when products tab is active
  useEffect(() => {
    const fetchClothes = async () => {
      if (tab !== "products") return;
      
      if (category === "user") {
        // 사용자 업로드 옷 목록
        try {
          setClothLoading(true);
          const res = await axios.get<string[]>(`${API_BASE}/uploads/user-clothes`);
          setClothList(res.data);
        } catch (e) {
          console.error(e);
          setClothList([]); // 사용자 옷이 없으면 빈 목록
        } finally {
          setClothLoading(false);
        }
      } else {
        // 기존 카테고리 옷 목록
        try {
          setClothLoading(true);
          const res = await axios.get<string[]>(`${API_BASE}/clothing/list`, {
            params: { category, limit: 200 }
          });
          setClothList(res.data);
        } catch (e) {
          console.error(e);
          alert(
            "상품 목록을 불러오지 못했습니다. 백엔드 서버 실행 여부와 /clothing/list 응답을 확인해 주세요."
          );
        } finally {
          setClothLoading(false);
        }
      }
    };
    void fetchClothes();
  }, [tab, category]);

  // Drag and drop handlers
  const handleUserDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      fileUpload.handleUserImageUpload(file);
      try {
        await virtualTryOnAPI.uploadUserImage(file);
      } catch (error) {
        console.error('User image upload failed:', error);
      }
    }
  }, [fileUpload, virtualTryOnAPI]);

  const handleClothDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      fileUpload.handleClothUpload(file);
      try {
        await virtualTryOnAPI.uploadClothImage(file);
      } catch (error) {
        console.error('Cloth image upload failed:', error);
      }
    }
  }, [fileUpload, virtualTryOnAPI]);

  const handleClothFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      fileUpload.handleClothUpload(file);
      try {
        await virtualTryOnAPI.uploadClothImage(file);
      } catch (error) {
        console.error('Cloth image upload failed:', error);
      }
    }
  }, [fileUpload, virtualTryOnAPI]);

  const onPickUserImage = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      fileUpload.handleUserImageUpload(file);
      try {
        await virtualTryOnAPI.uploadUserImage(file);
      } catch (error) {
        console.error('User image upload failed:', error);
      }
    }
  }, [fileUpload, virtualTryOnAPI]);

  // Memoized components
  const NavButton = useMemo(() => ({ id, children }: { id: Tab; children: React.ReactNode }) => (
    <button
      className={`navBtn ${tab === id ? "active" : ""}`}
      onClick={() => setTab(id)}
      type="button"
    >
      {children}
    </button>
  ), [tab]);

  return (
    <div className="page">
      <header className="topbar" role="banner">
        <div className="brand" role="img" aria-label="Nice Try 로고">
          <div className="logoMark" aria-hidden="true">NT</div>
          <div className="brandText">
            <div className="brandName">Nice Try</div>
            <div className="brandSub">가상 피팅 데모</div>
          </div>
        </div>
        <nav className="nav" role="navigation" aria-label="메인 네비게이션">
          <NavButton id="main">메인</NavButton>
          <NavButton id="products">상품</NavButton>
        </nav>
      </header>

      <main className="content">
        {tab === "main" && (
          <section id="tab-main" className="tab">
            <div className="hero">
              <h1 className="heroTitle">원하는 옷을 골라 빠르게 "입어보기"</h1>
              <p className="heroDesc">
                상품 번호(이미지 파일명)로 관리되어 이후 검색/연동 확장이 쉬운 구조입니다.
              </p>
            </div>
            
            <div className="mainGrid">
              <section className="card" aria-labelledby="user-photo-title">
                <div className="cardHeader">
                  <h2 className="cardTitle" id="user-photo-title">내 사진</h2>
                  <div className="cardHint">사진을 올리거나 드래그하세요</div>
                </div>
                <div 
                  className="frame" 
                  id="user-drop" 
                  role="button" 
                  tabIndex={0} 
                  aria-label="사용자 사진 업로드 영역"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleUserDrop}
                  onClick={() => userFileInputRef.current?.click()}
                >
                  {fileUpload.userImageUrl ? (
                    <img className="previewImg" src={fileUpload.userImageUrl} alt="사용자 업로드" />
                  ) : (
                    <div className="placeholder">사용자 사진 업로드</div>
                  )}
                </div>
                <div className="cardFooter">
                  <input 
                    ref={userFileInputRef}
                    id="user-file" 
                    className="fileInput" 
                    type="file" 
                    accept="image/*" 
                    aria-label="사용자 사진 파일 선택"
                    onChange={onPickUserImage}
                  />
                </div>
              </section>

              <section className="card" aria-labelledby="selected-cloth-title">
                <div className="cardHeader">
                  <h2 className="cardTitle" id="selected-cloth-title">선택한 옷</h2>
                  <div className="cardHint" id="selected-info">
                    {selectedProductId ? `상품 번호: ${selectedProductId}` : "옷을 선택하거나 파일을 업로드하세요"}
                  </div>
                </div>
                <div 
                  className="frame" 
                  id="cloth-drop" 
                  role="button" 
                  tabIndex={0} 
                  aria-label="옷 선택 및 업로드 영역"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleClothDrop}
                  onClick={() => clothFileInputRef.current?.click()}
                >
                  {clothSrc || fileUpload.userClothFile ? (
                    <img className="previewImg" src={clothSrc || (fileUpload.userClothFile ? URL.createObjectURL(fileUpload.userClothFile) : '')} alt={`선택된 옷 ${selectedProductId ?? ""}`} />
                  ) : (
                    <div className="placeholder">옷을 선택하거나 드래그하여 업로드하세요</div>
                  )}
                </div>
                <div className="cardFooter">
                  <input 
                    ref={clothFileInputRef}
                    id="cloth-file-input-main" 
                    className="fileInput" 
                    type="file" 
                    accept="image/*"
                    onChange={handleClothFileInput}
                  />
                  <button 
                    id="go-products" 
                    type="button" 
                    className="btn ghost"
                    onClick={() => setTab("products")}
                  >
                    옷 고르기
                  </button>

                  <div className="sessionRow">
                    <label className="sessionLabel" htmlFor="session">세션</label>
                    <input 
                      id="session" 
                      className="sessionInput" 
                      value={resultSession}
                      onChange={(e) => setResultSession(e.target.value)}
                    />
                  </div>

                  <button 
                    id="run-btn" 
                    type="button" 
                    className="btn primary"
                    onClick={() => {
                      const clothId = fileUpload.userClothFile 
                        ? virtualTryOnAPI.uploadedClothFilename || `user_${Date.now()}` 
                        : fileUpload.selectedCloth || '';
                      virtualTryOnAPI.runVirtualTryOn(resultSession, clothId);
                    }}
                    disabled={virtualTryOnAPI.running}
                  >
                    {virtualTryOnAPI.running ? "생성 중..." : "입어보기"}
                  </button>
                </div>
              </section>
            </div>

            <section className="resultSection" aria-label="결과" id="result-section">
              <div className="resultHeader">
                <div>
                  <div className="resultTitle">결과</div>
                  <div className="resultSub" id="result-sub">
                    {virtualTryOnAPI.lastResultFile
                      ? `최근 결과 파일: ${virtualTryOnAPI.lastResultFile}`
                      : "입어보기를 실행하면 아래에서 바로 확인할 수 있어요."}
                  </div>
                </div>
                <div className="resultActions">
                  <button 
                    id="clear-results" 
                    type="button" 
                    className="btn ghost sm"
                    onClick={virtualTryOnAPI.clearResults}
                  >
                    결과 초기화
                  </button>
                  <button 
                    id="refresh-results" 
                    type="button" 
                    className="btn ghost"
                    onClick={() => virtualTryOnAPI.refreshResults(resultSession, true)}
                  >
                    결과 새로고침
                  </button>
                </div>
              </div>

              <div className="resultGrid">
                <div className="resultCard">
                  <div className="resultLabel">적용된 사진</div>
                  <div className="resultBox" id="result-box">
                    {resultImageSrc ? (
                      <img className="resultImg" src={resultImageSrc} alt="적용된 사진" />
                    ) : (
                      <div className="placeholder">아직 결과가 없습니다</div>
                    )}
                  </div>
                </div>
                <div className="resultMeta">
                  <div className="metaRow">
                    <div className="metaKey">선택한 상품 번호</div>
                    <div className="metaVal">{selectedProductId ?? "-"}</div>
                  </div>
                  <div className="metaRow">
                    <div className="metaKey">세션</div>
                    <div className="metaVal">{resultSession || "web_demo"}</div>
                  </div>
                  <div className="metaRow">
                    <div className="metaKey">팁</div>
                    <div className="metaVal muted">
                      상품 페이지에서 번호로 검색해 다시 찾아갈 수 있어요.
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </section>
        )}

        {tab === "products" && (
          <section className="products">
            <div className="productsHeader">
              <div className="categoryRow">
                <button
                  type="button"
                  className={`segBtn ${category === "001" ? "active" : ""}`}
                  onClick={() => setCategory("001")}
                >
                  상의
                </button>
                <button
                  type="button"
                  className={`segBtn ${category === "002" ? "active" : ""}`}
                  onClick={() => setCategory("002")}
                >
                  아우터
                </button>
                <button
                  type="button"
                  className={`segBtn ${category === "user" ? "active" : ""}`}
                  onClick={() => setCategory("user")}
                >
                  내 옷
                </button>
              </div>
              <div className="searchWrap">
                <input
                  className="searchInput"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={category === "user" ? "옷 이름으로 검색" : "상품 번호로 검색 (예: 1116155)"}
                  inputMode={category === "user" ? "text" : "numeric"}
                />
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() => setSearch("")}
                >
                  초기화
                </button>
                {category === "user" && (
                  <button
                    type="button"
                    className="btn primary sm"
                    onClick={() => setShowClothUploadModal(true)}
                  >
                    옷 추가
                  </button>
                )}
              </div>
            </div>

            <div className="grid">
              {clothLoading ? (
                <div className="muted">상품 불러오는 중...</div>
              ) : filteredClothes.length === 0 ? (
                <div className="muted">
                  검색 결과가 없습니다. 다른 번호로 검색해 주세요.
                </div>
              ) : (
                filteredClothes.map((rel) => {
                  let pid, src;
                  
                  if (category === "user") {
                    // 사용자 업로드 옷
                    pid = rel.replace(/\.[^.]+$/, ""); // 확장자 제거
                    src = `${API_BASE}/static/uploads/cloth/${rel}?t=${Date.now()}`; // 캐시 방지
                    console.log('User cloth image URL:', src); // 디버깅 로그
                  } else {
                    // 기존 카테고리 옷
                    pid = rel.split("/")[1]?.replace(/\.[^.]+$/, "") ?? rel;
                    src = `${API_BASE}/static/clothing_only/${rel}`;
                    console.log('Category cloth image URL:', src); // 디버깅 로그
                  }
                  
                  return (
                    <div key={rel} className="gridItemContainer">
                      <button
                        type="button"
                        className={`gridItem ${fileUpload.selectedCloth === rel ? "selected" : ""}`}
                        onClick={() => {
                          fileUpload.handleClothSelect(rel);
                          setTab("main"); // 선택 후 메인 탭으로 이동
                        }}
                      >
                        <img 
                          className="cardImg" 
                          src={src} 
                          alt={pid} 
                          loading="lazy"
                          onError={(e) => {
                            console.error('Image load failed:', src);
                            // 대체 이미지 또는 플레이스홀더 표시
                            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+이W1lcGd8PC90ZXh0Pjwvc3ZnPg==';
                          }}
                        />
                        <div className="cardLabel">{pid}</div>
                      </button>
                      {category === "user" && (
                        <button
                          className="deleteBtn"
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (confirm(`"${pid}" 옷을 삭제하시겠습니까?`)) {
                              const success = await virtualTryOnAPI.deleteUserCloth(rel);
                              if (success) {
                                // 목록 새로고침
                                const fetchClothes = async () => {
                                  try {
                                    setClothLoading(true);
                                    const res = await axios.get<string[]>(`${API_BASE}/uploads/user-clothes`);
                                    setClothList(res.data);
                                  } catch (e) {
                                    console.error(e);
                                    setClothList([]);
                                  } finally {
                                    setClothLoading(false);
                                  }
                                };
                                fetchClothes();
                              }
                            }
                          }}
                          title="옷 삭제"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </section>
        )}

        {/* 옷 업로드 모달 */}
        {showClothUploadModal && (
          <div className="modal" onClick={() => setShowClothUploadModal(false)}>
            <div className="modalContent" onClick={(e) => e.stopPropagation()}>
              <div className="modalHeader">
                <h3>옷 이미지 업로드</h3>
                <button className="btn ghost" onClick={() => setShowClothUploadModal(false)}>&times;</button>
              </div>
              <div className="modalBody">
                <div className="uploadArea"
                     onDragOver={(e) => e.preventDefault()}
                     onDrop={async (e) => {
                       e.stopPropagation();
                       const files = e.dataTransfer.files;
                       if (files.length > 0) {
                         const file = files[0];
                         fileUpload.handleClothUpload(file);
                         try {
                           await virtualTryOnAPI.uploadClothImage(file);
                           // 내 옷 카테고리인 경우 목록 새로고침
                           if (category === "user") {
                             const fetchClothes = async () => {
                               try {
                                 setClothLoading(true);
                                 const res = await axios.get<string[]>(`${API_BASE}/uploads/user-clothes`);
                                 setClothList(res.data);
                               } catch (e) {
                                 console.error(e);
                                 setClothList([]);
                               } finally {
                                 setClothLoading(false);
                               }
                             };
                             fetchClothes();
                           }
                         } catch (error) {
                           console.error('Cloth image upload failed:', error);
                         }
                       }
                       setShowClothUploadModal(false);
                     }}
                     onClick={() => clothFileInputModalRef.current?.click()}>
                  <div className="uploadPlaceholder">
                    <div>클릭하거나 드래그하여 옷 이미지를 업로드하세요</div>
                    <small>지원 형식: JPG, PNG, WEBP</small>
                  </div>
                  <input
                    ref={clothFileInputModalRef}
                    type="file"
                    accept="image/*"
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        fileUpload.handleClothUpload(file);
                        try {
                          await virtualTryOnAPI.uploadClothImage(file);
                          // 내 옷 카테고리인 경우 목록 새로고침
                          if (category === "user") {
                            const fetchClothes = async () => {
                              try {
                                setClothLoading(true);
                                const res = await axios.get<string[]>(`${API_BASE}/uploads/user-clothes`);
                                setClothList(res.data);
                              } catch (e) {
                                console.error(e);
                                setClothList([]);
                              } finally {
                                setClothLoading(false);
                              }
                            };
                            fetchClothes();
                          }
                        } catch (error) {
                          console.error('Cloth image upload failed:', error);
                        }
                        setShowClothUploadModal(false);
                      }
                    }}
                    style={{ display: 'none' }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
