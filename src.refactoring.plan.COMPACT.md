# Refactoring Plan : Clean Architecture + DDD (COMPACT)

> 📌 **This is the actionable summary.** See `src.refactoring.plan.md` for full details, code examples, and Phase 2-5 specifications.

**Status** : Ready to start  
**Duration** : 2-3 weeks  
**Version** : 2.1 (Compact)

---

## 🎯 TL;DR

**Problem** : Spaghetti code (business logic + DB + LLM mixed)  
**Solution** : Clean Architecture with DDD + TDD

**Pattern** : Domain → Repository → Infrastructure → Service → API/Command

**Start** : Phase 1 (Domain + Repository)

---

## 📁 Target Structure

```
back/src/
├── domain/                    # Pure entities
│   ├── enums.py              # All enums
│   ├── email.py
│   ├── rfp.py
│   ├── opportunity.py
│   └── vendor.py
├── repository/               # Interfaces (contracts)
│   ├── email_repository.py
│   ├── rfp_repository.py
│   ├── opportunity_repository.py
│   └── vendor_repository.py
├── infrastructure/           # Implementations
│   ├── supabase/
│   │   ├── email_supabase.py
│   │   ├── dto.py           # Pydantic DTOs
│   │   └── SCHEMA_MAPPING.md
│   ├── factory.py            # Dependency Injection
│   └── exceptions.py         # RepositoryError, etc.
├── service/                  # Business logic
│   ├── email/
│   │   ├── email_service.py
│   │   ├── classification_service.py
│   │   └── workflow_service.py
│   ├── rfp/
│   ├── vendor/
│   └── opportunity/
├── command/                  # CLI
├── api/                      # HTTP routes
└── lib/                      # Utils

tests/
├── unit/
│   ├── domain/
│   ├── service/
│   ├── infrastructure/
│   └── fixtures/
│       ├── fake_repositories.py
│       ├── sample_data.py
│       └── conftest.py
└── integration/
```

---

## 🚀 PHASE 1: Domain + Repository (2-3 days)

### Step 1.1: Enums

```python
# src/domain/enums.py
class EmailStatus(Enum):
    UNREAD = "unread"
    CLASSIFIED = "classified"

class DocumentStatus(Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    # ... sync with schema/types/*.sql
```

**Checklist** :

- [ ] All PostgreSQL enums → Python equivalents
- [ ] Tests for enum values

---

### Step 1.2: Domain Entities

```python
# src/domain/email.py
from dataclasses import dataclass
from domain.enums import EmailStatus

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
        return Email(..., status=EmailStatus.CLASSIFIED, classification=category)
```

**Tests** (TDD - write BEFORE code):

```python
# tests/unit/domain/test_email.py
def test_mark_classified():
    email = Email(..., status=EmailStatus.UNREAD)
    classified = email.mark_classified("quote")
    assert classified.status == EmailStatus.CLASSIFIED
    assert email.status == EmailStatus.UNREAD  # Immutable

def test_cannot_classify_twice():
    email = Email(..., status=EmailStatus.CLASSIFIED)
    with pytest.raises(ValueError):
        email.mark_classified("invoice")
```

**Checklist** :

- [ ] `src/domain/email.py` + tests
- [ ] `src/domain/rfp.py` + tests
- [ ] `src/domain/opportunity.py` + tests
- [ ] `src/domain/vendor.py` + tests
- [ ] All domain entities 100% tested

---

### Step 1.3: Repository Interfaces

```python
# src/repository/email_repository.py
from abc import ABC, abstractmethod
from domain.email import Email

class EmailRepository(ABC):
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

**Checklist** :

- [ ] `src/repository/email_repository.py`
- [ ] `src/repository/rfp_repository.py`
- [ ] `src/repository/opportunity_repository.py`
- [ ] `src/repository/vendor_repository.py`

---

### Step 1.4: Test Fixtures

```python
# tests/conftest.py
@pytest.fixture
def fake_email_repo():
    return FakeEmailRepository()

@pytest.fixture
def mock_llm(mocker):
    mock = mocker.MagicMock()
    mock.chat.return_value = "quote"
    return mock

# tests/fixtures/fake_repositories.py
class FakeEmailRepository(EmailRepository):
    def __init__(self):
        self.emails = {}

    def get_by_id(self, email_id: str) -> Email:
        if email_id not in self.emails:
            raise ValueError(f"Email {email_id} not found")
        return self.emails[email_id]

    def save(self, email: Email) -> None:
        self.emails[email.id] = email

# tests/fixtures/sample_data.py
def sample_email(id="test-1", status=EmailStatus.UNREAD):
    return Email(id=id, subject="Test", body="...",
                 sender="test@example.com", status=status)
```

**Checklist** :

- [ ] `tests/conftest.py` with global fixtures
- [ ] `tests/fixtures/fake_repositories.py`
- [ ] `tests/fixtures/sample_data.py`

---

## ✅ Phase 1 Completion Checklist

- [ ] **Domain** : `email.py`, `rfp.py`, `opportunity.py`, `vendor.py` + tests
- [ ] **Enums** : `src/domain/enums.py` with all PostgreSQL types
- [ ] **Repository** : `email_repository.py`, `rfp_repository.py`, etc. (abstract)
- [ ] **Fixtures** : `conftest.py`, `fake_repositories.py`, `sample_data.py`
- [ ] **Tests** : `pytest tests/unit/domain/ -v` passes 100%
- [ ] **Commit** : `git commit -m "Phase 1: Domain + Repository interfaces"`

---

## 🔧 PHASE 2: Infrastructure (2-3 days) - SUMMARY

**What** : Implement Supabase + DTO mapping + factory pattern

**Files** :

- `src/infrastructure/supabase/email_supabase.py` (SupabaseEmailRepository)
- `src/infrastructure/database/dto.py` (Pydantic DTOs)
- `src/infrastructure/factory.py` (ServiceFactory)
- `src/infrastructure/exceptions.py` (RepositoryError)

**Key** :

- DTO validates SQL → Domain conversion
- Factory injects dependencies
- Error handling per-layer (Repository catches DB errors)

**Skip details** : See src.refactoring.plan.md sections 2.5-2.7 if needed

---

## 💼 PHASE 3: Services (3-4 days) - SUMMARY

**What** : Business logic layer (orchestration)

**Files** :

- `src/service/email/email_service.py`
- `src/service/email/classification_service.py`
- `src/service/email/workflow_service.py`

**Key** : Services use FakeRepository in tests (no Supabase mocks)

---

## 🔄 PHASE 4: Migrate Existing (3-4 days) - SUMMARY

**What** : Refactor old code → use new services

**Strategy** : Strangler pattern (old + new coexist)

**Impact** : Update `command/fetch_emails.py`, etc.

---

## 🚨 Critical DO's & DON'Ts

### ✅ DO

- Write tests BEFORE code (TDD)
- Keep existing tests passing (regression)
- Commit after each step
- Use FakeRepository (not real DB in tests)
- Document field mappings (SQL ↔ Domain)

### ❌ DON'T

- Refactor + change logic simultaneously
- Delete old code before new code stable
- Mock everything (use FakeRepository for real logic)
- Skip Phase 4 (migrating existing code = critical)

---

## 🔴 Known Gaps (Phase 2+, NOT blocking Phase 1)

| Gap                        | Phase | Solution               |
| -------------------------- | ----- | ---------------------- |
| Data migration             | 4     | Migration script       |
| Service dependency diagram | 2     | DAG documentation      |
| External provider testing  | 2     | Test doubles hierarchy |
| Concurrent requests        | 4     | Idempotency keys       |
| Code audit checklist       | 4     | Grep script            |
| Rollback strategy          | 4     | Feature flags          |

---

## 📚 Full Details

See `src.refactoring.plan.md` for:

- Phase 2-5 details
- Common pitfalls (5 examples)
- Performance considerations
- Error handling per-layer
- Schema mapping
- Dependency injection patterns

---

## 📖 Document Structure

| File                              | Use                 | Size        |
| --------------------------------- | ------------------- | ----------- |
| `src.refactoring.plan.COMPACT.md` | Phase 1 execution   | ~350 lines  |
| `src.refactoring.plan.md`         | Reference + details | ~1500 lines |

**Strategy** :

- Start with COMPACT (less overwhelm, clear next steps)
- Refer to full plan when you hit questions
- Keep both files in sync

---

## 🎬 Get Started NOW

```bash
# 1. Create directory structure
mkdir -p src/{domain,repository,infrastructure,service}
mkdir -p tests/{unit,fixtures,integration}

# 2. Start Phase 1
pytest tests/unit/domain/ -v

# 3. First file: enums
# Edit src/domain/enums.py
# Edit tests/unit/domain/test_enums.py

# All done? Commit!
git add src/ tests/
git commit -m "Phase 1 complete: Domain + Repository"
```
