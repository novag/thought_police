#!/usr/bin/env python3
"""
Supply Chain Optimizer - Main Application Entry Point

This module serves as the entry point for the Supply Chain Optimizer application.
It initializes all necessary components and starts the application.
"""

import sys
import logging
from pathlib import Path
import argparse
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Import application components
from config.settings import Settings
from services.database import DatabaseManager
from api.server import start_api_server
from dashboard.app import start_dashboard
from utils.logger import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Supply Chain Optimizer")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Start only the dashboard component",
    )
    parser.add_argument(
        "--api-only", action="store_true", help="Start only the API server component"
    )
    return parser.parse_args()


def initialize_application(config_path):
    """Initialize the application components."""
    # Load environment variables
    load_dotenv()

    # Load application settings
    settings = Settings(config_path)

    # Initialize database connection
    db_manager = DatabaseManager(settings.database)

    return settings, db_manager


def main():
    """Main application entry point."""
    args = parse_arguments()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting Supply Chain Optimizer")

    try:
        # Initialize application
        settings, db_manager = initialize_application(args.config)

        # Start components based on arguments
        if args.dashboard_only:
            logger.info("Starting dashboard only")
            start_dashboard(settings)
        elif args.api_only:
            logger.info("Starting API server only")
            start_api_server(settings, db_manager)
        else:
            # Start both components
            logger.info("Starting all components")
            # Start API server in a separate process
            import multiprocessing

            api_process = multiprocessing.Process(
                target=start_api_server, args=(settings, db_manager)
            )
            api_process.start()

            # Start dashboard in the main process
            start_dashboard(settings)

    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
