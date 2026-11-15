# Faction Command — Pass 35: employment identity and professional experience

Status: Pass 35A merged on main; Pass 35B implements one-at-a-time named professional travel through real ships and fully provisioned residences on PR #19 (Android debug v25 target). This remains a partial Pass 35: named ship employment, multiple concurrent named passengers, four additional professions and physical-device QA are outstanding. Check exact final PR CI before merge.
Base: main at Pass 34, e58507438477a82821b573521e5d09e0dcb49ad9.

## Goal
Give physically existing residents actual employed professions, bounded work experience, wages and professional continuity while retaining an Android map-first command surface. Keep the X4-style workforce/resource constraints without individual micromanagement of thousands of residents.

## Existing authoritative behavior
- `careers.gd` stores six practical certificate totals as per-station aggregate counts, and one-course `career_manifest` packets for passengers.
- `education.gd` holds theory completions as per-station aggregate counts.
- `population.gd` holds resident life stages as conserved aggregate cohorts. `personnel.gd` separately maintains stable named captains and ship crew.
- Existing apprenticeship graduation is attestation, not employment or ship skill.
- Move/copy of an aggregate certificate cannot be mistaken for creating another person. Do not retrofit fictitious names to historical workers.

## Implementation order (non-negotiable)
1. **Identity without population inflation.** Introduce a versioned `professional_roster` for only the subset of actual resident adults who enter vocational employment. Each professional receives a persistent deterministic ID, originating station/cohort reference, one current location (resident, passenger on one ship, or separately employed ship crew after a real transfer), supported foundation/practical qualifications and experience. Each named professional is a *reserved member* of an existing aggregate adult cohort, NOT an additional resident; `total_people` must not sum both. An audit must enforce roster residents <= counted adults and name uniqueness across stations and ships. Migrated saves start with empty rosters and unchanged historical totals. Historical aggregate certificates remain valid; converting one to a named professional reserves precisely one existing adult and its corresponding existing qualification, with no new graduation or XP.
2. **Identity-preserving transport.** Add a backward-compatible versioned named-professional manifest with explicit IDs, one-person-per-berth, source, theory, practicum and work-history snapshots. Existing Pass 34 grouped manifests remain readable; conversions must be transactional and reconcile both manifest formats. Arrival reassigns location rather than creating a resident. Partial disembark, save/reload, destroyed ships, full housing, unpaid cargo and caregiver constraints need explicit tests.
3. **Employment contracts.** Six initial jobs: navigator, engineer, station manager, archivist/research assistant, civilian safety officer and agricultural steward. Bind each contract to one existing named professional, one real available workstation, one employing station/ship, one current salary schedule and one active location; no duplicate assignment. Worksites must have the physical module, power and appropriate supplies. Employment is not merely a passive global skill modifier.
4. **Work XP from completed events only.** Navigation gains experience after actual sector crossings; engineering after legitimate production/maintenance; management after a funded resident service cycle; archives after copied records or a real research-lab cycle; safety after a real inspection/drill; agriculture after actual completed farm production. No XP while docked idle, blocked, unpowered, unpaid or unstaffed. Cap XP/skill 0–5 and avoid free resource/credit output from skill tiers. No instant conversion of an apprentice into a named ship captain or combat marine.
5. **Real wages and unemployment.** Salary is debited from employer credits and credited to an existing appropriate payroll sink/account. If the employer cannot pay, record arrears and suspend XP; no overdrafts. Contract termination frees the workstation and preserves the actual worker's skills, location, qualifications and employment history. One person cannot work at two sites in the same tick.
6. **Android integration.** Reuse station Careers and Ship & Crew tabs with staffed/open positions, location, profession, certification, wages, XP and blocking reason; long forms behind sub-tabs. No flight controls or implicit map-issued orders. Preserve touch targets, high UI scale and selected object.
7. **Validation and promotion.** Tests must cover no-people-created, no-double-certificates, no-double-pay, real work-event XP, power/resource stoppage, wage arrears, transfer, loss and cancellation, save migrations from all earlier versions, corrupted/repeated IDs, Android inspector buttons and signed APK packaging. Trigger both Godot and Android workflows on exact PR head, require both green; then merge and verify the exact main head. Never claim green or a release before checking both statuses.

## Architecture choice / X4 comparison
X4's skilled workforce, station modules and crew roles create deep production and staffing decisions. For Android, maintain aggregate ordinary residents but use persistent IDs only for licensed workers and notable people. A compact Careers panel exposes open posts, qualified candidates, current contracts and blockers. The simulation must enforce real resources, labour, ships, routes and funds underneath the simpler command UI.

## Deferred, deliberately distinct
Species-specific life support, health and elder mortality, NPC-run education, childcare transport, military boarding competency, advanced multispecies psychology, player-owned shipyards and full named multi-degree citizen history are not represented as completed by this pass.

## Implementation checkpoint
This document is the next scoped work package only. Pass 34 is the last merged implementation; do not advance the journal to 'Pass 35 completed' until game code, tests, both CI jobs and postmerge verification exist.

## Pass 35B implementation checkpoint

The original resident ID travels in the **same existing settler berth count** using `professional_passenger_id`, while `professional_registry[id].station_id` is empty only during ship transit. That record is returned to a physically eligible receiving player station on disembark. Academic and practical counters move through the existing permanent career-transfer ledger entries, with new per-ID professional board/arrival entries and location-aware wage/XP history replay. No new person, qualification, ship or skill is minted. Boarding suspends duty and future salary assessments, retains accrued arrears and real work XP, and blocks ordinary passenger mixing. A failed housing admission retains the ID and passenger record on the ship. Versioned additive ship migration preserves historic saves. Only one named passenger per ship and one certified track per named person are supported.

After Pass 35B, the next implementation gate is **Pass 35C**: support multiple identified professionals safely (capacity- and identity-bounded), give actual ship-based work contracts/events, then connect navigator, management, archive/research and civilian safety employment to corresponding genuine work completion. Multi-credential people, specialized medical/elder health and species-specific habitats require their own saved models and cannot be asserted as implemented.


## Pass 35C1 implementation status

Implemented on PR #20: persistent names for truly certified residents before employment; protected multiple named passenger slots per one owned ship; source/arrival educational and career counter audits; one-by-one resident arrival; old v25 single-worker migration; mobile selection of exactly which individual to board; XP from at most one actual worker per completed work cycle. The long integration test genuinely builds a recycler and pays for real academic/practical training for two engineers, without injecting the second citizen or their qualifications. Pass 35C's shipboard professional job contracts and the remaining unimplemented roles are **not** part of C1. Latest signed v26 APK requires both-green exact-final-head CI.
