# ABOUTME: Store 契约与用户标识校验测试
# ABOUTME: 验证 user_id、namespace 和文件封装值遵循运行时契约

import json
from pathlib import Path

import pytest

from voliti.store_contract import (
    CHAPTER_CURRENT_KEY,
    InvalidStoreValueError,
    InvalidUserIDError,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    make_file_value,
    make_interventions_namespace,
    make_user_namespace,
    parse_json_file_value,
    resolve_user_namespace,
    unwrap_file_value,
    validate_user_id,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "contracts" / "fixtures" / "store"


def test_validate_user_id_accepts_eval_style_identifier() -> None:
    assert validate_user_id("eval_0001") == "eval_0001"


@pytest.mark.parametrize("user_id", ["", " user_0001 ", "abc", "bad/user", "bad user"])
def test_validate_user_id_rejects_invalid_value(user_id: str) -> None:
    with pytest.raises(InvalidUserIDError):
        validate_user_id(user_id)


def test_make_user_namespace_uses_validated_user_id() -> None:
    assert make_user_namespace("device_1234") == ("voliti", "device_1234")


def test_make_interventions_namespace_uses_validated_user_id() -> None:
    assert make_interventions_namespace("device_1234") == (
        "voliti",
        "device_1234",
        "interventions",
    )


def test_resolve_user_namespace_raises_without_user_id() -> None:
    with pytest.raises(InvalidUserIDError):
        resolve_user_namespace({"configurable": {}})


def test_resolve_user_namespace_raises_on_invalid_user_id() -> None:
    with pytest.raises(InvalidUserIDError):
        resolve_user_namespace({"configurable": {"user_id": "bad/user"}})


def test_make_file_value_round_trip() -> None:
    value = make_file_value('line1\n{"a":1}')
    assert unwrap_file_value(value) == 'line1\n{"a":1}'
    assert value["version"] == "1"


def test_parse_json_file_value_reads_wrapped_json() -> None:
    value = make_file_value('{"status":"ok","count":2}')
    assert parse_json_file_value(value) == {"status": "ok", "count": 2}


def test_unwrap_file_value_rejects_non_list_content() -> None:
    with pytest.raises(InvalidStoreValueError):
        unwrap_file_value({"content": "plain string"})


def test_store_keys_are_stable() -> None:
    assert PROFILE_CONTEXT_KEY == "/profile/context.md"
    assert PROFILE_DASHBOARD_CONFIG_KEY == "/profile/dashboardConfig"
    assert CHAPTER_CURRENT_KEY == "/chapter/current.json"


def test_shared_profile_fixture_round_trip() -> None:
    fixture = FIXTURES_DIR / "profile_context.value.json"
    value = json.loads(fixture.read_text(encoding="utf-8"))
    content = unwrap_file_value(value)
    assert "fixture_type: profile_context" in content
    assert "onboarding_complete: true" in content
