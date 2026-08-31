from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate

# agent/prompts/, a sibling of src/ — kept outside src/ deliberately so prompt
# wording can be edited without touching Python code. Not packaged by
# pyproject.toml's [tool.hatch.build.targets.wheel], and not copied by the
# Dockerfile automatically — see the added `COPY prompts ./prompts` there.
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class PromptRegistry:
    """Loads prompt templates by name from agent/prompts/, caching each after first use."""

    def __init__(self, prompts_dir: Path = PROMPTS_DIR):
        self._prompts_dir = prompts_dir
        self._cache: dict[str, ChatPromptTemplate] = {}

    def get(self, name: str) -> ChatPromptTemplate:
        """Return the named prompt template (e.g. "rag" for agent/prompts/rag.yaml)."""
        if name not in self._cache:
            self._cache[name] = self._load(name)
        return self._cache[name]

    def _load(self, name: str) -> ChatPromptTemplate:
        path = self._prompts_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No prompt named '{name}' found in {self._prompts_dir}")

        prompt_data = yaml.safe_load(path.read_text())
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"{prompt_data['role']}\n\n{prompt_data['goal']}\n\n{prompt_data['constraints']}",
                ),
                ("human", prompt_data["task_template"]),
            ]
        )


prompt_registry = PromptRegistry()
