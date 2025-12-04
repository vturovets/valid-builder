from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .logging_utils import attach_summary_handler, log_final_summary, setup_logging
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
    summary_handler = attach_summary_handler(logger)

    exit_code = 0
    rule_count = None

    try:
        rules = orchestrate(
            args.input_file,
            args.output,
            config,
            lang_override=args.lang,
            logger=logger,
        )
        rule_count = len(rules)
    except ValueError as exc:
        logger.error(str(exc))
        exit_code = 2
    except FileNotFoundError:
        logger.error("Input file not found: %s", args.input_file)
        exit_code = 1
    except OrchestratorError as exc:
        logger.error(str(exc))
        exit_code = 1
    except Exception:  # pragma: no cover - defensive catch-all
        logger.error("Unexpected error during CLI execution", exc_info=True)
        exit_code = 1
    finally:
        if exit_code == 0 and rule_count is None:
            rule_count = 0
        log_final_summary(logger, summary_handler, rule_count=rule_count, success=exit_code == 0)
        for handler in list(logger.handlers):
            handler.close()
        logger.handlers.clear()

    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
