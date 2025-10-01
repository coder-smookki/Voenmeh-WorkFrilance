# database/repo/pending_submission.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.pending_submission import PendingSubmission
from typing import Optional

class PendingSubmissionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_pending_submission(self, submission_id: str, user_id: int, username: str, 
                                      first_name: str, subject: str, lvl_education: str, 
                                      course: str, work_name: str, files_data: str = None) -> PendingSubmission:
        submission = PendingSubmission(
            submission_id=submission_id,
            user_id=user_id,
            username=username,
            first_name=first_name,
            subject=subject,
            lvl_education=lvl_education,
            course=course,
            work_name=work_name,
            files_data=files_data
        )
        self.session.add(submission)
        await self.session.flush()
        return submission
    
    async def get_by_submission_id(self, submission_id: str) -> Optional[PendingSubmission]:
        stmt = select(PendingSubmission).where(PendingSubmission.submission_id == submission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete(self, submission_id: int) -> None:
        submission = await self.session.get(PendingSubmission, submission_id)
        if submission:
            await self.session.delete(submission)