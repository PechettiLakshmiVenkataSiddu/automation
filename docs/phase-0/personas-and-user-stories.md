# User Personas and User Stories

## Personas

### Priya — Operations professional

Priya coordinates meetings, email follow-ups, recurring reports, and cross-team tasks. She needs low-code automation with approval controls, clear failures, and calendar/email integration.

### Mateo — Independent developer

Mateo uses repositories, terminals, browser tools, and AI coding assistants. He needs safe tool execution, project-aware chat, reusable prompts, and traceable developer automations.

### Chen — Founder and workspace administrator

Chen configures users, connected accounts, budgets, policies, and audit access. He needs RBAC, organization boundaries, billing visibility, and a reliable activity record.

### Amina — Knowledge worker

Amina works from documents, conversations, and meeting notes. She needs a private knowledge base, accurate retrieval with sources, task capture, and a simple voice-first option.

## Core user stories

| ID    | Story                                                                                                                                  | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| US-01 | As Priya, I can sign in with a supported identity provider so that I do not manage another password.                                   | Must     |
| US-02 | As a user, I can chat with a selected AI model and see the conversation history.                                                       | Must     |
| US-03 | As a user, I can connect and revoke an external account with explicit scopes.                                                          | Must     |
| US-04 | As a user, I can create a workflow from a trigger and steps, validate it, and save a version.                                          | Must     |
| US-05 | As a user, I can approve, reject, or edit an action before the system sends, changes, or deletes external data.                        | Must     |
| US-06 | As Priya, I can schedule recurring work and receive a clear result or failure notification.                                            | Must     |
| US-07 | As Amina, I can ingest supported files into a knowledge base and receive answers with citations to retrieved sources.                  | Should   |
| US-08 | As a user, I can view, correct, export, and delete long-term memories associated with me.                                              | Should   |
| US-09 | As Mateo, I can authorize a developer tool to operate within a constrained repository or sandbox and inspect all commands and outputs. | Should   |
| US-10 | As Chen, I can assign roles and review immutable audit events for privileged or external actions.                                      | Must     |
| US-11 | As Chen, I can define organizational policies that require approval for selected tool categories.                                      | Should   |
| US-12 | As a user, I can see run status, inputs, outputs, retries, and error guidance for every workflow execution.                            | Must     |

## Jobs to be done

- When routine information arrives, help me classify it, extract the important parts, and propose the next action.
- When I delegate work to an agent, let me understand and control what it will access and do.
- When an automation fails, show me exactly where, why, and how to safely recover.
- When I ask a question about my work, use only the knowledge I have authorized and cite its origin.
