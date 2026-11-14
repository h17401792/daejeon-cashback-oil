"""Comprehensive tests and integrity checks for the PWA + Android APK project."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sync_android_assets  # noqa: E402
import update_prices  # noqa: E402


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class UIInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.inline_scripts: list[str] = []
        self._in_script = False
        self._buf: list[str] = []
        self.tag_stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if "id" in attr_map and attr_map["id"] is not None:
            self.ids.append(attr_map["id"])
        if tag == "script" and not attr_map.get("src"):
            self._in_script = True
            self._buf = []
        if tag not in VOID_ELEMENTS:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_script:
            self.inline_scripts.append("".join(self._buf))
            self._in_script = False
            self._buf = []
        if tag in VOID_ELEMENTS:
            return
        if not self.tag_stack or self.tag_stack[-1] != tag:
            self.errors.append(f"Mismatched </{tag}> (stack top: {self.tag_stack[-1] if self.tag_stack else 'NONE'})")
        else:
            self.tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._buf.append(data)


def check_js_delimiters(js_code: str) -> list[str]:
    errors: list[str] = []
    stack: list[tuple[str, int]] = []
    pairs = {"{": "}", "(": ")", "[": "]"}
    closing = {v: k for k, v in pairs.items()}
    i = 0
    n = len(js_code)
    line = 1
    in_line_comment = False
    in_block_comment = False
    quote: str | None = None
    in_template = False
    prev_sig = ""

    while i < n:
        ch = js_code[i]
        nxt = js_code[i + 1] if i + 1 < n else ""
        if ch == "\n":
            line += 1
            in_line_comment = False
            i += 1
            continue
        if in_line_comment:
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if in_template:
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                in_template = False
                i += 1
                continue
            if ch == "$" and nxt == "{":
                stack.append(("`${", line))
                in_template = False
                i += 2
                continue
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch == "/" and prev_sig in ("", "=", "(", "[", "{", ",", ":", ";", "!", "&", "|", "?", "\n"):
            i += 1
            in_class = False
            while i < n:
                rc = js_code[i]
                if rc == "\\":
                    i += 2
                    continue
                if rc == "[":
                    in_class = True
                elif rc == "]":
                    in_class = False
                elif rc == "/" and not in_class:
                    break
                elif rc == "\n":
                    errors.append(f"Unterminated regex at line {line}")
                    break
                i += 1
            i += 1
            prev_sig = "/"
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "`":
            in_template = True
            i += 1
            continue
        if ch in pairs:
            stack.append((ch, line))
        elif ch in closing:
            if ch == "}" and stack and stack[-1][0] == "`${":
                stack.pop()
                in_template = True
                i += 1
                prev_sig = ch
                continue
            if not stack or stack[-1][0] != closing[ch]:
                errors.append(f"Mismatched '{ch}' at line {line}")
            else:
                stack.pop()
        if not ch.isspace():
            prev_sig = ch
        i += 1

    if quote is not None:
        errors.append("Unterminated string")
    if in_template:
        errors.append("Unterminated template literal")
    if stack:
        errors.append(f"Unclosed delimiters: {stack}")
    return errors


class TestMobileProject(unittest.TestCase):
    def test_pwa_html_manifest_sw_and_icons(self) -> None:
        docs_dir = PROJECT_ROOT / "docs"
        html_text = (docs_dir / "index.html").read_text(encoding="utf-8")

        inspector = UIInspector()
        inspector.feed(html_text)
        inspector.close()
        self.assertEqual(inspector.errors, [])
        self.assertEqual(inspector.tag_stack, [])
        self.assertEqual(len(inspector.ids), len(set(inspector.ids)))
        self.assertEqual(len(inspector.inline_scripts), 1)

        js_code = inspector.inline_scripts[0]
        self.assertEqual(check_js_delimiters(js_code), [])

        id_set = set(inspector.ids)
        refs = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js_code))
        self.assertEqual(sorted(refs - id_set), [])

        manifest = json.loads((docs_dir / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        for icon in manifest["icons"]:
            icon_path = (docs_dir / icon["src"]).resolve()
            self.assertTrue(icon_path.exists(), f"Missing icon {icon_path}")
            expected_px = int(icon["sizes"].split("x")[0])
            with Image.open(icon_path) as im:
                self.assertEqual(im.size, (expected_px, expected_px))

        with Image.open(docs_dir / "icons" / "apple-touch-icon.png") as im:
            self.assertEqual(im.size, (180, 180))

        sw_text = (docs_dir / "sw.js").read_text(encoding="utf-8")
        assets_match = re.search(r"const SHELL_ASSETS = \[(.*?)\];", sw_text, re.S)
        self.assertIsNotNone(assets_match)
        assets = re.findall(r'"([^"]+)"', assets_match.group(1))
        for asset in assets:
            if asset == "./":
                self.assertTrue((docs_dir / "index.html").exists())
            else:
                self.assertTrue((docs_dir / asset).exists(), f"Missing SW asset {asset}")

    def test_stations_json_and_update_prices_mocked(self) -> None:
        data_path = PROJECT_ROOT / "docs" / "data" / "stations.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["stations"]), 82)
        self.assertEqual(len(data["unmatched_ontong_entries"]), 5)
        self.assertEqual(len(data["cover_points"]["gas_diesel"]), 7)
        self.assertEqual(len(data["cover_points"]["lpg"]), 5)
        self.assertIn("last_updated_kst", data["meta"])

        gas_uid = next(s["uni_id"] for s in data["stations"] if s["lpg_yn"] == "N")
        lpg_uid = next(s["uni_id"] for s in data["stations"] if s["lpg_yn"] == "Y")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_json = Path(tmp) / "stations.json"
            shutil.copy2(data_path, tmp_json)

            def fake_around(api_key: str, x: float, y: float, prodcd: str, radius: int = 5000):
                if prodcd == "K015":
                    return [{"UNI_ID": lpg_uid, "PRICE": 1066, "POLL_DIV_CD": "SKG"}]
                return [{"UNI_ID": gas_uid, "PRICE": 1777, "POLL_DIV_CD": "SKE"}]

            with patch.object(update_prices, "fetch_around_all", side_effect=fake_around):
                summary = update_prices.refresh_dataset(
                    tmp_json, "DUMMY_TEST_KEY", ["B027", "D047", "B034", "K015"]
                )
            self.assertEqual(summary["total_calls"], 26)
            self.assertEqual(summary["updated"]["B027"], 1)
            self.assertEqual(summary["updated"]["K015"], 1)

            updated = json.loads(tmp_json.read_text(encoding="utf-8"))
            gas_st = next(s for s in updated["stations"] if s["uni_id"] == gas_uid)
            lpg_st = next(s for s in updated["stations"] if s["uni_id"] == lpg_uid)
            self.assertEqual(gas_st["prices"]["B027"]["price"], 1777)
            self.assertEqual(lpg_st["prices"]["K015"]["price"], 1066)

            with self.assertRaises(ValueError):
                update_prices.refresh_dataset(tmp_json, "", ["B027"])
            with self.assertRaises(ValueError):
                update_prices.refresh_dataset(tmp_json, "DUMMY", ["INVALID"])

    def test_android_project_and_assets_sync(self) -> None:
        android_dir = PROJECT_ROOT / "android"
        res_dir = android_dir / "app" / "src" / "main" / "res"

        for xml_file in [
            android_dir / "app" / "src" / "main" / "AndroidManifest.xml",
            res_dir / "values" / "strings.xml",
            res_dir / "values" / "styles.xml",
        ]:
            ET.parse(xml_file)

        expected_mipmaps = {
            "mipmap-mdpi": 48,
            "mipmap-hdpi": 72,
            "mipmap-xhdpi": 96,
            "mipmap-xxhdpi": 144,
            "mipmap-xxxhdpi": 192,
        }
        for folder, px in expected_mipmaps.items():
            for fname in ("ic_launcher.png", "ic_launcher_round.png"):
                p = res_dir / folder / fname
                self.assertTrue(p.exists(), f"Missing {p}")
                with Image.open(p) as im:
                    self.assertEqual(im.size, (px, px))

        kt_text = (android_dir / "app" / "src" / "main" / "kotlin" / "kr" / "daejeon" / "cashbackoil" / "MainActivity.kt").read_text(encoding="utf-8")
        for required_symbol in [
            "WebViewAssetLoader",
            "onGeolocationPermissionsShowPrompt",
            "shouldOverrideUrlLoading",
            "AndroidBridge",
            "BuildConfig.PWA_URL",
        ]:
            self.assertIn(required_symbol, kt_text)

        www_dir = android_dir / "app" / "src" / "main" / "assets" / "www"
        self.assertTrue((www_dir / "index.html").exists())
        self.assertTrue((www_dir / "data" / "stations.json").exists())
        self.assertEqual(
            (www_dir / "index.html").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "docs" / "index.html").read_text(encoding="utf-8"),
        )

    def test_no_leaked_secret_api_key(self) -> None:
        leaked = []
        for path in PROJECT_ROOT.rglob("*"):
            if path.is_dir() or "assets" in path.parts or ".git" in path.parts:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".pyc"}:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "F26111" + "5177" in text:
                leaked.append(str(path))
        self.assertEqual(leaked, [], f"API key must NOT appear in deployable repo: {leaked}")

    def test_no_personal_github_username_in_repo(self) -> None:
        exposed = []
        forbidden = "h17401" + "792"
        for path in PROJECT_ROOT.rglob("*"):
            if path.is_dir() or ".git" in path.parts:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".pyc"}:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if forbidden in text:
                exposed.append(str(path))
        self.assertEqual(exposed, [], f"Personal username must NOT appear in repo: {exposed}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
