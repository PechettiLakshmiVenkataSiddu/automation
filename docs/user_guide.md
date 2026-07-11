# Aether Platform User and Administrator Guide

Welcome to the Aether Personal AI Automation Platform. This guide explains how to manage memories, construct visual automation workflows, approve drafts, and use administrative control centers.

---

## 1. User Guide

### 1.1 Long-Term Memory Controls
Aether logs persistent user memories to optimize AI personalization. You have full control over what Aether remembers:
* **Opt-In/Consent**: Toggle memory storage on or off in the memory settings panel.
* **View & Edit**: Check all stored facts. Correct inaccurate assumptions directly in the memory grid.
* **Delete & Forget**: Click the delete icon next to any memory item to permanently purge it.

### 1.2 Visual Workflow Builder
Construct automation graphs easily:
1. Navigate to `/workflows/builder` to open the graph workspace.
2. Drag and drop **Trigger Nodes** (e.g. Schedule cron, incoming email, webhooks) and connect them to **Action Nodes** (e.g. LLM model call, execute terminal script).
3. Connect edge sockets. The builder automatically blocks cycle loops and checks inputs/outputs formats.
4. Click **Publish** to run the workflow.

### 1.3 Communication Approvals & Proposals
To prevent prompt injection risks, high-privilege operations are queued pending explicit human approvals:
* **Email Outbox**: Outgoing Gmail messages are saved as drafts. Approve them at `/email` before they are sent.
* **Calendar Invites**: Scheduling proposals with conflicts are placed in the outbox queue at `/calendar` for verification.
* **Chat Integration**: Slack/Teams posts are held in the outbox at `/chat-integration` for confirmation.

---

## 2. Administrator Guide

### 2.1 System Policies & Data Retention
Authorized administrators (roles of `admin` or `owner`) can configure organization-wide variables:
* **Retention Sliders**: Configure notifications log delete periods and system audit trail durations.
* **Break-Glass Override**: In critical system outages, toggle the **Break-Glass Override** switch. This disables active policy checks, allowing manual commands to run immediately. *Requires entering a written justification that is stored permanently in the system audit logs.*

### 2.2 Members Control Room
* **User Invites**: Enter email addresses and select initial roles (`viewer`, `member`, `admin`) to add users to the workspace.
* **Role Modifications**: Upgrade or downgrade user roles to modify access levels.
* **Connection Disconnects**: Disconnect external OAuth integration scopes for specific users to secure access.

### 2.3 System Usage Analytics
Navigate to `/analytics` to review:
* Total computing costs and recorded events counts.
* Allocations split by LLM model tokens or subprocess execution time.
* Workflow execution success rates.
* CSV usage report downloads for offline audits.
