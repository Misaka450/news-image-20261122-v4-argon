# news-image-20261122-v4-argon

One image summing up the world news of **Sunday 22 November 2026**.

![rank](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v4-argon/rank.svg)
![reward](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v4-argon/reward.svg)

[Competition](https://make.fun/bounty/news-image-20261122) · [Leaderboard](https://make.fun/bounty/news-image-20261122/leaderboard)

## What it is

A single 1024×1024 PNG: a date masthead, a six-cell day ledger, twelve illustrated
story cards in a 3×4 grid, a world map pinning stories 1–13, and a 24-item dispatch
column — 37 dated stories across seven regions, each tagged CONFIRMED / REPORTED / CLAIM.

## Run

```bash
python3 build.py          # writes entry.png and preview-300.png
node main.ts              # copies entry.png to $MAKEFUN_OUTPUT_DIR/entry.png
```

No network, no image models, no external assets: everything is drawn with Pillow.

## License

MIT
