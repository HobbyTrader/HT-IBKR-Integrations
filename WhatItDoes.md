# What `app/main.py` Does

This document explains the runtime behavior of `app/main.py`, the sequence of operations it performs, and how it interacts with services and data objects.

## 1. High-Level Role

`app/main.py` is the orchestration entry point for the scanner and order workflow.

It does the following:
- Loads active strategies (or filtered by tags from CLI args).
- Runs a market scanner for each strategy.
- Loads short historical market data for each scanned instrument.
- Applies strategy logic to decide candidate instruments.
- Places bracket orders for candidates.
- Starts an asset watcher process for successfully placed orders.
- Cleans scanner candidate data and refreshes order status in DB.
- Optionally repeats this flow on a scheduler interval.

## 2. Startup and Configuration

### Logger and config
At startup, `main()` logs:
- application start
- active config file path (`get_active_config_path()`)

The scheduler behavior is controlled by `load_config_scheduler()` from `app.utils`.

### CLI arguments
`get_arguments()` supports optional positional args:
- `TAGS` as comma-separated values (example: `US,STOCK`)
- `ALL_MATCH` (`true` or `false`) to control tag matching mode

If no args are provided, it runs with all active strategies.

## 3. Strategy Selection

`get_strategies()` uses `StrategyDTO`:
- with tags: `get_strategies_by_tags(tags, all_must_match)`
- without tags: `get_active_strategies()`

Each selected strategy is processed independently.

## 4. Per-Strategy Execution Flow

For each strategy, `main()` does this in order:

1. Generate an execution key (`exec_key`) for scanner/result correlation.
2. Count today's non-retryable BUY orders for that strategy using `MarketOrderDTO`.
3. Skip strategy immediately if `max_trades_per_day` is already reached.
4. Fetch scanner results using `ScannerService`.
5. Process scanner instruments one by one until the strategy limit is hit.

## 5. Per-Instrument Processing

For each scanned instrument:

1. **Daily limit check**
   - If strategy already reached `max_trades_per_day`, stop processing more instruments.

2. **Duplicate BUY guard (DB-based)**
   - `has_buy_order_today()` checks `market_orders` for same contract id.
   - BUY orders in retryable terminal statuses are ignored:
     - `REJECTED`, `CANCELLED`, `APICANCELLED`, `INACTIVE`
   - If a non-retryable BUY exists, instrument is skipped.

3. **In-process duplicate guard**
   - `_instrument_candidate_ids` avoids placing multiple orders for the same instrument in one run.

4. **Market data load**
   - `MarketService.get_historical_day_data()` fetches short-term historical bars.
   - Bars are attached to the `Instrument` instance.

5. **Strategy evaluation**
   - `strategy.apply_strategy_on_instrument(instrument)` determines candidacy.
   - Candidate flag and computed fields (market price, quantity, SL/TP) are set on instrument.

6. **Persist candidate flag async**
   - `update_scanner_result_candidate()` calls `ScannerDTO.set_order_candidate(...)` in a background thread.

7. **Order placement for candidates only**
   - `OrderService.place_bracket_order(instrument)` places parent + target + stop orders.
   - If placement succeeds, watcher process is launched.

8. **Launch watcher (subprocess)**
   - `launch_asset_watcher()` starts `python -m app.asset_watcher` with:
     - encoded instrument payload
     - encoded strategy payload
     - generated watcher client id (`--client-id`)
   - A unique client id is generated to avoid IB API connection conflicts.

9. **Update counters**
   - Add instrument id to `_instrument_candidate_ids`.
   - Increment `placed_orders_today`.

## 6. End-of-Strategy Cleanup

After instrument loop finishes for a strategy:
- `clean_non_candidates(exec_key)` removes non-candidates from scanner result storage.
- `update_order_status()` refreshes open/completed order status from IB via `OrderService`.

## 7. Scheduler Behavior (`run_scheduler()`)

`run_scheduler()` reads scanner scheduler config:
- If disabled: run `main()` once and stop.
- If enabled: run `main()`, wait configured interval, repeat until stop event is set.

## 8. Service Interaction Map

`main.py` orchestrates these services:

- `ScannerService`
  - Sends scanner subscription request to IB API.
  - Returns matching instruments for the strategy.

- `MarketService`
  - Requests historical bar data for each instrument.
  - Populates instrument history used by strategy logic.

- `OrderService`
  - Places bracket orders for candidates.
  - Retrieves active/completed orders for status synchronization.

- `StrategyDTO`, `ScannerDTO`, `MarketOrderDTO`
  - Strategy retrieval and filtering.
  - Scanner candidate persistence/cleanup.
  - Duplicate-order and daily-limit checks against DB.

## 9. Example Walkthrough Using `Stock_us.json`

Strategy file: `app/strategies/Stock_us.json`

Important parameters used by runtime:
- `scanCode`: `HIGH_OPEN_GAP`
- `locationCode`: `STK.US.MAJOR`
- `filter_options`: volume/price/open-gap filters
- `maxResults`: `50`
- `max_trades_per_day`: `5`
- `increase_position_candidate_percentage`: `0.5`
- `stop_loss_percent`: `95.0`
- `take_profit_percent`: `110.0`

A typical run behaves like this:

1. Strategy `US Stock High Open Gap Scan` is loaded.
2. Scanner requests top US stocks with high open gaps and configured filters.
3. For each result, history is fetched and the strategy computes candidate conditions.
4. If candidate and not duplicate, bracket order is placed.
5. Stop-loss and take-profit are derived from strategy percentages.
6. Asset watcher subprocess is started for the instrument using a dedicated IB client id.
7. Processing stops once 5 non-retryable BUY orders are placed for the day.

## 10. Notes and Current Safeguards

- Duplicate BUY prevention is database-backed (same contract/day).
- Daily trade cap is strategy-specific and database-backed.
- Rejected/cancelled/inactive BUY orders do not block retries.
- Watcher subprocess receives a unique client id to avoid IB session collisions.

## 11. What `asset_watcher` Does After a Buy

When `main.py` places a bracket order successfully (`order_placed == True`), it starts a dedicated watcher process for that instrument:

```bash
python -m app.asset_watcher --instrument-b64 ... --strategy-b64 ... --client-id ...
```

### Inputs passed from `main.py`

- `--instrument-b64`: base64 JSON payload of the bought instrument
- `--strategy-b64`: base64 JSON payload of the strategy context
- `--client-id`: unique IB API client id for this watcher process

The watcher uses this dedicated `clientId` so it does not collide with the main process IB connection.

### Runtime behavior inside `asset_watcher`

1. **Decode arguments**
   - Parses instrument and strategy payloads.
   - If instrument payload is invalid/missing, watcher stops immediately.

2. **Refresh order statuses from IB**
   - Calls `OrderService(clientId=...)` and requests:
     - active orders (`get_active_orders()`)
     - completed orders (`get_completed_orders()`)
   - This updates order status state in DB through existing order callbacks.

3. **Load instrument orders from DB**
   - Queries `MarketOrderDTO.get_market_orders_by_contract_id_today(instrument.id)`.
   - Logs the number of orders found for that instrument.

4. **Detect status changes**
   - Keeps an in-memory `_order_status_cache`.
   - Logs only when an order status changed since the previous watcher cycle.

5. **Stop conditions**
   - Stops if no orders are found anymore for that instrument.
   - Stops if all orders are in terminal states:
     - `Filled`, `Cancelled`, `ApiCancelled`, `Inactive`

### Watcher scheduler loop

- Controlled by `config.scheduler.watcher`.
- If disabled, watcher runs once and exits.
- If enabled, watcher repeats every configured interval (default 300s) until one stop condition is met.

### Practical effect

After buy/order placement, watcher acts as a lightweight per-instrument order monitor:
- it synchronizes IB order state to local storage,
- logs status transitions,
- and exits automatically when no active order remains.

## 12. Partial Sell Rules and Bracket Adaptation

### What `asset_watcher` currently does regarding sells

At the moment, `asset_watcher` does not execute partial sells and does not modify open bracket child orders.
Its current behavior is monitoring and synchronization only:
- refresh order status from IB,
- track order status transitions in logs,
- stop when all orders are terminal.

### Strategy parameters related to partial sells

The strategy model includes partial-sell parameters in `details.partial_sell_rules`:
- `target_percentage`
- `quantity_percentage`
- `stop_loss_adjustment_percentage`

Example from `Stock_us.json`:
- Rule 1: target 30%, sell 30%, stop-loss adjustment 0%
- Rule 2: target 70%, sell 40%, stop-loss adjustment 5%

These parameters are currently defined in config/schema and available in the `Strategy` object, but no runtime logic in `main.py` or `asset_watcher.py` applies them yet.

### How sells are currently executed in the codebase

Current sell execution path is in `close_open_positions.py`:
- it cancels existing orders for a contract,
- then submits market sell orders for open positions.

This is a close-position workflow, not a staged partial-take-profit workflow tied to watcher events.

### Bracket adaptation status after partial sells

Current implementation status:
- automatic bracket adaptation after a partial sell is not implemented.
- no automatic resize of remaining take-profit/stop-loss order quantities is done.
- no automatic stop-loss repricing based on `stop_loss_adjustment_percentage` is done.

### Expected behavior when implemented (target design)

When partial-sell logic is implemented, the watcher (or another coordinator) should:
1. detect fill progress against each `partial_sell_rules` target,
2. submit a partial sell quantity from `quantity_percentage`,
3. cancel/replace remaining bracket children so quantities match remaining position,
4. adjust stop price according to `stop_loss_adjustment_percentage`,
5. persist all new order IDs/status transitions in `market_orders`.

This target behavior is documented here for clarity, but is not yet active in current runtime.
