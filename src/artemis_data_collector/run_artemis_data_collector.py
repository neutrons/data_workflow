#!/usr/bin/env python3
"""
Artemis Data Collector Entry Point with Failover Support

This script serves as the entry point for the artemis data collector
with failover broker functionality.
"""

if __name__ == "__main__":
    import sys

    from artemis_data_collector.artemis_data_collector import main

    sys.exit(main())
