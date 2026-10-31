# Vardath — Living Factions & Builders, v1.3

**Experimental X4: Foundations 9.00 extension; X4: Cradle of Humanity DLC is now REQUIRED for the bundled custom gamestart.** The distributed XML is well-formed and archive/source matched in GitHub Actions. The v1.2 payment logic has **not been run in X4 itself**; use a backup save.

## Features

- **NPC construction contracts for player builders:** faction construction sites issue native `request construction vessel` signals to eligible player-owned XL builders that have **Find Build Tasks** active. This includes standard-economy DLC factions, subject to travel, blacklists, station materials, relations and job availability. The special scripts used by Xenon/Kha'ak and some other factions are not necessarily integrated.
- **Active request broker:** an MD cue repeats at five-in-game-minute intervals. It **skips the galaxy-wide station query altogether** if there are no available player construction ships on Find Build Tasks. The native short-range requests still operate in parallel.
- **NPC station economic growth:** vanilla shortage-driven expansion may add additional production modules and construct larger factories; stock economic conditions and build queues are still respected.
- **Player construction jobs:** player stations can send requests to player-owned builders without authorizing NPC ships to accept them automatically.
- **New contract payroll, v1.2:** one **200,000 Cr hiring fee**, then **100,000 Cr per in-game hour** while the assigned buildmodule reports actively building, or **25,000 Cr per in-game hour** while assigned but not actively building (including transit, build-storage delays and resource waits). **No maximum duration/cap** on an active assignment.

## Contract billing and save/reload rules

The new separate `md/vardath_builder_contracts.xml` handles **all payments**. The earlier 50,000 Cr AI-script payment has been removed, so there is no competing fee.

- Every **one in-game minute**, the payroll script inspects player construction ships and the **actual game-assigned construction module**. It registers a new contract only if that module belongs to an NPC station and has real queued/in-progress building.
- The first tick detecting an assignment creates a **persistent Mission Director table** indexed by the player ship. The 200,000 Cr fee is invoiced once. If updating a save where a ship is **already on a job**, that existing assignment counts as a new v1.2 contract; you may also have received the older 50,000 Cr in v1.1.
- The table stores station, assigned module, employing faction, last accrued game time, unbilled earnings, billable time and outstanding debt. It is **not reset** by the billing timer or when the game loads.
- Each sampled minute is classified by `$BuildModule.isbuilding`: 100,000 Cr/hour when constructing; 25,000 Cr/hour otherwise. The accumulated amount is invoiced **after one hour of combined billable time**. If a contract ends earlier, its accrued **fractional hour is also invoiced**, including upon normal completion/cancellation or changed assignment.
- A money transfer records its actual result; only the credits actually transferred reduce outstanding debt. Unpaid balances remain in saved ledger state for retry; no re-invoicing an hour already billed, and reopening a saved game does not create another hiring fee for the same live contract.
- A per-sample upper bound of **two minutes** prevents a long game-time jump or an interrupted/disabled mod from generating arbitrarily large back-pay. Because billing samples at one-minute intervals, at most roughly the final minute of a suddenly ended contract may be missed before the departure is observed; accounting is designed to favour avoiding overpayment.
- A builder moved to a **new station** begins a new contract, with a new hiring fee, after its old balance has been settled. No player-owned station contracts are billed.

**Caution:** Save/reload persistence is based on X4's saved MD variables and a saved ledger; this design has not yet been confirmed by repeated in-game save/load tests. This version is ready for testing, but not certified bug-free.

## Install or update

Download the **[v1.3 ZIP](../vardath_living_factions_builders_v1.3.zip)** and extract the **single** `vardath_living_factions_builders` folder into your X4 `extensions` directory.

Example default Steam path:

`C:\Program Files (x86)\Steam\steamapps\common\X4 Foundations\extensions\vardath_living_factions_builders\content.xml`

When updating, **replace the existing mod directory**; do not install it beside v1.2. Enable the extension in the X4 Extensions menu, then restart the game. The extension declares no required DLC. Keep a backup save before trying new mod versions.

## Test checklist

1. With the v1.2 extension enabled, save, buy/use a player-owned XL builder and set **Find Build Tasks** as its current default behaviour.
2. Watch a friendly NPC station with a real queued build hire your ship. The hiring fee should be **200,000 Cr** (after the payroll tick, no more than about a minute of game time).
3. Leave it working for more than one in-game hour. Check for **100,000 Cr per active hour**; if it waits for resources, those minutes accrue at **25,000 Cr/hour**. Mixed hours yield a weighted amount.
4. **Save while it is working**, remember the player cash balance, reload and confirm that the hiring fee is not duplicated. Let the next hourly settlement occur exactly once.
5. End the job before an hour is complete and verify the last fractional accrual is paid; change ship assignments and ensure payments stop.
6. Test a save where two builders are on different NPC jobs. A periodic payroll scan should not interfere with the faction request broker.

If wages are absent or credits duplicate, capture your X4 script/debug log and builder/station state. The source may still need X4 runtime/XSD or payment-result adjustments.

## Performance / compatibility

- The payroll scan looks at **player builder ships and a small active-contract ledger** only. It does not scan every station each minute.
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
