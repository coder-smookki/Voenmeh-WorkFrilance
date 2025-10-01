from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.work_file import WorkFile
from typing import List

class WorkFileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_work_file(self, student_work_id: int, file_field: str, 
                             original_filename: str, file_path: str, file_size: int) -> WorkFile:
        work_file = WorkFile(
            student_work_id=student_work_id,
            file_field=file_field,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size
        )
        self.session.add(work_file)
        await self.session.flush()
        return work_file
    
    async def get_files_by_student_work(self, student_work_id: int) -> List[WorkFile]:
        stmt = select(WorkFile).where(WorkFile.student_work_id == student_work_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    # Оставляем старый метод для обратной совместимости
    async def get_files_by_bachelor(self, bachelor_id: int) -> List[WorkFile]:
        return await self.get_files_by_student_work(bachelor_id)