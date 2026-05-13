import importlib.util
import sys
from pathlib import Path


def _load_sibling(module_name: str):
    path = Path(__file__).parent / f"{module_name}.py"
    qualified_name = f"obsidian_gbrain_{module_name}"
    existing = sys.modules.get(qualified_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(qualified_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


schemas = _load_sibling("schemas")
tools = _load_sibling("tools")


def register(ctx):
    ctx.register_tool(
        name="obsidian_ingest",
        toolset="obsidian-gbrain",
        schema=schemas.OBSIDIAN_INGEST,
        handler=tools.obsidian_ingest,
    )
    ctx.register_tool(
        name="gbrain_import",
        toolset="obsidian-gbrain",
        schema=schemas.GBRAIN_IMPORT,
        handler=tools.gbrain_import,
    )
    ctx.register_tool(
        name="gbrain_maintain",
        toolset="obsidian-gbrain",
        schema=schemas.GBRAIN_MAINTAIN,
        handler=tools.gbrain_maintain,
    )
    ctx.register_tool(
        name="gbrain_query",
        toolset="obsidian-gbrain",
        schema=schemas.GBRAIN_QUERY,
        handler=tools.gbrain_query,
    )

    skill_path = Path(__file__).parent / "skills" / "obsidian-gbrain-workflow" / "SKILL.md"
    if skill_path.exists():
        ctx.register_skill("obsidian-gbrain-workflow", skill_path)
