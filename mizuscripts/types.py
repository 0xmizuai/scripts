from dataclasses import dataclass

@dataclass
class Embedding:
    id: str
    text: str
    embedding: list[float]
    model: str
