"""Component 4: claim-level explanation faithfulness verification."""

from .pipeline import C4Config, C4Pipeline, C4Result
from .explainer import OllamaExplanationGenerator, TemplateExplanationGenerator

__all__ = [
    "C4Config",
    "C4Pipeline",
    "C4Result",
    "OllamaExplanationGenerator",
    "TemplateExplanationGenerator",
]
