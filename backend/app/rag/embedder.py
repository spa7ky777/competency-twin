from threading import Lock

from app.config import get_settings

_model = None
_lock = Lock()


class EmbeddingModelUnavailableError(RuntimeError):
    """Raised when the local embedding model is unavailable on first use."""

    def __init__(self, model_name: str):
        super().__init__(
            f"The embedding model '{model_name}' could not be loaded. Connect to the internet once so it can download, then retry processing this document."
        )


def get_embedder():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                settings = get_settings()
                print(f"Loading embedding model {settings.embedding_model} (first run may download it)...")
                try:
                    _model = SentenceTransformer(settings.embedding_model)
                except Exception as exc:
                    raise EmbeddingModelUnavailableError(settings.embedding_model) from exc
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)
    return [v.tolist() for v in vecs]


def cosine(a: list[float], b: list[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))
