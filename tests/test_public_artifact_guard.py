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
        "api_secret = 'EXAMPLE_SECRET'\n"
        "conn = btcde.Connection(api_key, api_secret, ssl_verify=True)\n"
    )
    assert guard.check_text("README.md", text, ".md") == []


def test_literal_escaped_newline_is_flagged_in_docs():
    guard = load_guard()
    findings = guard.check_text("README.md", "Keep the line one\\nline two example.\n", ".md")
    assert any("literal escaped newline" in finding for finding in findings)


def test_secret_assignment_is_flagged():
    guard = load_guard()
    findings = guard.check_text(
        "README.md",
        "".join(["api", "_secret = \"", "AbCdEfGh1234567890IjKlMnOpQrStUv", "\"\n"]),
        ".md",
    )
    assert any("secret-looking assignment" in finding for finding in findings)


def test_local_path_and_bearer_token_are_flagged():
    guard = load_guard()
    findings = guard.check_text(
        "notes.txt",
        "".join(
            [
                "Save it in /",
                "home",
                "/alice/.config/btcde/token.txt\n",
                "Authorization: ",
                "Be",
                "arer ",
                "abcdefghijklmnopqrstu\n",
            ]
        ),
        ".txt",
    )
    assert any("local home path" in finding for finding in findings)
    assert any("bearer token" in finding for finding in findings)
