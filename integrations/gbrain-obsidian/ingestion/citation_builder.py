from .schema import IngestInput


def build_citation(item: IngestInput) -> str:
    parts = [
        f"source_type={item.source_type}",
        f"source_app={item.source_app}",
        f"captured_at={item.captured_at}",
    ]
    if item.attachments:
        links = ", ".join(f"[[attachments/{attachment}]]" for attachment in item.attachments)
        parts.append(f"attachments={links}")
    for key, value in sorted(item.metadata.items()):
        if value:
            parts.append(f"{key}={value}")
    return "; ".join(parts)

