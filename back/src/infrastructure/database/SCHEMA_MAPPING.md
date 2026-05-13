# SCHEMA_MAPPING

## Opportunity Mapping (Phase 1/2 baseline)

| Domain field                    | SQL column                      | Type               |
| ------------------------------- | ------------------------------- | ------------------ |
| Opportunity.id                  | opportunity.id                  | uuid               |
| Opportunity.owner_user_id       | opportunity.owner_user_id       | uuid               |
| Opportunity.account_id          | opportunity.account_id          | uuid               |
| Opportunity.name                | opportunity.name                | text               |
| Opportunity.stage               | opportunity.stage               | opportunity_stage  |
| Opportunity.status              | opportunity.status              | opportunity_status |
| Opportunity.amount_estimated    | opportunity.amount_estimated    | numeric            |
| Opportunity.probability         | opportunity.probability         | integer            |
| Opportunity.expected_close_date | opportunity.expected_close_date | date               |
| Opportunity.source              | opportunity.source              | text               |
| Opportunity.source_reference_id | opportunity.source_reference_id | uuid               |

## Vendor Mapping (Phase 1/2 baseline)

| Domain field      | SQL column        | Type        |
| ----------------- | ----------------- | ----------- |
| Vendor.id         | vendor.id         | uuid        |
| Vendor.name       | vendor.name       | text        |
| Vendor.email      | vendor.email      | text        |
| Vendor.phone      | vendor.phone      | text        |
| Vendor.website    | vendor.website    | text        |
| Vendor.created_at | vendor.created_at | timestamptz |

## Email Mapping

See DTO: src/infrastructure/database/dto.py
