# Kickoff: Claims email triage POC

Fabrikam Insurance · September 14, 2026

## Attendees

* Fabrikam: Dana Whitfield (Head of Claims Operations, sponsor), Raj Patel (Enterprise Architect), Maria Santos (Claims Intake Team Lead)
* Contoso: me (engagement lead), Wei Chen (ML engineer)

## Why we're here

* The claims inbox gets about 300 emails a day. Maria's intake team of 4 reads each one, works out the claim type, finds the policy number and the claimed amount, types them in, and forwards the email to the right team: Motor, Property, Travel, or Liability.
* Fabrikam's own time study in March: 6 min 10 s per email on average. That's about 30 hours of intake work a day.
* Dana: intake is the bottleneck. In storm weeks the backlog reaches 2 days and customers call to ask if their claim arrived. She wants to know if AI can do the first read.

## Success criteria

Agreed with Dana and Raj:

1. Routing: right team for at least 90% of emails.
2. Policy number read correctly for at least 95% of emails.
3. Claimed amount read correctly for at least 95% of the emails that state one.
4. Handling time under 1 minute per email, with a handler checking every suggestion.
5. No customer data leaves Fabrikam's Azure tenant.

Raj: number 5 is a hard requirement. He'll review the setup before we load any emails.

## Scope

* 4 weeks: September 14 to October 9. Readout on October 22 with Dana, Raj, and Maria.
* 600 past emails from January to June 2026, anonymized by Fabrikam IT. Maria's team labels the right team and fields for each.
* Out of scope: live email, connecting to ClaimsHub (their claims system), and any decision on the claim itself.

## Other notes

* Maria worries handlers will stop trusting it if it's confidently wrong. She wants them to see why it suggested a team.
* About 1 in 10 emails is in Spanish.
* Dana wants a rough cost for going live at the readout, including what it costs to run.
