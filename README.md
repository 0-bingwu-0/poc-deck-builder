# POC Deck Builder

A POC ends with a readout: a deck that tells the client what you set out to prove, what you found, and what it takes to go live. By then the work is done. But turning weeks of notes, test results, and screenshots into a deck that leads with the answer, shows every success criterion against its target, and ends with a clear ask still takes a day or two. It's also the part juniors find hardest, and seniors spend hours fixing.

This project has AI do it with you. It sorts your POC materials into a brief, proposes a storyline you can check in a minute, then writes the slides, with speaker notes. You get a PDF, and an editable PowerPoint when you need one.

## Getting started

Open this project in StashBase and tell the Agent:

1. **"Set me up."** It asks you a few questions, one at a time: what you do, who's usually in the room for a readout, your firm's rules for client decks, and your brand color and font. Have a past deck you liked? Drop it into `references/` and it picks up the structure.
2. **"Make a deck for the Acme invoice POC."** Drop the materials into `pocs/<client>-<poc>/materials/` first, or paste them in Chat: kickoff notes, success criteria, test results, cost estimates, screenshots. It writes `brief.md` with the facts, asks you if the success criteria, the results, or the ask are missing, and gives you the storyline: one headline per slide.
3. **"OK."** Or change the storyline. It writes the slides in `deck.html`, reviews them the way the client will, and builds `deck.pdf`. Ask for any edits you want, like "Merge slides 6 and 7." Need to edit it yourself, or send it to someone who will? Say **"Export to PowerPoint."**
4. **"Prep me for the meeting."** It lists the questions each person in the room will likely ask, with answers from your results, and flags the ones you can't answer yet.

Have a deck already, yours or a junior's? Say **"Review this deck"** and attach it. It reads it the way the client will and tells you the changes that matter most, with the reasons, so you can pass them on.

The template comes with an example: an AI triage POC for an insurer's claims inbox, with its materials, brief, and finished deck in `pocs/fabrikam-claims-triage/`. Open `deck.pdf` there to see what you get, or say "Review the Fabrikam deck" to try a review. Setup replaces the example with yours.

## Make it yours

Setup covers most of it. You can also change things anytime:

* **Your role, who's in the room, and your firm's deck rules** are in `context/profile.md`. Add a rule anytime, like "every deck has a security slide", or just tell the Agent.
* **The look** comes from Deck settings in `context/profile.md`: brand color, font, footer, and logo. The layouts are in `templates/deck.css`.
* **The default storyline and how slides are written** are in `workflows/deck.md`.
* **What a review checks** is in `workflows/review.md`.
* **The Agent's persona and rules** are in `AGENTS.md`.

## PDF and PowerPoint

The Agent writes each deck as HTML with the layouts in `templates/deck.css`, and builds it with `scripts/build.py`. You need Python 3, Chrome, Edge, or Chromium, and an Agent that can run local commands. The script uses only the Python standard library, so there's nothing to install.

Every build prints a PDF and checks each slide for text that runs off the edge, so the Agent cuts words instead of shrinking text. The PDF looks the same on every computer, so it's the one to send when the client only needs to read it.

Say "Export to PowerPoint" and it also writes a `.pptx`: every headline, bullet, box, and table where it is in the PDF, all editable, with the speaker notes. Diagrams and charts go in as pictures. It opens in PowerPoint, Keynote, and Google Slides, but it's not identical to the PDF: PowerPoint sets text itself, so a line can break in a different place, and a font the other computer doesn't have gets swapped out. It uses its own layouts with your brand color, font, and logo, not your firm's PowerPoint template.

You can run it yourself: `python3 scripts/build.py pocs/fabrikam-claims-triage/deck.html`, with `--pptx` for PowerPoint.

## Files

* `AGENTS.md`: the Agent's persona, the rules for facts, and the task index.
* `CLAUDE.md`: points Claude Code to `AGENTS.md`.
* `context/profile.md`: your role, who's in the room, your firm's deck rules, and deck settings.
* `references/`: past decks and your logo. The Agent reads them but never changes them.
* `workflows/setup.md`: the setup Q&A.
* `workflows/deck.md`: the brief, the storyline, how slides are written, and the deck format.
* `workflows/review.md`: the review checklist, and reviewing someone else's deck.
* `workflows/prep.md`: the questions to prepare for before the meeting.
* `workflows/export.md`: building the PDF and the PowerPoint, and fixing what doesn't fit.
* `templates/deck.css`: the slide layouts the Agent builds with.
* `scripts/build.py`: turns `deck.html` into a PDF, and a PowerPoint when asked, and checks that everything fits.
* `scripts/read_deck.py`: pulls the text and speaker notes out of a PowerPoint file.
* `pocs/`: one folder per POC, with `materials/`, `brief.md`, `deck.html`, `deck.pdf`, `deck.pptx`, and `prep.md`.
