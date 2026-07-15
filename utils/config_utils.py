import json
import os


def _infer_tool_name(path: str) -> str:
    filename = os.path.basename(path)
    if filename.endswith("_args.json"):
        return filename[: -len("_args.json")]
    return os.path.splitext(filename)[0]


def _normalize_positional_args(positional_args) -> list[dict]:
    normalized = []
    for idx, item in enumerate(positional_args or []):
        if isinstance(item, dict):
            normalized.append(
                {
                    "name": str(item.get("name") or f"arg{idx + 1}"),
                    "description": str(item.get("description") or ""),
                    "required": bool(item.get("required", True)),
                }
            )
        else:
            normalized.append(
                {
                    "name": f"arg{idx + 1}",
                    "description": str(item),
                    "required": True,
                }
            )
    return normalized


def _normalize_kwarg_spec(flag_name: str, spec) -> tuple[str, dict]:
    key = str(flag_name).lstrip("-")
    cli_flag = f"--{key}" if len(key) > 1 else f"-{key}"
    if isinstance(spec, dict):
        return key, {
            "cli_flag": cli_flag,
            "type": str(spec.get("type") or "str"),
            "required": bool(spec.get("required", False)),
            "description": str(spec.get("description") or ""),
        }
    return key, {
        "cli_flag": cli_flag,
        "type": "str",
        "required": False,
        "description": str(spec),
    }


def _normalize_args_block(args_block: dict | None) -> dict:
    args_block = args_block or {}
    positional_args = _normalize_positional_args(
        args_block.get("positional_args") or args_block.get("pos_args") or []
    )

    kwargs: dict[str, dict] = {}
    for key, spec in (args_block.get("kwargs") or {}).items():
        norm_key, norm_spec = _normalize_kwarg_spec(key, spec)
        kwargs[norm_key] = norm_spec

    reserved = {"positional_args", "pos_args", "kwargs", "description", "usage", "name", "subcommand"}
    for key, spec in args_block.items():
        if key in reserved:
            continue
        norm_key, norm_spec = _normalize_kwarg_spec(key, spec)
        kwargs.setdefault(norm_key, norm_spec)

    return {
        "positional_args": positional_args,
        "kwargs": kwargs,
    }


def _normalize_list_schema(tool_name: str, raw_config: list) -> dict:
    commands = {}
    for item in raw_config:
        if not isinstance(item, dict):
            continue
        command_name = str(item.get("name") or "").strip()
        if not command_name:
            continue
        commands[command_name] = {
            "description": str(item.get("description") or ""),
            "usage": str(item.get("usage") or ""),
            **_normalize_args_block(item.get("args")),
        }
    return {
        "tool": tool_name,
        "schema_version": "2",
        "llm_guidance": {
            "command_key_rule": "Choose exactly one key from commands as tool_name/subcommand output.",
            "kwargs_key_rule": "Use kwargs keys exactly as shown under each command. They are normalized keys without leading hyphens; cli_flag shows the real shell flag.",
            "positional_arg_rule": "Fill tool_args.pos_args in the same order as positional_args.",
        },
        "commands": commands,
        "_raw": raw_config,
    }


def _normalize_dict_schema(tool_name: str, raw_config: dict) -> dict:
    commands = {}

    if tool_name in raw_config and isinstance(raw_config[tool_name], dict):
        root = raw_config[tool_name]
    else:
        root = raw_config

    subcommands = root.get("subcommands") if isinstance(root, dict) else None
    if isinstance(subcommands, dict):
        for sub_name, sub_spec in subcommands.items():
            canonical_name = f"{tool_name}_{sub_name}"
            commands[canonical_name] = {
                "description": str((sub_spec or {}).get("description") or ""),
                "usage": str((sub_spec or {}).get("usage") or ""),
                **_normalize_args_block(sub_spec),
                "subcommand": str(sub_name),
            }
    else:
        commands[tool_name] = {
            "description": str(root.get("description") or ""),
            "usage": str(root.get("usage") or ""),
            **_normalize_args_block(root.get("args") if isinstance(root, dict) else {}),
        }

    return {
        "tool": tool_name,
        "schema_version": "2",
        "llm_guidance": {
            "command_key_rule": "Choose exactly one key from commands as tool_name/subcommand output.",
            "kwargs_key_rule": "Use kwargs keys exactly as shown under each command. They are normalized keys without leading hyphens; cli_flag shows the real shell flag.",
            "positional_arg_rule": "Fill tool_args.pos_args in the same order as positional_args.",
        },
        "commands": commands,
        "_raw": raw_config,
    }


def normalize_tool_config(raw_config, path: str = "") -> dict:
    tool_name = _infer_tool_name(path) if path else "tool"
    if isinstance(raw_config, list):
        return _normalize_list_schema(tool_name, raw_config)
    if isinstance(raw_config, dict):
        return _normalize_dict_schema(tool_name, raw_config)
    return {"tool": tool_name, "schema_version": "2", "commands": {}, "_raw": raw_config}


def load_tool_config(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            print(f"[Config] Warning: {path} is empty, skipping.")
            return {}
        raw_config = json.loads(content)
    return normalize_tool_config(raw_config, path=path)


def format_tool_schema(schema: dict) -> str:
    if not schema:
        return "{}"
    clean_schema = {k: v for k, v in schema.items() if k != "_raw"}
    return json.dumps(clean_schema, ensure_ascii=False, indent=2)
