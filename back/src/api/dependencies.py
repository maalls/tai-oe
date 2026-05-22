"""Dependency providers for FastAPI routers."""

import os
from pathlib import Path

from src.service.action.service import ActionService
from src.service.auth.auth_service import AuthService
from src.service.auth.oauth_service import OAuthService
from src.service.csv.file_service import CsvFileService
from src.service.document.document_service import DocumentService
from src.service.email.gmail_service import GmailService
from src.service.email.outlook_service import OutlookService
from src.service.email.quote_send_service import QuoteSendService
from src.service.invoice.invoice_service import InvoiceService
from src.service.product.service import ProductService
from src.service.quote.quote_controller import QuoteController
from src.service.rfq.rfq_service import RfqService
from src.service.rfq.rfq_source_service import RfqSourceService
from src.service.utility.utility_service import UtilityService
from src.repository.email_repository import EmailRepository
from src.repository.database.repository import DatabaseRepository
from src.repository.opportunity import OpportunityRepository
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.factory import ServiceFactory
from src.lib.storage_paths import get_storage_path
from src.lib.readers.csv import CSVReader


def get_auth_service() -> AuthService:
    return AuthService()


def get_action_service() -> ActionService:
    return ActionService()


def get_oauth_service() -> OAuthService:
    return OAuthService()


def get_gmail_service() -> GmailService:
    return GmailService()


def get_outlook_service() -> OutlookService:
    return OutlookService()


def get_utility_service() -> UtilityService:
    src_dir = Path(__file__).resolve().parents[1]
    base_dir = src_dir.parents[1]
    prompt_base_dir = src_dir / "infrastructure" / "prompts"
    return UtilityService(base_dir=base_dir, prompt_base_dir=prompt_base_dir)


def get_quote_send_service() -> QuoteSendService:
    repository = EmailRepository()
    return QuoteSendService(
        send_email=repository.send_email,
        storage_path_resolver=get_storage_path,
    )


def get_quote_controller() -> QuoteController:
    return QuoteController()


def get_invoice_handlers() -> InvoiceService:
    repository = EmailRepository()
    return InvoiceService(
        send_email_with_attachments=repository.send_email,
        storage_path_resolver=get_storage_path,
    )


def get_service_factory() -> ServiceFactory:
    return ServiceFactory()


def get_file_handler() -> CsvFileService:
    storage_dir = Path(os.environ.get("STORAGE_DIR", "var/storage")).resolve()
    return CsvFileService(storage_dir=storage_dir, csv_reader=CSVReader())


def get_opportunity_repository() -> OpportunityRepository:
    return OpportunityRepository()


def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository(DatabaseHandler())


def get_email_repository() -> EmailRepository:
    return EmailRepository()


def get_rfq_source_service() -> RfqSourceService:
    return RfqSourceService()


def get_rfq_handlers() -> RfqService:
    return RfqService()


def get_document_service() -> DocumentService:
    return DocumentService()


def get_product_service() -> ProductService:
    return ProductService()
