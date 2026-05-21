-- Table Definition
CREATE TABLE "public"."oauth_tokens" (
    "user_id" uuid NOT NULL,
    "provider" text NOT NULL,
    "service" text NOT NULL,
    "token_json" text NOT NULL,
    "scope" text,
    "expires_at" timestamptz,
    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY ("user_id", "provider", "service"),
    CONSTRAINT "oauth_tokens_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "public"."profile"("id") ON DELETE CASCADE
);
