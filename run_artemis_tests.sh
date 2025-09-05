#!/bin/bash

# Test script for Artemis Data Collector with Failover Support

echo "Running Artemis Data Collector Failover Tests..."

# Set up Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run the tests
python -m pytest src/artemis_data_collector/test_artemis_data_collector_failover.py -v

echo "Test execution completed."
