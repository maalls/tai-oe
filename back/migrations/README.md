# Database Migrations

This folder contains SQL migration files for the database schema.

## Naming Convention

Migration files should be named with a numeric prefix followed by a descriptive name:

- `001_add_last_email_id.sql`
- `002_create_new_table.sql`
- etc.

## Running Migrations

Execute the SQL files in order in your Supabase SQL Editor or using a database client.

## Current Migrations

- `001_add_last_email_id.sql` - Adds `last_email_id` column to `email_fetch_metadata` table for tracking the last fetched email
