# Make the Deck

A POC deck answers the question the client asked when they agreed to the POC: does this work well enough to do for real? Everything for one POC goes in `pocs/<client>-<poc>/`:

* `materials/`: what I give you, as is.
* `brief.md`: the facts the deck stands on.
* `deck.html`: the slides. [build.py](../scripts/build.py) turns it into `deck.pdf`, and into `deck.pptx` when I need PowerPoint.

## 1. Gather the materials

For a new POC, make its folder. I drop files into `materials/` or paste text in Chat. Save pasted text as a file in `materials/`, like `materials/kickoff-notes.md`. Typical material: the proposal, kickoff notes with the success criteria, test results, weekly notes, cost estimates, screenshots, and diagrams.

Read all of it. For PowerPoint files, run `python3 scripts/read_deck.py <file>` to get the text. Look at screenshots and diagrams too: they can go on slides as they are.

## 2. Write the brief

Write `brief.md` from the materials, under the headings below. Keep every fact with its number, as short bullets. Use the client's names for their teams, systems, and metrics.

* **Audience:** who's in the room, and what each person decides or cares about. Start from "Who's in the room" in my [profile](../context/profile.md).
* **The problem:** what it costs the client today, in their numbers.
* **What we set out to prove:** the success criteria agreed at the start, each with its target.
* **What we did:** scope, data, setup, timeline, and what was out of scope.
* **Results:** each criterion against its target, marked Met, Not met, or Partly met. Then any other result worth knowing.
* **What didn't work:** misses and limits, with the cause when we know it.
* **Path to production:** phases, time, cost, and what the client needs to provide.
* **Recommendation and ask:** what we recommend, the decision we need, who makes it, and by when.
* **Still missing:** anything above the materials don't answer.

A deck can't do without three things: the success criteria, the results against them, and the ask. If any is missing, ask me before going on, one question at a time. Leave anything else that's missing out of the deck, and keep it under "Still missing".

## 3. Propose the storyline

Before writing slides, give me the storyline in Chat: one line per slide, numbered, with the headline and the block it uses (see [Format](#format)). This is the one time you stop to check with me.

A headline is the slide's takeaway as a full sentence: "Four of five criteria met; claimed amounts fell short at 88.2%", not "Results". Read only the headlines, in order. They should tell the whole story. If they don't, fix the storyline before showing me.

Start from this storyline, unless the house style in my [profile](../context/profile.md) gives another:

| Slide | It answers |
| --- | --- |
| Cover | The title, the client, my firm, and the date |
| Executive summary | Did it work, the two or three numbers that prove it, and what we recommend |
| The problem | What it costs them today, in their numbers |
| How it works | What we built, with what data, and where their data went |
| Results | Each success criterion against its target |
| What it looks like | A screenshot or an example output |
| What didn't work | Misses and limits, and how we'd fix them |
| Path to production | Phases, time, cost, and what they need to provide |
| Next steps | The decision we need, who makes it, and by when |
| Appendix | The detail behind the results, for questions |

Cut a slide when there's nothing real to put on it. Merge two that say the same thing. Most POC decks come to 8–12 slides, plus the appendix. The answer always comes first: the sponsor may only stay for the first five minutes.

## Slides

When I OK the storyline, or after my changes:

1. Write `deck.html`, following the rules and format below. Every slide gets speaker notes.
2. Review it, following [review.md](review.md#checklist), and fix what you can.
3. Build it, following [export.md](export.md).
4. Tell me where the deck is in a sentence or two. Then name anything still missing or uncertain, at most three, most important first.

### Writing slides

* **Headline:** One sentence with the takeaway, two lines at most (about 90 characters). Put the number in it when the number is the point.
* **One message per slide.** Everything on the slide backs up the headline. If something doesn't, cut it or move it.
* **Few words:** Six bullets at most, each a line or two. Open a bullet with a short bold label when it helps scanning, like `<b>Scanned forms:</b>`. Details go in the speaker notes or the appendix.
* **Their words:** The client's names for their teams, systems, and metrics. Explain a technical term in plain words the first time, or leave it out. The sponsor usually isn't technical.
* **Numbers:** Every number has its unit and what it's compared to: the target, the baseline, or before. The same number looks the same everywhere: not "92.5%" on one slide and "about 93%" on another.
* **Honest:** A missed target gets said on the results slide and explained on its own slide, with the cause and the fix. Don't soften it or hide it in the appendix.
* **Source:** A slide with results gets a source line saying where the numbers come from, like the test set and its size.
* **Show, don't list:** When the point is how parts connect or how numbers compare, draw it: an architecture diagram or a chart says it faster than bullets.
* **Speaker notes:** Two to four sentences, the way I'd say them: what to stress, and the one detail to have ready if someone asks.

### Format

Write `deck.html` with the kit in [deck.css](../templates/deck.css). Read the comment at its top first: it lists every block. [build.py](../scripts/build.py) adds the accent bar, footer, slide number, logo, and the arrows in a flow, and sets the brand color and font, so leave those out.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Deck title</title>
<link rel="stylesheet" href="../../templates/deck.css">
</head>
<body>

<section class="slide cover">
  <h1>Deck title</h1>
  <p>Client · My firm</p>
  <p>Month D, YYYY</p>
</section>

<section class="slide">
  <h2>The headline: this slide's takeaway, as one sentence</h2>
  <ul>
    <li><b>Label:</b> A point.</li>
  </ul>
  <p class="source">Source: Where the numbers come from.</p>
  <aside class="notes">What to say on this slide.</aside>
</section>

</body>
</html>
```

Each slide is a `<section class="slide">` that starts with an `<h2>` headline, then one or two blocks:

| Block | Good for |
| --- | --- |
| `ul` or `ol` | The problem, next steps |
| `.cols` | Comparisons, phases, what didn't work |
| `.numbers` | The executive summary |
| `table` | Results against criteria |
| `.flow` | How it works, when it's a few steps in a line |
| `.split` with a `figure` | A screenshot, with what to notice beside it |
| `figure` with an `svg` | Architecture diagrams and charts |
| `.box` | A callout, or the parts of a diagram |
| `.section` | The appendix divider |

More rules:

* Build only with the kit's blocks and classes. Inline styles are for sizes and positions inside a diagram or chart, and nothing else: no colors, fonts, or text sizes of your own. If a slide needs something the kit can't do, tell me.
* Draw diagrams and charts in SVG, with the kit's colors, like `style="fill: var(--brand)"`, and text at 15px or more. Bars in a chart start at zero. In the PowerPoint, SVG becomes a picture; everything else stays editable.
* Pictures are PNG or JPG, with paths relative to `deck.html`.
* Tables have no merged cells. A status cell gets the class `met`, `partly`, or `missed`.
* Bullets go one level deep at most.
* Write `&lt;`, `&gt;`, and `&amp;` for <, >, and & in text.

## Edits

When I ask for a change, make it in `deck.html` and build again. When I give new facts, add them to `brief.md` first. If a change affects other slides, like a new result that changes the executive summary, update those too and tell me which.
