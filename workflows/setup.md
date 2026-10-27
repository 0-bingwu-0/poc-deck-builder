# Set Me Up

Make this project mine through a short Q&A. Ask these one at a time, and wait for each answer before asking the next. Keep each question to a sentence or two, with a quick example if it helps.

1. **What do you do?** Your role, your firm, and the kind of POCs you run.
2. **Who's usually in the room for a readout?** Their roles, and what each of them decides or cares about.
3. **Does your firm have rules for client decks?** Like a slide every deck must have, how costs are shown, or words to avoid. A past deck you liked works even better: drop it into `references/`, as PowerPoint or PDF.
4. **What should your decks look like?** Your brand color as a hex code, your font, the footer text, and a logo as PNG or JPG if you want one on every slide. "Use the defaults" is fine.
5. **What language do you write decks in?**

If my setup message already answers some of these, skip them.

If I gave you a past deck, read it (for PowerPoint, `python3 scripts/read_deck.py references/<file>`). Note how it's built: the order of slides, how headlines are written, and how results and costs are shown. Save what should carry over to House style in my profile. If it follows a different storyline from the one in [deck.md](deck.md#3-propose-the-storyline), write that storyline into House style too.

Then, in one go:

* Rewrite [profile.md](../context/profile.md) from my answers, in my words, under its headings. Drop the example content. Keep it short and specific. If I gave a logo, save it in `references/` and put its path in Deck settings.
* If my font isn't a common one like Arial, Calibri, or Helvetica, tell me in a sentence: the PDF is fine, but a PowerPoint opened on a computer without the font will swap in another.
* Delete the example POC, `pocs/fabrikam-claims-triage/`.
* Tell me it's done in a sentence or two. Then ask which POC to start with, and tell me to drop its materials into `pocs/<client>-<poc>/materials/` or paste them in Chat.
