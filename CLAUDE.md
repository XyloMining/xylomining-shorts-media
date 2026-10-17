# Runbook for Claude sessions (XyloMining Shorts)

This repo is the whole pipeline. A weekly Claude session builds a week of Shorts, and Metricool publishes them.
Metricool tools only exist inside a Claude session, so scheduling is done by you (Claude) following this runbook.
Never schedule anything the user has not approved. Never claim a step worked without checking its output.

## Session start (every time; the sandbox is fresh)
1. `pip install -r requirements.txt --break-system-packages` then `python -m yt_auto setup` (downloads ~350 MB narration model from GitHub) then `python -m yt_auto doctor`.
2. `python -m yt_auto status` to see what is already built/scheduled. State lives in `state/shorts.db` (committed).

## Weekly flow
1. **Content bank**: doctor warns when fewer unused items than `pipeline.buffer_slots` remain. Write more in the same JSON shape as `content_bank/claude_week1_2.json`
   (see `python -m yt_auto bank-prompt 14`), using ONLY claims in `facts/facts.md` (add sourced facts there first). Save to a file and run `python -m yt_auto bank-import FILE`; fix whatever it rejects.
2. `python -m yt_auto run` builds up to `buffer_slots` future slots (script, Kokoro narration, 1080x1920 video, thumbnail) and pushes approved ones to `videos/`.
   The first `approval.required_count` (3) videos are held as `pending_approval`. Send the user the videos (SendUserFile) and wait for explicit approval, then `python -m yt_auto approve all` and `python -m yt_auto run` again.
3. `python -m yt_auto queue` prints one JSON object per staged post. For EACH item:
   a. Call Metricool `getScheduledPosts` for that day (brand from config `metricool.blog_id`, timezone Australia/Sydney). If a post with the same title or time already exists, skip it and `mark-scheduled` with its id/uuid.
   b. Call `createScheduledPost` with `blogId`, `date`, and `info` (the item's `info` object as a JSON string, unchanged).
   c. On success run `python -m yt_auto mark-scheduled ID --metricool-id ... --uuid ... --url PLANNER_URL`. On error, report it verbatim; do not retry blindly.
4. `python -m yt_auto persist` so the next session sees the state. Report: what is scheduled (title + local time), anything failed, anything waiting for approval.

## Sunday report
Use Metricool `getAnalyticsAvailableMetrics` (network youtube) then `getAnalyticsDataByMetrics` for the last 7 days, write `data/metrics.json` as rows keyed by `title`
(views, engagedViews, averageViewDuration, averageViewPercentage, likes, comments, subscribersGained as available), run `python -m yt_auto report`.
Link clicks and "viewed vs swiped away" are not available via API; say so. Never delete or re-upload underperformers.

## Pause / hold
`python -m yt_auto pause` stops new builds. To hold already-scheduled posts, call `updateScheduledPost` with the full original content and `draft: true`; resume reverses it.

## Rules that must not be broken
- No profit promises, no invented results, no claims outside `facts/facts.md`. The validator enforces banned phrases and dollar figures.
- The referral link always carries the disclosure (added by code in the description).
- Uploaded media URLs must be public raw GitHub URLs under `media.raw_base`; GitHub Releases are blocked for these sessions, so media is committed under `videos/`.
