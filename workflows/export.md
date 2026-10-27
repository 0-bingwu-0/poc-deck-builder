# Build the Deck

Turn `deck.html` into `deck.pdf`, and into `deck.pptx` when I ask for PowerPoint. [build.py](../scripts/build.py) does both. Your job is the HTML. Don't edit the PDF or the PowerPoint, and don't change the script or the kit to make something fit.

## 1. Run the build script

Run it from the project folder with the path to `deck.html`:

```bash
python3 scripts/build.py pocs/<client>-<poc>/deck.html --pictures
```

On Windows, use `python` or `py` instead of `python3`.

It renders the deck in Chrome, Edge, or Chromium and prints `deck.pdf` next to it, with the brand color, font, footer, and logo from Deck settings in my [profile](../context/profile.md). Then it checks every slide and lists anything that runs past the edge of a slide, and any headline over two lines:

```text
Slide 7: "Done when all five criteria hold on live…" runs 0.42 in past the edge of the slide.
```

`--pictures` also saves a PNG of each slide and prints the folder. If you can't look at images, leave it off.

## 2. Fix what doesn't fit

For each slide on the list, cut words from it in `deck.html`, move detail to the speaker notes, or split it into two slides. Then build again.

## 3. Look at the slides

Look through the slide pictures: each slide should read at a glance, pictures and diagrams should be readable and show what the slide says, and nothing should look crowded or empty. Fix what you can in `deck.html` and build again.

When it's clean, tell me where `deck.pdf` is.

## PowerPoint

When I ask for PowerPoint, add `--pptx`:

```bash
python3 scripts/build.py pocs/<client>-<poc>/deck.html --pptx
```

It writes `deck.pptx` next to the PDF: every headline, bullet, box, and table in the same place as in the PDF, all editable, with the speaker notes. SVG diagrams and charts go in as pictures. Once a deck has a PowerPoint, keep adding `--pptx` when you build it, so the two stay the same.

The PDF looks the same on every computer. The PowerPoint comes close, but PowerPoint sets the text itself: a line can break in a different place, and if my font isn't on the computer that opens it, PowerPoint swaps in another. Tell me this the first time. When a deck goes to a client who only needs to read it, the PDF is the safer one to send.

## If something goes wrong

* **No browser:** the script needs Chrome, Edge, or Chromium to build anything. Ask me to install one.
* **A picture won't load:** it needs to be a PNG or JPG. Convert it, save the copy next to the original in `materials/`, and point `deck.html` at the copy.
* **My firm's font isn't on this computer:** the PDF uses Arial instead. Mention it once.
