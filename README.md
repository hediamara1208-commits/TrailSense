# CodeJam 16: Brim AP Automation

Our team's project for the **Brim Fintech track** at McGill CodeJam 16 (Nov 20–22, 2026).

We're building accounts payable (AP) automation for a business card platform. It takes a supplier invoice from the inbox to payment, routes it to the right approvers, and keeps a full audit trail. The customer is **Harborline Logistics Inc.**, a fictional 40-person Canadian logistics company with about 50 suppliers and about 50 invoices a month (CAD/USD, GST/HST/PST/QST, EFT payments, CRA-ready records).

The full challenge brief is in [`docs/BRIEF.md`](docs/BRIEF.md).

## Status

- [ ] Stack chosen
- [ ] Synthetic dataset received (Brim hasn't released it yet; it goes in `data/`)
- [ ] Data model
- [ ] Required features (see below)
- [ ] Bonus features
- [ ] Demo + 2–4 min pitch

## Required features (40% of score, tested on a hidden invoice batch)

| # | Feature | Owner | Status |
|---|---------|-------|--------|
| 1 | Invoice intake (uploads + AP inbox; ignore/route non-invoices) | | |
| 2 | Data extraction (PDF + scans, EN/FR, line items, currency, taxes → tax codes) | | |
| 3 | Smart coding (GL account + department per line, learned from history, explained) | | |
| 4 | Validation & matching (vendor master, contract, PO, tax vs province, arithmetic) | | |
| 5 | Duplicate detection (exact, near, reformatted, already paid by card) | | |
| 6 | Approval workflow (rules by amount/dept/vendor, admin-editable, delegation) | | |
| 7 | Payments (simulated EFT, release limits by role, dashboard, statuses) | | |
| 8 | Audit trail (every action, who/when, payment → invoice → approvals → codes) | | |
| 9 | Vendor management (master, onboarding, holds, controlled bank-detail changes) | | |

### Roles (enforced on the server, not just hidden in the UI)
Employee (requester) · AP Clerk · Approver (dept manager) · Finance Manager (releases up to $100k CAD) · Controller/Admin · Auditor (read-only + export)

Rules for every role:
- Nobody approves their own request. It escalates to their manager.
- Whoever approves an invoice can't release its payment.
- Actions taken by a delegate are recorded as delegated.

## Judging

| Criterion | Weight |
|---|---|
| Required features (end to end, accuracy) | 40% |
| Technical depth (live Q&A: every member must defend the design) | 25% |
| Clean, intuitive UI per role | 20% |
| Bonus features (depth over count) | 15% |

## CodeJam rules that affect us
- **Submission is through GitHub.** This repo is private for now. It needs to be public or shared with the judges before the deadline.
- **No code written before Fri Nov 20, 7:00 PM.**
- **No edits after Sun Nov 22, 12:00 PM.**
- Pitch is 2–4 minutes, then judge Q&A. Our judging location will be posted on the codejam.mcgilleus.ca portal.

## Repo layout
```
docs/   challenge brief, design notes
data/   synthetic Harborline dataset (once Brim releases it)
```
