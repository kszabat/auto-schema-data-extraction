from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExtractedText:
    text: str
    source: Path
    partial: bool = False
