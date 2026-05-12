-- Table Definition
CREATE TABLE "public"."profile" (
    "id" uuid NOT NULL,
    "email" text,
    "full_name" text,
    "created_at" timestamptz NOT NULL DEFAULT now(),
    "google_token_pickle" text,
    "imap_host" text,
    "imap_port" integer,
    "imap_username" text,
    "imap_password" text,
    "imap_mailbox" text,
    "imap_use_ssl" boolean NOT NULL DEFAULT true,
    "imap_enabled" boolean NOT NULL DEFAULT false,
    PRIMARY KEY ("id")
);