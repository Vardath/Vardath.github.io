# Vardath — Living Factions & Builders, v1.6

**Experimental X4: Foundations 9.00 extension; X4: Cradle of Humanity DLC is now REQUIRED for the bundled custom gamestart.** The distributed XML is well-formed and archive/source matched in GitHub Actions. The v1.6 direct-pay code has **not been run in X4 itself**; use a backup save.

## Features

- **NPC construction contracts for player builders:** non-hostile faction construction sites issue native `request construction vessel` signals to eligible player-owned XL builders that have **Find Build Tasks** active. This includes standard-economy DLC factions, subject to travel, blacklists, station materials, relations and job availability. The special scripts used by Xenon/Kha'ak and some other factions are not necessarily integrated.
- **Active request broker:** an MD cue repeats at five-in-game-minute intervals. It **skips the galaxy-wide station query altogether** if there are no available player construction ships on Find Build Tasks. The native short-range requests still operate in parallel.
- **NPC station economic growth:** vanilla shortage-driven expansion may add additional production modules and construct larger factories; stock economic conditions and build queues are still respected.
- **Player construction jobs:** player stations can send requests to player-owned builders without authorizing NPC ships to accept them automatically.
- **Contract payroll, v1.6:** one **200,000 Cr hiring fee**, then **100,000 Cr per in-game hour** while the assigned buildmodule reports actively building, or **25,000 Cr per in-game hour** while assigned but not actively building (including transit, build-storage delays and resource waits). **No maximum duration/cap** on an active assignment.

## Contract diplomacy (v1.6)

- **Non-hostile employer filter:** NPC faction must allow player docking (normally -9 reputation or better). The five-minute dispatcher will not signal hostile NPC stations. The `Find Build Tasks` request handler independently rejects hostile employer stations, including native requests. Registration/payment likewise requires a non-hostile employing faction. Player-owned construction projects are unaffected.
- **Diplomacy changes mid-contract:** If the faction turns hostile, no more paid construction time is accrued after the next payroll tick and no reputation is awarded. Already invoiced debt remains in the persistent contract ledger for settlement; the builder's in-game order is not forcibly cancelled.
- **Completion reputation:** once per builder contract, **+0.00064 raw faction relation** is added with X4's mission-completed reason when that builder has been observed actively building and the employer's station has no queued or in-progress modules remaining. This is roughly +1 displayed point around neutral, but the display relation curve is nonlinear. There is **no reputation merely for taking a job or waiting for materials**.
- **Save/reload:** the existing global MD contract table stores `SawConstruction` and `RepGranted`; the latter is marked before applying the relation action. Existing v1.3 contracts gain credit for new observed construction after the upgrade, but prior activity cannot be inferred from past saves. The code is XML-verified but untested in-game; especially check completion across save/reload.

**Test:** A neutral NPC station should offer builder contracts and pay as before; a hostile faction should never dispatch a new request, and a job completed after actual building should improve reputation once. Save immediately before completion and reload to confirm no duplicate reputation, then confirm a cancelled or reassigned project with unfinished queued modules gives no reputation.

## Contract billing and save/reload rules (v1.6)

The separate `md/vardath_builder_contracts.xml` handles **all payments**. As of v1.6 it credits the player through X4's normal `<reward_player>` mission-reward action rather than relying on faction-to-player account transfers. NPC faction bankruptcy therefore cannot silently prevent payment. The earlier 50,000 Cr AI-script payment has been removed, so there is no competing fee.

- Every **one in-game minute**, the payroll script inspects player construction ships and the **actual game-assigned construction module**. It registers a new contract only if that module belongs to an NPC station and has real queued/in-progress building.
- The first tick detecting an assignment creates a **persistent Mission Director table** indexed by the player ship. The 200,000 Cr fee is credited immediately on registration. If updating a save where a ship is **already on a job**, that existing assignment counts as a new v1.2 contract; you may also have received the older 50,000 Cr in v1.1.
- The table stores station, assigned module, employing faction, last accrued game time, earnings, billable time and outstanding debt. It is **not reset** by the billing timer or when the game loads.
- Each sampled minute is classified by `$BuildModule.isbuilding`: **100,000 Cr/hour when constructing**, and **25,000 Cr/hour otherwise**. **Wages are paid every in-game minute** as incremental credit rewards (about 1,667 Cr/min active and 417 Cr/min waiting), without requiring a full hour to elapse. Outstanding accrual is also settled when the contract closes.
- Rewards clear the persisted owed amount before X4's normal player-credit action, preventing duplicated payouts on a saved running contract. The extension manifest now uses `save=1` because it carries a persistent Mission Director ledger. A completed job does not trigger another signing bonus.
- **SETA and late payroll checks (v1.6):** Bill the **full positive elapsed in-game time** between the previous saved `player.age` sample and the current payroll tick. There is no two-minute cap. For example, if a tick is delayed for 10 in-game minutes under SETA, the next valid tick pays all ten minutes instead of only two. The cue still checks for a live, eligible NPC construction assignment, and a nonpositive time difference earns nothing. Because the script samples whether the build module is actively building at each check, unusually long delayed intervals use the observed status at the next sample; it cannot reconstruct every intervening change from game history. **Important:** a contract is detected only after X4 actually assigns the XL builder to an NPC station build module; simply enabling Find Build Tasks while idle does not earn a fee or wages.
- A builder moved to a **new station** begins a new contract, with a new hiring fee, after its old balance has been settled. No player-owned station contracts are billed.

**Caution:** Save/reload persistence is based on X4's saved MD variables and a saved ledger; this design has not yet been confirmed by repeated in-game save/load tests. This version is ready for testing, but not certified bug-free.

## Install or update

Download the **[current TEST ZIP](../vardath_living_factions_builders_TEST.zip)** and extract the **single** `vardath_living_factions_builders` folder into your X4 `extensions` directory.

Example default Steam path:

`C:\Program Files (x86)\Steam\steamapps\common\X4 Foundations\extensions\vardath_living_factions_builders\content.xml`

When updating, **replace the existing mod directory**; do not install it beside an earlier version. Enable the extension in the X4 Extensions menu, then restart the game. Cradle of Humanity is required for the bundled new game start. Keep a backup save before trying new mod versions.

## Test checklist

1. With the v1.6 extension enabled, save, buy/use a player-owned XL builder and set **Find Build Tasks** as its current default behaviour.
2. Watch a friendly NPC station with a real queued build hire your ship. The hiring fee should be **200,000 Cr** once the NPC job is assigned and the next payroll scan registers it (typically within one game minute).
3. Watch the money balance over the next few in-game minutes: active work should add roughly **1,667 Cr/minute**, waiting for materials roughly **417 Cr/minute**. Mixed rates are proportional to the time sampled.
4. **Save while it is working**, remember the player cash balance, reload and confirm that the hiring fee is not duplicated. Let the next one-minute payment occur exactly once.
5. End the job before an hour is complete and verify the last fractional accrual is paid; change ship assignments and ensure payments stop.
6. Test a save where two builders are on different NPC jobs. A periodic payroll scan should not interfere with the faction request broker.

If wages are absent or credits duplicate, capture your X4 script/debug log and builder/station state. The source may still need X4 runtime/XSD or payment-result adjustments.

## Performance / compatibility

- The payroll scan looks at **player XL construction ships, including deployed ones, and a small active-contract ledger** only. It does not scan every station each minute.
- The job request broker checks faction stations every five in-game minutes **only while an available idle builder exists**.
- Avoid other builder dispatcher mods that patch `aiscripts/order.build.find.task.xml` and `aiscripts/build.buildstorage.xml`, notably **Player Builder Autodispatch**.
- Major faction economy overhaul mods may conflict with `md/factionlogic_economy.xml`, `libraries/parameters.xml` and `libraries/modules.xml`.
- No construction materials are fabricated, no fictitious build jobs are created, and faction bankruptcy/payment edge cases still need testing.
- The extension is a folder of unpacked XML; X4 loads it directly. No C++ compilation or DLL is needed.

## New custom game start (v1.3)

Under **New Game → Terran**, choose **Terran Shipwright — Yaki Company**.

- **Player:** Terran human female with an independent character macro copied from the vanilla female Project Genesis character, wearing the base-game-DLC **white Terran formal dress/skirt** (`char_ter_f_crew_uniform_01`). The original Project Genesis character and all other starts are unchanged.
- **Initial player-owned ship:** **Kyushu — Yaki Company**, the Terran **Kyushu XL construction ship** (`ship_ter_xl_builder_01_a_macro`).
- **Equipment:** Terran XL travel engine, two XL shields, five M shields, eight M defensive turrets, Mk2 XL thrusters, standard software and **36 construction drones**, plus repair/cargo drones.
- **Captain and crew:** Yaki pilot and 85% complement drawn from **Yaki veteran freighter crew**, primarily service crew with a small marine contingent. You are the player character aboard the ship.
- **Location:** Terran space, using the Terran Cadet's valid starting sector. **Starting credits: 250,000 Cr.**
- **Diplomacy:** Friendly starting relations with Terran Protectorate, Segaris Pioneers and Yaki. Standard universe and story systems remain enabled.

This is a **fixed additional start**, not the game's configurable Creative Custom Game editor. It appears when you choose *New Game*, not when loading an existing save. The `ego_dlc_terran` dependency is now **required** by this combined mod package. If you do not own Cradle of Humanity, do not install v1.3; instead use the v1.2 package without this start.

Files: `libraries/gamestarts.xml`, `libraries/character_macros.xml`, `libraries/loadouts.xml`, and English text `t/0001-l044.xml`. The start is XML-based and does not require a separate start-up script.

**Unverified in game:** This game's exact modified 9.00 XSD/runtime and rendering are not available in CI. Confirm the start displays in the New Game list, the ship has a working Yaki captain and build drones, the crew is Yaki, and the white skirt renders correctly. Keep a backup save.

## Attribution and licensing

See `ATTRIBUTION.md` and `LICENSE`. GPL-3.0-or-later (economy portions are based on DeadAir Eco). Player build-storage dispatch uses patterns adapted from drjele/Player Builder Autodispatch (MIT). X4: Foundations is owned by Egosoft GmbH; this is an independent community mod.
