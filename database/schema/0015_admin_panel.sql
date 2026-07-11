-- Phase 22: Admin Panel. Apply after 0014_notifications.sql.

CREATE TABLE system_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
    retention_days_notifications integer NOT NULL DEFAULT 30,
    retention_days_audit_logs integer NOT NULL DEFAULT 365,
    allow_unsecure_sandboxes boolean NOT NULL DEFAULT false,
    break_glass_active boolean NOT NULL DEFAULT false,
    break_glass_reason text,
    break_glass_activated_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);
