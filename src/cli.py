from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .logging_utils import setup_logging
from .orchestrator import OrchestratorError, orchestrate


LANG_CHOICES = ["kotlin", "openapi"]


def parse_cli_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("--output", default="output.csv", help="Output CSV path")
    parser.add_argument("--lang", choices=LANG_CHOICES, help="Language override")
    parser.add_argument("--config", default=".env", help="Path to configuration file")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_cli_args(argv)

    config = load_config(Path(args.config))
    logger = setup_logging(config.log_level, config.log_file)

    try:
        orchestrate(
            args.input_file,
            args.output,
            config,
            lang_override=args.lang,
            logger=logger,
        )
    except ValueError as exc:
        logger.error(str(exc))
        return 2
    except FileNotFoundError:
        logger.error("Input file not found: %s", args.input_file)
        return 1
    except OrchestratorError as exc:
        logger.error(str(exc))
        return 1
    except Exception:  # pragma: no cover - defensive catch-all
        logger.error("Unexpected error during CLI execution", exc_info=True)
        return 1
    finally:
        for handler in list(logger.handlers):
            handler.close()
        logger.handlers.clear()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
