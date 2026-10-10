import pytest
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
from app.services.upload_service import (
    validate_extension,
    save_upload,
    extract_shapefile_zip,
    cleanup_dir
)
from app.core.errors import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    InvalidArchiveError
)

def test_validate_extension():
    assert validate_extension("test.zip") == ".zip"
    assert validate_extension("TEST.KML") == ".kml"
    
    with pytest.raises(UnsupportedFileTypeError):
        validate_extension("test.txt")
    with pytest.raises(UnsupportedFileTypeError):
        validate_extension("test.geojson")
    with pytest.raises(UnsupportedFileTypeError):
        validate_extension("no_extension")

def test_save_upload(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.upload_service.settings.UPLOAD_DIR", tmp_path)
    
    content = b"kml content"
    upload_file = UploadFile(filename="survey.kml", file=BytesIO(content))
    
    saved_path = save_upload(upload_file, "file-123")
    assert saved_path == tmp_path / "file-123" / "source.kml"
    assert saved_path.read_bytes() == content

def test_save_upload_too_large(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.upload_service.settings.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.services.upload_service._get_max_size", lambda: 5)
    
    content = b"this is larger than 5 bytes"
    upload_file = UploadFile(filename="big.zip", file=BytesIO(content))
    
    with pytest.raises(FileTooLargeError):
        save_upload(upload_file, "file-456")
        
    assert not (tmp_path / "file-456" / "source.zip").exists()

def test_extract_shapefile_zip(shapefile_zip, tmp_path):
    dest_dir = tmp_path / "extract_ok"
    dest_dir.mkdir()
    
    shp_path = extract_shapefile_zip(shapefile_zip, dest_dir)
    assert shp_path.exists()
    assert shp_path.suffix == ".shp"

def test_extract_zip_slip(zip_slip_archive, tmp_path):
    dest_dir = tmp_path / "extract_slip"
    dest_dir.mkdir()
    
    with pytest.raises(InvalidArchiveError, match="Zip slip"):
        extract_shapefile_zip(zip_slip_archive, dest_dir)
        
    assert not (tmp_path / "evil.txt").exists()

def test_extract_missing_dbf(tmp_path):
    import zipfile
    bad_zip = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_zip, 'w') as zf:
        zf.writestr("test.shp", "shp data")
        zf.writestr("test.shx", "shx data")
        # missing .dbf
        
    dest_dir = tmp_path / "extract_missing"
    dest_dir.mkdir()
    
    with pytest.raises(InvalidArchiveError, match="missing required .shx or .dbf files"):
        extract_shapefile_zip(bad_zip, dest_dir)

def test_extract_not_a_zip(not_a_zip, tmp_path):
    dest_dir = tmp_path / "extract_not_zip"
    dest_dir.mkdir()
    
    with pytest.raises(InvalidArchiveError, match="Invalid zip archive"):
        extract_shapefile_zip(not_a_zip, dest_dir)

def test_cleanup_dir(tmp_path):
    target = tmp_path / "todel"
    target.mkdir()
    (target / "file.txt").write_text("hello")
    cleanup_dir(target)
    assert not target.exists()
    
    cleanup_dir(tmp_path / "does_not_exist")
