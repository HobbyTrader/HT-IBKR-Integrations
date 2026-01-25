-- Script de création de table pour exemple SQLite
-- Table des stratégies de trading
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    strategy_tags TEXT,
    strategy_details TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Script de création de table pour exemple SQLite
CREATE TABLE IF NOT EXISTS scanner_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_key TEXT NOT NULL,
    strategy_id INTEGER NOT NULL,
    req_id INTEGER NOT NULL, 
    rank INTEGER NOT NULL, 
    contract_id INTEGER NOT NULL,
    contract_symbol TEXT NOT NULL, 
    contract_sectype TEXT NOT NULL,
    contract_currency TEXT NOT NULL,
    contract_trading_class TEXT NOT NULL,
    contract_exchange TEXT,
    is_order_candidate BOOLEAN NOT NULL DEFAULT 0,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- Table des ordres passés par les stratégies
-- Permet de suivre les ordres et leurs statuts. 
-- On pourra donc faire un suivi des gains/pertes
-- On pourra aussi vérifier ce qui n'est pas encore vendu afin de forcer une vente si besoin
CREATE TABLE IF NOT EXISTS market_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    strategy_id INTEGER NOT NULL,
    order_contract_id INTEGER NOT NULL,
    order_symbol TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_quantity INTEGER NOT NULL DEFAULT 0,
    order_currency TEXT NOT NULL, -- USD, EUR, etc. vient de l'instrument
    order_price REAL,
    order_type TEXT NOT NULL,
    order_action TEXT NOT NULL,
    order_parent_id INTEGER DEFAULT 0,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- Table des exécutions d'ordres
-- Permet de suivre les exécutions des ordres passés
-- Utile pour le calcul des PnL et le suivi des positions
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL,
    order_id INTEGER NOT NULL,
    side TEXT NOT NULL,
    shares REAL NOT NULL,
    price REAL NOT NULL,
    execution_time TEXT NOT NULL,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (order_id) REFERENCES market_orders(order_id)
);

-- Table des données historiques des instruments
-- Permet de stocker les données historiques pour analyse et backtesting
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    bar_time TEXT NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume INTEGER NOT NULL,
    wap REAL DEFAULT 0,
    bar_count INTEGER DEFAULT 0 ,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now'))
);
