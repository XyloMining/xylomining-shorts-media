# XyloMining Shorts pipeline

Original, fact-checked Bitcoin-mining education Shorts (20-40 s, 9:16), one per day in Australia/Sydney time, with a referral
link in the description plus disclosure. Claude writes the content; local tools render it; **Metricool** publishes it to YouTube.

## How it works
```
Claude writes script/title/description  ->  validator (facts, banned phrases, length, disclosure)
  -> Kokoro narration (offline, free) + Pillow/FFmpeg video + thumbnail
  -> approval gate (first 3 videos need your OK)
  -> pushed to this public repo (videos/)  ->  Metricool pulls the URL and publishes on schedule
```
Weekly rhythm: open a Claude session, say "run the weekly Shorts batch". Claude follows `CLAUDE.md`. Because Metricool schedules
the posts, publishing happens even when nobody is online.

## What is free / what is not
| Piece | Cost |
|---|---|
| Script, title, description (Claude in your own sessions, content bank) | included in your Claude plan |
| Narration: Kokoro-82M offline model | free, open source |
| Video and thumbnail: Pillow + FFmpeg | free |
| Media hosting: public GitHub repo | free |
| Scheduling/publishing: your Metricool plan | whatever your Metricool plan includes |
| Unattended daily runs (scheduled tasks) | **not on the free Claude plan**, hence the weekly session |

## Commands (`python -m yt_auto ...`)
`setup` `doctor` `status` `run` `approve all|ID` `reject ID` `queue` `mark-scheduled` `persist` `pause` `resume` `report`
`bank-prompt N` `bank-import FILE` `test-render [--silent]` `dry-run [--silent --slots N]`

## Tests
`python -m unittest tests.test_core tests.test_pipeline_mock` (18 tests, ~4 min because it renders videos): DST scheduling, validator,
duplicate guards, approval gate, staging, Metricool payload shape, pause, stale-slot handling, analytics report.

## Known limits (read these)
- **Links in Shorts descriptions are not clickable** on YouTube (since 31 Aug 2023, per TechCrunch / Search Engine Journal). Put your link in the channel profile
  links and set `cta.where` / `cta.label` in `config.yaml` accordingly, or viewers cannot tap it.
- YouTube's API has no metric for description-link clicks or "viewed vs swiped away"; the report says so. Linkvertise/GoMining numbers are imported from CSVs you export.
- Metricool rejects a post if a custom thumbnail is not supported by the channel, so thumbnails are generated but not sent (`metricool.send_thumbnail: false`).
- GoMining facts come from a third-party explainer; confirm current terms on gomining.com before adding numbers to `facts/facts.md`.
- Narration quality was only measured (levels, silence), not listened to: check the first video yourself.
- Whether YouTube treats your channel's content as reused/templated is outside this pipeline's control; vary topics and keep every Short educational.
