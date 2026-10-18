"""Component 4: claim-level explanation faithfulness verification."""

from .pipeline import C4Config, C4Pipeline, C4Result
from .explainer import TemplateExplanationGenerator

__all__ = ["C4Config", "C4Pipeline", "C4Result", "TemplateExplanationGenerator"]
