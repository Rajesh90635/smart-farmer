# AI Privacy

## What the assistant sees

Only the authenticated farmer's own data, resolved server-side from their
session - never data parsed from their message, never another farmer's
data (see docs/AI_TOOL_SYSTEM.md). Specifically, per intent: crop cycle
status, AI disease-analysis results, farm weather, harvest records,
buyer offers on the farmer's own listings, sale records, order/delivery
records, and expert case status/reviews.

## What the assistant stores

- **Every message** (farmer's own text and the assistant's response),
  in `AssistantMessage`, linked to an `AssistantConversation` scoped to
  one farmer.
- **Intent, tools called, sources, and confidence** for every assistant
  response - this IS the audit trail (Requirement 81), not a separate
  system.
- **Feedback** (`AssistantFeedback`) if the farmer submits it.
- **Preferences** (`AssistantPreference`) - response mode, voice/summary
  opt-ins.

## What the assistant does NOT store

- Voice audio - voice is handled entirely client-side (device STT
  converts speech to text before it ever reaches this backend; device
  TTS converts the response to speech after leaving this backend). No
  audio ever reaches or is stored by this backend.
- Photos beyond what Prompt 5's existing crop-photo storage already
  retains - the assistant's disease-status tool reads `AIAnalysis` rows,
  never touches photo bytes directly.
- Payment instrument details - no tool ever returns or stores card/UPI
  data (there is none anywhere in this codebase to begin with).

## Conversation retention

No automatic expiry job exists this phase - conversations persist
indefinitely until the farmer deletes them (see below) or an admin
process is built later. Disclosed limitation.

## Deletion process (Requirement 90)

`DELETE /assistant/history/{conversation_id}` sets `is_archived=true` -
the farmer-visible effect is that the conversation no longer appears as
their active conversation and its content is no longer surfaced. **This
is a soft archive, not a hard delete** this phase - the underlying rows
remain in the database. A future hard-delete endpoint (matching the
"mandatory transaction/audit records are never deleted" carve-out
already established for order/case audit logs elsewhere in this project)
would need to decide whether `AssistantMessage` rows count as "mandatory"
- they likely do not (unlike financial/audit records), so a real
hard-delete is reasonable future work, not built yet.

## Photo/expert/order/location data surfaced through the assistant

All governed by the SAME privacy rules already established in their
originating phases (Prompt 5's photo privacy, Prompt 8's location
privacy, Prompt 9/10's order/payment privacy) - the assistant does not
loosen or bypass any of them; it only reads already-authorized data
through the farmer's own existing access rights.
