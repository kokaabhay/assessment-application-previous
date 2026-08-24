import csv
import io
import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.db.models import Contract, Job
from app.repositories.job_repository import JobRepository
from app.repositories.vendor_repository import VendorRepository

logger = logging.getLogger(__name__)


async def process_contract_import(
    job_id: int,
    file_content: bytes,
    owner_id: int,
) -> None:
    """Process a contract CSV import in the background."""

    async with AsyncSessionLocal() as db:

        job = await JobRepository.get_by_id(
            db,
            job_id,
        )

        if job is None:
            logger.error(
                "Import job %s not found.",
                job_id,
            )
            return

        try:
            job.status = "processing"
            job.started_at = datetime.utcnow()
            await JobRepository.update(db, job)

            text = file_content.decode("utf-8-sig")

            reader = csv.DictReader(
                io.StringIO(text)
            )

            rows = list(reader)
            total = len(rows)

            accepted = 0
            rejected = 0

            for index, row in enumerate(rows, start=1):

                try:
                    vendor_id = int(
                        row["vendor_id"]
                    )

                    vendor = await VendorRepository.get_by_id(
                        db,
                        vendor_id,
                    )

                    if vendor is None:
                        raise ValueError(
                            "Vendor does not exist."
                        )

                    contract_value = Decimal(
                        row["contract_value"]
                    )

                    spend = Decimal(
                        row["spend"]
                    )

                    if spend > contract_value:
                        raise ValueError(
                            "Spend exceeds contract value."
                        )

                    contract = Contract(
                        vendor_id=vendor_id,
                        title=row["title"],
                        contract_value=contract_value,
                        spend=spend,
                        start_date=datetime.strptime(
                            row["start_date"],
                            "%Y-%m-%d",
                        ).date(),
                        end_date=datetime.strptime(
                            row["end_date"],
                            "%Y-%m-%d",
                        ).date(),
                        renewal_type=row["renewal_type"],
                        status=row["status"],
                        owner_id=owner_id,
                        service_scope=row.get(
                            "service_scope"
                        ),
                    )

                    db.add(contract)

                    accepted += 1

                except Exception as exc:
                    rejected += 1

                    logger.warning(
                        "Rejected CSV row %s: %s",
                        index,
                        exc,
                    )

                if total:
                    job.progress = int(
                        index / total * 100
                    )

                job.accepted_count = accepted
                job.rejected_count = rejected

                await db.commit()

            job.status = "completed"
            job.progress = 100
            job.finished_at = datetime.utcnow()

            await db.commit()

        except Exception as exc:

            logger.exception(
                "Contract import failed for job %s",
                job_id,
            )

            job.status = "failed"
            job.error = str(exc)
            job.finished_at = datetime.utcnow()

            await db.commit()