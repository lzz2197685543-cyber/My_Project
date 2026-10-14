import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ecommerce_automation import ProjectPaths, RunContext, Settings, load_json
from ecommerce_automation.errors import ConfigError


class ConfigTests(unittest.TestCase):
    def test_paths_use_project_root_without_import_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new_project"
            paths = ProjectPaths(root)
            self.assertFalse(root.exists())
            paths.ensure_runtime()
            self.assertTrue(paths.data.is_dir())
            self.assertTrue(paths.logs.is_dir())
            self.assertFalse(paths.config.exists())

    def test_environment_precedence_and_strict_types(self):
        with patch.dict(os.environ, {"EA_TEST_PORT": "44"}):
            settings = Settings.load(defaults={"EA_TEST_PORT": "33", "EA_TEST_BAD": "one"})
        self.assertEqual(settings.integer("EA_TEST_PORT"), 44)
        self.assertEqual(settings.integer("absent", 5, minimum=1), 5)
        with self.assertRaises(ConfigError):
            settings.integer("EA_TEST_BAD")
        with self.assertRaises(ConfigError):
            settings.require("MISSING_SETTING")
        with self.assertRaises(ConfigError):
            Settings({"flag": "truthy"}).boolean("flag")
        self.assertFalse(Settings({"flag": "false"}).boolean("flag"))
        self.assertNotIn("44", repr(settings))

    def test_dotenv_does_not_modify_global_environment(self):
        try:
            import dotenv
        except ImportError:
            self.skipTest("config extra not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("EA_TEST_ONLY=file\nEA_TEST_OVERRIDE=file\nLITERAL=${EA_TEST_ONLY}\n", encoding="utf-8")
            before = os.environ.copy()
            settings = Settings.load(
                env_file=path, defaults={"EA_TEST_ONLY": "default"},
                environ={"EA_TEST_OVERRIDE": "environment"},
            )
            self.assertEqual(settings.require("EA_TEST_ONLY"), "file")
            self.assertEqual(settings.require("EA_TEST_OVERRIDE"), "environment")
            self.assertEqual(settings.require("LITERAL"), "${EA_TEST_ONLY}")
            self.assertEqual(os.environ, before)

    def test_json_object_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"batch_size": 5}), encoding="utf-8-sig")
            self.assertEqual(load_json(path), {"batch_size": 5})
            path.write_text("[]")
            with self.assertRaises(ConfigError):
                load_json(path)


class LoggingTests(unittest.TestCase):
    def test_project_isolation_redaction_and_handler_cleanup(self):
        root_handlers = logging.getLogger().handlers[:]
        with tempfile.TemporaryDirectory() as directory:
            with RunContext("shop", directory, console=False, secrets=["private-token"]) as first:
                first.logger.bind(stage="publish", shop="shop1", task_id="sku1").info("value=%s", "private-token")
                try:
                    raise ValueError("private-token in traceback")
                except ValueError:
                    first.logger.exception("failure")
            with RunContext("shop", directory, console=False) as second:
                second.logger.info("another run")
            self.assertNotEqual(first.log_file, second.log_file)
            text = first.log_file.read_text(encoding="utf-8")
            self.assertNotIn("private-token", text)
            self.assertIn("[REDACTED]", text)
            self.assertIn("stage=publish shop=shop1 task=sku1", text)
            self.assertEqual(text.count("run_started"), 1)
            self.assertEqual(first.logger.logger.handlers, [])
            self.assertEqual(logging.getLogger().handlers, root_handlers)

    def test_unsafe_path_component_is_rejected(self):
        with self.assertRaises(ValueError):
            RunContext("../escape", ".")


if __name__ == "__main__":
    unittest.main()
