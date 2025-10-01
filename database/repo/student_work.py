from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.student_work import StudentWork
from typing import Optional, List

class StudentWorkRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_work(
        self, 
        education_level: int, 
        course: int, 
        subject: str,
        work_name: str,
        archive_path: str
    ) -> StudentWork:
        work = StudentWork(
            education_level=education_level,
            course=course,
            subject=subject,
            work_name=work_name,
            archive_path=archive_path
        )
        self.session.add(work)
        await self.session.flush()
        await self.session.refresh(work)
        return work
    
    async def get_work_by_id(self, work_id: int) -> Optional[StudentWork]:
        stmt = select(StudentWork).where(StudentWork.id == work_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_works(self) -> List[StudentWork]:
        stmt = select(StudentWork)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_works_by_filters(
        self, 
        education_level: Optional[int] = None,
        course: Optional[int] = None
    ) -> List[StudentWork]:
        stmt = select(StudentWork)
        
        if education_level is not None:
            stmt = stmt.where(StudentWork.education_level == education_level)
        if course is not None:
            stmt = stmt.where(StudentWork.course == course)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()