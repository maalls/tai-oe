


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."contact_role" AS ENUM (
    'DECISION_MAKER',
    'INFLUENCER',
    'BUYER',
    'TECHNICAL',
    'FINANCE'
);


ALTER TYPE "public"."contact_role" OWNER TO "supabase_admin";


CREATE TYPE "public"."document_channel" AS ENUM (
    'EMAIL',
    'PORTAL',
    'PHONE',
    'MANUAL',
    'OTHER'
);


ALTER TYPE "public"."document_channel" OWNER TO "supabase_admin";


CREATE TYPE "public"."document_link_type" AS ENUM (
    'QUOTE_TO_PO',
    'PO_TO_INVOICE',
    'QUOTE_TO_INVOICE',
    'CONTRACT_TO_SOW',
    'DELIVERY_TO_INVOICE',
    'ACCEPTANCE_TO_INVOICE',
    'QUOTE_REVISION'
);


ALTER TYPE "public"."document_link_type" OWNER TO "supabase_admin";


CREATE TYPE "public"."document_status" AS ENUM (
    'DRAFT',
    'SENT',
    'RECEIVED',
    'SUBMITTED',
    'SHORTLISTED',
    'ACCEPTED',
    'REJECTED',
    'CONFIRMED',
    'FULFILLED',
    'CANCELLED',
    'EXPIRED',
    'PAID',
    'PARTIALLY_PAID',
    'OVERDUE',
    'DISPUTED',
    'APPLIED'
);


ALTER TYPE "public"."document_status" OWNER TO "supabase_admin";


CREATE TYPE "public"."document_type" AS ENUM (
    'RFI',
    'RFP',
    'RFQ',
    'PROPOSAL',
    'QUOTE',
    'PO',
    'CONTRACT',
    'DELIVERY_NOTE',
    'ACCEPTANCE',
    'INVOICE',
    'CREDIT_NOTE',
    'NDA',
    'DPA',
    'SLA',
    'CGV',
    'ATTACHMENT',
    'FAMILY_DISCOUNT'
);


ALTER TYPE "public"."document_type" OWNER TO "supabase_admin";


CREATE TYPE "public"."invoice_payment_status" AS ENUM (
    'UNPAID',
    'PARTIAL',
    'PAID',
    'CANCELLED'
);


ALTER TYPE "public"."invoice_payment_status" OWNER TO "supabase_admin";


CREATE TYPE "public"."opportunity_stage" AS ENUM (
    'NEW_LEAD',
    'QUALIFYING',
    'NEEDS_DEFINED',
    'RFP_IN_PROGRESS',
    'RFQ_IN_PROGRESS',
    'OFFER_SENT',
    'NEGOTIATION',
    'COMMITMENT',
    'PREPARATION',
    'DELIVERY_IN_PROGRESS',
    'ACCEPTED',
    'INVOICED',
    'PAID',
    'CLOSED_WON',
    'CLOSED_LOST',
    'ON_HOLD'
);


ALTER TYPE "public"."opportunity_stage" OWNER TO "supabase_admin";


CREATE TYPE "public"."opportunity_status" AS ENUM (
    'OPEN',
    'WON',
    'LOST',
    'ON_HOLD'
);


ALTER TYPE "public"."opportunity_status" OWNER TO "supabase_admin";


CREATE TYPE "public"."quote_acceptance_mode" AS ENUM (
    'SIGNED_QUOTE',
    'EMAIL_OK',
    'PORTAL_CLICK'
);


ALTER TYPE "public"."quote_acceptance_mode" OWNER TO "supabase_admin";


CREATE TYPE "public"."unit_type" AS ENUM (
    'U',
    'M',
    'H',
    'DAY',
    'PACK',
    'KG',
    'L'
);


ALTER TYPE "public"."unit_type" OWNER TO "supabase_admin";


CREATE OR REPLACE FUNCTION "public"."enforce_document_type_for_specialization"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE doc_type document_type;
BEGIN
  SELECT type INTO doc_type FROM document WHERE id = NEW.document_id;

  IF TG_TABLE_NAME = 'quote' AND doc_type <> 'QUOTE' THEN
    RAISE EXCEPTION 'quote.document_id must reference a document of type QUOTE (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'purchase_order' AND doc_type <> 'PO' THEN
    RAISE EXCEPTION 'purchase_order.document_id must reference a document of type PO (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'contract' AND doc_type <> 'CONTRACT' THEN
    RAISE EXCEPTION 'contract.document_id must reference a document of type CONTRACT (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'invoice' AND doc_type <> 'INVOICE' THEN
    RAISE EXCEPTION 'invoice.document_id must reference a document of type INVOICE (got %)', doc_type;
  END IF;

  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."enforce_document_type_for_specialization"() OWNER TO "supabase_admin";


CREATE OR REPLACE FUNCTION "public"."update_sent_email_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_sent_email_updated_at"() OWNER TO "supabase_admin";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."account" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "vat_number" "text",
    "siret" "text",
    "address_line1" "text",
    "address_line2" "text",
    "postal_code" "text",
    "city" "text",
    "country_code" character(2) DEFAULT 'FR'::"bpchar",
    "payment_terms_default" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "industry" "text",
    "phone" "text",
    "website" "text"
);


ALTER TABLE "public"."account" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."action" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "opportunity_id" "uuid" NOT NULL,
    "action_type" character varying(50) NOT NULL,
    "status" character varying(20) DEFAULT 'active'::character varying NOT NULL,
    "schedule_type" character varying(20) NOT NULL,
    "schedule_config" "jsonb",
    "config" "jsonb",
    "last_executed_at" timestamp with time zone,
    "next_execution_at" timestamp with time zone,
    "execution_count" integer DEFAULT 0 NOT NULL,
    "max_executions" integer,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "created_by" "uuid",
    CONSTRAINT "valid_action_type" CHECK ((("action_type")::"text" = ANY ((ARRAY['recurring_quote'::character varying, 'recurring_invoice'::character varying, 'follow_up_email'::character varying, 'stage_reminder'::character varying])::"text"[]))),
    CONSTRAINT "valid_schedule_type" CHECK ((("schedule_type")::"text" = ANY ((ARRAY['monthly'::character varying, 'weekly'::character varying, 'daily'::character varying, 'one_time'::character varying, 'custom_cron'::character varying])::"text"[]))),
    CONSTRAINT "valid_status" CHECK ((("status")::"text" = ANY ((ARRAY['active'::character varying, 'paused'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::"text"[])))
);


ALTER TABLE "public"."action" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."action_execution_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "action_id" "uuid" NOT NULL,
    "executed_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "status" character varying(20) NOT NULL,
    "result_data" "jsonb",
    "error_message" "text",
    "duration_ms" integer,
    CONSTRAINT "action_execution_log_status_check" CHECK ((("status")::"text" = ANY (ARRAY[('success'::character varying)::"text", ('failed'::character varying)::"text", ('skipped'::character varying)::"text"])))
);


ALTER TABLE "public"."action_execution_log" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."brand" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "legal_name" "text",
    "website" "text",
    "email" "text",
    "phone" "text",
    "address_line1" "text",
    "address_line2" "text",
    "city" "text",
    "state" "text",
    "postal_code" "text",
    "country_code" character(2) DEFAULT 'FR'::"bpchar",
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "marque" "text" NOT NULL,
    "vendor_id" "uuid" NOT NULL,
    "minimum_margin" numeric(5,2) DEFAULT 0.00,
    "target_margin" numeric(5,2) DEFAULT 0.00
);


ALTER TABLE "public"."brand" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."brand_margin" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "brand_id" "uuid" NOT NULL,
    "contract_id" "uuid" NOT NULL,
    "margin" numeric(12,4) NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."brand_margin" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."contact" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "account_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "email" "text",
    "phone" "text",
    "role_title" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."contact" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."contract" (
    "document_id" "uuid" NOT NULL,
    "start_date" "date",
    "end_date" "date",
    "renewal_terms" "text"
);


ALTER TABLE "public"."contract" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."document" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "opportunity_id" "uuid",
    "type" "public"."document_type" NOT NULL,
    "status" "public"."document_status" DEFAULT 'DRAFT'::"public"."document_status" NOT NULL,
    "title" "text" NOT NULL,
    "external_ref" "text",
    "issued_at" timestamp with time zone,
    "received_at" timestamp with time zone,
    "valid_until" "date",
    "currency" character(3) DEFAULT 'EUR'::"bpchar" NOT NULL,
    "total_excl_tax" numeric(14,2) DEFAULT 0,
    "total_tax" numeric(14,2) DEFAULT 0,
    "total_incl_tax" numeric(14,2) DEFAULT 0,
    "storage_key" "text",
    "version" integer DEFAULT 1 NOT NULL,
    "parent_document_id" "uuid",
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "channel" "public"."document_channel",
    "source_message_id" "text",
    CONSTRAINT "document_version_check" CHECK (("version" >= 1))
);


ALTER TABLE "public"."document" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."document_line" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "document_id" "uuid" NOT NULL,
    "position" integer DEFAULT 1 NOT NULL,
    "sku" "text",
    "description" "text" NOT NULL,
    "quantity" numeric(14,3) DEFAULT 1 NOT NULL,
    "unit" "public"."unit_type" DEFAULT 'U'::"public"."unit_type" NOT NULL,
    "unit_price_excl_tax" numeric(14,4) DEFAULT 0 NOT NULL,
    "tax_rate" numeric(5,2) DEFAULT 20 NOT NULL,
    "discount_rate" numeric(5,2) DEFAULT 0,
    "line_total_excl_tax" numeric(14,2) DEFAULT 0 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "brand" "text",
    "is_ref_verified" boolean DEFAULT false,
    "is_quantity_verified" boolean DEFAULT false,
    "is_price_verified" boolean DEFAULT false,
    "client_discount_rate" numeric(6,3),
    CONSTRAINT "document_line_discount_rate_check" CHECK (("discount_rate" >= (0)::numeric)),
    CONSTRAINT "document_line_quantity_check" CHECK (("quantity" >= (0)::numeric))
);


ALTER TABLE "public"."document_line" OWNER TO "supabase_admin";


COMMENT ON COLUMN "public"."document_line"."brand" IS 'Brand associated with the line item.';



CREATE TABLE IF NOT EXISTS "public"."document_link" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "from_document_id" "uuid" NOT NULL,
    "to_document_id" "uuid" NOT NULL,
    "link_type" "public"."document_link_type" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."document_link" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."document_status_transition" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "document_id" "uuid" NOT NULL,
    "from_status" "public"."document_status",
    "to_status" "public"."document_status" NOT NULL,
    "changed_by" "uuid",
    "changed_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "note" "text"
);


ALTER TABLE "public"."document_status_transition" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."email" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "provider" "text" NOT NULL,
    "provider_account_id" "text",
    "provider_message_id" "text" NOT NULL,
    "provider_thread_id" "text",
    "provider_metadata" "jsonb",
    "subject" "text",
    "from_email" "text",
    "to_email" "text",
    "email_date" timestamp without time zone,
    "body_preview" "text",
    "body_full" "text",
    "category" "text",
    "classification_reason" "text",
    "is_classified" boolean DEFAULT false,
    "classified_at" timestamp without time zone,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "updated_at" timestamp without time zone DEFAULT "now"(),
    "category_suggestion" "text",
    "important" boolean DEFAULT false NOT NULL,
    "from_name" "text",
    "from_raw" "text",
    "from_domain" "text",
    "from_local" "text",
    "from_is_valid" boolean,
    "cc_email" "text",
    "fetched_at" timestamp without time zone DEFAULT "now"(),
    "spf_status" "text",
    "dkim_status" "text",
    "dmarc_status" "text",
    "auth_score" integer DEFAULT 0,
    "is_verified" boolean DEFAULT false,
    "auth_headers" "jsonb",
    "sender_verified_at" timestamp without time zone,
    "account_id" "uuid",
    "contact_id" "uuid"
);


ALTER TABLE "public"."email" OWNER TO "supabase_admin";


COMMENT ON COLUMN "public"."email"."category_suggestion" IS 'Suggestion for new Category name, useful if category hasn''t been recognized.';



COMMENT ON COLUMN "public"."email"."account_id" IS 'Reference to the account (company) associated with the sender';



CREATE TABLE IF NOT EXISTS "public"."email_attachment" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email_id" "uuid" NOT NULL,
    "provider_attachment_id" "text" NOT NULL,
    "filename" "text",
    "mime_type" "text",
    "size" integer,
    "storage_path" "text",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."email_attachment" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."email_labels" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email_id" "uuid" NOT NULL,
    "provider_label_id" "text" NOT NULL,
    "label_name" "text" NOT NULL,
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."email_labels" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."family" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text",
    "type" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "brand_id" "uuid" NOT NULL,
    "code" "text",
    "product_code" "text",
    "quantity" numeric(14,3),
    "discount" numeric(5,2),
    "unit" "text",
    "packing" "text",
    "lead_time_week" integer,
    "net_price" numeric(14,4),
    "markup" numeric(5,2),
    "minimum_margin" numeric(5,2) DEFAULT 0.00,
    "target_margin" numeric(5,2) DEFAULT 0.00
);


ALTER TABLE "public"."family" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."invoice" (
    "document_id" "uuid" NOT NULL,
    "invoice_number" "text",
    "due_date" "date",
    "paid_at" timestamp with time zone,
    "payment_status" "public"."invoice_payment_status" DEFAULT 'UNPAID'::"public"."invoice_payment_status" NOT NULL
);


ALTER TABLE "public"."invoice" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."lead" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "full_name" "text",
    "email" "text",
    "phone" "text",
    "company_name" "text",
    "status" "text" DEFAULT 'NEW'::"text" NOT NULL,
    "owner_user_id" "uuid",
    "source" "text",
    "notes" "text",
    "converted_account_id" "uuid",
    "converted_contact_id" "uuid",
    "converted_opportunity_id" "uuid",
    "converted_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "lead_status_check" CHECK (("status" = ANY (ARRAY['NEW'::"text", 'CONTACTED'::"text", 'QUALIFIED'::"text", 'DISQUALIFIED'::"text", 'CONVERTED'::"text"])))
);


ALTER TABLE "public"."lead" OWNER TO "supabase_admin";


CREATE SEQUENCE IF NOT EXISTS "public"."migrations_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."migrations_id_seq" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."migrations" (
    "id" integer DEFAULT "nextval"('"public"."migrations_id_seq"'::"regclass") NOT NULL,
    "migration_name" "text" NOT NULL,
    "executed_at" timestamp without time zone DEFAULT "now"(),
    "checksum" "text"
);


ALTER TABLE "public"."migrations" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."opportunity" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "account_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "stage" "public"."opportunity_stage" DEFAULT 'NEW_LEAD'::"public"."opportunity_stage" NOT NULL,
    "status" "public"."opportunity_status" DEFAULT 'OPEN'::"public"."opportunity_status" NOT NULL,
    "currency" character(3) DEFAULT 'EUR'::"bpchar" NOT NULL,
    "amount_estimated" numeric(14,2) DEFAULT 0,
    "probability" integer DEFAULT 10 NOT NULL,
    "expected_close_date" "date",
    "owner_user_id" "uuid",
    "source" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "source_reference_id" "uuid",
    CONSTRAINT "opportunity_probability_check" CHECK ((("probability" >= 0) AND ("probability" <= 100)))
);


ALTER TABLE "public"."opportunity" OWNER TO "supabase_admin";


COMMENT ON COLUMN "public"."opportunity"."source_reference_id" IS 'UUID reference to the source record (e.g., email.id when source=''email'', meeting.id when source=''meeting'')';



CREATE TABLE IF NOT EXISTS "public"."opportunity_participant" (
    "opportunity_id" "uuid" NOT NULL,
    "contact_id" "uuid" NOT NULL,
    "role" "public"."contact_role" NOT NULL
);


ALTER TABLE "public"."opportunity_participant" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."opportunity_state_transition" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "opportunity_id" "uuid" NOT NULL,
    "from_stage" "public"."opportunity_stage",
    "to_stage" "public"."opportunity_stage" NOT NULL,
    "changed_by" "uuid",
    "changed_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "note" "text"
);


ALTER TABLE "public"."opportunity_state_transition" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."product" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "sku" "text" NOT NULL,
    "name" "text" NOT NULL,
    "default_unit" "public"."unit_type" DEFAULT 'U'::"public"."unit_type" NOT NULL,
    "default_tax_rate" numeric(5,2) DEFAULT 20 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "price" numeric(12,4),
    "brand_id" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "fabdis_appli_date" "date",
    "fabdis_edited_date" "date",
    CONSTRAINT "product_default_tax_rate_check" CHECK ((("default_tax_rate" >= (0)::numeric) AND ("default_tax_rate" <= (100)::numeric)))
);


ALTER TABLE "public"."product" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."product_family" (
    "product_id" "uuid" NOT NULL,
    "family_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."product_family" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."profile" (
    "id" "uuid" NOT NULL,
    "email" "text",
    "full_name" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "google_token_pickle" "text"
);


ALTER TABLE "public"."profile" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."purchase_order" (
    "document_id" "uuid" NOT NULL,
    "po_number" "text",
    "ordered_at" timestamp with time zone,
    "requested_delivery_date" "date"
);


ALTER TABLE "public"."purchase_order" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."quote" (
    "document_id" "uuid" NOT NULL,
    "payment_terms" "text",
    "delivery_terms" "text",
    "incoterm" "text",
    "cgv_document_id" "uuid",
    "acceptance_mode" "public"."quote_acceptance_mode",
    "accepted_at" timestamp with time zone,
    "checked_by" "uuid",
    "checked_at" timestamp with time zone,
    "all_lines_verified" boolean DEFAULT false,
    "last_verification_update" timestamp with time zone
);


ALTER TABLE "public"."quote" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."sender_verification" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "sender_email" "text" NOT NULL,
    "sender_domain" "text" NOT NULL,
    "sender_name" "text",
    "trust_score" integer DEFAULT 0,
    "auth_history" "jsonb",
    "is_trusted" boolean DEFAULT false,
    "is_blocklisted" boolean DEFAULT false,
    "domain_spf_configured" boolean DEFAULT false,
    "domain_dkim_configured" boolean DEFAULT false,
    "domain_dmarc_configured" boolean DEFAULT false,
    "total_emails_received" integer DEFAULT 0,
    "verified_emails_count" integer DEFAULT 0,
    "failed_auth_count" integer DEFAULT 0,
    "last_verified_at" timestamp without time zone,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "updated_at" timestamp without time zone DEFAULT "now"(),
    "is_verified" boolean DEFAULT false
);


ALTER TABLE "public"."sender_verification" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."sent_email" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "document_id" "uuid",
    "opportunity_id" "uuid",
    "from_email" "text" NOT NULL,
    "to_emails" "text"[] NOT NULL,
    "cc_emails" "text"[],
    "bcc_emails" "text"[],
    "subject" "text" NOT NULL,
    "body" "text" NOT NULL,
    "provider" "text" DEFAULT 'gmail'::"text",
    "provider_message_id" "text",
    "provider_metadata" "jsonb",
    "status" "text" DEFAULT 'sent'::"text",
    "sent_at" timestamp without time zone DEFAULT "now"(),
    "delivered_at" timestamp without time zone,
    "opened_at" timestamp without time zone,
    "bounced_at" timestamp without time zone,
    "error_message" "text",
    "attachment_names" "text"[],
    "sent_by_user_id" "uuid",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "updated_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."sent_email" OWNER TO "supabase_admin";


CREATE TABLE IF NOT EXISTS "public"."vendor" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "email" "text",
    "phone" "text",
    "website" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."vendor" OWNER TO "supabase_admin";


ALTER TABLE ONLY "public"."account"
    ADD CONSTRAINT "account_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."action_execution_log"
    ADD CONSTRAINT "action_execution_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profile"
    ADD CONSTRAINT "app_user_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."profile"
    ADD CONSTRAINT "app_user_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."brand_margin"
    ADD CONSTRAINT "brand_margin_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."brand"
    ADD CONSTRAINT "brand_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."brand"
    ADD CONSTRAINT "brand_vendor_name_key" UNIQUE ("vendor_id", "name");



ALTER TABLE ONLY "public"."contact"
    ADD CONSTRAINT "contact_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."contract"
    ADD CONSTRAINT "contract_pkey" PRIMARY KEY ("document_id");



ALTER TABLE ONLY "public"."document_line"
    ADD CONSTRAINT "document_line_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_link"
    ADD CONSTRAINT "document_link_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_status_transition"
    ADD CONSTRAINT "document_status_transition_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_attachment"
    ADD CONSTRAINT "email_attachment_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_labels"
    ADD CONSTRAINT "email_labels_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "emails_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."family"
    ADD CONSTRAINT "family_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."invoice"
    ADD CONSTRAINT "invoice_pkey" PRIMARY KEY ("document_id");



ALTER TABLE ONLY "public"."lead"
    ADD CONSTRAINT "lead_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."migrations"
    ADD CONSTRAINT "migrations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."opportunity_participant"
    ADD CONSTRAINT "opportunity_participant_pkey" PRIMARY KEY ("opportunity_id", "contact_id");



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."opportunity_state_transition"
    ADD CONSTRAINT "opportunity_state_transition_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_brand_id_sku_key" UNIQUE ("brand_id", "sku");



ALTER TABLE ONLY "public"."product_family"
    ADD CONSTRAINT "product_family_pkey" PRIMARY KEY ("product_id", "family_id");



ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."purchase_order"
    ADD CONSTRAINT "purchase_order_pkey" PRIMARY KEY ("document_id");



ALTER TABLE ONLY "public"."quote"
    ADD CONSTRAINT "quote_pkey" PRIMARY KEY ("document_id");



ALTER TABLE ONLY "public"."sender_verification"
    ADD CONSTRAINT "sender_verification_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sent_email"
    ADD CONSTRAINT "sent_email_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "unique_provider_message" UNIQUE ("user_id", "provider", "provider_message_id");



ALTER TABLE ONLY "public"."vendor"
    ADD CONSTRAINT "vendor_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."vendor"
    ADD CONSTRAINT "vendor_pkey" PRIMARY KEY ("id");



CREATE UNIQUE INDEX "brand_margin_brand_id_contract_id_key" ON "public"."brand_margin" USING "btree" ("brand_id", "contract_id");



CREATE UNIQUE INDEX "document_link_from_document_id_to_document_id_link_type_key" ON "public"."document_link" USING "btree" ("from_document_id", "to_document_id", "link_type");



CREATE INDEX "idx_account_name" ON "public"."account" USING "btree" ("name");



CREATE INDEX "idx_action_execution_log_action_id" ON "public"."action_execution_log" USING "btree" ("action_id");



CREATE INDEX "idx_action_execution_log_executed_at" ON "public"."action_execution_log" USING "btree" ("executed_at");



CREATE INDEX "idx_action_next_execution" ON "public"."action" USING "btree" ("next_execution_at") WHERE (("status")::"text" = 'active'::"text");



CREATE INDEX "idx_action_opportunity_id" ON "public"."action" USING "btree" ("opportunity_id");



CREATE INDEX "idx_action_type" ON "public"."action" USING "btree" ("action_type");



CREATE INDEX "idx_action_user_id" ON "public"."action" USING "btree" ("user_id");



CREATE INDEX "idx_brand_email" ON "public"."brand" USING "btree" ("email");



CREATE INDEX "idx_brand_margin_brand" ON "public"."brand_margin" USING "btree" ("brand_id");



CREATE INDEX "idx_brand_margin_contract" ON "public"."brand_margin" USING "btree" ("contract_id");



CREATE INDEX "idx_brand_marque" ON "public"."brand" USING "btree" ("marque");



CREATE INDEX "idx_brand_name" ON "public"."brand" USING "btree" ("name");



CREATE INDEX "idx_brand_vendor_id" ON "public"."brand" USING "btree" ("vendor_id");



CREATE INDEX "idx_contact_account" ON "public"."contact" USING "btree" ("account_id");



CREATE INDEX "idx_contact_email" ON "public"."contact" USING "btree" ("email");



CREATE INDEX "idx_doc_line_doc" ON "public"."document_line" USING "btree" ("document_id");



CREATE INDEX "idx_doc_line_is_price_verified" ON "public"."document_line" USING "btree" ("is_price_verified");



CREATE INDEX "idx_doc_line_is_quantity_verified" ON "public"."document_line" USING "btree" ("is_quantity_verified");



CREATE INDEX "idx_doc_line_is_ref_verified" ON "public"."document_line" USING "btree" ("is_ref_verified");



CREATE INDEX "idx_doc_line_price_verified_status" ON "public"."document_line" USING "btree" ("document_id", "is_price_verified");



CREATE INDEX "idx_doc_line_quantity_verified_status" ON "public"."document_line" USING "btree" ("document_id", "is_quantity_verified");



CREATE INDEX "idx_doc_line_verified_status" ON "public"."document_line" USING "btree" ("document_id", "is_ref_verified");



CREATE INDEX "idx_doc_link_from" ON "public"."document_link" USING "btree" ("from_document_id");



CREATE INDEX "idx_doc_link_to" ON "public"."document_link" USING "btree" ("to_document_id");



CREATE INDEX "idx_doc_transition_doc" ON "public"."document_status_transition" USING "btree" ("document_id", "changed_at" DESC);



CREATE INDEX "idx_document_opp" ON "public"."document" USING "btree" ("opportunity_id", "type");



CREATE INDEX "idx_document_parent" ON "public"."document" USING "btree" ("parent_document_id");



CREATE INDEX "idx_document_source_message" ON "public"."document" USING "btree" ("channel", "source_message_id") WHERE ("source_message_id" IS NOT NULL);



CREATE INDEX "idx_document_status" ON "public"."document" USING "btree" ("type", "status");



CREATE INDEX "idx_email_account_id" ON "public"."email" USING "btree" ("account_id");



CREATE INDEX "idx_email_attachment_email_id" ON "public"."email_attachment" USING "btree" ("email_id");



CREATE INDEX "idx_email_attachment_provider_attachment_id" ON "public"."email_attachment" USING "btree" ("provider_attachment_id");



CREATE INDEX "idx_email_auth_score" ON "public"."email" USING "btree" ("auth_score" DESC);



CREATE INDEX "idx_email_contact_id" ON "public"."email" USING "btree" ("contact_id");



CREATE INDEX "idx_email_dkim_status" ON "public"."email" USING "btree" ("dkim_status");



CREATE INDEX "idx_email_dmarc_status" ON "public"."email" USING "btree" ("dmarc_status");



CREATE INDEX "idx_email_is_verified" ON "public"."email" USING "btree" ("is_verified");



CREATE INDEX "idx_email_labels_email_id" ON "public"."email_labels" USING "btree" ("email_id");



CREATE INDEX "idx_email_labels_label_name" ON "public"."email_labels" USING "btree" ("label_name");



CREATE INDEX "idx_email_spf_status" ON "public"."email" USING "btree" ("spf_status");



CREATE INDEX "idx_email_user_provider_date" ON "public"."email" USING "btree" ("user_id", "provider", "email_date" DESC);



CREATE INDEX "idx_emails_category" ON "public"."email" USING "btree" ("category");



CREATE INDEX "idx_emails_classified" ON "public"."email" USING "btree" ("is_classified");



CREATE INDEX "idx_emails_created_at" ON "public"."email" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_emails_provider" ON "public"."email" USING "btree" ("provider");



CREATE INDEX "idx_emails_provider_message_id" ON "public"."email" USING "btree" ("provider_message_id");



CREATE INDEX "idx_emails_user_id" ON "public"."email" USING "btree" ("user_id");



CREATE INDEX "idx_family_brand" ON "public"."family" USING "btree" ("brand_id");



CREATE INDEX "idx_family_code" ON "public"."family" USING "btree" ("code");



CREATE INDEX "idx_family_name" ON "public"."family" USING "btree" ("name");



CREATE INDEX "idx_family_type" ON "public"."family" USING "btree" ("type");



CREATE INDEX "idx_invoice_due" ON "public"."invoice" USING "btree" ("due_date");



CREATE INDEX "idx_invoice_payment_status" ON "public"."invoice" USING "btree" ("payment_status");



CREATE INDEX "idx_lead_email" ON "public"."lead" USING "btree" ("email");



CREATE INDEX "idx_lead_status" ON "public"."lead" USING "btree" ("status");



CREATE INDEX "idx_migrations_name" ON "public"."migrations" USING "btree" ("migration_name");



CREATE INDEX "idx_opp_transition_opp" ON "public"."opportunity_state_transition" USING "btree" ("opportunity_id", "changed_at" DESC);



CREATE INDEX "idx_opportunity_account" ON "public"."opportunity" USING "btree" ("account_id");



CREATE INDEX "idx_opportunity_close_date" ON "public"."opportunity" USING "btree" ("expected_close_date");



CREATE INDEX "idx_opportunity_source_ref" ON "public"."opportunity" USING "btree" ("source", "source_reference_id") WHERE ("source_reference_id" IS NOT NULL);



CREATE INDEX "idx_opportunity_stage_status" ON "public"."opportunity" USING "btree" ("stage", "status");



CREATE INDEX "idx_po_number" ON "public"."purchase_order" USING "btree" ("po_number");



CREATE INDEX "idx_product_brand_id" ON "public"."product" USING "btree" ("brand_id");



CREATE INDEX "idx_product_family_family" ON "public"."product_family" USING "btree" ("family_id");



CREATE INDEX "idx_product_family_product" ON "public"."product_family" USING "btree" ("product_id");



CREATE INDEX "idx_quote_checked_by" ON "public"."quote" USING "btree" ("checked_by");



CREATE INDEX "idx_sender_verification_domain" ON "public"."sender_verification" USING "btree" ("sender_domain");



CREATE INDEX "idx_sender_verification_email" ON "public"."sender_verification" USING "btree" ("sender_email");



CREATE INDEX "idx_sender_verification_is_blocklisted" ON "public"."sender_verification" USING "btree" ("is_blocklisted");



CREATE INDEX "idx_sender_verification_is_trusted" ON "public"."sender_verification" USING "btree" ("is_trusted");



CREATE INDEX "idx_sender_verification_is_verified" ON "public"."sender_verification" USING "btree" ("is_verified");



CREATE INDEX "idx_sender_verification_trust_score" ON "public"."sender_verification" USING "btree" ("trust_score" DESC);



CREATE INDEX "idx_sender_verification_user_id" ON "public"."sender_verification" USING "btree" ("user_id");



CREATE INDEX "idx_sent_email_document_id" ON "public"."sent_email" USING "btree" ("document_id");



CREATE INDEX "idx_sent_email_opportunity_id" ON "public"."sent_email" USING "btree" ("opportunity_id");



CREATE INDEX "idx_sent_email_provider_message_id" ON "public"."sent_email" USING "btree" ("provider_message_id");



CREATE INDEX "idx_sent_email_sent_at" ON "public"."sent_email" USING "btree" ("sent_at" DESC);



CREATE INDEX "idx_sent_email_status" ON "public"."sent_email" USING "btree" ("status");



CREATE INDEX "idx_vendor_name" ON "public"."vendor" USING "btree" ("name");



CREATE UNIQUE INDEX "invoice_invoice_number_key" ON "public"."invoice" USING "btree" ("invoice_number");



CREATE UNIQUE INDEX "product_brand_sku_unique" ON "public"."product" USING "btree" ("brand_id", "sku");



CREATE UNIQUE INDEX "product_sku_key" ON "public"."product" USING "btree" ("sku");



CREATE UNIQUE INDEX "unique_email_attachment" ON "public"."email_attachment" USING "btree" ("email_id", "provider_attachment_id");



CREATE UNIQUE INDEX "unique_email_label" ON "public"."email_labels" USING "btree" ("email_id", "provider_label_id");



CREATE UNIQUE INDEX "unique_migration_name" ON "public"."migrations" USING "btree" ("migration_name");



CREATE UNIQUE INDEX "unique_sender_per_user" ON "public"."sender_verification" USING "btree" ("user_id", "sender_email");



CREATE UNIQUE INDEX "uq_doc_line_position" ON "public"."document_line" USING "btree" ("document_id", "position");



CREATE UNIQUE INDEX "uq_document_email_message" ON "public"."document" USING "btree" ("source_message_id") WHERE (("channel" = 'EMAIL'::"public"."document_channel") AND ("source_message_id" IS NOT NULL));



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_created_by_fkey1" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."action_execution_log"
    ADD CONSTRAINT "action_execution_log_action_id_fkey" FOREIGN KEY ("action_id") REFERENCES "public"."action"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_opportunity_id_fkey1" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."action"
    ADD CONSTRAINT "action_user_id_fkey1" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."brand_margin"
    ADD CONSTRAINT "brand_margin_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "public"."brand"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."brand_margin"
    ADD CONSTRAINT "brand_margin_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "public"."contract"("document_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."brand"
    ADD CONSTRAINT "brand_vendor_id_fkey" FOREIGN KEY ("vendor_id") REFERENCES "public"."vendor"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."contact"
    ADD CONSTRAINT "contact_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."contact"
    ADD CONSTRAINT "contact_account_id_fkey1" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."contract"
    ADD CONSTRAINT "contract_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_created_by_fkey1" FOREIGN KEY ("created_by") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_line"
    ADD CONSTRAINT "document_line_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_link"
    ADD CONSTRAINT "document_link_from_document_id_fkey" FOREIGN KEY ("from_document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_link"
    ADD CONSTRAINT "document_link_to_document_id_fkey" FOREIGN KEY ("to_document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_opportunity_id_fkey1" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_parent_document_id_fkey" FOREIGN KEY ("parent_document_id") REFERENCES "public"."document"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document"
    ADD CONSTRAINT "document_parent_document_id_fkey1" FOREIGN KEY ("parent_document_id") REFERENCES "public"."document"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_status_transition"
    ADD CONSTRAINT "document_status_transition_changed_by_fkey" FOREIGN KEY ("changed_by") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_status_transition"
    ADD CONSTRAINT "document_status_transition_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "email_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "email_account_id_fkey1" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email_attachment"
    ADD CONSTRAINT "email_attachment_email_id_fkey" FOREIGN KEY ("email_id") REFERENCES "public"."email"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "email_contact_id_fkey" FOREIGN KEY ("contact_id") REFERENCES "public"."contact"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "email_contact_id_fkey1" FOREIGN KEY ("contact_id") REFERENCES "public"."contact"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email_labels"
    ADD CONSTRAINT "email_labels_email_id_fkey" FOREIGN KEY ("email_id") REFERENCES "public"."email"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "email_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profile"("id");



ALTER TABLE ONLY "public"."email"
    ADD CONSTRAINT "emails_user_id_fkey1" FOREIGN KEY ("user_id") REFERENCES "public"."profile"("id");



ALTER TABLE ONLY "public"."family"
    ADD CONSTRAINT "family_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "public"."brand"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."invoice"
    ADD CONSTRAINT "invoice_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."lead"
    ADD CONSTRAINT "lead_converted_account_id_fkey" FOREIGN KEY ("converted_account_id") REFERENCES "public"."account"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."lead"
    ADD CONSTRAINT "lead_converted_contact_id_fkey" FOREIGN KEY ("converted_contact_id") REFERENCES "public"."contact"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."lead"
    ADD CONSTRAINT "lead_converted_opportunity_id_fkey" FOREIGN KEY ("converted_opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."lead"
    ADD CONSTRAINT "lead_owner_user_id_fkey" FOREIGN KEY ("owner_user_id") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_account_id_fkey1" FOREIGN KEY ("account_id") REFERENCES "public"."account"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_owner_user_id_fkey" FOREIGN KEY ("owner_user_id") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_owner_user_id_fkey1" FOREIGN KEY ("owner_user_id") REFERENCES "auth"."users"("id") ON UPDATE CASCADE ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_owner_user_id_fkey2" FOREIGN KEY ("owner_user_id") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."opportunity"
    ADD CONSTRAINT "opportunity_owner_user_id_fkey3" FOREIGN KEY ("owner_user_id") REFERENCES "auth"."users"("id") ON UPDATE CASCADE ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."opportunity_participant"
    ADD CONSTRAINT "opportunity_participant_contact_id_fkey" FOREIGN KEY ("contact_id") REFERENCES "public"."contact"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."opportunity_participant"
    ADD CONSTRAINT "opportunity_participant_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."opportunity_state_transition"
    ADD CONSTRAINT "opportunity_state_transition_changed_by_fkey" FOREIGN KEY ("changed_by") REFERENCES "public"."profile"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."opportunity_state_transition"
    ADD CONSTRAINT "opportunity_state_transition_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "public"."brand"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."product_family"
    ADD CONSTRAINT "product_family_family_id_fkey" FOREIGN KEY ("family_id") REFERENCES "public"."family"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."product_family"
    ADD CONSTRAINT "product_family_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."profile"
    ADD CONSTRAINT "profile_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON UPDATE CASCADE ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."purchase_order"
    ADD CONSTRAINT "purchase_order_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."quote"
    ADD CONSTRAINT "quote_cgv_document_id_fkey" FOREIGN KEY ("cgv_document_id") REFERENCES "public"."document"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."quote"
    ADD CONSTRAINT "quote_checked_by_fkey" FOREIGN KEY ("checked_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."quote"
    ADD CONSTRAINT "quote_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sender_verification"
    ADD CONSTRAINT "sender_verification_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profile"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sent_email"
    ADD CONSTRAINT "sent_email_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."document"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sent_email"
    ADD CONSTRAINT "sent_email_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "public"."opportunity"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."sent_email"
    ADD CONSTRAINT "sent_email_sent_by_user_id_fkey" FOREIGN KEY ("sent_by_user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."profile"
    ADD CONSTRAINT "user_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON UPDATE CASCADE ON DELETE RESTRICT;



CREATE POLICY "Users can delete own emails" ON "public"."email" FOR DELETE USING (("user_id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Users can insert own emails" ON "public"."email" FOR INSERT WITH CHECK (("user_id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Users can update own emails" ON "public"."email" FOR UPDATE USING (("user_id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Users can view own emails" ON "public"."email" FOR SELECT USING (("user_id" = ( SELECT "auth"."uid"() AS "uid")));



ALTER TABLE "public"."email" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";






ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."email";






GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";











































































































































































GRANT ALL ON FUNCTION "public"."enforce_document_type_for_specialization"() TO "postgres";
GRANT ALL ON FUNCTION "public"."enforce_document_type_for_specialization"() TO "anon";
GRANT ALL ON FUNCTION "public"."enforce_document_type_for_specialization"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."enforce_document_type_for_specialization"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_sent_email_updated_at"() TO "postgres";
GRANT ALL ON FUNCTION "public"."update_sent_email_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_sent_email_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_sent_email_updated_at"() TO "service_role";


















GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."account" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."account" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."account" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."account" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action_execution_log" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action_execution_log" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action_execution_log" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."action_execution_log" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand_margin" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand_margin" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand_margin" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."brand_margin" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contact" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contact" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contact" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contact" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contract" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contract" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contract" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."contract" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_line" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_line" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_line" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_line" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_link" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_link" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_link" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_link" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_status_transition" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_status_transition" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_status_transition" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."document_status_transition" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_attachment" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_attachment" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_attachment" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_attachment" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_labels" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_labels" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_labels" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."email_labels" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."family" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."family" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."family" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."family" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."invoice" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."invoice" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."invoice" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."invoice" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."lead" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."lead" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."lead" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."lead" TO "service_role";



GRANT ALL ON SEQUENCE "public"."migrations_id_seq" TO "postgres";
GRANT ALL ON SEQUENCE "public"."migrations_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."migrations_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."migrations_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."migrations" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."migrations" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."migrations" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."migrations" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_participant" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_participant" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_participant" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_participant" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_state_transition" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_state_transition" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_state_transition" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."opportunity_state_transition" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product_family" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product_family" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product_family" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."product_family" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profile" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profile" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profile" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profile" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."purchase_order" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."purchase_order" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."purchase_order" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."purchase_order" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."quote" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."quote" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."quote" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."quote" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sender_verification" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sender_verification" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sender_verification" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sender_verification" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sent_email" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sent_email" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sent_email" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."sent_email" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."vendor" TO "postgres";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."vendor" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."vendor" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."vendor" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "service_role";































