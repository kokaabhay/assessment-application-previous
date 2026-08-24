import csv
import io
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleError,
    ForbiddenError,
    ResourceNotFoundError,
)
from app.db.models import Contract, User
from app.repositories.contract_repository import ContractRepository
from app.repositories.vendor_repository import VendorRepository
from app.schemas.contracts import (
    ContractCreateRequest,
    ContractUpdateRequest,
)


class ContractService:
    """Business logic for contract management."""

    @staticmethod
    async def get_contract(
        db: AsyncSession,
        contract_id: int,
        current_user: User,
    ) -> Contract:
        """Get a contract with ownership authorization."""

        contract = await ContractRepository.get_by_id(
            db,
            contract_id,
        )

        if contract is None:
            raise ResourceNotFoundError(
                "Contract not found."
            )

        if (
            current_user.role != "admin"
            and contract.owner_id != current_user.id
        ):
            raise ForbiddenError(
                "You do not have access to this contract."
            )

        return contract

    @staticmethod
    async def get_contracts(
        db: AsyncSession,
        current_user: User,
    ) -> list[Contract]:
        """Get contracts according to the user's role."""

        if current_user.role == "admin":
            return await ContractRepository.get_all(db)

        return await ContractRepository.get_by_owner(
            db,
            current_user.id,
        )

    @staticmethod
    async def create_contract(
        db: AsyncSession,
        data: ContractCreateRequest,
        current_user: User,
    ) -> Contract:
        """Create a contract owned by the current user."""

        vendor = await VendorRepository.get_by_id(
            db,
            data.vendor_id,
        )

        if vendor is None:
            raise ResourceNotFoundError(
                "Vendor not found."
            )

        if data.end_date <= data.start_date:
            raise BusinessRuleError(
                "Contract end date must be after start date."
            )

        if data.spend > data.contract_value:
            raise BusinessRuleError(
                "Contract spend cannot exceed contract value."
            )

        contract = Contract(
            vendor_id=data.vendor_id,
            title=data.title,
            contract_value=data.contract_value,
            spend=data.spend,
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_type=data.renewal_type,
            status=data.status,
            owner_id=current_user.id,
            service_scope=data.service_scope,
        )

        return await ContractRepository.create(
            db,
            contract,
        )

    @staticmethod
    async def update_contract(
        db: AsyncSession,
        contract_id: int,
        data: ContractUpdateRequest,
        current_user: User,
    ) -> Contract:
        """Update a contract with ownership authorization."""

        contract = await ContractService.get_contract(
            db,
            contract_id,
            current_user,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "vendor_id" in update_data:
            vendor = await VendorRepository.get_by_id(
                db,
                update_data["vendor_id"],
            )

            if vendor is None:
                raise ResourceNotFoundError(
                    "Vendor not found."
                )

        new_start_date = update_data.get(
            "start_date",
            contract.start_date,
        )

        new_end_date = update_data.get(
            "end_date",
            contract.end_date,
        )

        new_contract_value = update_data.get(
            "contract_value",
            contract.contract_value,
        )

        new_spend = update_data.get(
            "spend",
            contract.spend,
        )

        if new_end_date <= new_start_date:
            raise BusinessRuleError(
                "Contract end date must be after start date."
            )

        if new_spend > new_contract_value:
            raise BusinessRuleError(
                "Contract spend cannot exceed contract value."
            )

        for field, value in update_data.items():
            setattr(contract, field, value)

        return await ContractRepository.update(
            db,
            contract,
        )

    @staticmethod
    async def delete_contract(
        db: AsyncSession,
        contract_id: int,
        current_user: User,
    ) -> None:
        """Delete a contract with ownership authorization."""

        contract = await ContractService.get_contract(
            db,
            contract_id,
            current_user,
        )

        await ContractRepository.delete(
            db,
            contract,
        )

    @staticmethod
    async def export_contracts_csv(
        db: AsyncSession,
        current_user: User,
    ) -> str:
        """Export contracts accessible to the current user as CSV."""

        contracts = await ContractService.get_contracts(
            db,
            current_user,
        )

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow(
            [
                "id",
                "vendor_id",
                "title",
                "contract_value",
                "spend",
                "start_date",
                "end_date",
                "renewal_type",
                "status",
                "owner_id",
                "service_scope",
            ]
        )

        for contract in contracts:
            writer.writerow(
                [
                    contract.id,
                    contract.vendor_id,
                    contract.title,
                    contract.contract_value,
                    contract.spend,
                    contract.start_date,
                    contract.end_date,
                    contract.renewal_type,
                    contract.status,
                    contract.owner_id,
                    contract.service_scope,
                ]
            )

        return output.getvalue()

    @staticmethod
    async def export_contracts_json(
        db: AsyncSession,
        current_user: User,
    ) -> str:
        """Export contracts accessible to the current user as JSON."""

        contracts = await ContractService.get_contracts(
            db,
            current_user,
        )

        data = []

        for contract in contracts:
            data.append(
                {
                    "id": contract.id,
                    "vendor_id": contract.vendor_id,
                    "title": contract.title,
                    "contract_value": float(
                        contract.contract_value
                    ),
                    "spend": float(
                        contract.spend
                    ),
                    "start_date": contract.start_date.isoformat(),
                    "end_date": contract.end_date.isoformat(),
                    "renewal_type": contract.renewal_type,
                    "status": contract.status,
                    "owner_id": contract.owner_id,
                    "service_scope": contract.service_scope,
                }
            )

        return json.dumps(
            data,
            indent=2,
        )