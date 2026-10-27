# Brief: Fabrikam claims email triage POC

## Audience

* **Dana Whitfield, Head of Claims Operations (sponsor):** decides whether to fund the pilot. Cares about the intake backlog, time saved, and cost.
* **Raj Patel, Enterprise Architect:** can block it. Data must stay in Fabrikam's Azure tenant. Owns mailbox access and Azure.
* **Maria Santos, Claims Intake Team Lead:** her team would use it. Worried handlers stop trusting it if it's confidently wrong.

## The problem

* About 300 claim emails a day. A 4-person intake team reads each one, finds the claim type, policy number, and claimed amount, types them in, and forwards it.
* 6 min 10 s per email on average (Fabrikam's March time study). About 30 hours of intake work a day.
* In storm weeks the backlog reaches 2 days, and customers call to ask if their claim arrived.

## What we set out to prove

| Criterion | Target |
| --- | --- |
| Routed to the right team | ≥ 90% of emails |
| Policy number read correctly | ≥ 95% of emails |
| Claimed amount read correctly | ≥ 95% of emails that state one |
| Handling time, with a handler checking | < 1 min per email |
| Customer data stays in Fabrikam's Azure tenant | Required |

## What we did

* 4 weeks, September 14 to October 9, 2026.
* 600 past emails from January to June 2026, anonymized by Fabrikam IT and labeled by Maria's team. 540 in English, 60 in Spanish.
* The AI reads each email and its attachments, suggests a team, policy number, and claimed amount, and says why. A handler accepts or changes it on a review screen.
* Azure OpenAI in Fabrikam's own tenant (East US 2). Raj signed off on the setup on September 30, before any emails were loaded.
* Out of scope: live email, connecting to ClaimsHub, and claim decisions.

## Results

| Criterion | Target | Result | Status |
| --- | --- | --- | --- |
| Routing | ≥ 90% | 92.5% (555 of 600) | Met |
| Policy number | ≥ 95% | 97.8% (587 of 600) | Met |
| Claimed amount | ≥ 95% | 88.2% (300 of 340) | Not met |
| Handling time | < 1 min | 41 s average, from 6 min 10 s | Met |
| Data stays in tenant | Required | Signed off by Raj, September 30 | Met |

* Routing by claim type: Motor 95.0% (247 of 260), Property 91.7% (165 of 180), Travel 91.1% (82 of 90), Liability and other 87.1% (61 of 70).
* Routing by language: English 94.4% (510 of 540), Spanish 75.0% (45 of 60).
* Time study: 3 handlers, 50 emails each, October 5–7. Median 33 s. Handlers changed the suggested team on 11 of 150.
* Two handlers said the "Why" line is what made them trust the suggestions.
* Azure OpenAI usage: $0.012 per email on average.

## What didn't work

* **Claimed amount, 88.2% against 95%:** 29 of the 40 misses are scanned or handwritten claim forms, which the model reads badly without OCR. The other 11 have more than one amount or a range.
* **Spanish emails, 75.0% routed right:** against 94.4% for English. Only 60 in the test set.
* **Liability, 87.1%:** most misses are injury emails that mention a car, sent to Motor.

## Path to production

* **Phase 1, pilot, 8 weeks:** Motor inbox only (about 43% of emails), handlers check every suggestion. Add OCR for scanned forms and 200 labeled Spanish emails, then retest. Done when all five criteria hold on live email for 4 weeks in a row. Contoso: $85,000 fixed fee.
* **Phase 2, rollout, 10–12 weeks:** all claim types, confirmed fields go straight into ClaimsHub, and an accuracy dashboard. Estimate $140,000–180,000, firmed up after the pilot.
* **Fabrikam provides:** IT about 2 days a week from Raj's team; 2 handlers, about 3 hours a week each.
* **Running cost:** about $900 a year in Azure OpenAI usage at today's volume (300 emails × 250 working days × $0.012). OCR adds about $0.01 per scanned page; yearly cost known after the pilot.

## Recommendation and ask

* Recommend the 8-week pilot on the Motor inbox, with the OCR and Spanish fixes.
* Decision: Dana approves the pilot ($85,000) by November 13, to start December 1 with the same team.
* Raj: mailbox access through Microsoft Graph. Maria: name 2 handlers for the pilot.

## Still missing

* Who signs off on the budget besides Dana, if anyone.
* Dates for Raj's and Maria's steps. For now the deck says before the December 1 start.
