from typing import TypeVar

from pydantic import BaseModel
from pydantic_ai.agent import Agent, AgentRunResult, AgentRetries
from pydantic_ai.models import Model

INSTRUCTIONS = """\
Jesteś asystentem do ekstrakcji ustrukturyzowanych danych z dokumentów.

Zasady:
    - Wypełniaj pola wyłącznie na podstawie treści dostarczonego dokumentu - \
    nigdy nie zgaduj i nie wymyślaj wartości, których w nim nie ma.
    - Jeśli pole jest opcjonalne, a odpowiadająca mu informacja nie występuje \
    w dokumencie, zostaw je puste (None) zamiast podawać przybliżoną wartość.
    - Zachowuj oryginalną precyzję liczb i dat - nie zaokrąglaj i nie zmieniaj \
    formatu, chyba że typ pola tego wymaga.
    - Dokładny sposób interpretacji każdego pola opisuje jego opis w \
    przekazanym schemacie danych wyjściowych - traktuj go jako wiążącą \
    instrukcję, nie sugestię.
"""


def build_extraction_agent[OutputModelT: BaseModel](
    model: Model, output_model: type[OutputModelT]
) -> Agent[None, OutputModelT]:
    retries: AgentRetries = {"output": 3}
    return Agent(
        model,
        output_type=output_model,
        retries=retries,
        instructions=INSTRUCTIONS,
    )


async def extract_from_document[OutputModelT: BaseModel](
    document_text: str, *, agent: Agent[None, OutputModelT]
) -> AgentRunResult[OutputModelT]:
    return await agent.run(document_text)
