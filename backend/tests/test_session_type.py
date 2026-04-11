# ABOUTME: SessionType 运行时契约测试
# ABOUTME: 验证 session_type 的严格读取与显式收敛规则

from __future__ import annotations

from unittest.mock import patch

import pytest

from voliti.session_type import (
    InvalidSessionTypeError,
    coerce_session_type,
    get_current_session_type,
)


def test_coerce_session_type_accepts_supported_values() -> None:
    assert coerce_session_type("coaching") == "coaching"
    assert coerce_session_type("onboarding") == "onboarding"


def test_coerce_session_type_rejects_other_values() -> None:
    assert coerce_session_type("invalid") is None
    assert coerce_session_type(None) is None


def test_get_current_session_type_reads_valid_runtime_config() -> None:
    with patch(
        "voliti.session_type.get_config",
        return_value={"configurable": {"session_type": "onboarding"}},
    ):
        assert get_current_session_type() == "onboarding"


def test_get_current_session_type_rejects_missing_runtime_value() -> None:
    with patch(
        "voliti.session_type.get_config",
        return_value={"configurable": {}},
    ):
        with pytest.raises(InvalidSessionTypeError):
            get_current_session_type()


def test_get_current_session_type_rejects_invalid_runtime_value() -> None:
    with patch(
        "voliti.session_type.get_config",
        return_value={"configurable": {"session_type": "legacy"}},
    ):
        with pytest.raises(InvalidSessionTypeError):
            get_current_session_type()
