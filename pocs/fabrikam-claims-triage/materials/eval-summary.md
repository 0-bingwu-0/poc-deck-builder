# Evaluation summary: claims triage POC

Wei Chen · October 9, 2026

Test set: 600 anonymized emails from January to June 2026, labeled by Maria's team. 540 in English, 60 in Spanish.

## Routing

| Claim type | Emails | Right team | Accuracy |
| --- | --- | --- | --- |
| Motor | 260 | 247 | 95.0% |
| Property | 180 | 165 | 91.7% |
| Travel | 90 | 82 | 91.1% |
| Liability and other | 70 | 61 | 87.1% |
| **Total** | **600** | **555** | **92.5%** |

By language: English 510 of 540 (94.4%), Spanish 45 of 60 (75.0%).

Most Liability misses were emails that mention a car but are about an injury, which it sent to Motor.

## Fields

* Policy number: 587 of 600 correct (97.8%).
* Claimed amount: 340 emails state one. 300 of 340 correct (88.2%).
  * 29 of the 40 misses are in scanned or handwritten claim forms. The model reads those badly without OCR.
  * The other 11 have more than one amount (an estimate and a final bill) or a range.

## Handling time

Time study October 5–7: 3 handlers, 50 emails each, 150 in total, using the review screen.

* 41 s per email on average (median 33 s). Fabrikam's March baseline: 6 min 10 s.
* Handlers changed the suggested team on 11 of the 150.
* Maria's team liked the "Why" line. Two handlers said it's what made them trust the suggestions.

## Setup

* Azure OpenAI in Fabrikam's own Azure tenant, East US 2. Emails and attachments stay in Fabrikam's Blob Storage.
* Raj reviewed the setup on September 30 and signed off before any emails were loaded.
* Cost: $0.012 per email in Azure OpenAI usage, on average.
