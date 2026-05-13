from .schema import IngestInput

CUSTOMER_KEYWORDS = ["woolworths", "coles", "bunnings", "dan murphy", "fairprice", "customer", "client"]
PROJECT_KEYWORDS = ["project", "poc", "trial", "rollout", "pilot", "deployment", "roadmap", "budget"]
DECISION_KEYWORDS = ["decision", "approved", "confirmed", "agreed", "rejected", "risk", "issue"]
COMMERCIAL_KEYWORDS = ["price", "cost", "budget", "po", "quote", "irr", "discount", "commercial"]
MODEL_CONFIG_KEYWORDS = [
    "model", "chatgpt", "chatgtp", "qwen", "hermes", "router", "routing",
    "模型", "路由", "当前使用", "现在用的模型"
]

def score_input(item: IngestInput) -> int:
    text = f"{item.title}\n{item.content}".lower()
    score = 0

    if any(k in text for k in CUSTOMER_KEYWORDS):
        score += 3
    if any(k in text for k in COMMERCIAL_KEYWORDS):
        score += 3
    if any(k in text for k in MODEL_CONFIG_KEYWORDS):
        score += 3
    if any(k in text for k in PROJECT_KEYWORDS):
        score += 2
    if any(k in text for k in DECISION_KEYWORDS):
        score += 2
    if item.source_type in ["email", "voice", "file"]:
        score += 1
    if item.title.strip():
        score += 1
    if len(item.content.strip()) >= 20:
        score += 1
    else:
        score -= 2

    return score
