# TAF/tframex/model/__init__.py

# Import the classes you want to expose directly from the 'model' package
from .model_logic import BaseModel, VLLMModel

# Optional: Define __all__ to control 'from tframex.model import *' behaviour
__all__ = ['BaseModel', 'VLLMModel']