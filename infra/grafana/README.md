# Grafana Configuration

This directory contains Grafana dashboard and alerting configurations for Deal Brain monitoring.

## Directory Structure

```
infra/grafana/
├── dashboards/              # Dashboard JSON definitions
│   └── entity-crud-dashboard.json
├── provisioning/            # Grafana provisioning configs
│   ├── dashboards/          # Dashboard provisioning
│   │   └── dashboard.yml
│   ├── datasources/         # Data source provisioning
│   │   └── datasource.yml
│   └── alerting/            # Alert rule provisioning
│       └── entity-crud-alerts.yml
└── README.md                # This file
```

## Dashboards

### Entity CRUD Operations
**File**: `dashboards/entity-crud-dashboard.json`

Monitors UPDATE and DELETE operations for all catalog entities:
- Request rates
- Error rates (4xx, 5xx)
- Latency percentiles (P50, P95, P99)
- Business metrics (entities updated/deleted, blocked deletes)

**Panels**: 10 panels covering performance and operational metrics

**Auto-refresh**: 30 seconds

**Default time range**: Last 1 hour

## Provisioning

### Data Sources
**File**: `provisioning/datasources/datasource.yml`

Configures Prometheus as the default data source:
- **URL**: `http://prometheus:9090`
- **Type**: Prometheus
- **Access**: Proxy (via Grafana backend)

### Dashboard Provisioning
**File**: `provisioning/dashboards/dashboard.yml`

Automatically loads dashboards from `/etc/grafana/dashboards`:
- Auto-discovers JSON files in the dashboards directory
- Allows UI updates (changes won't persist across restarts)
- 10-second update interval

### Alert Rules
**File**: `provisioning/alerting/entity-crud-alerts.yml`

Defines 3 alert rules:
1. **High Error Rate** (Critical): 5xx errors > 5% for 5 minutes
2. **Slow DELETE Operations** (Warning): P95 latency > 2s for 5 minutes
3. **Slow UPDATE Operations** (Warning): P95 latency > 500ms for 5 minutes

## Usage

### Accessing Grafana

```bash
# Start the stack
make up

# Access Grafana
open http://localhost:3021
```

**Credentials**: `admin` / `admin`

### Making Changes

#### Option 1: Edit JSON Directly (Recommended for Version Control)

1. Edit the JSON file in `dashboards/`
2. Restart Grafana to apply changes:
   ```bash
   docker-compose restart grafana
   ```

#### Option 2: Edit in UI, Export to JSON

1. Make changes in Grafana UI
2. Export dashboard: Dashboard Settings → JSON Model
3. Copy JSON to `dashboards/entity-crud-dashboard.json`
4. Commit to version control
5. Changes will persist across Grafana restarts

### Adding New Dashboards

1. Create new JSON file in `dashboards/` directory
2. Dashboard will be auto-discovered on Grafana restart
3. Alternatively, create in UI and export to JSON

### Modifying Alerts

1. Edit `provisioning/alerting/entity-crud-alerts.yml`
2. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```
3. Verify in Grafana UI: Alerting → Alert Rules

## Development

### Testing Dashboard Changes

```bash
# Validate JSON syntax
cat dashboards/entity-crud-dashboard.json | jq .

# Restart Grafana to load changes
docker-compose restart grafana

# Check logs for errors
docker-compose logs grafana | tail -50
```

### Testing Alert Rules

```bash
# Validate YAML syntax
yamllint provisioning/alerting/entity-crud-alerts.yml

# Check Grafana alert rule loading
docker-compose logs grafana | grep -i alert
```

### Generating Test Metrics

```bash
# Run API tests to generate metrics
make test

# Make manual API requests
curl -X PATCH http://localhost:8020/api/v1/catalog/cpu/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Test CPU"}'
```

## Docker Configuration

The Grafana service mounts these directories:

```yaml
# docker-compose.yml
grafana:
  volumes:
    - ./infra/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./infra/grafana/dashboards:/etc/grafana/dashboards:ro
```

**Note**: `:ro` means read-only. Changes made in the Grafana UI won't persist to these files.

## Troubleshooting

### Dashboard Not Appearing

**Check provisioning**:
```bash
docker-compose exec grafana ls -la /etc/grafana/provisioning/dashboards/
docker-compose exec grafana ls -la /etc/grafana/dashboards/
```

**Check logs**:
```bash
docker-compose logs grafana | grep -i dashboard
```

### Data Source Not Working

**Verify Prometheus is accessible**:
```bash
docker-compose exec grafana wget -qO- http://prometheus:9090/api/v1/status/config
```

**Check data source config**:
```bash
docker-compose exec grafana cat /etc/grafana/provisioning/datasources/datasource.yml
```

### Alerts Not Showing

**Check alert provisioning**:
```bash
docker-compose exec grafana ls -la /etc/grafana/provisioning/alerting/
docker-compose logs grafana | grep -i alert
```

## Resources

- [Grafana Provisioning Documentation](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana Dashboard JSON Model](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/)
- [Grafana Alerting Documentation](https://grafana.com/docs/grafana/latest/alerting/)
- [Deal Brain Monitoring Guide](/docs/observability/entity-crud-monitoring.md)
