# Runbook for Claude sessions (XyloMining Shorts)

This repo is the whole pipeline. A weekly Claude session builds a week of Shorts, and Metricool publishes them.
Metricool tools only exist inside a Claude session, so scheduling is done by you (Claude) following this runbook.
Never schedule anything the user has not approved. Never claim a step worked without checking its output.

## NOTE (18 Oct 2026): publishing moved from Metricool to Buffer
- Buffer org `6ad38249b692c4ab06ad53ec`; channels YouTube `6ad382fe778b240e2f3a0081`, TikTok `6ad3833b778b240e2f3a0347`, Instagram `6ad3cd59778b240e2f3e1aff` (Reels: metadata type reel, shouldShareToFeed true, isAiGenerated true; caption = title, body, "Link in my bio.", disclosure, hashtags; branded-content toggle cannot be set via Buffer). Posts 1-7 (all 7 days) are scheduled there (ids in `state/buffer_posts.json`), Mon-Fri 18:00, Sat-Sun 11:00 Sydney, same video and time on all three channels.
- Use `mcp__Buffer__create_post` (mode customScheduled, schedulingType automatic, video asset = raw GitHub URL, YouTube metadata title + categoryId 28, TikTok metadata title + isAiGenerated true). Check `list_posts` for duplicates first.
- Buffer free plan: 10 scheduled posts at once PER CHANNEL (verified: an 11th org-wide post was accepted), so up to 10 videos ahead; 7 a week fits. Buffer has no best-time API; times are fixed at 18:00 unless the user sets others.
- Buffer cannot set TikTok's "branded content" toggle; the caption carries the referral disclosure.
- Metricool account and all its posts were deleted by the user on 18 Oct 2026. The Metricool sections below are legacy and the Metricool ids in the DB are dead. 
- Schedule is all 7 days (config.yaml); `queue`/`mark-scheduled` still describe Metricool and have not been reworked for Buffer.

## GoMining reference skills
- `.claude/skills/gomining-*` holds the vendor's 16 GoMining skills (SKILL.md plus references/), vendored from github.com/gomining-ai/gomining-agent-skills. Read the matching one when researching a topic for scripts or the content bank (Skill tool, or open the files).
- They are vendor material, not verified facts: copy a claim into `facts/facts.md` with a source URL before any script uses it. Never use ROI/APR examples, price snapshots or dollar figures from them.

## Session start (every time; the sandbox is fresh)
1. `pip install -r requirements.txt --break-system-packages` then `python -m yt_auto setup` (downloads ~350 MB narration model from GitHub) then `python -m yt_auto doctor`.
2. `python -m yt_auto status` to see what is already built/scheduled. State lives in `state/shorts.db` (committed).

## Automation split (GitHub Actions + one message)
- `.github/workflows/weekly-build.yml` runs every Friday evening (Sydney) and also on demand: it builds up to 7 future Shorts, stages approved ones under `videos/`, and commits `state/` + `log/`. Content comes from the bank first, then Gemini (repo secret `GEMINI_API_KEY`).
- The user then sends ONE message ("schedule this week's Shorts"). In that session do only: `git pull`, `python -m yt_auto queue`, schedule each item in Metricool (step 3 below), `mark-scheduled`, `persist`. No need to render anything or download the model.
- Failed workflow runs email the repo owner (GitHub default). If the user reports one, read the run log with `gh run view --log-failed` if permitted.

## Weekly flow (manual / first-time version)
1. **Content bank**: doctor warns when fewer unused items than `pipeline.buffer_slots` remain. Write more in the same JSON shape as `content_bank/claude_week1_2.json`
   (see `python -m yt_auto bank-prompt 14`), using ONLY claims in `facts/facts.md` (add sourced facts there first). Save to a file and run `python -m yt_auto bank-import FILE`; fix whatever it rejects.
2. `python -m yt_auto run` builds up to `buffer_slots` future slots (script, Kokoro narration, 1080x1920 video, thumbnail) and pushes approved ones to `videos/`.
   The first `approval.required_count` (3) videos are held as `pending_approval`. Send the user the videos (SendUserFile) and wait for explicit approval, then `python -m yt_auto approve all` and `python -m yt_auto run` again.
3. `python -m yt_auto queue` prints one JSON object per (staged post, network): `network` is `youtube` or `tiktok` (config `metricool.networks`). Same video, same slot, separate Metricool post per network
   (TikTok gets a short caption; YouTube gets the full description with link, disclosure and sources). For EACH item:
   a. Call Metricool `getScheduledPosts` for that day (brand from config `metricool.blog_id`, timezone Australia/Sydney). If a post for the same network with the same title or time already exists, skip creating it and `mark-scheduled` with its id/uuid.
   b. Call `createScheduledPost` with `blogId`, `date`, and `info` (the item's `info` object as a JSON string, unchanged).
   c. On success run `python -m yt_auto mark-scheduled ID --network youtube|tiktok --metricool-id ... --uuid ... --url PLANNER_URL`. On error, report it verbatim; do not retry blindly.
      A failure on one network must not block or duplicate the other: the post stays `staged` until every network is done, and `queue` re-lists only what is missing.
4. `python -m yt_auto persist` so the next session sees the state. Report: what is scheduled (title + local time), anything failed, anything waiting for approval.

## Sunday report
Use Metricool `getAnalyticsAvailableMetrics` (network youtube) then `getAnalyticsDataByMetrics` for the last 7 days, write `data/metrics.json` as rows keyed by `title`
(views, engagedViews, averageViewDuration, averageViewPercentage, likes, comments, subscribersGained as available), run `python -m yt_auto report`.
Link clicks and "viewed vs swiped away" are not available via API; say so. Never delete or re-upload underperformers.

## Pause / hold
`python -m yt_auto pause` stops new builds. To hold already-scheduled posts, call `updateScheduledPost` with the full original content and `draft: true`; resume reverses it.

## Rules that must not be broken
- No profit promises, no invented results, no claims outside `facts/facts.md`. The validator enforces banned phrases and dollar figures.
- The referral link always carries the disclosure (added by code in the description; TikTok gets the same disclosure and is flagged as third-party commercial content plus AI-generated content, see config `tiktok`).
- Uploaded media URLs must be public raw GitHub URLs under `media.raw_base`; GitHub Releases are blocked for these sessions, so media is committed under `videos/`.

## Video style rules (set by the user, 18 Oct 2026)
- Money in narration is spoken in words ("4 dollars and 30 cents") but captioned as "$4.30"; `render.py` merges "N dollars and M cents" into "$N.MM" automatically.
- Dollar figures are only allowed if they appear in `personal_results` (config.yaml). Personal-results videos always say they are the creator's own numbers, not typical, and can be lower.
- `tts.clause_sync: true` synthesises clause by clause so caption timing is measured (off by default; the dashboard Short was built with it). Scenes may carry `"image": <path>` (screenshot) and an item may set `"style": {"bg": "aurora"}`.

## Daily site update (set by the user, 28 Oct 2026)
When the user sends the daily message ("update instagram and tiktok on my website and the stats"), do this in `/home/claude/xylomining.github.io`:
1. `mcp__Buffer__list_posts` (org above, channels Instagram + TikTok, status sent, includeMetrics, first 50) and `execute_query` for each post's `externalLink` (posts(input:{organizationId, filter:{channelIds, status:[sent]}}) { edges { node { id channelService dueAt externalLink } } }). Save the list result and a "postId url" text file.
2. `python3 scripts/buffer_to_json.py LIST_RESULT LINKS.txt` merges into `postsig.json` and `poststt.json`. These files are a growing data set: nothing is ever removed and counts never go down. Put any follower numbers the user gave into `data/followers.json` (Buffer has none).
3. Data files are one per platform: `postsyt.json` and `postsrd.json` are written by the automated `refresh-posts` workflow (accumulating, YouTube/Reddit are blocked in the sandbox so do NOT run `scripts/fetch-posts.mjs` here), `postsig.json`/`poststt.json` by step 2, `postsx.json` is filled by hand: X cannot be read from the sandbox and has no free API, so when the user pastes X post links/text/counts, add rows {id "x-<status id>", platform "X", title (post text, short), url, date, views, likes, comments} (merge by id, counts never go down). `node scripts/fetch-stats.mjs` merges all of them into `stats.json`. `posts.json` is a short legacy combined list for the old site build: delete it after the new site build is published. Commit, `git pull --rebase`, push to main. Data files only: site code changes still wait for "publish".
The site shows each platform's top post (most views, then likes) plus its 5 most recent; the files keep everything.
Buffer metrics lag by about a day. Stories and untitled posts are skipped.

## Publishing the site ("publish")
The live repo (`/home/claude/xylomining.github.io`, GitHub XyloMining/xylomining.github.io) has a manual workflow, Actions > "Publish site" (`.github/workflows/publish-site.yml`, logic in `scripts/publish-from-source.sh`): it builds the source repo branch (default `feature/stats-page`), copies it over the live site, and saves the previous live site as the next `backup-N` branch first (no backup if nothing changed). It never overwrites `stats.json`, `articles.json`, `prices.json`, `posts{yt,rd,ig,tt,x}.json` or `sitemap.xml` (sitemap is hand-edited on the live repo). Use the "dry run" input to preview. The user can run it themselves; when they say "publish" in a session you can do the same steps by running the script locally with BUILD_DIR set to the source repo's `dist/client`.
