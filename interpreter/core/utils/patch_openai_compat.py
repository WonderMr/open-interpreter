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
            class _PydanticAnyMixin:
                @classmethod
                def __get_pydantic_core_schema__(cls, source_type, handler):  # type: ignore
                    try:
                        from pydantic_core import core_schema

                        return core_schema.any_schema()
                    except Exception:
                        return None

                @classmethod
                def __get_pydantic_json_schema__(cls, core_schema, handler):  # type: ignore
                    return {"type": "object"}

            class ResponseTextConfig(_PydanticAnyMixin):  # type: ignore
                """Compatibility stub for older openai versions."""

                def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
                    for k, v in kwargs.items():
                        setattr(self, k, v)

            setattr(resp_module, "ResponseTextConfig", ResponseTextConfig)
            # Ensure subsequent from-imports see the attribute
            sys.modules[module_name] = resp_module
    except Exception:
        # Never fail due to patching attempts
        pass


def patch_openai() -> None:
    patch_openai_response_text_config()
    try:
        # Newer litellm expects ResponseTextConfigParam from response_create_params
        module_name = "openai.types.responses.response_create_params"
        resp_params_module = None
        try:
            resp_params_module = importlib.import_module(module_name)
        except Exception:
            resp_params_module = None

        if resp_params_module is not None and not hasattr(
            resp_params_module, "ResponseTextConfigParam"
        ):
            class _PydanticAnyMixin:
                @classmethod
                def __get_pydantic_core_schema__(cls, source_type, handler):  # type: ignore
                    try:
                        from pydantic_core import core_schema

                        return core_schema.any_schema()
                    except Exception:
                        return None

                @classmethod
                def __get_pydantic_json_schema__(cls, core_schema, handler):  # type: ignore
                    return {"type": "object"}

            class ResponseTextConfigParam(_PydanticAnyMixin):  # type: ignore
                """Compatibility stub for older openai versions."""

                def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
                    # Accept any kwargs; store for potential debugging
                    for k, v in kwargs.items():
                        setattr(self, k, v)

            setattr(resp_params_module, "ResponseTextConfigParam", ResponseTextConfigParam)
            sys.modules[module_name] = resp_params_module
    except Exception:
        pass

