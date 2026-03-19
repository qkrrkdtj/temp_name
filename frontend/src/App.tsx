import React, { useEffect, useMemo, useState, useRef, useCallback } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

type Tab = "main" | "products";
type Category = "all" | "user";

function App() {
  const [tab, setTab] = useState<Tab>("main");

  const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
  const [userImageFile, setUserImageFile] = useState<File | null>(null);

  const [selectedCloth, setSelectedCloth] = useState<string | null>(null);
  const [userClothFile, setUserClothFile] = useState<File | null>(null);

  const [showClothUploadModal, setShowClothUploadModal] = useState(false);

  const [category, setCategory] = useState<Category>("all");
  const [clothList, setClothList] = useState<string[]>([]);
  const [clothLoading, setClothLoading] = useState(false);
  const [search, setSearch] = useState("");

  const [running, setRunning] = useState(false);

  const [serverMessage, setServerMessage] = useState<string>("");
  const [resultImageUrl, setResultImageUrl] = useState<string | null>(null);

  const userFileInputRef = useRef<HTMLInputElement>(null);
  const clothFileInputRef = useRef<HTMLInputElement>(null);
  const clothFileInputModalRef = useRef<HTMLInputElement>(null);

  const selectedProductId = useMemo(() => {
    if (!selectedCloth) return null;
    const file = selectedCloth.split("/").pop() ?? selectedCloth;
    return file.replace(/\.[^.]+$/, "");
  }, [selectedCloth]);

  const clothSrc = useMemo(() => {
    if (userClothFile) {
      return URL.createObjectURL(userClothFile);
    }
    if (!selectedCloth) return null;
    return `${API_BASE}/static/cloth/${selectedCloth}`;
  }, [selectedCloth, userClothFile]);

  const filteredClothes = useMemo(() => {
    const q = search.trim();
    if (!q) return clothList;

    return clothList.filter((fileName) => {
      const id = fileName.replace(/\.[^.]+$/, "");
      return id.includes(q);
    });
  }, [clothList, search]);

  useEffect(() => {
    return () => {
      if (userImageUrl) URL.revokeObjectURL(userImageUrl);
    };
  }, [userImageUrl]);

  useEffect(() => {
    return () => {
      if (userClothFile && clothSrc?.startsWith("blob:")) {
        URL.revokeObjectURL(clothSrc);
      }
    };
  }, [userClothFile, clothSrc]);

  useEffect(() => {
    const fetchClothes = async () => {
      if (tab !== "products") return;

      if (category === "user") {
        setClothList([]);
        return;
      }

      try {
        setClothLoading(true);

        const res = await axios.get<{ files: string[]; count: number }>(
          `${API_BASE}/clothing/list`,
          {
            params: { limit: 3000 }
          }
        );

        setClothList(res.data.files ?? []);
      } catch (e) {
        console.error("상품 목록 로딩 실패:", e);
        setClothList([]);
      } finally {
        setClothLoading(false);
      }
    };

    void fetchClothes();
  }, [tab, category]);

  const handleUserImageUpload = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("이미지 파일만 업로드할 수 있습니다.");
      return;
    }

    if (userImageUrl) URL.revokeObjectURL(userImageUrl);
    setUserImageFile(file);
    setUserImageUrl(URL.createObjectURL(file));
  }, [userImageUrl]);

  const handleClothUpload = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("이미지 파일만 업로드할 수 있습니다.");
      return;
    }

    setUserClothFile(file);
    setSelectedCloth(null);
    setTab("main");
  }, []);

  const handleClothSelect = useCallback((fileName: string) => {
    setSelectedCloth(fileName);
    setUserClothFile(null);
    setTab("main");
  }, []);

  const onPickUserImage = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleUserImageUpload(file);
    }
  }, [handleUserImageUpload]);

  const handleClothFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleClothUpload(file);
    }
  }, [handleClothUpload]);

  const handleUserDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleUserImageUpload(files[0]);
    }
  }, [handleUserImageUpload]);

  const handleClothDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleClothUpload(files[0]);
    }
  }, [handleClothUpload]);

  const runViton = useCallback(async () => {
    if (!userImageFile) {
      alert("사용자 사진을 먼저 업로드해 주세요.");
      return;
    }

    if (!userClothFile && !selectedCloth) {
      alert("옷을 선택하거나 업로드해 주세요.");
      return;
    }

    try {
      setRunning(true);
      setServerMessage("");
      setResultImageUrl(null);

      const formData = new FormData();
      formData.append("person_image", userImageFile);

      if (userClothFile) {
        formData.append("cloth_image", userClothFile);
      } else if (selectedCloth) {
        formData.append("cloth_id", selectedCloth);
      }

      const res = await axios.post(`${API_BASE}/tryon`, formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      setServerMessage(res.data.message || "실행 완료");
      setResultImageUrl(
        res.data.result_image_url
          ? `${API_BASE}${res.data.result_image_url}?t=${Date.now()}`
          : null
      );

      document.getElementById("result-section")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    } catch (e: any) {
      console.error(e);
      setResultImageUrl(null);

      const detail = e?.response?.data?.detail;
      if (detail) {
        if (typeof detail === "string") {
          setServerMessage(detail);
          alert(detail);
        } else {
          setServerMessage(detail.message || "pipeline execution failed");
          alert(detail.message || "서버 실행 중 오류가 발생했습니다.");
        }
      } else {
        alert("전처리 실행 중 오류가 발생했습니다. 백엔드 서버를 확인해 주세요.");
      }
    } finally {
      setRunning(false);
    }
  }, [userImageFile, userClothFile, selectedCloth]);

  const NavButton = ({
    id,
    children
  }: {
    id: Tab;
    children: React.ReactNode;
  }) => (
    <button
      className={`navBtn ${tab === id ? "active" : ""}`}
      onClick={() => setTab(id)}
      type="button"
    >
      {children}
    </button>
  );

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <div className="logoMark">NT</div>
          <div className="brandText">
            <div className="brandName">Nice Try</div>
            <div className="brandSub">가상 피팅 데모</div>
          </div>
        </div>
        <nav className="nav">
          <NavButton id="main">메인</NavButton>
          <NavButton id="products">상품</NavButton>
        </nav>
      </header>

      <main className="content">
        {tab === "main" && (
          <section>
            <div className="hero">
              <div className="heroTitle">원하는 옷을 골라 빠르게 "입어보기"</div>
              <div className="heroDesc">
                가상 피팅 결과를 확인할 수 있습니다.
              </div>
            </div>

            <div className="mainGrid">
              <div className="card">
                <div className="cardHeader">
                  <div className="cardTitle">내 사진</div>
                  <div className="cardHint">사진을 올리거나 드래그하세요</div>
                </div>
                <div
                  className="frame"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleUserDrop}
                  onClick={() => userFileInputRef.current?.click()}
                >
                  {userImageUrl ? (
                    <img className="previewImg" src={userImageUrl} alt="사용자 업로드" />
                  ) : (
                    <div className="placeholder">사용자 사진 업로드</div>
                  )}
                </div>
                <div className="cardFooter">
                  <input
                    ref={userFileInputRef}
                    className="fileInput"
                    type="file"
                    accept="image/*"
                    onChange={onPickUserImage}
                  />
                </div>
              </div>

              <div className="card">
                <div className="cardHeader">
                  <div className="cardTitle">선택한 옷</div>
                  <div className="cardHint">
                    {selectedProductId
                      ? `상품 번호: ${selectedProductId}`
                      : userClothFile
                        ? `업로드한 옷: ${userClothFile.name}`
                        : "옷을 선택하거나 파일을 업로드하세요"}
                  </div>
                </div>
                <div
                  className="frame"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleClothDrop}
                  onClick={() => clothFileInputRef.current?.click()}
                >
                  {clothSrc || userClothFile ? (
                    <img className="previewImg" src={clothSrc || ""} alt="선택된 옷" />
                  ) : (
                    <div className="placeholder">옷을 선택하거나 드래그하여 업로드하세요</div>
                  )}
                </div>
                <div className="cardFooter">
                  <input
                    ref={clothFileInputRef}
                    className="fileInput"
                    type="file"
                    accept="image/*"
                    onChange={handleClothFileInput}
                  />
                  <button
                    type="button"
                    className="btn ghost"
                    onClick={() => setTab("products")}
                  >
                    옷 고르기
                  </button>

                  <button
                    type="button"
                    className="btn primary"
                    onClick={runViton}
                    disabled={running}
                  >
                    {running ? "생성 중..." : "입어보기"}
                  </button>
                </div>
              </div>
            </div>

            <section id="result-section" className="resultSection" aria-label="결과">
              <div className="resultHeader">
                <div>
                  <div className="resultTitle">서버 실행 결과</div>
                  <div className="resultSub">
                    가상 피팅 결과를 확인할 수 있습니다.
                  </div>
                </div>
              </div>

              <div className="resultCard" style={{ marginTop: "16px" }}>
                <div className="resultLabel">실행 상태</div>

                {resultImageUrl && (
                  <div style={{ marginBottom: "20px" }}>
                    <strong>가상 피팅 결과</strong>
                    <div
                      style={{
                        marginTop: "8px",
                        padding: "12px",
                        border: "1px solid #ddd",
                        borderRadius: "12px",
                        background: "#fff"
                      }}
                    >
                      <img
                        src={resultImageUrl}
                        alt="가상 피팅 결과"
                        style={{
                          display: "block",
                          width: "100%",
                          maxWidth: "420px",
                          borderRadius: "12px",
                          margin: "0 auto"
                        }}
                      />
                    </div>
                  </div>
                )}

                <div style={{ marginBottom: "16px" }}>
                  <strong>메시지</strong>
                  <div
                    style={{
                      marginTop: "8px",
                      padding: "12px",
                      border: "1px solid #ddd",
                      borderRadius: "12px",
                      background: "#fff"
                    }}
                  >
                    {serverMessage || "-"}
                  </div>
                </div>
              </div>

              <div className="resultGrid" style={{ marginTop: "16px" }}>
                <div className="resultMeta">
                  <div className="metaRow">
                    <div className="metaKey">선택한 상품 번호</div>
                    <div className="metaVal">
                      {selectedProductId ?? (userClothFile ? "내 옷 업로드" : "-")}
                    </div>
                  </div>
                  <div className="metaRow">
                    <div className="metaKey">사용자 사진</div>
                    <div className="metaVal">{userImageFile ? userImageFile.name : "-"}</div>
                  </div>
                  <div className="metaRow">
                    <div className="metaKey">옷 이미지</div>
                    <div className="metaVal">
                      {userClothFile ? userClothFile.name : selectedCloth ?? "-"}
                    </div>
                  </div>
                  <div className="metaRow">
                    <div className="metaKey">상태</div>
                    <div className="metaVal muted">
                      {running ? "가상 피팅 생성 중..." : "가상 피팅 결과 표시 가능"}
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
                  className={`segBtn ${category === "user" ? "active" : ""}`}
                  onClick={() => setCategory("user")}
                >
                  내 옷
                </button>
                <button
                  type="button"
                  className={`segBtn ${category === "all" ? "active" : ""}`}
                  onClick={() => setCategory("all")}
                >
                  상의
                </button>
              </div>

              <div className="searchWrap">
                <button
                  type="button"
                  className="btn primary"
                  onClick={() => setShowClothUploadModal(true)}
                >
                  + 옷 업로드
                </button>
                <input
                  className="searchInput"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="상품 번호로 검색"
                />
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() => setSearch("")}
                >
                  초기화
                </button>
              </div>
            </div>

            <div className="grid">
              {category === "user" ? (
                userClothFile ? (
                  <div className="cardItem selected" onClick={() => setTab("main")}>
                    <img className="cardImg" src={clothSrc || ""} alt="내 옷" />
                    <div className="cardLabel">내 옷</div>
                  </div>
                ) : (
                  <div className="muted">업로드한 옷이 없습니다. '+ 옷 업로드' 버튼을 눌러 주세요.</div>
                )
              ) : clothLoading ? (
                <div className="muted">옷 불러오는 중...</div>
              ) : filteredClothes.length === 0 ? (
                <div className="muted">검색 결과가 없습니다.</div>
              ) : (
                filteredClothes.map((fileName) => {
                  const pid = fileName.replace(/\.[^.]+$/, "");
                  const src = `${API_BASE}/static/cloth/${fileName}`;

                  return (
                    <button
                      key={fileName}
                      type="button"
                      className={`cardItem ${selectedCloth === fileName ? "selected" : ""}`}
                      onClick={() => handleClothSelect(fileName)}
                    >
                      <img className="cardImg" src={src} alt={pid} loading="lazy" />
                      <div className="cardLabel">{pid}</div>
                    </button>
                  );
                })
              )}
            </div>
          </section>
        )}

        {showClothUploadModal && (
          <div className="modal" onClick={() => setShowClothUploadModal(false)}>
            <div className="modalContent" onClick={(e) => e.stopPropagation()}>
              <div className="modalHeader">
                <h3>옷 이미지 업로드</h3>
                <button className="btn ghost" onClick={() => setShowClothUploadModal(false)}>
                  &times;
                </button>
              </div>
              <div className="modalBody">
                <div
                  className="uploadArea"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    handleClothDrop(e);
                    setShowClothUploadModal(false);
                  }}
                  onClick={() => clothFileInputModalRef.current?.click()}
                >
                  <div className="uploadPlaceholder">
                    <div>클릭하거나 드래그하여 옷 이미지를 업로드하세요</div>
                    <small>지원 형식: JPG, PNG, WEBP</small>
                  </div>
                  <input
                    ref={clothFileInputModalRef}
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      handleClothFileInput(e);
                      setShowClothUploadModal(false);
                    }}
                    style={{ display: "none" }}
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