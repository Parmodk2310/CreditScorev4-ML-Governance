"""CLI for data ingestion operations."""

import typer
from datetime import datetime, timezone
from loguru import logger

from .ingestor import DataIngestor

app = typer.Typer(help="CreditScoreV4 Data Ingestion CLI")


@app.command()
def ingest(
    date: str = typer.Option(None, help="Date to ingest (YYYY-MM-DD, default: today)"),
    batch_size: int = typer.Option(10000, help="Batch size per API call"),
    raw_path: str = typer.Option("data/raw", help="Raw data output path"),
):
    """Ingest data from upstream vendor for a specific date."""
    ingestion_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now(timezone.utc)
    
    ingestor = DataIngestor(raw_data_path=raw_path)
    file_path = ingestor.ingest_daily_batch(
        ingestion_date=ingestion_date,
        batch_size=batch_size,
    )
    
    if file_path:
        typer.echo(f"✅ Ingestion complete: {file_path}")
    else:
        typer.echo("⚠️ No data ingested")
        raise typer.Exit(code=1)


@app.command()
def backfill(
    start_date: str = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
    batch_size: int = typer.Option(10000, help="Batch size per API call"),
):
    """Backfill data for a date range."""
    from_date = datetime.strptime(start_date, "%Y-%m-%d")
    to_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    ingestor = DataIngestor()
    current = from_date
    
    while current <= to_date:
        try:
            file_path = ingestor.ingest_daily_batch(
                ingestion_date=current,
                batch_size=batch_size,
            )
            typer.echo(f"✅ {current.strftime('%Y-%m-%d')}: {file_path}")
        except Exception as e:
            logger.error(f"Failed to ingest {current.strftime('%Y-%m-%d')}: {e}")
            typer.echo(f"❌ {current.strftime('%Y-%m-%d')}: FAILED - {e}")
        
        current = current + datetime.timedelta(days=1)


if __name__ == "__main__":
    app()