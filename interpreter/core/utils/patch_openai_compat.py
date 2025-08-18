"""
Utilities to patch OpenAI's Python package for compatibility with litellm imports.

Some litellm versions import symbols that exist only in newer openai releases
(e.g., ResponseTextConfig). When users have an older openai installed, this
causes an ImportError at interpreter startup. To make the CLI resilient, we
add a minimal stub for the missing symbol before importing litellm.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any


def patch_openai_response_text_config() -> None:
    """
    Ensure openai.types.responses.response.ResponseTextConfig exists.

    If missing, define a minimal no-op class to satisfy litellm's import-time
    references. This avoids crashing on startup due to dependency skew.
    """
    try:
        # Quick path: if symbol already exists, nothing to do
        try:
            from openai.types.responses.response import ResponseTextConfig as _RTC  # type: ignore

            _ = _RTC  # silence linter unused
            return
        except Exception:
            pass

        # Try importing the target module
        module_name = "openai.types.responses.response"
        try:
            resp_module = importlib.import_module(module_name)
        except Exception:
            # If we can't import the module at all, nothing to patch
            return

        # If attribute missing, add a simple stub
        if not hasattr(resp_module, "ResponseTextConfig"):
            class ResponseTextConfig:  # type: ignore
                """Compatibility stub for older openai versions."""

                def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
                    pass

            setattr(resp_module, "ResponseTextConfig", ResponseTextConfig)
            # Ensure subsequent from-imports see the attribute
            sys.modules[module_name] = resp_module
    except Exception:
        # Never fail due to patching attempts
        pass


def patch_openai() -> None:
    patch_openai_response_text_config()

