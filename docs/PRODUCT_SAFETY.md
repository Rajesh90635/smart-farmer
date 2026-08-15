# Product Safety

## The absolute rule, restated and mapped to actual code

**The application must NOT independently prescribe pesticides,
fertilizers, medicines, or chemicals.** This is not a UI-copy guideline -
it's a structural fact about this codebase:

| Could this component prescribe a chemical? | Why not |
|---|---|
| AI disease detection (Prompt 6) | `ResultStatus`/`predicted_class` only ever name a disease class or "healthy" - there is no field, template, or code path anywhere in `app/services/ai*` that outputs a chemical name, product, or dosage. `farmer_messages.py`'s AI-result templates are 100% dosage-free text. |
| Expert case review (Prompt 8) | `CaseReview` has `outcome` (a controlled vocabulary: confirmed/different_diagnosis/etc.) and free-text `notes` - no dosage/product field exists on the model at all. |
| Product catalog (this phase) | `Product.usage_information` is explicitly documented as generic-only ("for foliar application," never "apply 2ml/L") - enforced by admin-review convention, since it's admin-entered content, not farmer- or AI-generated. |
| Order/checkout | Has no relationship to disease/diagnosis data at all - a farmer can order any approved product regardless of any case or AI result; nothing "recommends" a specific product based on a diagnosis this phase (see docs/EXPERT_VERIFICATION.md's "Expert -> Product workflow" section below). |

## Expert -> Product workflow: prepared, not fully connected

Requirement 10/11's full vision (AI disease candidate -> expert
verification -> approved agricultural guidance -> eligible product
category -> farmer sees products) is **NOT implemented this phase**. What
exists:
- `CropHealthCase`/`CaseReview` (Prompt 8) - expert verification, fully
  separate from AI.
- `Product`/`DealerProduct` (this phase) - the catalog, fully separate
  from cases.

**There is no code path connecting a `CaseReview` outcome to a filtered
product list.** A farmer viewing `GET /products` sees ALL approved
products, not products scoped to their specific case/diagnosis. This is
a disclosed, deliberate scope limit: building "product eligibility
inference from a diagnosis" is exactly the kind of automatic
AI-to-commerce connection Requirement 10 warns against building without
explicit authorization, and no such authorization workflow (e.g. an
expert explicitly tagging which product categories are appropriate for a
given case) was built this phase either. **This is real, disclosed
follow-up work, not a hidden shortcut.**

## Regulatory assumptions - see PROMPT9_ASSUMPTIONS_RISKS.md

This document states what the code does; PROMPT9_ASSUMPTIONS_RISKS.md
covers what is ASSUMED about regulatory requirements this codebase does
not and cannot verify (licensing, registration, regional pesticide law).

## Expired/recalled products

`DealerProduct.is_expired()` and `Product.status in
(SUSPENDED, RECALLED)` are checked at checkout time
(`order_service.checkout`) - an expired or recalled product cannot be
newly ordered. **Not yet built:** proactively flagging or notifying
farmers about ALREADY-PLACED orders for a product that gets recalled
after purchase (Requirement 7's "flag affected orders if required") -
disclosed gap.
