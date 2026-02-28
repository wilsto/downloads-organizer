import re
from dataclasses import dataclass

from organizer.config import ContextConfig


@dataclass
class Classification:
    context: str
    file_type: str
    matched_by: str  # "regex" | "default" | "llm"


class RegexClassifier:
    def __init__(
        self,
        contexts: dict[str, ContextConfig],
        type_mapping: dict[str, list[str]],
        default_context: str = "Perso",
        default_type: str = "Autres",
    ):
        self._contexts = contexts
        self._type_mapping = type_mapping
        self._default_context = default_context
        self._default_type = default_type
        # Pre-compile regex patterns
        self._compiled: dict[str, list[re.Pattern]] = {
            name: [re.compile(p) for p in ctx.patterns]
            for name, ctx in contexts.items()
        }
        # Build reverse extension lookup
        self._ext_to_type: dict[str, str] = {}
        for type_name, extensions in type_mapping.items():
            for ext in extensions:
                self._ext_to_type[ext.lower()] = type_name

    def classify(self, filename: str) -> Classification:
        context = self._match_context(filename)
        file_type = self._match_type(filename)
        matched_by = "regex" if context != self._default_context else "default"
        # If type was matched by extension but context was default, still "default"
        if context == self._default_context and file_type != self._default_type:
            matched_by = "default"
        return Classification(
            context=context, file_type=file_type, matched_by=matched_by
        )

    def _match_context(self, filename: str) -> str:
        for name, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.search(filename):
                    return name
        return self._default_context

    def _match_type(self, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return self._ext_to_type.get(ext, self._default_type)
