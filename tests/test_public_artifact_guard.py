from pathlib import Path
import importlib.util


def load_guard():
    guard_path = Path(__file__).resolve().parents[1] / "tools" / "check_public_artifacts.py"
    spec = importlib.util.spec_from_file_location("check_public_artifacts", guard_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_clean_public_artifacts_pass():
    guard = load_guard()
    text = (
        "api_key = <YourAPIKey>\n"
        "api_secret = ${EXAMPLE_SECRET}\n"
        "conn = btcde.Connection(api_key, api_secret, ssl_verify=True)\n"
    )
    assert guard.check_text("README.md", text) == []


def test_literal_escaped_newline_is_flagged_in_docs():
    guard = load_guard()
    findings = guard.check_text("README.md", "Keep the line one\\nline two example.\n")
    assert any("literal-escaped-newline" in finding for finding in findings)


def test_secret_assignment_is_flagged():
    guard = load_guard()
    findings = guard.check_text(
        "README.md",
        "".join(["api", "_secret = \"", "AbCdEfGh1234567890IjKlMnOpQrStUv", "\"\n"]),
    )
    assert any("secret-assignment" in finding for finding in findings)


def test_windows_local_path_is_flagged():
    guard = load_guard()
    findings = guard.check_text(
        "notes.txt",
        "Open it from C:\\Users\\alice\\AppData\\Roaming\\btcde\\config.ini\n",
    )
    assert any("local-user-path" in finding for finding in findings)
