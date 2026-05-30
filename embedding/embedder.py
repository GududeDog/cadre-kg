from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, EMBEDDING_DEVICE, EMBEDDING_DIM


class Embedder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(
                EMBEDDING_MODEL,
                device=EMBEDDING_DEVICE,
            )
        return self._model

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(embs, dtype=np.float32)

    def embed_one(self, text: str) -> List[float]:
        return self.embed(text)[0].tolist()
