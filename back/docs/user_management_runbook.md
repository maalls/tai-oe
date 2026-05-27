# User Management Runbook

## Scope

This runbook covers safe operations for user role management:

- bootstrap first admin user
- recover admin access
- rollback strategy for role-policy rollout

## Preconditions

- Backend environment is configured (same settings used by backend runtime).
- Target user already exists in `profile` table.
- Operator has terminal access to backend repository.

## Bootstrap First Admin

When no admin exists yet, promote one existing profile to `admin`.

Command:

```bash
cd back
venv/bin/python script/bootstrap_admin.py --email user@example.com
```

Expected behavior:

- If no admin exists: target user is promoted to `admin`.
- If target user does not exist: command exits with error and no change.
- If target user is already admin: command exits successfully with no change.

## Controlled Role Overwrite

If at least one admin already exists, the bootstrap command refuses overwrite by default.

Command with explicit override:

```bash
cd back
venv/bin/python script/bootstrap_admin.py --email user@example.com --force
```

Safety guardrail:

- Without `--force`, role overwrite is blocked when admins already exist.

## Recovery Procedure

Use this when admin access is lost or blocked.

1. Verify candidate user exists in `profile` with expected email.
2. Run bootstrap command for that user.
3. If admins already exist but recovery requires reassignment, re-run with `--force`.
4. Validate by calling an admin endpoint (for example `GET /api/admin/users`) with the recovered account token.

## Rollback Strategy

If role-policy rollout causes production issues:

1. Keep authentication active, but temporarily relax route-policy mapping in backend RBAC policy.
2. Re-run targeted RBAC test suite before redeploy.
3. If needed, revert the RBAC policy commit only (do not drop role column).
4. Keep migration `045_add_profile_role.sql` in place; rollback should target authorization policy, not data schema.

## Verification Checklist

- Bootstrap command returns success for intended user.
- Recovered admin can access admin endpoints.
- Non-admin users still receive `403` on admin endpoints.
- Invalid token still returns `401`.
