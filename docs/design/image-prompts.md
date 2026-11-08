# Image prompts for the lifelog dashboard

Generate the images with an image model (for example ChatGPT). Save them as **PNG with a
transparent background** under `web/public/img/` using the file names below. Before generating,
paste the shared style block below into the chat and ask the model to keep it for every image.

## Shared style block

```
Visual style for a personal "life tracks" dashboard (dark UI, background #0D0D0D).
Soft 3D clay / glassmorphism illustration, rounded friendly shapes, subtle grain,
gentle studio lighting, no outlines, no text, no letters, no logos, no faces with detailed features
(simple abstract characters only), centered composition with generous padding,
TRANSPARENT background (PNG). Calm, warm, hopeful mood — never clinical or medical.
Palette: body = blue #2A78D6, mind = orange #EB6834, growth = aqua #1BAF7A,
money & social = yellow #EDA100; emotion quadrants: yellow #EDA100, red #E34948,
blue #2A78D6, green #008300. Use only colors from this palette plus soft whites.
```

## 1. Life areas (4 images, 1024×1024): `area-body.png`, `area-mind.png`, `area-growth.png`, `area-money-social.png`

```
Using the shared style: a single iconic object representing the life area "BODY":
a soft blue crescent moon resting on a small sneaker, with a tiny heartbeat wave floating above.
```
```
Using the shared style: a single iconic object representing "MIND": a smooth orange translucent
head-shaped stone with a small glowing sprout inside, tiny sparkles around it.
```
```
Using the shared style: a single iconic object representing "GROWTH": an aqua-green open book whose
pages turn into a small staircase going up, with a little flag at the top.
```
```
Using the shared style: a single iconic object representing "MONEY & SOCIAL": two golden-yellow coffee cups
touching (cheers) next to a small stack of rounded coins.
```

## 2. Emotion quadrants (4 images, 768×768): `quadrant-yellow.png`, `quadrant-red.png`, `quadrant-blue.png`, `quadrant-green.png`

```
Using the shared style: an abstract soft blob character made of yellow (#EDA100) clay,
bouncing upward with small motion lines and sparkles — feeling energetic and joyful.
No face details, just two dot eyes.
```
```
Using the shared style: an abstract soft blob character made of red (#E34948) clay,
slightly spiky edges and a small storm cloud above it — feeling tense and restless, but cute,
not scary. Two dot eyes.
```
```
Using the shared style: an abstract soft blob character made of blue (#2A78D6) clay,
drooping and sitting low under a tiny rain cloud — feeling tired and down, tender, not dramatic.
Two dot eyes.
```
```
Using the shared style: an abstract soft blob character made of green (#008300) clay,
resting peacefully on a small cushion with a leaf on top — feeling calm and content.
Two dot eyes, closed and relaxed.
```

## 3. Hero illustration (1 image, 1792×1024): `hero-tracks.png`

```
Using the shared style: a wide panoramic scene of several parallel winding paths ("life tracks")
flowing from left to right across soft rolling hills at dusk. Each path is a different palette color
(blue, orange, aqua-green, golden yellow) and they occasionally cross each other. Small glowing dots along the
paths mark moments. A tiny abstract figure walks on the paths in the middle distance. Leave the left
third mostly empty (calm gradient sky) so text can be placed over it. Transparent background is
NOT needed for this one — use a dark near-black gradient sky (#0D0D0D → #1A1A19).
```

## 4. Feature illustrations (5 images, 1024×1024)

`feature-sleep.png`
```
Using the shared style: a cozy rounded bed floating in space with a blue crescent moon pillow
and a small clock showing nighttime, a few soft stars around.
```
`feature-habits.png`
```
Using the shared style: a small aqua-green plant growing in a pot, with a soft rising curve
(like a growth chart) made of glowing dots wrapping around it.
```
`feature-wellbeing.png`
```
Using the shared style: an orange hot-air balloon gently rising, with five small rounded
sandbags (representing five questions) hanging below it.
```
`feature-patterns.png`
```
Using the shared style: two translucent rounded shapes (one blue, one orange) connected by
a softly glowing thread with small nodes, suggesting a discovered connection between things.
```
`feature-needs.png`
```
Using the shared style: a soft triangle made of three rounded pillars in orange, aqua-green and golden yellow
leaning on each other to stay standing — balance and support.
```

## 5. Empty states and safety (3 images, 768×768)

`empty-state.png`
```
Using the shared style: a small open notebook with a soft pencil and a single sparkle,
inviting to start writing.
```
`support.png` (shown next to the "Precisa conversar?" / CVV 188 card)
```
Using the shared style: two soft rounded hands (no detailed fingers) gently holding a small
warm glowing heart, in calm orange and green tones. Tender, reassuring, non-medical.
```
`celebrate.png`
```
Using the shared style: gentle confetti made of rounded shapes in all palette colors falling
around a small trophy-shaped star.
```

## 6. App icon (1 image, 1024×1024): `icon.png`

```
App icon, rounded square, dark background #0D0D0D. Four smooth parallel curved lines in
blue, orange, aqua-green and golden yellow flowing diagonally like tracks, with one small glowing dot on each.
Minimal, flat with a subtle soft-3D sheen, no text.
```

After generating, put the files in `web/public/img/` with exactly these names. The app falls back
to emoji/icons when an image is missing, so you can add them gradually.
