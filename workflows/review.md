# Review a Deck

Read a deck the way the client will, and catch what would lose them. Run the [checklist](#checklist) on every deck you write, before building it. Use the rest when I give you a deck to review, mine or someone else's.

## Someone else's deck

When I give you a deck, as PowerPoint, PDF, or HTML:

1. Get the text. For PowerPoint, run `python3 scripts/read_deck.py <file>`. If it belongs to a POC in `pocs/`, read its brief and materials too, so you can check the numbers.
2. Go through the [checklist](#checklist).
3. Tell me in Chat, the storyline first, since that's what matters most. Does it answer the client's question, in the right order? Then the slides. For each problem, name the slide, say what's wrong in a sentence, and show the fix: a rewritten headline, a cut, or a move. Stick to the five or so changes that matter most, and offer the rest.
4. If I say "Fix it", write it as `deck.html` in the POC's folder, following [deck.md](deck.md#slides), and build it.

If it's a junior's deck, write the feedback so I can pass it on: for each change, say why it matters to the client, not just what to change. That's how they learn to catch it themselves next time.

## Checklist

First, read only the headlines, about ten seconds, the way a sponsor flips through. Then go slide by slide.

* **The answer first:** The executive summary says whether it worked, with numbers, and what we recommend. Someone who sees only that slide knows the outcome.
* **Headlines:** Each one is a full-sentence takeaway, and the headlines alone tell the story. "Results" or "Architecture" as a headline fails.
* **Every criterion:** Each success criterion agreed at the start shows up in the results, against its target. None quietly dropped or reworded to pass.
* **Honest:** Missed targets are said plainly, with the cause and the fix. No "promising early results" covering a miss.
* **One message:** Everything on a slide backs up its headline.
* **Numbers:** Each one matches the brief or materials exactly, with its unit and what it's compared to. The same number looks the same on every slide. Slides with results have a Source line.
* **Their words:** No jargon the sponsor wouldn't use. The client's names for their teams, systems, and metrics.
* **The ask:** The last slide before the appendix names the decision, who makes it, and by when. Cost and what the client must provide are in the deck, not left for a follow-up email.
* **Room to breathe:** No slide over six bullets or about 60 words, tables aside. Detail goes in the notes or the appendix.
* **Everyone in the room:** Each person in the brief's audience finds what they came for: the sponsor the outcome and cost, IT where the data went, the team lead what changes for their people.
* **House style:** The rules in my [profile](../context/profile.md) are followed.
