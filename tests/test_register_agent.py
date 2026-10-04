# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path

from kmb.cli import main as cli_main
from kmb.register import register_from_args, write_agent_pack


class RegisterAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.configs = Path(self.tmp.name) / "configs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_agent_pack_creates_three_types_without_secrets(self):
        paths = write_agent_pack(
            configs_root=self.configs,
            agent_id="demo-bot",
            display_name="DemoBot",
            base_url="https://api.example.test/v1",
            model="demo-model",
            api_key_env="DEMO_BOT_API_KEY",
        )
        self.assertEqual(len(paths), 3)
        types = {}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("api_key_env: DEMO_BOT_API_KEY", text)
            self.assertNotIn("sk-", text)
            self.assertNotIn("api_key:", text.lower())
            for line in text.splitlines():
                if line.startswith("type:"):
                    types[path.name] = line.split(":", 1)[1].strip()
        self.assertEqual(types.get("agent-demo-bot.yaml"), "http")
        self.assertEqual(types.get("agent-demo-bot-memory.yaml"), "memory_controller")
        self.assertEqual(types.get("agent-demo-bot-no-memory.yaml"), "memory_disabled")

    def test_write_agent_pack_rejects_existing_without_partial(self):
        write_agent_pack(
            configs_root=self.configs,
            agent_id="dup",
            display_name="Dup",
            base_url="https://api.example.test/v1",
            model="m",
            api_key_env="DUP_API_KEY",
        )
        with self.assertRaises(FileExistsError):
            write_agent_pack(
                configs_root=self.configs,
                agent_id="dup",
                display_name="Dup2",
                base_url="https://api.example.test/v1",
                model="m",
                api_key_env="DUP_API_KEY",
            )
        text = (self.configs / "agent-dup.yaml").read_text(encoding="utf-8")
        self.assertIn("name: dup", text)
        self.assertNotIn("Dup2", text)

    def test_invalid_api_key_env(self):
        with self.assertRaises(ValueError):
            write_agent_pack(
                configs_root=self.configs,
                agent_id="bad",
                display_name="Bad",
                base_url="https://api.example.test/v1",
                model="m",
                api_key_env="not-valid",
            )

    def test_cli_register_agent(self):
        code = cli_main([
            "register-agent",
            "--name", "CliBot",
            "--base-url", "https://api.example.test/v1",
            "--model", "cli-model",
            "--id", "clibot",
            "--api-key-env", "CLIBOT_API_KEY",
            "--configs-dir", str(self.configs),
        ])
        self.assertEqual(code, 0)
        self.assertTrue((self.configs / "agent-clibot.yaml").is_file())
        self.assertTrue((self.configs / "agent-clibot-memory.yaml").is_file())
        self.assertTrue((self.configs / "agent-clibot-no-memory.yaml").is_file())
        with self.assertRaises(SystemExit):
            cli_main([
                "register-agent",
                "--name", "CliBot",
                "--base-url", "https://api.example.test/v1",
                "--model", "cli-model",
                "--id", "clibot",
                "--api-key-env", "CLIBOT_API_KEY",
                "--configs-dir", str(self.configs),
            ])

    def test_register_from_args_defaults_env_name(self):
        paths = register_from_args(
            name="OpenRouter Mini",
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-4.1-mini",
            configs_root=self.configs,
            print_fn=lambda *a, **k: None,
        )
        self.assertEqual(len(paths), 3)
        text = (self.configs / "agent-openrouter-mini.yaml").read_text(encoding="utf-8")
        self.assertIn("OPENROUTER_MINI_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
