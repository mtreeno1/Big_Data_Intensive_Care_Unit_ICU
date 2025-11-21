#!/usr/bin/env python3
"""Train the vital-sign alert classifier from the labelled patient dataset."""

import argparse
import logging
import sys
from pathlib import Path

# Make src importable when executed as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings  # noqa: E402
from src.ml.alert_model import train_alert_model  # noqa: E402


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the streaming alert classifier")
    default_input = Path(settings.TRAINING_DATA_PATH)
    if not default_input.is_absolute():
        default_input = (Path(__file__).parent.parent / default_input).resolve()
    default_model = Path(settings.ALERT_MODEL_PATH)
    if not default_model.is_absolute():
        default_model = (Path(__file__).parent.parent / default_model).resolve()
    default_metrics = default_model.with_name(default_model.stem + "_metrics.json")

    parser.add_argument("--input", type=Path, default=default_input, help="Path to patients_data_with_alerts.xlsx")
    parser.add_argument("--model-out", type=Path, default=default_model, help="Destination for the trained model artifact")
    parser.add_argument("--metrics-out", type=Path, default=default_metrics, help="Where to write evaluation metrics JSON")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument("--n-estimators", type=int, default=300, help="Random forest tree count")
    parser.add_argument("--max-depth", type=int, default=None, help="Random forest max depth")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(verbose=args.verbose)

    logging.info("Training alert model from %s", args.input)
    metrics = train_alert_model(
        input_path=args.input,
        model_path=args.model_out,
        metrics_path=args.metrics_out,
        test_size=args.test_size,
        random_state=args.random_state,
        estimator_kwargs={
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
        },
    )

    logging.info("Training complete. Metrics:\n%s", metrics)


if __name__ == "__main__":
    main()
