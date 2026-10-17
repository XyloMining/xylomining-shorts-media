# XyloMining Shorts pipeline

Original, fact-checked Bitcoin-mining education Shorts (20-40 s, 9:16), one per day in Australia/Sydney time, with a referral
link plus disclosure. Claude writes the content; local tools render it; **Metricool** publishes it to YouTube Shorts and TikTok.

## How it works
```
Claude writes script/title/description  ->  validator (facts, banned phrases, length, disclosure)
  -> Kokoro narration (offline, free) + Pillow/FFmpeg video + thumbnail
  -> approval gate (first 3 videos need your OK)
  -> pushed to this public repo (videos/)  ->  Metricool pulls the URL and publishes on schedule
```
Weekly rhythm: **Friday evening** a GitHub Action builds the next 7 Shorts on its own (free). **Once a week you send Claude one message**
("schedule this week's Shorts"); Claude queues them in Metricool, about a minute. Metricool then publishes even when nobody is online.

### One-time setup for the automation
1. Repo **Settings > Actions > General**: allow Actions, and set Workflow permissions to *Read and write*.
2. Repo **Settings > Secrets and variables > Actions > New repository secret**: `GEMINI_API_KEY` (a free key from Google AI Studio). Only used once the 14 Claude-written bank items run out.
3. Optional: run it now from the **Actions** tab ("Weekly Shorts build" > Run workflow) to test.

Why not fully hands-off: Metricool's tools exist only inside a Claude session, and scheduled Claude tasks are a paid feature. If your Metricool plan includes API access, the last step could also be scripted.

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
`python -m unittest tests.test_core tests.test_pipeline_mock` (20 tests, ~5 min because it renders videos): DST scheduling, validator,
duplicate guards, approval gate, staging, Metricool payload shape, pause, stale-slot handling, analytics report.

## TikTok
Each video is posted to TikTok through Metricool at the same time as YouTube, with a short caption (no URL, since TikTok captions aren't clickable; add your Linkvertise link to your TikTok **bio**).
Defaults you should know about (`tiktok:` in `config.yaml`): posts are marked **AI-generated** (the narration is a synthetic voice) and as **third-party commercial content** (you may earn a benefit from the GoMining referral, and TikTok's rules require that disclosure).
Whether TikTok accepts automatic publishing for your account type is decided by TikTok/Metricool; if a post is rejected, Claude reports the exact error.

## Known limits (read these)
- **Links in Shorts descriptions are not clickable** on YouTube (since 31 Aug 2023, per TechCrunch / Search Engine Journal). Put your link in the channel profile
  links and set `cta.where` / `cta.label` in `config.yaml` accordingly, or viewers cannot tap it.
- YouTube's API has no metric for description-link clicks or "viewed vs swiped away"; the report says so. Linkvertise/GoMining numbers are imported from CSVs you export.
- Metricool rejects a post if a custom thumbnail is not supported by the channel, so thumbnails are generated but not sent (`metricool.send_thumbnail: false`).
- GoMining facts come from a third-party explainer; confirm current terms on gomining.com before adding numbers to `facts/facts.md`.
- Narration quality was only measured (levels, silence), not listened to: check the first video yourself.
- Whether YouTube treats your channel's content as reused/templated is outside this pipeline's control; vary topics and keep every Short educational.
