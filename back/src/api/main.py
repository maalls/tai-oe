"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.action.router import router as action_router
from src.api.admin.router import router as admin_router
from src.api.brand.router import router as brand_router
from src.api.auth.router import router as auth_router
from src.api.catalog.router import router as catalog_router
from src.api.family.router import router as family_router
from src.api.contact.router import router as contact_router
from src.api.csv.router import router as csv_router
from src.api.document.router import router as document_router
from src.api.email.router import router as email_router
from src.api.opportunity.router import router as opportunity_router
from src.api.product.router import router as product_router
from src.api.quote.router import router as quote_router
from src.api.rfq.router import router as rfq_router
from src.api.rfp.router import router as rfp_router
from src.api.utils.router import router as utils_router
from src.api.vendor.router import router as vendor_router


def create_app() -> FastAPI:
    from src.api.profile.router import router as profile_router
    from src.api.account.router import router as account_router
    app = FastAPI(title="RAG Server API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(action_router)
    app.include_router(admin_router)
    app.include_router(brand_router)
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(family_router)
    app.include_router(contact_router)
    app.include_router(csv_router)
    app.include_router(document_router)
    app.include_router(email_router)
    app.include_router(opportunity_router)
    app.include_router(product_router)
    app.include_router(quote_router)
    app.include_router(rfq_router)
    app.include_router(rfp_router)
    app.include_router(utils_router)
    app.include_router(vendor_router)
    app.include_router(profile_router)
    app.include_router(account_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
