import os
import shutil
import zipfile
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
from app.core.errors import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    InvalidArchiveError
)

def _get_allowed_extensions():
    return getattr(settings, "ALLOWED_EXTENSIONS", getattr(settings, "ALLOWED_EXTENSION", {".zip", ".kml"}))

def _get_max_size():
    return getattr(settings, "MAX_UPLOAD_SIZE_BYTES", getattr(settings, "MAX_UPLOAD_SIZE_MB", 10 * 1024 * 1024))

def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in _get_allowed_extensions():
        raise UnsupportedFileTypeError(f"Unsupported file type. Allowed: {_get_allowed_extensions()}")
    return ext

def save_upload(upload_file: UploadFile, file_id: str) -> Path:
    ext = validate_extension(upload_file.filename or "")
    
    upload_dir = settings.UPLOAD_DIR / file_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    fixed_name = "source" + ext
    dest_path = upload_dir / fixed_name
    
    max_size = _get_max_size()
    
    bytes_written = 0
    try:
        with open(dest_path, "wb") as f:
            while chunk := upload_file.file.read(8192):
                if not isinstance(chunk, bytes):
                    # In case of async upload file read
                    pass
                bytes_written += len(chunk)
                if bytes_written > max_size:
                    raise FileTooLargeError("File exceeds maximum allowed size")
                f.write(chunk)
    except FileTooLargeError:
        cleanup_dir(upload_dir)
        raise
    except Exception as e:
        cleanup_dir(upload_dir)
        raise e
        
    return dest_path

def extract_shapefile_zip(zip_path: Path, dest_dir: Path) -> Path:
    dest_dir = dest_dir.resolve()
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.namelist()
            
            shp_files = []
            has_shx = False
            has_dbf = False
            
            # zip bomb protection
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > 200 * 1024 * 1024:
                raise InvalidArchiveError("Archive extracts to over 200MB, too large.")
            
            for member in members:
                # zip-slip prevention
                member_path = (dest_dir / member).resolve()
                if not member_path.is_relative_to(dest_dir):
                    raise InvalidArchiveError(f"Zip slip detected for member: {member}")
                
                lower_name = member.lower()
                if lower_name.endswith('.shp'):
                    shp_files.append(member)
                elif lower_name.endswith('.shx'):
                    has_shx = True
                elif lower_name.endswith('.dbf'):
                    has_dbf = True

            if len(shp_files) == 0:
                raise InvalidArchiveError("Archive does not contain a .shp file")
            if len(shp_files) > 1:
                raise InvalidArchiveError("Archive contains multiple .shp files")
            if not has_shx or not has_dbf:
                raise InvalidArchiveError("Archive is missing required .shx or .dbf files")
            
            zf.extractall(path=dest_dir)
            
            return dest_dir / shp_files[0]
            
    except zipfile.BadZipFile:
        raise InvalidArchiveError("Invalid zip archive")

def cleanup_dir(path: Path):
    shutil.rmtree(path, ignore_errors=True)
