#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


PATCH_MAP = {
    "main.nf": "methylong/modules/local/dorado/basecaller/main.nf",
    "nextflow.config": "methylong/nextflow.config",
}


def main():
    parser = argparse.ArgumentParser(
        description="Apply ModFlowAgent methylong compatibility patches."
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Path to the methylong source directory.",
    )

    args = parser.parse_args()

    patch_dir = Path(__file__).resolve().parent
    base_dir = Path(args.base).resolve()

    if not base_dir.exists():
        raise FileNotFoundError(f"Methylong base directory not found: {base_dir}")

    for src_name, dst_rel in PATCH_MAP.items():
        src = patch_dir / src_name
        dst = base_dir / dst_rel

        if not src.exists():
            raise FileNotFoundError(f"Patch source file not found: {src}")

        if not dst.exists():
            raise FileNotFoundError(f"Target file not found: {dst}")

        backup = dst.with_suffix(dst.suffix + ".modflowagent.bak")
        shutil.copy2(dst, backup)
        print(f"[BACKUP] {dst} -> {backup}")

        shutil.copy2(src, dst)
        print(f"[PATCH] {src} -> {dst}")

    print("[OK] Methylong compatibility patches applied.")


if __name__ == "__main__":
    main()