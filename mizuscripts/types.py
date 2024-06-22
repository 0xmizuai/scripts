from dataclasses import dataclass

@dataclass
class Embedding:
    text: str
    embedding: list[float]
    model: str
