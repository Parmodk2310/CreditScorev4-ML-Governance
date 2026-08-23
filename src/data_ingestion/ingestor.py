"""
Data Ingestion Module for CreditScoreV4
Handles upstream vendor API integration, batch processing, and raw data landing.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class VendorAPIClient:
    """Client for upstream credit data aggregator API with retry logic."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url or os.getenv("UPSTREAM_VENDOR_API_URL", "")
        self.api_key = api_key or os.getenv("UPSTREAM_VENDOR_API_KEY", "")
        self.timeout = timeout
        
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Client-Version": "4.2.1",
        })
        
        logger.info(f"Initialized VendorAPIClient for {self.base_url}")
    
    def fetch_batch(
        self,
        batch_date: datetime,
        batch_size: int = 10000,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch a batch of credit application data from upstream vendor."""
        endpoint = f"{self.base_url}/v2/applications"
        
        params = {
            "date_from": batch_date.strftime("%Y-%m-%d"),
            "date_to": batch_date.strftime("%Y-%m-%d"),
            "limit": batch_size,
            "offset": offset,
            "include_features": "all",
        }
        
        try:
            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(
                f"Fetched batch: {len(data.get('applications', []))} records, "
                f"offset={offset}, has_more={data.get('has_more', False)}"
            )
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch batch from vendor API: {e}")
            raise VendorAPIError(f"API request failed: {e}") from e
    
    def fetch_schema(self) -> Dict[str, Any]:
        """Fetch current schema from upstream vendor for validation."""
        endpoint = f"{self.base_url}/v2/schema"
        
        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch schema: {e}")
            raise VendorAPIError(f"Schema fetch failed: {e}") from e


class DataIngestor:
    """Orchestrates data ingestion from upstream vendor to data lake."""
    
    def __init__(
        self,
        raw_data_path: str = "data/raw",
        vendor_client: Optional[VendorAPIClient] = None,
    ):
        self.raw_data_path = Path(raw_data_path)
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.vendor_client = vendor_client or VendorAPIClient()
        
        # Track ingestion metadata
        self.ingestion_metadata: Dict[str, Any] = {}
        
        logger.info(f"Initialized DataIngestor with raw path: {self.raw_data_path}")
    
    def ingest_daily_batch(
        self,
        ingestion_date: Optional[datetime] = None,
        batch_size: int = 10000,
    ) -> str:
        """
        Ingest a full day of data from upstream vendor.
        
        Returns:
            Path to the saved parquet file.
        """
        ingestion_date = ingestion_date or datetime.now(timezone.utc)
        date_str = ingestion_date.strftime("%Y-%m-%d")
        
        logger.info(f"Starting daily ingestion for {date_str}")
        
        all_records: List[Dict[str, Any]] = []
        offset = 0
        total_records = 0
        
        while True:
            try:
                batch = self.vendor_client.fetch_batch(
                    batch_date=ingestion_date,
                    batch_size=batch_size,
                    offset=offset,
                )
                
                records = batch.get("applications", [])
                if not records:
                    break
                
                all_records.extend(records)
                total_records += len(records)
                
                if not batch.get("has_more", False):
                    break
                
                offset += batch_size
                
                # Safety limit
                if total_records > 1_000_000:
                    logger.warning("Hit safety limit of 1M records, stopping ingestion")
                    break
                    
            except VendorAPIError:
                logger.error(f"Failed at offset {offset}, saving partial data")
                break
        
        if not all_records:
            logger.warning(f"No records found for {date_str}")
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Add ingestion metadata
        df["_ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
        df["_ingestion_date"] = date_str
        df["_ingestion_version"] = "4.2.1"
        df["_record_hash"] = df.apply(
            lambda row: hashlib.sha256(
                json.dumps(row.to_dict(), default=str, sort_keys=True).encode()
            ).hexdigest()[:16],
            axis=1,
        )
        
        # Save to parquet with partitioning
        output_path = self.raw_data_path / f"date={date_str}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        parquet_file = output_path / f"credit_applications_{date_str}.parquet"
        df.to_parquet(parquet_file, index=False, compression="snappy")
        
        # Save ingestion metadata
        self.ingestion_metadata = {
            "date": date_str,
            "total_records": total_records,
            "file_path": str(parquet_file),
            "file_size_mb": parquet_file.stat().st_size / (1024 * 1024),
            "schema_version": batch.get("schema_version", "unknown"),
            "vendor_api_version": batch.get("api_version", "unknown"),
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "null_counts": df.isnull().sum().to_dict(),
            "column_dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
        
        metadata_path = output_path / f"metadata_{date_str}.json"
        with open(metadata_path, "w") as f:
            json.dump(self.ingestion_metadata, f, indent=2, default=str)
        
        logger.info(
            f"Ingestion complete: {total_records} records saved to {parquet_file} "
            f"({self.ingestion_metadata['file_size_mb']:.2f} MB)"
        )
        
        return str(parquet_file)
    
    def get_ingestion_metadata(self) -> Dict[str, Any]:
        """Return metadata from the most recent ingestion."""
        return self.ingestion_metadata
    
    def load_raw_data(self, date_str: str) -> pd.DataFrame:
        """Load raw data for a specific date."""
        parquet_file = self.raw_data_path / f"date={date_str}" / f"credit_applications_{date_str}.parquet"
        
        if not parquet_file.exists():
            raise FileNotFoundError(f"No raw data found for date: {date_str}")
        
        return pd.read_parquet(parquet_file)


class VendorAPIError(Exception):
    """Custom exception for vendor API failures."""
    pass


class IngestionMetrics:
    """Collect and expose ingestion metrics for monitoring."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "total_ingestions": 0,
            "total_records_ingested": 0,
            "failed_ingestions": 0,
            "avg_records_per_ingestion": 0,
            "last_ingestion_timestamp": None,
        }
    
    def record_ingestion(self, record_count: int, success: bool = True):
        """Record metrics for a single ingestion run."""
        self.metrics["total_ingestions"] += 1
        self.metrics["last_ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
        
        if success:
            self.metrics["total_records_ingested"] += record_count
            self.metrics["avg_records_per_ingestion"] = (
                self.metrics["total_records_ingested"] / self.metrics["total_ingestions"]
            )
        else:
            self.metrics["failed_ingestions"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return current metrics."""
        return self.metrics.copy()


if __name__ == "__main__":
    # Example usage
    ingestor = DataIngestor()
    file_path = ingestor.ingest_daily_batch()
    print(f"Ingested data saved to: {file_path}")