class ProviderError(RuntimeError):
    """Raised when a chatbot provider cannot return a response."""


class RecommendationError(RuntimeError):
    """Raised when recommendations cannot be generated."""
