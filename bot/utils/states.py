from aiogram.fsm.state import State, StatesGroup
from collections import deque
import asyncio
from asyncio import Lock


# План чтения работы для предложки(Текст -> Файл -> Подтверждение)
class SubmissionStates(StatesGroup):
    waiting_text = State()
    waiting_files = State()
    waiting_confirmation = State()
    
# Словарь для отправки в предложку
submission_data = {}

# Словарь для отправки заказа
order_data ={}

# План чтения работы для заказа(Текст -> Файл -> Подтверждение)
class OrderStates(StatesGroup):
    waiting_text = State()
    waiting_files = State()
    waiting_confirmation = State()
    waiting_message_to_executor = State()

class RobustUploadManager:
    def __init__(self):
        self.pending_uploads = {} 
        self.next_expected = 1
        self.lock = asyncio.Lock()
    
    async def add_upload(self, order: int, message_data: dict):
        async with self.lock:
            self.pending_uploads[order] = message_data
            return await self._check_sequential_uploads()
    
    async def _check_sequential_uploads(self):
        messages_to_send = []
        
        while self.next_expected in self.pending_uploads:
            messages_to_send.append(self.pending_uploads[self.next_expected])
            del self.pending_uploads[self.next_expected]
            self.next_expected += 1
        
        return messages_to_send
    
    async def wait_for_order(self, order: int, timeout: float = 10.0):
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            async with self.lock:
                if self.next_expected >= order:
                    return True
            await asyncio.sleep(0.1)
        return False

upload_manager = RobustUploadManager()

order_upload_manager = RobustUploadManager()