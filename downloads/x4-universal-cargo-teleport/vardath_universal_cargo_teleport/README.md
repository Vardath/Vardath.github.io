# Vardath – Universal Cargo Teleportation (v1.00, X4 9.00)

Native AI-script extension. **No Lua**, UI hooks, Bit library, Mod Support APIs, research, or disabling Protected UI Mode.

## Automatic behaviour

- Applies to **every player-owned S, M, L and XL ship running an AI trade or ware-exchange order**, including ships added to an existing saved game. No individual unlock or equipment item required.
- Normal trade orders: when a player ship travels to any valid station (player or NPC) or ship trade partner, it attempts to close to **30 km**, then skips docking and uses the game's original `execute_trade` transaction. Normal prices, trade offers, ware amounts and trade-result bookkeeping remain in the original script.
- Ship-to-ship ware-exchange orders: when **both ships are player-owned**, the active ship approaches and cargo can transfer directly within the same zone and 30 km, even across S/M and L/XL sizes. The passive ship keeps its native order wait. No dropped cargo crates needed on this special path.
- If no valid 30 km transfer can be made, the original game docking/transfer path remains in the script. No random stock balancing, manufacturing or stealing cargo.
- The player ship under *direct manual control* is not given an independent teleport UI button. AI orders run on pilot-controlled ships, not on the player piloting them directly.

## Installation

1. Fully remove the previous `cargo_teleportation` extension from both Steam Workshop subscriptions and local `extensions` if applicable.
2. Unzip `vardath_universal_cargo_teleport` as a single folder into the X4 `extensions` directory. Do not put the ZIP itself into `extensions`.
3. Keep **Protected UI Mode ON**, restart X4 and load your existing save. No new game required.
4. Issue a normal player-ship trade order to a station or a ware-exchange order between two owned ships. The actual order triggers teleportation when in range. Check the ship's cargo before/after.

## Compatibility and limitations

- Patches two vanilla AI scripts: `aiscripts/order.trade.perform.xml` and `aiscripts/order.trade.wareexchange.ship.xml`. Other mods patching the same routines might conflict.
- This is not a global anything-to-anything teleport or a global resource network: it honours existing trade/transfer orders and requires proximity (30 km, same zone). It does not add trading orders by itself.
- NPC-vs-NPC ship exchanges and stations without valid trade offers are unchanged.
- Static XML checks can verify that the patch matches reference script layout, but **X4 runtime testing is still necessary**. In particular, whether 9.00 permits `execute_trade` without docking for every ship/partner combination needs confirmation on your installation.
- There is no Lua, which avoids the `require('bit')` Protected UI failure in the removed third-party mod.
