# WordPress Scheduling Checkpoint — 2026-09-18

**Site:** https://vardathcosmology.wordpress.com  
**WordPress site timezone:** UTC  
**Reader-facing cadence:** one post per day at **9:00 AM Brisbane time (UTC+10)**  
**Storage convention:** WordPress stores those dates as **23:00 UTC on the previous calendar date**.

## Existing first-pass queue

The original 48-post onboarding / first-pass queue remains unchanged:

- WordPress post IDs: **8–55**
- Reader-facing dates: **18 September 2026 through 4 November 2026**
- Stored WordPress dates: **17 September 2026 23:00 UTC through 3 November 2026 23:00 UTC**
- Status verified: **future**

## Expanded E-series now scheduled

The first 52 audited expanded Cosmology articles have now been created and scheduled:

- **E01 → WordPress post ID 56 → 5 November 2026, 9:00 AM Brisbane**
- One post every day thereafter
- **E52 → WordPress post ID 107 → 26 December 2026, 9:00 AM Brisbane**
- Stored WordPress range: **4 November 2026 23:00 UTC through 25 December 2026 23:00 UTC**
- Status verified for all: **future**
- Content warnings returned during creation: **none**

The E-series posts use their canonical audited title, categories, excerpt, final article, authoritative archive link and research/source boundary.

## Queue verification

Live WordPress verification after E52 scheduling returned:

- **100 total future posts**
- **48 original first-pass posts**
- **52 expanded E-series posts**
- No day gaps in the 100-post queue
- First future post: ID 8
- Last future post: ID 107 / E52
- The live queue is now at the current 100-future-post scheduling ceiling.

## Next scheduling action

**Next unscheduled expanded article: E53.**

Do not recreate E01–E52.

When scheduling resumes after enough currently scheduled posts have published and future-post slots have opened:

1. Check the live WordPress `future` queue first.
2. Continue with **E53**.
3. Preserve one-per-day publication with no date gap after the latest already scheduled E-series post.
4. Use the canonical audited source mapping in `WORDPRESS-SCHEDULING-READY-E001-E453.md` and `wordpress-scheduling-manifest-E001-E453.json`.
5. Preserve 9:00 AM Brisbane reader-facing publication time unless Stephen explicitly changes it.

## Remaining expanded series

- Total audited expanded series: **E01–E453**
- Scheduled so far: **E01–E52**
- Remaining unscheduled: **E53–E453**
- Remaining count: **401**

This checkpoint records scheduling state only. It does not alter the 453-article canonical content bank.
