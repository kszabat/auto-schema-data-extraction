from collections.abc import Sequence

from pydantic_ai import Agent, AgentRetries
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model

from auto_schema_data_extraction.schema.meta_models import TemplateSpec

SYSTEM_PROMPT = """\
Jesteś asystentem, który na podstawie opisu użytkownika w języku naturalnym \
tworzy specyfikację szablonu do ekstrakcji danych z dokumentów.

Zasady:
    - Nazwa szablonu (`name`) oraz nazwy pól (`FieldDefinition.name`) muszą być \
    poprawnymi identyfikatorami Pythona w snake_case (np. `invoice_number`, \
    nie `Invoice Number` ani `numer-faktury`).
    - Każde pole musi mieć jasny, jednoznaczny `description` - będzie on \
    jedynym kontekstem dla innego modelu, który później faktycznie wyciągnie \
    wartość z dokumentu, więc nie może być ogólnikowy.
    - Ustaw `required=False` tylko dla pól, które w typowym dokumencie tego \
    rodzaju mogą realnie nie występować.
    - Nie dodawaj pól, o które użytkownik nie prosił, chyba że są oczywistym \
    elementem tego typu dokumentu i ich pominięcie byłoby zaskakujące \
    (np. przy fakturze - waluta).

Jeśli w kolejnej wiadomości użytkownik poprosi o poprawki do wcześniej \
wygenerowanej specyfikacji, zmodyfikuj ją zgodnie z jego uwagami, zamiast \
tworzyć ją od nowa - zachowaj pola, o których zmianę nikt nie prosił.
"""


def build_schema_agent(model: Model) -> Agent[None, TemplateSpec]:
    retries: AgentRetries = {"output": 3}
    return Agent(
        model,
        output_type=TemplateSpec,
        system_prompt=SYSTEM_PROMPT,
        retries=retries,
    )


async def generate_template_spec(
    user_prompt: str,
    *,
    agent: Agent[None, TemplateSpec],
    message_history: Sequence[ModelMessage] | None = None,
) -> TemplateSpec:
    return await agent.run(user_prompt, message_history=message_history)
