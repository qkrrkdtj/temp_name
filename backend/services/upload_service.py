from pathlib import Path
import aiofiles
from typing import List
import time

from ..models import UploadResponse

class UploadService:
    def __init__(self):
        from ..main import BASE_DIR, PROCESSING_TMP_DIR, UPLOAD_USER_DIR
        self.base_dir = BASE_DIR
        self.processing_tmp_dir = PROCESSING_TMP_DIR
        self.upload_user_dir = UPLOAD_USER_DIR
        self.cloth_dir = BASE_DIR / "uploads" / "cloth"
        
        # 디렉토리 생성
        self.cloth_dir.mkdir(parents=True, exist_ok=True)

    async def process_user_image(self, file: UploadFile) -> str:
        """사용자 이미지 업로드 및 전처리"""
        from ..main import preprocess_user_image
        
        # 고유 ID 생성
        upload_id = uuid.uuid4().hex[:12]
        
        # 파일 내용 읽기
        contents = await file.read()
        
        # 임시 파일로 저장
        temp_file = self.processing_tmp_dir / f"{upload_id}_temp.jpg"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(temp_file, 'wb') as f:
            await f.write(contents)
        
        # 전처리 실행
        processed_dir = self.processing_tmp_dir / upload_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        preprocess_user_image(
            input_path=temp_file,
            output_dir=processed_dir,
            person_filename=f"{upload_id}.jpg"
        )
        
        # 임시 파일 삭제
        temp_file.unlink()
        
        return upload_id

    async def save_cloth_image(self, file: UploadFile) -> str:
        """옷 이미지 저장"""
        # 고유 파일명 생성
        timestamp = int(time.time())
        filename = f"user_{timestamp}.jpg"
        
        # 파일 내용 읽기
        contents = await file.read()
        
        # 저장
        cloth_path = self.cloth_dir / filename
        async with aiofiles.open(cloth_path, 'wb') as f:
            await f.write(contents)
        
        return filename

    def get_user_clothes_list(self) -> List[str]:
        """사용자 업로드 옷 목록 조회"""
        clothes = []
        for file_path in self.cloth_dir.glob("*.jpg"):
            clothes.append(file_path.name)
        
        # 최신순으로 정렬
        clothes.sort(reverse=True)
        return clothes

    def delete_user_cloth(self, filename: str) -> bool:
        """사용자 옷 삭제"""
        cloth_path = self.cloth_dir / filename
        
        if not cloth_path.exists():
            return False
        
        cloth_path.unlink()
        return True
