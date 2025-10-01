import os
import zipfile
import uuid
from pathlib import Path
import tempfile
import asyncio
from aiogram import Bot
import logging
from typing import List, Dict, Tuple

class FileService:
    def __init__(self, uploads_base_path: str = "uploads"):
        self.uploads_base_path = Path(uploads_base_path)
        self.uploads_base_path.mkdir(parents=True, exist_ok=True)
    
    async def process_submission_files(
        self, 
        bot: Bot, 
        files_data: List[Dict[str, any]], 
        user_id: int, 
        work_id: int
    ) -> str:
        """Обработка файлов и создание архива"""
        
        # Создаем директорию для работы
        work_dir = self.uploads_base_path / str(work_id)
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем временную директорию для скачивания файлов
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Скачиваем все файлы во временную директорию
            downloaded_files = []
            for file_info in files_data:
                try:
                    # Получаем file_path из file_id
                    file = await bot.get_file(file_info['id'])
                    file_extension = self._get_file_extension(file_info['type'])
                    
                    # Формируем имя файла
                    base_name = file_info.get('name', 'file')
                    if not any(base_name.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.mp4', '.mp3', '.doc', '.docx']):
                        base_name = f"{base_name}{file_extension}"
                    
                    temp_file_path = temp_path / base_name
                    
                    # Скачиваем файл используя file_path
                    await bot.download_file(file.file_path, temp_file_path)
                    downloaded_files.append((base_name, temp_file_path))
                    
                    logging.info(f"Successfully downloaded file: {base_name}")
                    
                except Exception as e:
                    logging.error(f"Error downloading file {file_info.get('name', 'unknown')}: {e}")
                    continue
            
            if not downloaded_files:
                logging.error(f"No files were downloaded for work_id {work_id}")
                raise Exception("Failed to download any files")
            
            # Создаем ZIP-архив
            archive_name = f"work_{work_id}.zip"
            archive_path = work_dir / archive_name
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for original_name, file_path in downloaded_files:
                    zipf.write(file_path, original_name)
            
            logging.info(f"Archive created: {archive_path}")
            return str(archive_path)
    
    def _get_field_name_by_order(self, order: int) -> str:
        """Определяет название поля по порядковому номеру файла"""
        fields = ['h1_education', 'course', 'discipline', 'file_work']
        return fields[order - 1] if order <= len(fields) else f'additional_{order - len(fields)}'
    
    def _get_file_extension(self, file_type: str) -> str:
        """Возвращает расширение файла по его типу"""
        extensions = {
            'document': '.pdf',
            'photo': '.jpg',
            'video': '.mp4',
            'audio': '.mp3'
        }
        return extensions.get(file_type, '.bin')