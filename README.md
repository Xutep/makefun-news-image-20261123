# The World in One Day — Monday 23 November 2026

Entry for make.fun bounty
[`news-image-20261123`](https://make.fun/bounty/news-image-20261123):
sum up 23 November 2026's world news in one image.

`main.py` (pure Python standard library, deterministic, no network) draws a
1024x1024 newspaper front page and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`
(or `/output/entry.png`):

- **COP31 climate talks fail** — no deal as nations split over fossil-fuel wording
- **Iran strikes US bases in Bahrain** — retaliation; Gulf shipping on alert
- **Drone hits a building in the Kyiv region** — at least 14 missing
- **Deadly factory fire in Indonesia** — dozens killed and missing
- **Mexico seizes 'El Chapo Isidro'** — FBI most-wanted cartel boss captured
- **Seoul minister quits over AI cheating** — South Korea's education chief resigns

Plus a footer line: India's record 720/9 in the Wellington Test, and UN talks
on lethal AI weapons to continue.

Run it locally:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The PNG is encoded by hand (zlib + struct) and all text is rendered with a
small built-in 5x7 bitmap font, so the program needs no fonts or libraries.
Two runs produce byte-identical output.
