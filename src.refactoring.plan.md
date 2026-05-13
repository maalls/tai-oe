# Refactoring Plan : Migration vers Architecture par Domaine

**Statut** : À faire
**Approche** : Test-Driven, micro-étapes, pas de breaking changes
**Version** : 2.0 (Revisited & Improved)

---

## 🚨 Critical Issues Fixed

1. ✅ **DTO integration** : Maintenant utilisé dans tous les exemples (Phase 2+)
2. ✅ **Dependency Injection** : Nouvelle section avec factory pattern
3. ✅ **Setup/Init** : Comment initialiser les services
4. ✅ **Error handling** : Approche claire par couche
5. ✅ **Cleanup strategy** : Migration progressive (old + new coexist)
6. ✅ **Fixtures & conftest** : Définition complète du test setup
7. ✅ **Common pitfalls** : 5 pièges majeurs + solutions
8. ✅ **Performance** : DTO overhead mitigé + scalability pattern

---

## 📋 TL;DR (Executive Summary)

**Problème actuel** : Code mélangé (business logic + DB + LLM), difficile à tester et maintenir.

**Solution** : Clean Architecture avec DDD + TDD

**Timeline** : 2-3 semaines

**Key Pattern** :

```
Domain (entités pures)
    ↓ (via Repository)
Infrastructure (DTO + Supabase)
    ↓
Service (orchestration + logique métier)
    ↓
API/Command (HTTP routes ou CLI)
```

**Immediate Next Steps** :

1. Review sections 2.5-2.7 (DI, Enums, Error Handling)
2. Review section 5 (Test Fixtures)
3. Start Phase 1: `domain/email.py` + tests

---

## 1. Structure de Tests : Overkill ou Logique ? 🤔

### Ce que tu proposes :

```
tests/unit/email/
├── email_service/
│   ├── test_get_email.py
│   ├── test_classify.py
│   └── test_save.py
```

### Verdict : **Overkill** ⚠️ (mais tu es pas loin)

**Pourquoi overkill** :

- 1 fichier de test par fonction = trop fragmenté
- Harder à naviguer (40 fichiers pour 1 service)
- Overkill pour la plupart des cas

**Pragmatique** :

```
tests/unit/email/
├── test_email_service.py        # Tous les tests d'email_service
├── test_classification_service.py
└── test_workflow_service.py
```

✅ Clair, pas fragmenté, facile à trouver

### Si tu veux vraiment par-fonction :

```
tests/unit/email/email_service/
├── test_get_email.py
├── test_classify.py
└── test_save.py
```

✅ **Acceptable** si les fonctions sont complexes (extraction RFP, classification LLM)
❌ Overkill si c'est du CRUD simple

---

## 2. Structure Recommandée (Pragmatique + Testable)

```
back/
├── src/
│   ├── domain/                  # Entités métier pures
│   │   ├── email.py
│   │   ├── rfp.py
│   │   ├── opportunity.py
│   │   ├── vendor.py
│   │   └── __init__.py
│   ├── repository/              # Interfaces (contrats)
│   │   ├── email_repository.py
│   │   ├── rfp_repository.py
│   │   ├── opportunity_repository.py
│   │   ├── vendor_repository.py
│   │   └── __init__.py
│   ├── infrastructure/          # Implémentations techniques
│   │   ├── supabase/
│   │   │   ├── email_supabase.py      # Implémente EmailRepository
│   │   │   ├── rfp_supabase.py
│   │   │   ├── opportunity_supabase.py
│   │   │   └── vendor_supabase.py
│   │   ├── google_auth/
│   │   │   └── google_auth_client.py
│   │   ├── llm/
│   │   │   ├── openai_client.py
│   │   │   └── ollama_client.py
│   │   └── __init__.py
│   ├── service/                 # Logique métier organisée par domaine
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── email_service.py          # Récupère/sauvegarde emails
│   │   │   ├── classification_service.py # Appelle LLM, classifie
│   │   │   └── workflow_service.py       # Orchestre email + classification
│   │   ├── rfp/
│   │   │   ├── __init__.py
│   │   │   ├── rfp_service.py
│   │   │   └── extraction_service.py     # Extrait RFP d'un email
│   │   ├── vendor/
│   │   │   ├── __init__.py
│   │   │   └── vendor_service.py
│   │   └── opportunity/
│   │       ├── __init__.py
│   │       └── opportunity_service.py
│   ├── command/                 # CLI (garde comme c'est)
│   │   ├── fetch_emails.py
│   │   ├── fetch_emails_loop.py
│   │   └── __init__.py
│   ├── api/                     # FastAPI routes
│   │   ├── routes/
│   │   │   ├── email_routes.py
│   │   │   └── opportunity_routes.py
│   │   └── __init__.py
│   ├── lib/                     # Utilitaires
│   │   ├── pdf_utils.py
│   │   ├── date_utils.py
│   │   └── __init__.py
│   └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_email.py         # Tests entités
│   │   │   ├── test_rfp.py
│   │   │   └── test_opportunity.py
│   │   ├── service/
│   │   │   ├── email/
│   │   │   │   ├── test_email_service.py          # 1 fichier = tous les tests
│   │   │   │   ├── test_classification_service.py
│   │   │   │   └── test_workflow_service.py
│   │   │   ├── rfp/
│   │   │   │   ├── test_rfp_service.py
│   │   │   │   └── test_extraction_service.py
│   │   │   └── vendor/
│   │   │       └── test_vendor_service.py
│   │   ├── infrastructure/
│   │   │   ├── test_email_supabase.py
│   │   │   └── test_openai_client.py
│   │   └── fixtures/
│   │       ├── fake_repositories.py
│   │       └── sample_data.py
│   ├── integration/
│   │   ├── test_email_workflow_integration.py
│   │   └── test_vendor_sync_integration.py
│   └── conftest.py              # Pytest fixtures globales
```

---

## 2.5 Dependency Injection & Service Initialization

**Problème** : Comment initialiser les services et injecter les dépendances?

### Option 1 : Factory Pattern (recommandé)

```python
# src/infrastructure/factory.py
from infrastructure.supabase.email_supabase import SupabaseEmailRepository
from service.email.email_service import EmailService
from infrastructure.llm.openai_client import OpenAIClient
from service.email.classification_service import ClassificationService

class ServiceFactory:
    """Crée et configure tous les services"""

    def __init__(self, supabase_client, config):
        self.supabase = supabase_client
        self.config = config

    def create_email_service(self) -> EmailService:
        """Crée EmailService avec dépendances injectées"""
        repo = SupabaseEmailRepository(self.supabase)
        return EmailService(repo)

    def create_classification_service(self) -> ClassificationService:
        llm = OpenAIClient(api_key=self.config.get("OPENAI_KEY"))
        return ClassificationService(llm)

    def create_email_workflow_service(self):
        from service.email.workflow_service import EmailWorkflowService
        email_svc = self.create_email_service()
        classifier_svc = self.create_classification_service()
        return EmailWorkflowService(email_svc, classifier_svc)
```

### Utilisation dans command :

```python
# src/command/fetch_emails.py
from infrastructure.factory import ServiceFactory
from supabase import create_client

def run():
    # Init factory (une seule fois au démarrage)
    supabase = create_client(url=os.getenv("SUPABASE_URL"), key=os.getenv("SUPABASE_KEY"))
    factory = ServiceFactory(supabase, config={
        "OPENAI_KEY": os.getenv("OPENAI_KEY")
    })

    # Utiliser les services
    workflow = factory.create_email_workflow_service()
    emails = workflow.email.get_all_unclassified(limit=100)
    for email in emails:
        workflow.process_new_email(email.id)
```

### Checklist Dependency Injection

- [ ] `src/infrastructure/factory.py` créé
- [ ] Tous les services initialisés via factory
- [ ] Tests utilisent FakeRepositories (pas de factory)
- [ ] Config externalisée (env vars, config.yml)

---

## 2.6 Enums : Organisation

**Décision** : Tous les enums dans un fichier centralisé

```python
# src/domain/enums.py (centralise)
from enum import Enum

class EmailStatus(Enum):
    UNREAD = "unread"
    CLASSIFIED = "classified"

class DocumentStatus(Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    # ... sync avec schema/types/document_status.sql

class InvoicePaymentStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    DISPUTED = "DISPUTED"
```

**Puis import dans entities** :

```python
# src/domain/email.py
from domain.enums import EmailStatus

@dataclass
class Email:
    id: str
    status: EmailStatus  # ← Import depuis enums.py
```

**Avantage** : Un seul endroit pour sync avec PostgreSQL types

---

## 2.7 Error Handling & Logging Strategy

### Par couche :

**Domain** (ne throw que ValueError, logique métier) :

```python
class Email:
    def mark_classified(self, category: str) -> "Email":
        if self.status == EmailStatus.CLASSIFIED:
            raise ValueError("Already classified")  # ← Domain logic
```

**Repository** (catch DB errors, lance RepositoryError) :

```python
class SupabaseEmailRepository(EmailRepository):
    def get_by_id(self, email_id: str) -> Email:
        try:
            response = self.supabase.table("email").select(...).execute()
        except Exception as e:
            logger.error(f"Supabase error: {e}")
            raise RepositoryError(f"Failed to fetch email {email_id}") from e
```

**Service** (compose logic, gère erreurs) :

```python
class EmailWorkflowService:
    def process_new_email(self, email_id: str) -> dict:
        try:
            email = self.email.get_email(email_id)
            category = self.classifier.classify(email.body)
            return self.email.mark_classified(email_id, category)
        except ValueError as e:
            logger.warning(f"Business logic error: {e}")
            raise
        except RepositoryError as e:
            logger.error(f"Repository failed: {e}")
            raise
```

**Command** (log + exit gracefully) :

```python
def run():
    try:
        workflow.process_new_email(email_id)
    except Exception as e:
        logger.exception(f"Failed to process email: {e}")
        exit(1)
```

### Checklist Error Handling

- [ ] Custom exceptions : `RepositoryError`, `ClassificationError`
- [ ] Logging setup (src/lib/logging_config.py)
- [ ] Tous les services log leurs actions
- [ ] Command handles exceptions gracefully

---

**Objectif** : Mapper les entités domain vers les tables Supabase existantes

### 3.1 Correspondance Domain ↔ Schema SQL

```
Existant (Supabase)          Nouveau (Domain)         Infrastructure Mapping
─────────────────────────────────────────────────────────────────────────
email.sql                 ← src/domain/email.py    ← infrastructure/supabase/email_supabase.py
├── id                    ← Email.id
├── subject               ← Email.subject
├── from_email            ← Email.sender
├── body_full             ← Email.body
├── is_classified         ← Email.status (UNREAD→false, CLASSIFIED→true)
├── category              ← Email.classification
└── classified_at         ← Email.classified_at

opportunity.sql           ← src/domain/opportunity.py
├── id                    ← Opportunity.id
├── stage                 ← Opportunity.stage (sync with document_status enum)
├── estimated_value       ← Opportunity.estimated_value
└── ...

vendor.sql                ← src/domain/vendor.py
├── id                    ← Vendor.id
├── name                  ← Vendor.name
└── ...

contact.sql               ← src/domain/contact.py
├── id                    ← Contact.id
├── email                 ← Contact.email
└── ...
```

### 3.2 Enums PostgreSQL → Python

**PostgreSQL Types** (schema/types/) :

```sql
-- invoice_payment_status.sql
CREATE TYPE invoice_payment_status AS ENUM ('PENDING', 'PAID', 'OVERDUE', 'DISPUTED');

-- document_status.sql
CREATE TYPE document_status AS ENUM ('DRAFT', 'SENT', 'PAID', ...);
```

**Créer les équivalents Python** :

```python
# src/domain/enums.py
from enum import Enum

class InvoicePaymentStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    DISPUTED = "DISPUTED"

class DocumentStatus(Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    # ... (sync avec schema/types/document_status.sql)

class EmailStatus(Enum):
    UNREAD = "unread"
    CLASSIFIED = "classified"
```

### 3.3 Pydantic DTOs pour le Mapping Automatique

**Créer une couche DTO** (Data Transfer Objects) pour auto-mapper SQL → Python :

```python
# src/infrastructure/database/dto.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailDTO(BaseModel):
    """Auto-mapped from SQL email table"""
    id: str
    subject: Optional[str] = None
    from_email: str
    body_full: Optional[str] = None
    is_classified: bool = False
    category: Optional[str] = None
    classified_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # ← Permet auto-mapping depuis SQL row

class OpportunityDTO(BaseModel):
    """Auto-mapped from SQL opportunity table"""
    id: str
    stage: str  # DocumentStatus enum (SQL string)
    estimated_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VendorDTO(BaseModel):
    """Auto-mapped from SQL vendor table"""
    id: str
    name: str
    email_domain: Optional[str] = None

    class Config:
        from_attributes = True
```

**Conversion : SQL → DTO → Domain** :

```python
# infrastructure/supabase/email_supabase.py
from infrastructure.database.dto import EmailDTO
from domain.email import Email, EmailStatus

class SupabaseEmailRepository(EmailRepository):
    def _to_domain(self, row: dict) -> Email:
        """SQL row → Pydantic DTO → Domain Entity"""
        # 1. Auto-validation + mapping SQL → DTO (Pydantic)
        dto = EmailDTO(**row)

        # 2. Transformation avec logique métier (DTO → Domain)
        status = EmailStatus.CLASSIFIED if dto.is_classified else EmailStatus.UNREAD

        return Email(
            id=dto.id,
            subject=dto.subject,
            sender=dto.from_email,
            body=dto.body_full,
            status=status,
            classification=dto.category
        )

    def _to_sql(self, email: Email) -> dict:
        """Domain Entity → SQL row (pour sauvegarde)"""
        return {
            "id": email.id,
            "subject": email.subject,
            "from_email": email.sender,
            "body_full": email.body,
            "is_classified": email.status == EmailStatus.CLASSIFIED,
            "category": email.classification,
            "classified_at": datetime.now() if email.status == EmailStatus.CLASSIFIED else None
        }

    def get_by_id(self, email_id: str) -> Email:
        response = self.supabase.table("email").select("*").eq("id", email_id).execute()
        if not response.data:
            raise ValueError(f"Email {email_id} not found")
        return self._to_domain(response.data[0])

    def save(self, email: Email) -> None:
        row = self._to_sql(email)
        self.supabase.table("email").update(row).eq("id", email.id).execute()
```

**Avantages du DTO** :

- ✅ Auto-validation (Pydantic)
- ✅ Type hints clairs
- ✅ Facile à déboguer
- ✅ Réutilisable (même DTO pour API responses)
- ✅ Zéro overhead supplémentaire

### 3.4 Documentations de Mapping

**Créer un fichier de référence** :

```markdown
# infrastructure/database/SCHEMA_MAPPING.md

## Email Table Mapping

| Domain (Python)      | SQL Column          | DTO Field     | Type | Notes                              |
| -------------------- | ------------------- | ------------- | ---- | ---------------------------------- |
| Email.id             | email.id            | id            | str  | PK                                 |
| Email.subject        | email.subject       | subject       | str  |                                    |
| Email.sender         | email.from_email    | from_email    | str  |                                    |
| Email.body           | email.body_full     | body_full     | str  | Full body content                  |
| Email.status         | email.is_classified | is_classified | bool | UNREAD (false) → CLASSIFIED (true) |
| Email.classification | email.category      | category      | str  | RFP, Invoice, Quote, etc.          |

## Type Mappings

| Python Enum          | PostgreSQL Type        | File                                    |
| -------------------- | ---------------------- | --------------------------------------- |
| EmailStatus          | (BOOLEAN)              | (custom)                                |
| InvoicePaymentStatus | invoice_payment_status | schema/types/invoice_payment_status.sql |
| DocumentStatus       | document_status        | schema/types/document_status.sql        |

## DTO Location

All DTOs: `src/infrastructure/database/dto.py`
```

### 3.5 Checklist Pre-requis

- [ ] Analyser tous les schemas (back/schema/tables/\*)
- [ ] Lister les enums PostgreSQL (back/schema/types/\*)
- [ ] Créer src/domain/enums.py avec tous les enums
- [ ] Créer infrastructure/database/SCHEMA_MAPPING.md
- [ ] Valider mappings (pas de champs oubliés)

## 4. Existing Tests & Migration Strategy (CRITICAL)

**Problème** : Comment passer de l'ancien code au nouveau sans casser?

### 4.1 Strategy : "Strangler Pattern" (ancien + nouveau coexistent)

**Semaine 1** :

- Old code continue de fonctionner
- Nouveau code: domain + repository + infrastructure (testé)
- Tests existants continuent de passer ✅

**Semaine 2** :

- Services + tests
- Services commencent à être utilisés par commands
- Ancien code partiellement remplacé

**Semaine 3** :

- Migration complète
- Ancien code supprimé
- Tests existants adaptés aux nouvelles structures

### 4.2 Adapter les tests existants

**Avant** (tests existants utilisent peut-être `src/repository/` directement) :

```python
# tests/test_something.py (old)
from src.repository.email_repository import get_unclassified_emails

def test_fetch():
    emails = get_unclassified_emails()
    assert len(emails) > 0
```

**Après** (adapte pour utiliser la nouvelle architecture) :

```python
# tests/test_something.py (updated)
from src.service.email import EmailService
from tests.fixtures.fake_repositories import FakeEmailRepository
from domain.email import Email, EmailStatus

@pytest.fixture
def email_service():
    repo = FakeEmailRepository()
    return EmailService(repo)

def test_fetch():
    # Setup
    email = Email(...)
    email_service.repo.save(email)

    # Execute (maintenant via EmailService)
    unclassified = email_service.get_all_unclassified()

    # Assert
    assert len(unclassified) > 0
```

### 4.3 Checklist Migration Existants

- [ ] Lister tous les tests existants (`find tests/ -name "test_*.py"`)
- [ ] Identifier lesquels testent `src/repository/email_repository.py`
- [ ] Pour chacun : adapter pour utiliser `EmailService` + `FakeRepository`
- [ ] Vérifier tous les tests passent avant de supprimer ancien code

---

## 5. Cleanup Timeline (après Phase 4)

**Une fois les services adoptés** :

```bash
# Week 3 (after migration)
rm -rf src/repository/*  # ← Ancien repository pattern
rm -rf src/old_email.py  # ← Code directement Supabase
rm -rf back/script/email_classifier.py  # ← Old CLI
```

**Verify** :

```bash
grep -r "old_repository_pattern" src/  # ← Doit être 0 résultats
pytest tests/ -v  # ← Tous doivent passer
```

---

## 5. Test Fixtures & conftest.py

**Missing piece** : Comment les FakeRepository et sample_data sont organisés

### 5.1 conftest.py (Global Fixtures)

```python
# tests/conftest.py
import pytest
from tests.fixtures.fake_repositories import FakeEmailRepository, FakeRFPRepository
from tests.fixtures.sample_data import sample_email, sample_rfp

# Global fixtures (available in all tests)

@pytest.fixture
def fake_email_repo():
    """Fournit un FakeEmailRepository vide"""
    return FakeEmailRepository()

@pytest.fixture
def fake_rfp_repo():
    return FakeRFPRepository()

@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client pour les tests classification"""
    mock = mocker.MagicMock()
    mock.chat.return_value = "quote"
    return mock

@pytest.fixture(autouse=True)  # Run before every test
def reset_logging(caplog):
    """Reset logging entre les tests"""
    caplog.clear()
```

### 5.2 fake_repositories.py

```python
# tests/fixtures/fake_repositories.py
from repository.email_repository import EmailRepository
from domain.email import Email, EmailStatus

class FakeEmailRepository(EmailRepository):
    """In-memory implementation pour tests"""

    def __init__(self):
        self.emails: Dict[str, Email] = {}

    def get_by_id(self, email_id: str) -> Email:
        if email_id not in self.emails:
            raise ValueError(f"Email {email_id} not found")
        return self.emails[email_id]

    def get_all_unclassified(self, limit: int = 100) -> List[Email]:
        return [
            e for e in self.emails.values()
            if e.status == EmailStatus.UNREAD
        ][:limit]

    def save(self, email: Email) -> None:
        self.emails[email.id] = email

class FakeRFPRepository(EmailRepository):
    """Similar for RFP"""
    def __init__(self):
        self.rfps: Dict[str, RFP] = {}
    # ... implement interface
```

### 5.3 sample_data.py

```python
# tests/fixtures/sample_data.py
from domain.email import Email, EmailStatus
from datetime import datetime

def sample_email(
    id: str = "test-1",
    status: EmailStatus = EmailStatus.UNREAD,
    classification: str = None
) -> Email:
    """Factory pour créer des emails test"""
    return Email(
        id=id,
        subject="Test email",
        body="Lorem ipsum dolor",
        sender="test@example.com",
        status=status,
        classification=classification
    )

def sample_rfp(**kwargs) -> RFP:
    """Factory pour RFP"""
    return RFP(
        id=kwargs.get("id", "rfp-1"),
        ...
    )
```

### 5.4 Unit Test Example (using fixtures)

```python
# tests/unit/service/email/test_email_service.py
def test_mark_classified(fake_email_repo):
    """Utilise fixture fake_email_repo"""
    # Setup
    email = sample_email(status=EmailStatus.UNREAD)
    fake_email_repo.save(email)

    service = EmailService(fake_email_repo)

    # Execute
    result = service.mark_classified(email.id, "quote")

    # Assert
    assert result.classification == "quote"
    assert result.status == EmailStatus.CLASSIFIED
```

### 5.5 Checklist Fixtures

- [ ] `tests/conftest.py` créé avec fixtures globales
- [ ] `tests/fixtures/fake_repositories.py` avec FakeEmailRepository, etc.
- [ ] `tests/fixtures/sample_data.py` avec factories
- [ ] `tests/__init__.py` vide (Python package)
- [ ] `tests/fixtures/__init__.py` vide

---

## 6. Micro-Étapes de Migration (Test-Driven)

**Durée estimée** : 2-3 jours

#### Étape 1.1 : Créer les domaines (entités pures)

```python
# src/domain/email.py
from dataclasses import dataclass
from enum import Enum

class EmailStatus(Enum):
    UNREAD = "unread"
    CLASSIFIED = "classified"

@dataclass
class Email:
    id: str
    subject: str
    body: str
    sender: str
    status: EmailStatus
    classification: str = None

    def mark_classified(self, category: str) -> "Email":
        if self.status == EmailStatus.CLASSIFIED:
            raise ValueError("Already classified")
        return Email(
            id=self.id,
            subject=self.subject,
            body=self.body,
            sender=self.sender,
            status=EmailStatus.CLASSIFIED,
            classification=category
        )
```

**Tests** (TDD : tests avant implémentation) :

```python
# tests/unit/domain/test_email.py
def test_email_can_be_classified_once():
    email = Email(id="1", subject="...", body="...", sender="...", status=EmailStatus.UNREAD)
    classified = email.mark_classified("quote")
    assert classified.status == EmailStatus.CLASSIFIED
    assert classified.classification == "quote"

def test_email_cannot_be_classified_twice():
    email = Email(..., status=EmailStatus.UNREAD)
    email.mark_classified("quote")
    with pytest.raises(ValueError):
        email.mark_classified("invoice")  # ← Erreur

def test_original_email_unchanged():
    original = Email(..., status=EmailStatus.UNREAD)
    classified = original.mark_classified("quote")
    assert original.status == EmailStatus.UNREAD  # Immutable
    assert classified.status == EmailStatus.CLASSIFIED
```

**Checklist** :

- [ ] `src/domain/email.py` créé
- [ ] `src/domain/rfp.py` créé
- [ ] `src/domain/opportunity.py` créé
- [ ] `src/domain/vendor.py` créé
- [ ] Tests unitaires pour tous (domain/ testé à 100%)

---

#### Étape 1.2 : Créer les interfaces (Repository)

```python
# src/repository/email_repository.py
from abc import ABC, abstractmethod
from domain.email import Email

class EmailRepository(ABC):
    """Contrat : j'accède aux emails"""

    @abstractmethod
    def get_by_id(self, email_id: str) -> Email:
        pass

    @abstractmethod
    def get_all_unclassified(self, limit: int = 100) -> List[Email]:
        pass

    @abstractmethod
    def save(self, email: Email) -> None:
        pass
```

**Tests** (tests d'interface avec mocks) :

```python
# tests/unit/infrastructure/test_email_repository_contract.py
class FakeEmailRepository(EmailRepository):
    def __init__(self):
        self.emails = {}

    def get_by_id(self, email_id: str) -> Email:
        return self.emails.get(email_id)

    def get_all_unclassified(self, limit: int = 100) -> List[Email]:
        return [e for e in self.emails.values() if e.status == EmailStatus.UNREAD][:limit]

    def save(self, email: Email) -> None:
        self.emails[email.id] = email

def test_repository_contract():
    repo = FakeEmailRepository()
    email = Email(..., status=EmailStatus.UNREAD)
    repo.save(email)
    retrieved = repo.get_by_id(email.id)
    assert retrieved.status == EmailStatus.UNREAD
```

**Checklist** :

- [ ] `src/repository/email_repository.py` créé (abstract)
- [ ] `src/repository/rfp_repository.py` créé
- [ ] `src/repository/opportunity_repository.py` créé
- [ ] `src/repository/vendor_repository.py` créé

---

### **Phase 2 : Infrastructure (Implémentations Supabase)**

**Durée estimée** : 2-3 jours

#### Étape 2.1 : Implémenter Supabase Email Repository

**IMPORTANT** : Utilise Pydantic DTO pour auto-validation et mapping

```python
# src/infrastructure/supabase/email_supabase.py
from repository.email_repository import EmailRepository
from domain.email import Email, EmailStatus
from infrastructure.database.dto import EmailDTO
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    """Base exception pour les erreurs repository"""
    pass

class SupabaseEmailRepository(EmailRepository):
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def get_by_id(self, email_id: str) -> Email:
        try:
            response = self.supabase.table("email").select("*").eq("id", email_id).execute()
            if not response.data:
                raise RepositoryError(f"Email {email_id} not found")
            logger.debug(f"Retrieved email {email_id}")
            return self._to_domain(response.data[0])
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            raise RepositoryError(f"Database error: {e}") from e

    def get_all_unclassified(self, limit: int = 100) -> List[Email]:
        try:
            response = self.supabase.table("email").select("*").eq("is_classified", False).limit(limit).execute()
            logger.info(f"Retrieved {len(response.data)} unclassified emails")
            return [self._to_domain(row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to get unclassified emails: {e}")
            raise RepositoryError(f"Database error: {e}") from e

    def save(self, email: Email) -> None:
        try:
            row = self._to_sql(email)
            self.supabase.table("email").update(row).eq("id", email.id).execute()
            logger.debug(f"Saved email {email.id}")
        except Exception as e:
            logger.error(f"Failed to save email {email.id}: {e}")
            raise RepositoryError(f"Database error: {e}") from e

    def _to_domain(self, row: dict) -> Email:
        """SQL row → Pydantic DTO → Domain Entity"""
        try:
            # 1. Auto-validation + mapping (Pydantic)
            dto = EmailDTO(**row)

            # 2. Transformation avec logique métier
            status = EmailStatus.CLASSIFIED if dto.is_classified else EmailStatus.UNREAD

            return Email(
                id=dto.id,
                subject=dto.subject,
                body=dto.body_full,
                sender=dto.from_email,
                status=status,
                classification=dto.category
            )
        except Exception as e:
            logger.error(f"Failed to convert row to domain: {e}")
            raise RepositoryError(f"Mapping error: {e}") from e

    def _to_sql(self, email: Email) -> dict:
        """Domain Entity → SQL row (pour sauvegarde)"""
        return {
            "id": email.id,
            "subject": email.subject,
            "from_email": email.sender,
            "body_full": email.body,
            "is_classified": email.status == EmailStatus.CLASSIFIED,
            "category": email.classification,
            "classified_at": datetime.now() if email.status == EmailStatus.CLASSIFIED else None
        }
```

**Tests** (avec mock Supabase, pas réel) :

```python
# tests/unit/infrastructure/test_email_supabase.py
@pytest.fixture
def mock_supabase():
    return MagicMock()

def test_get_by_id(mock_supabase):
    mock_supabase.table().select().eq().execute.return_value = Mock(
        data=[{
            "id": "1", "subject": "Test", "body": "...",
            "sender": "x@y.com", "status": "unread", "classification": None
        }]
    )

    repo = SupabaseEmailRepository(mock_supabase)
    email = repo.get_by_id("1")

    assert email.id == "1"
    assert email.status == EmailStatus.UNREAD
```

**Checklist** :

- [ ] `src/infrastructure/supabase/email_supabase.py` créé
- [ ] Tests pour Supabase impl (mocks, pas real DB)

---

### **Phase 3 : Services (Logique Métier)**

**Durée estimée** : 3-4 jours

#### Étape 3.1 : Service Email (accès + sauvegarde)

```python
# src/service/email/email_service.py
from repository.email_repository import EmailRepository
from domain.email import Email

class EmailService:
    def __init__(self, email_repo: EmailRepository):
        self.repo = email_repo

    def get_email(self, email_id: str) -> Email:
        return self.repo.get_by_id(email_id)

    def mark_classified(self, email_id: str, category: str) -> Email:
        email = self.repo.get_by_id(email_id)
        classified = email.mark_classified(category)
        self.repo.save(classified)
        return classified
```

**Tests** (TDD avec FakeRepository) :

```python
# tests/unit/service/email/test_email_service.py
@pytest.fixture
def fake_repo():
    return FakeEmailRepository()

@pytest.fixture
def service(fake_repo):
    return EmailService(fake_repo)

def test_mark_classified(service, fake_repo):
    email = Email(..., status=EmailStatus.UNREAD)
    fake_repo.save(email)

    result = service.mark_classified(email.id, "quote")

    assert result.classification == "quote"
    assert result.status == EmailStatus.CLASSIFIED

    # Vérifier persistence
    retrieved = fake_repo.get_by_id(email.id)
    assert retrieved.classification == "quote"
```

**Checklist** :

- [ ] `src/service/email/email_service.py` créé
- [ ] Tests complets (sans Supabase)

---

#### Étape 3.2 : Classification Service (LLM)

```python
# src/service/email/classification_service.py
from infrastructure.llm import LLMProvider

class ClassificationService:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def classify(self, email_text: str) -> str:
        """Appelle LLM, retourne catégorie"""
        prompt = f"""Classifie cet email:
{email_text}

Categories: quote, invoice, rfp, other
Réponse: """
        response = self.llm.chat(prompt)
        return response.strip().lower()
```

**Tests** (mock LLM) :

```python
# tests/unit/service/email/test_classification_service.py
def test_classify():
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "quote"

    service = ClassificationService(mock_llm)
    result = service.classify("I need a quote for...")

    assert result == "quote"
```

**Checklist** :

- [ ] `src/service/email/classification_service.py` créé
- [ ] Tests avec mock LLM

---

#### Étape 3.3 : Workflow Service (orchestration)

```python
# src/service/email/workflow_service.py
class EmailWorkflowService:
    def __init__(
        self,
        email_service: EmailService,
        classification_service: ClassificationService
    ):
        self.email = email_service
        self.classifier = classification_service

    def process_new_email(self, email_id: str) -> dict:
        # 1. Récupère email
        email = self.email.get_email(email_id)

        # 2. Classifie
        category = self.classifier.classify(email.body)

        # 3. Sauvegarde classification
        classified = self.email.mark_classified(email_id, category)

        return {"email_id": email_id, "category": category}
```

**Tests** :

```python
# tests/unit/service/email/test_workflow_service.py
def test_process_new_email():
    fake_repo = FakeEmailRepository()
    email = Email(..., status=EmailStatus.UNREAD)
    fake_repo.save(email)

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "quote"

    email_svc = EmailService(fake_repo)
    classifier_svc = ClassificationService(mock_llm)
    workflow = EmailWorkflowService(email_svc, classifier_svc)

    result = workflow.process_new_email(email.id)

    assert result["category"] == "quote"
    assert fake_repo.get_by_id(email.id).classification == "quote"
```

**Checklist** :

- [ ] `src/service/email/workflow_service.py` créé
- [ ] Tests integration (sans Supabase réel)

---

### **Phase 4 : Migrer le existant (graduel)**

**Durée estimée** : 3-4 jours

#### Étape 4.1 : Refactorer `command/fetch_emails.py`

- Remplace appels directs Supabase → utilise `EmailService`
- Remplace appels LLM → utilise `ClassificationService`
- Teste avec nouvelles architecture

**Avant** :

```python
# command/fetch_emails.py (old)
def run():
    emails = supabase.table("email").select("*").eq("status", "unread").execute()
    for email in emails.data:
        response = openai.chat(email["body"])
        supabase.table("email").update({"classification": response}).execute()
```

**Après** :

```python
# command/fetch_emails.py (new)
from service.email import EmailWorkflowService

def run(workflow_service: EmailWorkflowService):
    emails = workflow_service.email.get_all_unclassified(limit=100)
    for email in emails:
        workflow_service.process_new_email(email.id)
```

**Checklist** :

- [ ] `command/fetch_emails.py` refactorisé
- [ ] Tests existants passent (regression)
- [ ] Pas de breaking changes

---

#### Étape 4.2 : Supprimer `repository/` old (si existe)

- Supprime l'ancien `src/repository/*` (repository pattern ancien)
- Remplace par le nouveau `infrastructure/`

**Checklist** :

- [ ] Ancien `src/repository/` supprimé
- [ ] Références pointent vers `infrastructure/`
- [ ] Tests passent

---

### **Phase 5 : API + CLI (optionnel, pour plus tard)**

**Durée estimée** : 2-3 jours

#### Étape 5.1 : Créer routes FastAPI

```python
# src/api/routes/email_routes.py
from fastapi import APIRouter
from service.email import EmailService

router = APIRouter(prefix="/emails", tags=["emails"])

@router.post("/{email_id}/classify")
def classify_email(email_id: str, service: EmailService = Depends(get_email_service)):
    return service.mark_classified(email_id, "quote")
```

---

## 5. Checklist Complète (à cocher)

### Domain

- [ ] `domain/email.py`
- [ ] `domain/rfp.py`
- [ ] `domain/opportunity.py`
- [ ] `domain/vendor.py`
- [ ] Tests 100% coverage domain/

### Repository (Interfaces)

- [ ] `repository/email_repository.py`
- [ ] `repository/rfp_repository.py`
- [ ] `repository/opportunity_repository.py`
- [ ] `repository/vendor_repository.py`

### Infrastructure (Supabase)

- [ ] `infrastructure/supabase/email_supabase.py`
- [ ] `infrastructure/supabase/rfp_supabase.py`
- [ ] Tests avec mocks (pas real DB)

### Service (par domaine)

- [ ] `service/email/email_service.py` + tests
- [ ] `service/email/classification_service.py` + tests
- [ ] `service/email/workflow_service.py` + tests
- [ ] `service/rfp/rfp_service.py` + tests
- [ ] `service/rfp/extraction_service.py` + tests
- [ ] `service/vendor/vendor_service.py` + tests

### Refactor existant

- [ ] `command/fetch_emails.py` utilise `EmailService`
- [ ] Tous tests passent (regression)
- [ ] Supprimer code dupliqué/old

---

## 7. Points d'Attention (Critique Objective)

### ⚠️ Critical DO's

- ✅ **TDD First** : Écrire le test AVANT le code
- ✅ **Keep Regression Tests** : Les tests existants doivent continuer à passer
- ✅ **Commit Frequently** : Après chaque phase, pas à la fin (pour rollback facile)
- ✅ **No Breaking Changes** : Graduel, pas big bang
- ✅ **Document Mappings** : Garde SCHEMA_MAPPING.md à jour (sinon confusion)
- ✅ **Log Errors Clearly** : Facile à debug when things break

### ❌ Critical DON'Ts

- ❌ **Refactor + Change Logic Simultaneously** : (impossible à debug)
- ❌ **Delete Old Tests Before New Tests Pass** : (regression invisible)
- ❌ **Big Bang Refactor** : All at once = disaster
- ❌ **Over-Engineer** : Use FakeRepository, not complex test framework
- ❌ **Skip Phase 4** : Migrating existing code is critical
- ❌ **Ignore Logging** : Will regret when debugging Phase 4
- ❌ **Use DTOs in Domain** : Creates circular dependencies

### 🎯 Pragmatism Over Perfection

- **1 test file per service** ≠ 1 test file per function
- **FakeRepository is enough** (not SQLite test DB, not real Supabase)
- **50% code coverage > 0%** (better than perfect-but-nothing)
- **Move fast on Phase 1-2** (foundation must be solid though)

---

## 7. Commandes (à exécuter dans l'ordre)

```bash
# Phase 1 : Domain + tests
pytest tests/unit/domain/ -v

# Phase 2 : Infrastructure + tests
pytest tests/unit/infrastructure/ -v

# Phase 3 : Services + tests
pytest tests/unit/service/ -v

# Tous les tests
pytest tests/unit/ -v --cov=src

# Intégration (plus tard)
pytest tests/integration/ -v
```

---

## 8. Points d'Attention (Critique Objective)

---

## 8. Performance & Scalability Considerations

### 8.1 DTO Overhead

**Concern** : SQL row → DTO → Domain crée 2 transformations

- ❌ Potential performance hit for large datasets
- ✅ Mitigated: DTO validation happens once, then domain is immutable

**Mitigation** :

- Use batch operations (limit 100 emails at a time, not 10k)
- Cache domain entities if frequently accessed
- Lazy loading: don't fetch body_full unless needed

```python
# Example: lazy loading (add to Email)
@dataclass
class Email:
    id: str
    subject: str
    body: str = None  # ← Optional, load on demand

    def get_full_body(self, repo: EmailRepository) -> str:
        if not self.body:
            # Fetch from DB
            full_email = repo.get_by_id(self.id)
            self.body = full_email.body
        return self.body
```

### 8.2 Scalability: Adding New Domains

**Pattern** : Si tu ajoutes un nouveau domaine (ex: `Invoice`), copie ce pattern :

1. **Domain** : `src/domain/invoice.py`
2. **Repository** : `src/repository/invoice_repository.py`
3. **Infrastructure** : `src/infrastructure/supabase/invoice_supabase.py`
4. **Service** : `src/service/invoice/invoice_service.py`
5. **Tests** : `tests/unit/service/invoice/test_invoice_service.py`
6. **DTO** : Ajoute dans `src/infrastructure/database/dto.py`

This repeatable pattern scales to 10+ domains without architectural changes.

---

## 9. Common Pitfalls & Solutions

### ❌ Pitfall 1: Circular Imports

**Problem** :

```python
# src/domain/email.py
from infrastructure.database.dto import EmailDTO  # ← WRONG! Domain shouldn't import infrastructure
```

**Solution** : Domain pures (pas d'imports infra) :

```python
# src/domain/email.py
from enum import Enum  # ← Only stdlib + other domain

class Email:
    # Pure business logic, no DTO
```

### ❌ Pitfall 2: Mutating Domain Entities

**Problem** :

```python
email.status = EmailStatus.CLASSIFIED  # ← WRONG! Breaks immutability
```

**Solution** : Retourner une nouvelle entité :

```python
email = email.mark_classified("quote")  # ← Return new Email
```

### ❌ Pitfall 3: Repository in Domain

**Problem** :

```python
class Email:
    def save(self):  # ← WRONG! Domain doesn't know about DB
        pass
```

**Solution** : Service calls repository :

```python
# Service handles persistence
service.mark_classified(email_id, category)  # ← Service saves
```

### ❌ Pitfall 4: Mock Everything in Tests

**Problem** :

```python
def test_workflow():
    mock_repo = MagicMock()  # Mock everything
    mock_llm = MagicMock()
    # ← Hard to catch real integration bugs
```

**Solution** : Mix real + mocks :

```python
def test_workflow():
    real_repo = FakeEmailRepository()  # Real (in-memory)
    mock_llm = MagicMock()  # Only LLM is mocked
    # ← Catch real repository bugs
```

### ❌ Pitfall 5: Refactor + Change Logic Together

**Problem** : While refactoring, also "optimize" the classification logic

- Hard to debug (what broke, refactor or logic change?)
- Breaks regression tests

**Solution** : One thing at a time

- Phase 4: ONLY migrate code (same behavior)
- Phase 5+: Optimize logic (after migration stable)

---

## 10. Durée Estimée

| Phase                   | Durée | Cumul  |
| ----------------------- | ----- | ------ |
| 1 : Domain + Repository | 2-3j  | 2-3j   |
| 2 : Infrastructure      | 2-3j  | 4-6j   |
| 3 : Services            | 3-4j  | 7-10j  |
| 4 : Migration existant  | 3-4j  | 10-14j |
| 5 : API/CLI             | 2-3j  | 12-17j |

**Total** : ~2-3 semaines pour refactoring complet

---

## 11. Recommandation de Démarrage

**Semaine 1** :

- Phase 1 : Domain + tests
- Phase 2 : Infrastructure

**Semaine 2** :

- Phase 3 : Services

**Semaine 3** :

- Phase 4 : Migrer existant + cleanup

**Post** :

- Phase 5 : API/CLI (optionnel)
