# Next phase estimate (draft)

October 14, 2026

## Phase 1: Pilot, 8 weeks

* Live on the Motor inbox only, about 43% of claim emails.
* Handlers check every suggestion before it's forwarded, same as in the POC.
* Add OCR (Azure AI Document Intelligence) for scanned forms, then retest claimed amounts.
* Add 200 labeled Spanish emails, then retest routing for Spanish.
* Read from the shared mailbox through Microsoft Graph. Suggestions show in the review screen.
* Done when all five POC criteria hold on live email for 4 weeks in a row.
* Contoso: $85,000 fixed fee.
* Fabrikam: IT about 2 days a week from Raj's team (mailbox access, Azure). 2 handlers, about 3 hours a week each, for feedback.

## Phase 2: Rollout, 10–12 weeks

* All claim types.
* Send the confirmed fields straight into ClaimsHub, so nobody types them in.
* Dashboard for accuracy and volume.
* Estimate $140,000–180,000. We firm it up after the pilot.

## Running cost

* About $900 a year in Azure OpenAI usage at today's volume: 300 emails × 250 working days × $0.012.
* OCR adds about $0.01 per scanned page. We'll know the yearly cost after the pilot.

## Timing

* Start December 1 with the same team. Wei moves to another project on December 15 if we haven't started.
* That needs a decision by November 13.
