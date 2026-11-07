# Universal Cargo Teleport 1.01 — native trade recovery

A player-owned ship attempts the existing 30 km dockless native trade path. If the engine rejects an undocked attempt and reports **zero goods transferred**, it receives one normal docking retry. That partner then uses the normal docking path for one game hour, avoiding repeated unsuccessful wireless attempts. If docking is unavailable, native failure handling remains in charge.

The supplied debug(7).log contains 1,423 `order.trade.perform` failures with reason code `0x100000`. The dock-bypass patch is a plausible contributor; the log does not prove every failure has that cause. This update does not invent or silently reinterpret that engine reason code. Native cargo, escrow, trade-offer, reservation, money and ledger handling remain unchanged. No manual stock copy, free goods or duplicate payment is introduced.

Dockless transfer acceptance is engine-dependent and is **not proven for every ship/station combination**. Small ships may need actual docking. The recovery preserves trade completion where the former fast path was refused; it is not represented as verified universal wireless support. The player-to-player ship exchange patch is unchanged.

Close X4, overwrite `vardath_universal_cargo_teleport`, restart and load the existing save. Protected UI remains enabled. No new game, equipment change or removal of Inventory Collector is required. New fallback behavior needs in-game verification with the next log.
