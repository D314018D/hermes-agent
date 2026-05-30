import importlib.util
import sys
from pathlib import Path


def _load_sibling(module_name: str):
    path = Path(__file__).parent / f"{module_name}.py"
    qualified_name = f"codex_delegate_plugin_{module_name}"
    existing = sys.modules.get(qualified_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(qualified_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


schemas = _load_sibling("schemas")


def _load_delegate_module():
    path = Path(__file__).parent / "tools" / "codex_delegate.py"
    qualified_name = "codex_delegate_plugin_tool"
    existing = sys.modules.get(qualified_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(qualified_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


def codex_delegate(args: dict, **kwargs) -> str:
    import json

    delegate_module = _load_delegate_module()
    context = delegate_module.ContextPack.from_mapping(args or {})
    result = delegate_module.delegate(context)
    return json.dumps(result, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(
        name="codex_delegate",
        toolset="codex-delegate",
        schema=schemas.CODEX_DELEGATE,
        handler=codex_delegate,
    )
