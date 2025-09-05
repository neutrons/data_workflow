# WebMon Artemis Data Collector Failover Setup Guide

## Overview

This guide explains how to configure and deploy the WebMon Artemis Data Collector with failover broker support. The failover functionality allows the data collector to automatically switch to a backup broker when the primary broker becomes unavailable.

## Production Setup

### 1. Broker Configuration

Configure two Artemis brokers with identical settings:

**Primary Broker (e.g., amqbroker1.sns.gov:8161)**
- Main production broker
- Should be monitored and maintained as primary

**Failover Broker (e.g., amqbroker2.sns.gov:8161)**
- Backup broker with same configuration
- Should mirror the primary broker's queue structure

### 2. Environment Configuration

Update your `.env` file or environment variables:

```bash
# Primary broker (required)
ARTEMIS_URL=http://amqbroker1.sns.gov:8161

# Failover broker (optional but recommended for production)
ARTEMIS_FAILOVER_URL=http://amqbroker2.sns.gov:8161

# Standard configuration
ARTEMIS_USER=artemis
ARTEMIS_PASSWORD=your_password
ARTEMIS_BROKER_NAME=Artemis-Broker
```

### 3. Docker Compose Configuration

The docker-compose.yml already includes failover support:

```yaml
artemis_data_collector:
  restart: always
  build:
    context: .
    dockerfile: Dockerfile.artemis_data_collector
  environment:
    ARTEMIS_URL: http://activemq:8161
    ARTEMIS_FAILOVER_URL: ${ARTEMIS_FAILOVER_URL:-}
    # ... other settings
```

### 4. Deployment

Deploy the updated configuration:

```bash
# Build and start the container
docker-compose up -d artemis_data_collector

# Check logs for failover configuration
docker-compose logs artemis_data_collector
```

## Monitoring and Alerting

### Log Messages to Monitor

**Normal Operation:**
```
INFO - Successfully collected data for 4 queues
INFO - Successfully added records to the database
```

**Failover Events:**
```
ERROR - Primary broker connection error: Connection refused
INFO - Primary broker failed, trying failover broker
INFO - Successfully connected to failover broker
```

**Complete Failure:**
```
ERROR - Primary broker connection error: Connection refused
ERROR - Failover broker connection error: Connection refused
WARNING - No failover broker configured
```

### Recommended Monitoring

1. **Log Monitoring**: Set up alerts for "failover broker" messages
2. **Database Monitoring**: Check for gaps in `report_statusqueuemessagecount` table
3. **Broker Health**: Monitor both primary and failover broker health
4. **Network Connectivity**: Ensure network path to both brokers

## Testing Failover

### Manual Testing Steps

1. **Verify Normal Operation**
   ```bash
   # Check logs show successful data collection
   docker-compose logs artemis_data_collector | grep "Successfully collected"
   ```

2. **Simulate Primary Failure**
   ```bash
   # Option 1: Block network access to primary broker
   # Option 2: Temporarily stop primary broker service
   # Option 3: Update ARTEMIS_URL to invalid URL and restart container
   ```

3. **Verify Failover**
   ```bash
   # Look for failover messages in logs
   docker-compose logs artemis_data_collector | grep -i failover

   # Verify data collection continues
   docker-compose logs artemis_data_collector | grep "Successfully collected"
   ```

4. **Restore Primary**
   ```bash
   # Restore primary broker
   # Next collection cycle should use primary again
   ```

### Automated Testing

Create a monitoring script to test failover regularly:

```bash
#!/bin/bash
# Check if data collection is working
RECENT_RECORDS=$(psql -h localhost -U workflow -d workflow -t -c \
  "SELECT COUNT(*) FROM report_statusqueuemessagecount WHERE created_on > NOW() - INTERVAL '10 minutes'")

if [ "$RECENT_RECORDS" -eq 0 ]; then
  echo "ALERT: No recent data collection records found"
  exit 1
else
  echo "OK: Found $RECENT_RECORDS recent records"
fi
```

## Troubleshooting

### Common Issues

**Issue**: Failover not working
- **Check**: ARTEMIS_FAILOVER_URL is set correctly
- **Check**: Failover broker is accessible from container
- **Check**: Network connectivity and firewall rules

**Issue**: Both brokers failing
- **Check**: Broker services are running
- **Check**: Authentication credentials
- **Check**: Network connectivity
- **Check**: Broker configuration (broker name, ports)

**Issue**: Data collection stops
- **Check**: Database connectivity
- **Check**: Queue configuration in database
- **Check**: Container resource limits

### Debug Commands

```bash
# Check container logs
docker-compose logs artemis_data_collector

# Check container environment
docker-compose exec artemis_data_collector env | grep ARTEMIS

# Test network connectivity from container
docker-compose exec artemis_data_collector curl -f http://amqbroker1.sns.gov:8161/console/

# Check database records
psql -h localhost -U workflow -d workflow -c \
  "SELECT * FROM report_statusqueuemessagecount ORDER BY created_on DESC LIMIT 10;"
```

## Performance Considerations

### Timeout Settings

The current implementation uses default HTTP timeouts. For production, consider:

- **Connection Timeout**: How long to wait for initial connection
- **Read Timeout**: How long to wait for response
- **Retry Delay**: Time between primary and failover attempts

### Resource Usage

- **Memory**: Minimal additional memory overhead
- **Network**: Failover attempts add minimal network overhead
- **Database**: No additional database overhead

### Scaling

- **Multiple Collectors**: Each collector instance handles failover independently
- **Load Balancing**: Can use multiple failover brokers with round-robin
- **Geographic Distribution**: Failover brokers can be in different locations

## Security Considerations

### Authentication

- Both brokers should use the same authentication credentials
- Credentials should be stored securely (environment variables, secrets)
- Regular credential rotation should include both brokers

### Network Security

- Firewall rules should allow access to both brokers
- Consider using VPN or private networks for broker communication
- Monitor access logs on both brokers

### Monitoring Access

- Log access attempts to both brokers
- Alert on repeated failover events (may indicate attack or misconfiguration)
- Monitor for unusual access patterns

## Migration Guide

### From External Image

If migrating from the external artemis_data_collector image:

1. **Backup Current Configuration**
   ```bash
   docker-compose config > backup-docker-compose.yml
   ```

2. **Update docker-compose.yml**
   Replace the image reference with build configuration (already done)

3. **Add Failover Configuration**
   Set ARTEMIS_FAILOVER_URL environment variable

4. **Test Migration**
   ```bash
   docker-compose down artemis_data_collector
   docker-compose up -d artemis_data_collector
   ```

5. **Verify Operation**
   Monitor logs and database for continued data collection

### Rollback Plan

To rollback to external image:

```yaml
artemis_data_collector:
  restart: always
  image: ghcr.io/neutrons/artemis_data_collector/artemis_data_collector:latest-prod
  # Remove build section
  # Keep environment variables (ARTEMIS_FAILOVER_URL will be ignored)
```

## Support and Maintenance

### Regular Maintenance

1. **Monitor Logs**: Weekly review of failover events
2. **Test Failover**: Monthly failover testing
3. **Update Brokers**: Coordinate updates of both brokers
4. **Review Configuration**: Quarterly review of settings

### Escalation Procedures

1. **Data Collection Stops**: Contact Neutron Data Sciences Group
2. **Frequent Failovers**: Check primary broker health
3. **Both Brokers Fail**: Emergency broker restart procedure
4. **Performance Issues**: Review container resources and network

For technical support, contact the development team with:
- Container logs
- Network connectivity test results
- Database query results
- Timeline of issues
