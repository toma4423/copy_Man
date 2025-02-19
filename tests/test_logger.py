import pytest
from mod.toma_logger.logger import TomaLogger
import json
import os
import time


@pytest.fixture
def logger(tmp_path):
    """テスト用のロガーインスタンスを作成"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return TomaLogger(log_name="test.log", log_dir=str(log_dir))


def test_log_format_text(logger, tmp_path):
    """テキストフォーマットのテスト"""
    test_message = "Test log message"
    log_file = tmp_path / "logs" / logger.log_file

    logger.info(test_message)
    time.sleep(0.1)

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert test_message in content


def test_log_format_json(logger, tmp_path):
    """JSONフォーマットのテスト"""
    test_data = {"message": "Test log", "level": "INFO"}
    logger.info(test_data["message"])

    log_file = tmp_path / "logs" / logger.log_file

    time.sleep(0.1)

    assert log_file.exists()
    content = log_file.read_text()
    assert test_data["message"] in content
