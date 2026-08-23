# Project Structure

```text
creditscorev4-ml-governance
├── .github
│   └── workflows
│       ├── cd.yml
│       ├── ci.yml
│       └── drift-detection.yml
├── airflow
│   ├── config
│   │   └── airflow.cfg
│   ├── dags
│   │   ├── data_quality_gate_dag.py
│   │   ├── drift_monitoring_dag.py
│   │   ├── fairness_audit_dag.py
│   │   └── retraining_pipeline.py
│   └── plugins
│       ├── hooks
│       │   └── mlflow_hook.py
│       └── operators
│           ├── drift_detector.py
│           ├── fairness_check.py
│           └── model_validation.py
├── configs
│   ├── data
│   │   ├── data_contract.yaml
│   │   └── schema_definitions.yaml
│   ├── infrastructure
│   │   ├── kubernetes
│   │   │   ├── model-deployment.yaml
│   │   │   └── monitoring-stack.yaml
│   │   └── docker-compose.yml
│   ├── model
│   │   ├── creditscorev4_config.yaml
│   │   └── feature_config.yaml
│   └── monitoring
│       ├── alert_rules.yaml
│       ├── drift_thresholds.yaml
│       └── fairness_thresholds.yaml
├── data
│   ├── great_expectations
│   │   ├── checkpoints
│   │   │   ├── ingestion_checkpoint.yml
│   │   │   └── pretraining_checkpoint.yml
│   │   ├── expectations
│   │   │   ├── creditscore_suite.json
│   │   │   └── vendor_data_suite.json
│   │   └── great_expectations.yml
│   ├── processed
│   │   ├── inference
│   │   ├── training
│   │   └── validation
│   ├── raw
│   │   ├── vendor_a
│   │   └── vendor_b
│   └── reference
│       ├── baseline_distributions
│       └── fairness_baseline
├── docker
│   ├── Dockerfile.airflow
│   ├── Dockerfile.model
│   ├── Dockerfile.monitoring
│   └── entrypoint.sh
├── docs
│   ├── api
│   │   ├── model_api.md
│   │   └── monitoring_api.md
│   ├── architecture
│   │   ├── data_flow_diagram.md
│   │   ├── mlops_pipeline.md
│   │   └── system_architecture.md
│   ├── fairness
│   │   ├── bias_mitigation.md
│   │   ├── fairness_framework.md
│   │   └── regulatory_compliance.md
│   ├── incident
│   │   ├── incident_report.md
│   │   ├── post_mortem.md
│   │   └── timeline.md
│   └── runbooks
│       ├── incident_response.md
│       ├── model_rollback.md
│       ├── retraining.md
│       └── shadow_deployment.md
├── notebooks
│   ├── 01_eda_and_root_cause.ipynb
│   ├── 02_drift_analysis.ipynb
│   ├── 03_fairness_audit.ipynb
│   ├── 04_shap_bias_attribution.ipynb
│   ├── 05_model_remediation.ipynb
│   └── 06_monitoring_dashboard.ipynb
├── scripts
│   ├── deploy_shadow_model.sh
│   ├── generate_fairness_report.sh
│   ├── run_drift_check.sh
│   ├── setup_environment.sh
│   └── trigger_retraining.sh
├── src
│   ├── data
│   │   ├── __init__.py
│   │   ├── contracts.py
│   │   ├── ingestion.py
│   │   ├── preprocessing.py
│   │   └── validation.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── creditscorev4.py
│   │   ├── evaluation.py
│   │   ├── registry.py
│   │   ├── rollback.py
│   │   └── training.py
│   ├── monitoring
│   │   ├── dashboards
│   │   │   ├── __init__.py
│   │   │   ├── drift_dashboard.py
│   │   │   └── fairness_dashboard.py
│   │   ├── drift
│   │   │   ├── __init__.py
│   │   │   ├── alerts.py
│   │   │   ├── feature_drift.py
│   │   │   ├── psi.py
│   │   │   └── score_drift.py
│   │   ├── fairness
│   │   │   ├── __init__.py
│   │   │   ├── disparate_impact.py
│   │   │   ├── metrics.py
│   │   │   ├── reports.py
│   │   │   └── shap_analysis.py
│   │   └── __init__.py
│   ├── pipelines
│   │   ├── __init__.py
│   │   ├── deployment_pipeline.py
│   │   ├── retraining.py
│   │   └── validation_pipeline.py
│   ├── serving
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── batch_inference.py
│   │   ├── canary.py
│   │   └── shadow_deployment.py
│   └── utils
│       ├── __init__.py
│       ├── config_loader.py
│       ├── exceptions.py
│       └── logging.py
├── terraform
│   ├── environments
│   │   ├── dev
│   │   ├── prod
│   │   └── staging
│   ├── modules
│   │   ├── airflow
│   │   ├── eks
│   │   ├── mlflow
│   │   ├── prometheus
│   │   ├── rds
│   │   └── s3
│   ├── main.tf
│   └── variables.tf
├── tests
│   ├── e2e
│   │   ├── test_full_pipeline.py
│   │   └── test_incident_response.py
│   ├── fixtures
│   │   ├── expected_metrics.yaml
│   │   ├── mock_predictions.json
│   │   └── sample_data.csv
│   ├── integration
│   │   ├── test_deployment_pipeline.py
│   │   ├── test_ingestion_pipeline.py
│   │   ├── test_monitoring_stack.py
│   │   └── test_retraining_pipeline.py
│   └── unit
│       ├── test_data_validation.py
│       ├── test_drift_detection.py
│       ├── test_fairness_metrics.py
│       ├── test_model_training.py
│       └── test_preprocessing.py
├── .dockerignore
├── .gitignore
├── CHANGELOG.md
├── env.example
├── LICENSE
├── Makefile
├── PROJECT_STRUCTURE.md
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.txt
└── setup.py
```

## Statistics

- Total folders: **64**
- Total files: **123**
