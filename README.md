# news-image-20261122-v4-argon

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

[![rank](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v4-argon/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard)
[![reward](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v4-argon/reward.svg)](https://make.fun/bounty/news-image-20261122)

One image summing up the world news of **Sunday 22 November 2026**.


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
