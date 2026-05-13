def parse_document(file_path: str, mime_type: str | None = None) -> str:
    """Local document parsing hook for future document sources."""
    raise NotImplementedError("Document parser backend is not configured")
