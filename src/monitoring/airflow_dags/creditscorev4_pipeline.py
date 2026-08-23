"""
Airflow DAG for CreditScoreV4 MLOps Pipeline.
Orchestrates: ingestion → validation → preprocessing → training → validation → drift → fairness → deployment
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.dates import days_ago

# Default args
default_args = {
    "owner": "ml-engineering",
    "depends_on_past": False,
    "email": ["ml-alerts@company.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

dag = DAG(
    "creditscorev4_pipeline",
    default_args=default_args,
    description="CreditScoreV4 ML Pipeline - Daily retraining and monitoring",
    schedule_interval="0 2 * * *",  # Daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["creditscorev4", "ml", "production"],
)


def data_ingestion_task(**context):
    """Task: Ingest data from upstream vendor."""
    from src.data_ingestion.ingestor import DataIngestor
    
    ingestor = DataIngestor()
    file_path = ingestor.ingest_daily_batch()
    
    context["ti"].xcom_push(key="raw_data_path", value=file_path)
    context["ti"].xcom_push(key="ingestion_metadata", value=ingestor.get_ingestion_metadata())
    
    return f"Ingested: {file_path}"


def data_validation_task(**context):
    """Task: Validate data quality with Great Expectations."""
    from src.data_validation.great_expectations_suite import CreditScoreV4ValidationSuite
    from src.data_validation.schema_validator import SchemaDriftDetector
    
    ti = context["ti"]
    raw_path = ti.xcom_pull(task_ids="data_ingestion", key="raw_data_path")
    
    import pandas as pd
    df = pd.read_parquet(raw_path)
    
    # Schema drift check
    schema_detector = SchemaDriftDetector()
    drift_result = schema_detector.detect_drift(df)
    
    if drift_result["drift_detected"] and drift_result["critical_violations"] > 0:
        raise ValueError(f"Critical schema drift detected: {drift_result['violations']}")
    
    # Great Expectations validation
    validator = CreditScoreV4ValidationSuite()
    validation_result = validator.validate_dataframe(df)
    
    if not validation_result["passed"]:
        raise ValueError(f"Data quality validation failed: {validation_result['failed_expectations']} expectations failed")
    
    return "Data validation passed"


def preprocessing_task(**context):
    """Task: Preprocess data."""
    from src.preprocessing.preprocessor import CreditScoreV4Preprocessor, PreprocessingConfig
    
    ti = context["ti"]
    raw_path = ti.xcom_pull(task_ids="data_ingestion", key="raw_data_path")
    
    import pandas as pd
    df = pd.read_parquet(raw_path)
    
    config = PreprocessingConfig(
        numerical_features=["annual_income", "debt_to_income_ratio", "credit_history_length",
                          "device_risk_score", "employment_length", "num_credit_lines", "avg_credit_utilization"],
        categorical_features=["loan_purpose", "home_ownership", "verification_status"],
        protected_attributes=["race", "gender", "age_group"],
    )
    
    preprocessor = CreditScoreV4Preprocessor(config)
    processed_df = preprocessor.fit_transform(df)
    
    # Save preprocessor
    preprocessor_path = f"models/preprocessor_{context['ds']}.pkl"
    preprocessor.save(preprocessor_path)
    
    # Save processed data
    processed_path = f"data/processed/processed_{context['ds']}.parquet"
    processed_df.to_parquet(processed_path)
    
    ti.xcom_push(key="processed_data_path", value=processed_path)
    ti.xcom_push(key="preprocessor_path", value=preprocessor_path)
    
    return f"Preprocessed: {processed_path}"


def model_training_task(**context):
    """Task: Train XGBoost model."""
    from src.model_training.trainer import CreditScoreV4Trainer, ModelConfig
    
    ti = context["ti"]
    processed_path = ti.xcom_pull(task_ids="preprocessing", key="processed_data_path")
    
    import pandas as pd
    df = pd.read_parquet(processed_path)
    
    trainer = CreditScoreV4Trainer()
    X_train, y_train, X_test, y_test = trainer.prepare_data(df)
    
    # Cross-validation
    cv_results = trainer.cross_validate(
        pd.concat([X_train, X_test]),
        pd.concat([y_train, y_test]),
    )
    
    # Train final model
    trainer.train(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)
    
    # Check thresholds
    passed, failures = metrics.meets_thresholds(trainer.config)
    if not passed:
        raise ValueError(f"Model does not meet thresholds: {failures}")
    
    # Log to MLflow
    run_id = trainer.log_to_mlflow()
    
    # Save model
    model_path = f"models/creditscorev4_{context['ds']}.pkl"
    trainer.save_model(model_path)
    
    ti.xcom_push(key="model_path", value=model_path)
    ti.xcom_push(key="mlflow_run_id", value=run_id)
    ti.xcom_push(key="model_auc", value=metrics.metrics["auc"])
    
    return f"Model trained: AUC={metrics.metrics['auc']:.4f}"


def drift_detection_task(**context):
    """Task: Run drift detection."""
    from src.drift_detection.psi_calculator import PSICalculator, PSIDriftConfig
    
    ti = context["ti"]
    processed_path = ti.xcom_pull(task_ids="preprocessing", key="processed_data_path")
    
    import pandas as pd
    df = pd.read_parquet(processed_path)
    
    # Load baseline
    calculator = PSICalculator.load_baseline("data/validation/baseline_psi.json")
    
    report = calculator.detect_all_drift(df)
    calculator.save_report(report)
    
    if report["overall_status"] == "critical":
        raise ValueError(f"Critical drift detected: {report['critical_features']} features")
    
    return f"Drift check: {report['overall_status']}"


def fairness_audit_task(**context):
    """Task: Run fairness audit."""
    from src.fairness_monitoring.fairness_metrics import FairnessMetricsCalculator, FairnessConfig
    
    ti = context["ti"]
    processed_path = ti.xcom_pull(task_ids="preprocessing", key="processed_data_path")
    
    import pandas as pd
    df = pd.read_parquet(processed_path)
    
    # Add predictions
    from src.model_training.trainer import CreditScoreV4Trainer
    model_path = ti.xcom_pull(task_ids="model_training", key="model_path")
    model, _ = CreditScoreV4Trainer.load_model(model_path)
    
    feature_cols = [c for c in df.columns if c not in ["race", "gender", "age_group", "delinquent"]]
    df["predicted_score"] = model.predict_proba(df[feature_cols])[:, 1]
    
    calculator = FairnessMetricsCalculator()
    report = calculator.compute_all_metrics(df)
    calculator.save_report(report)
    
    if report["overall_status"] == "critical":
        raise ValueError(f"Critical fairness violations: {report['critical_violations']}")
    
    return f"Fairness audit: {report['overall_status']}"


def model_registration_task(**context):
    """Task: Register model in MLflow model registry."""
    import mlflow
    
    ti = context["ti"]
    run_id = ti.xcom_pull(task_ids="model_training", key="mlflow_run_id")
    
    # Transition to staging
    client = mlflow.tracking.MlflowClient()
    model_version = client.create_model_version(
        name="creditscorev4",
        source=f"runs:/{run_id}/model",
        run_id=run_id,
    )
    
    client.transition_model_version_stage(
        name="creditscorev4",
        version=model_version.version,
        stage="Staging",
    )
    
    return f"Model registered: version {model_version.version}"


# Define tasks
t1_ingestion = PythonOperator(
    task_id="data_ingestion",
    python_callable=data_ingestion_task,
    dag=dag,
)

t2_validation = PythonOperator(
    task_id="data_validation",
    python_callable=data_validation_task,
    dag=dag,
)

t3_preprocessing = PythonOperator(
    task_id="preprocessing",
    python_callable=preprocessing_task,
    dag=dag,
)

t4_training = PythonOperator(
    task_id="model_training",
    python_callable=model_training_task,
    dag=dag,
)

t5_drift = PythonOperator(
    task_id="drift_detection",
    python_callable=drift_detection_task,
    dag=dag,
)

t6_fairness = PythonOperator(
    task_id="fairness_audit",
    python_callable=fairness_audit_task,
    dag=dag,
)

t7_register = PythonOperator(
    task_id="model_registration",
    python_callable=model_registration_task,
    dag=dag,
)

# Dependencies
t1_ingestion >> t2_validation >> t3_preprocessing
t3_preprocessing >> [t4_training, t5_drift]
t4_training >> t6_fairness >> t7_register
