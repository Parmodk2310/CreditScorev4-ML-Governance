# CreditScoreV4 ML Governance

> Production ML Incident Simulation, Remediation & Governance

## Overview

This project simulates and remediates a real production ML failure in a consumer lending platform where **CreditScoreV4** degraded from **AUC 0.81 to 0.74** after an upstream vendor migration introduced silent data quality failures.

## Key Metrics

| Metric | Before | After Incident | After Remediation |
|--------|--------|----------------|-------------------|
| Model AUC | 0.81 | 0.74 | 0.82 |
| Delinquency Rate | 3.1% | 5.4% | 3.2% |
| device_risk_score NULL Rate | 3% | 22% | < 1% |
| PSI (Score) | 0.03 | 0.35 | 0.04 |
| Disparate Impact (Race) | 0.92 | 0.71 | 0.89 |

## Architecture

```
Data Sources -> Data Quality Gate -> Feature Store -> Model Training -> Model Registry
                                              -> Drift Detection -> Fairness Audit
                                              -> Shadow Deployment -> Canary -> Production
```

## Project Structure

```
creditscorev4-ml-governance/
├── .github/workflows/       # CI/CD pipelines
├── airflow/dags/            # Orchestration DAGs
├── configs/                 # All configuration files
├── data/                    # Raw, processed, reference data
├── docs/                    # Architecture, runbooks, incident reports
├── notebooks/               # Analysis notebooks
├── src/                     # Production source code
├── tests/                   # Unit, integration, e2e tests
├── scripts/                 # Utility scripts
├── docker/                  # Container definitions
└── terraform/               # Infrastructure-as-code
```

## Quick Start

```bash
# 1. Setup environment
make setup

# 2. Start local stack
make up

# 3. Run data quality validation
make validate-data

# 4. Run drift detection
make check-drift

# 5. Run fairness audit
make audit-fairness
```

## Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Complete directory structure |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture & data flow |
| [BUILD_GUIDE.md](BUILD_GUIDE.md) | Step-by-step build instructions |

## Technology Stack

- **ML**: scikit-learn, XGBoost, LightGBM
- **Feature Store**: Feast
- **Model Registry**: MLflow
- **Data Validation**: Great Expectations
- **Drift Detection**: Custom PSI + KS Test
- **Fairness**: Fairlearn, SHAP
- **Serving**: FastAPI, Docker
- **Orchestration**: Apache Airflow
- **Monitoring**: Prometheus, Grafana
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform, AWS EKS

## Business Outcomes

- Diagnosed root cause of AUC degradation within 48-hour SLA
- Eliminated monitoring blind spots via automated data contracts
- Quantified fairness violations: 11pp minority approval rate drop
- Designed governance framework meeting regulatory compliance standards
- Reduced model drift detection time from weeks to hours
- Enabled safe deployment lifecycle with shadow testing infrastructure

## License

MIT License - See [LICENSE](LICENSE) for details.
