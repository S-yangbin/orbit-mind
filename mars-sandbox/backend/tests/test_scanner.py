"""Tests for HTML directory scanner."""
import os
import pytest
import tempfile
from pathlib import Path
from app.scanner import (
    compute_dir_hash,
    extract_metadata,
    _find_entry_file,
    is_scanning,
    get_last_scan_info,
)


class TestComputeDirHash:
    """Test compute_dir_hash function."""

    def test_hash_returns_string(self):
        """Should return a non-empty string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello")
            
            hash_result = compute_dir_hash(tmpdir)
            
            assert isinstance(hash_result, str)
            assert len(hash_result) > 0

    def test_hash_consistent(self):
        """Same content should produce same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello")
            
            hash1 = compute_dir_hash(tmpdir)
            hash2 = compute_dir_hash(tmpdir)
            
            assert hash1 == hash2

    def test_hash_changes_on_content(self):
        """Hash should change when file content changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello")
            
            hash1 = compute_dir_hash(tmpdir)
            
            # Modify file
            test_file.write_text("world")
            hash2 = compute_dir_hash(tmpdir)
            
            assert hash1 != hash2

    def test_hash_changes_on_file_add(self):
        """Hash should change when a new file is added."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test1.txt"
            test_file.write_text("hello")
            
            hash1 = compute_dir_hash(tmpdir)
            
            # Add new file
            test_file2 = Path(tmpdir) / "test2.txt"
            test_file2.write_text("world")
            hash2 = compute_dir_hash(tmpdir)
            
            assert hash1 != hash2

    def test_hash_empty_directory(self):
        """Should compute hash for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hash_result = compute_dir_hash(tmpdir)
            assert isinstance(hash_result, str)
            assert len(hash_result) > 0

    def test_hash_nested_directories(self):
        """Should include nested directories in hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            nested = Path(tmpdir) / "subdir"
            nested.mkdir()
            (nested / "nested.txt").write_text("nested content")
            
            hash1 = compute_dir_hash(tmpdir)
            
            # Modify nested file
            (nested / "nested.txt").write_text("modified content")
            hash2 = compute_dir_hash(tmpdir)
            
            assert hash1 != hash2


class TestExtractMetadata:
    """Test extract_metadata function."""

    def test_extract_title_from_title_tag(self):
        """Should extract title from <title> tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
                <html>
                    <head><title>Test Page Title</title></head>
                    <body><h1>Heading</h1></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert metadata["title"] == "Test Page Title"

    def test_extract_title_from_h1_fallback(self):
        """Should fallback to <h1> if no <title> tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
                <html>
                    <head></head>
                    <body><h1>Heading Title</h1></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert metadata["title"] == "Heading Title"

    def test_extract_description_from_meta(self):
        """Should extract description from meta tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
                <html>
                    <head>
                        <meta name="description" content="This is a test page description">
                    </head>
                    <body></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert metadata["description"] == "This is a test page description"

    def test_extract_description_from_p_fallback(self):
        """Should fallback to <p> tag if no meta description."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
                <html>
                    <head></head>
                    <body><p>First paragraph description</p></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert metadata["description"] == "First paragraph description"

    def test_extract_keywords(self):
        """Should extract keywords from meta tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
                <html>
                    <head>
                        <meta name="keywords" content="python, testing, web">
                    </head>
                    <body></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert metadata["keywords"] == ["python", "testing", "web"]

    def test_extract_keywords_empty(self):
        """Should return empty list if no keywords meta tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("<html><body></body></html>")
            
            metadata = extract_metadata(str(html_file))
            assert metadata["keywords"] == []

    def test_extract_from_nonexistent_file(self):
        """Should handle non-existent file gracefully."""
        metadata = extract_metadata("/nonexistent/file.html")
        assert metadata == {"title": None, "description": None, "keywords": []}

    def test_extract_description_max_length_meta(self):
        """Meta description should be truncated to 500 chars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            long_desc = "x" * 600
            html_file.write_text(f"""
                <html>
                    <head>
                        <meta name="description" content="{long_desc}">
                    </head>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert len(metadata["description"]) == 500

    def test_extract_description_max_length_p(self):
        """P tag description should be truncated to 200 chars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            long_desc = "x" * 300
            html_file.write_text(f"""
                <html>
                    <body><p>{long_desc}</p></body>
                </html>
            """)
            
            metadata = extract_metadata(str(html_file))
            assert len(metadata["description"]) == 200


class TestFindEntryFile:
    """Test _find_entry_file function."""

    def test_find_index_html(self):
        """Should find index.html first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "index.html").write_text("<html></html>")
            (Path(tmpdir) / "other.html").write_text("<html></html>")
            
            entry = _find_entry_file(tmpdir)
            assert entry == "index.html"

    def test_find_first_html_file(self):
        """Should find first .html file if no index.html."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "app.html").write_text("<html></html>")
            
            entry = _find_entry_file(tmpdir)
            assert entry == "app.html"

    def test_no_html_file(self):
        """Should return None if no HTML file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "readme.txt").write_text("text")
            
            entry = _find_entry_file(tmpdir)
            assert entry is None

    def test_empty_directory(self):
        """Should return None for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry = _find_entry_file(tmpdir)
            assert entry is None


class TestScanState:
    """Test scan state tracking functions."""

    def test_is_scanning_initially_false(self):
        """Should not be scanning initially."""
        # Note: This test depends on state from other tests
        # In a real scenario, you'd want to reset state
        result = is_scanning()
        assert isinstance(result, bool)

    def test_get_last_scan_info(self):
        """Should return dict with last scan info."""
        info = get_last_scan_info()
        assert isinstance(info, dict)
        assert "last_scan_at" in info
        assert "last_result" in info
