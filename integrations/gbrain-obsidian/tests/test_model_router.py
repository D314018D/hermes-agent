from routing.model_router import route_model


def test_default_text_uses_qwen_directly():
    result = route_model("hello")
    assert result.route == "direct_qwen"
    assert result.model == "Qwen2.5-7B-Instruct-4bit"
    assert result.router_model == "Qwen2.5-7B-Instruct-4bit"
    assert result.metadata["selected_by"] == "qwen_brain_router"
    assert result.metadata["switch_main_model"] is False


def test_obsidian_capture_routes_to_ingestion_tool():
    result = route_model("请把这条内容写入 Obsidian inbox")
    assert result.route == "tool_first_obsidian"
    assert result.tool_action == "run_ingest"
    assert result.tool_entrypoint == "python3 scripts/ingest.py -"
    assert result.metadata["should_call_tool"] is True


def test_complex_request_switches_to_hermes():
    result = route_model("please analyze this architecture and implement the refactor")
    assert result.route == "delegate_hermes_complex"
    assert result.model == "Hermes-3-Llama-3.1-8B-4bit"
    assert result.metadata["switch_main_model"] is True


def test_vision_attachment_switches_to_qwen_vl():
    result = route_model("what is this", attachments=["photo.png"])
    assert result.route == "vision_qwen_vl"
    assert result.model == "Qwen3-VL-4B-Instruct-MLX-4bit"
    assert result.metadata["switch_main_model"] is True


def test_tts_without_voice_clone_uses_tts_route():
    result = route_model("朗读这段话", wants_tts=True, has_voice_clone=False)
    assert result.route == "tts_qwen"
    assert result.model == "Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit"
    assert result.metadata["tool"] == "tts"


def test_tts_with_voice_clone_preserves_clone_flag():
    result = route_model("朗读这段话", wants_tts=True, has_voice_clone=True)
    assert result.route == "tts_qwen"
    assert result.metadata["has_voice_clone"] is True


def test_router_flag_marks_deliberate_routing_without_forcing_escalation():
    result = route_model("route this", force_router=True)
    assert result.route == "direct_qwen"
    assert result.metadata["forced_router"] is True
    assert result.metadata["switch_main_model"] is False
