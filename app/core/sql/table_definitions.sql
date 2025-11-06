-- Script de création de table pour exemple SQLite
CREATE TABLE IF NOT EXISTS scanner_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- strategy_id INTEGER NOT NULL,
    req_id INTEGER NOT NULL, 
    rank INTEGER NOT NULL, 
    contract_id INTEGER NOT NULL,
    contract_symbol TEXT NOT NULL, 
    contract_sectype TEXT NOT NULL,
    contract_currency TEXT NOT NULL,
    trading_class TEXT NOT NULL,
    exchange TEXT,
    -- chiffres en lien avec le scanner => valeurs en lien avec le ranking du scanner
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now'))
    -- FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    strategy_details TEXT NOT NULL,
    is_actif BOOLEAN NOT NULL DEFAULT 1,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Table des ordres passés par les stratégies
-- Permet de suivre les ordres et leurs statuts. 
-- On pourra donc faire un suivi des gains/pertes
-- On pourra aussi vérifier ce qui n'est pas encore vendu afin de forcer une vente si besoin
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    order_details TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_buy REAL NOT NULL DEFAULT 0,
    amount_sell REAL,
    amount_currency TEXT NOT NULL, -- USD, EUR, etc. vient de la stratégie
    instrument_price REAL NOT NULL,
    order_stop_loss REAL NOT NULL,
    order_take_profit REAL NOT NULL,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- Tables à creer pour l'application HT-IBKR-Integrations   
-- MARKET SCANNER DATA  
-- scannerData. reqId: 7, rank: 0, contractDetails: ConId: 505405587, Symbol: RANI, SecType: STK, LastTradeDateOrContractMonth: , Strike: 0, Right: , Multiplier: , Exchange: SMART, PrimaryExchange: , Currency: USD, LocalSymbol: RANI, TradingClass: NMS, IncludeExpired: False, SecIdType: , SecId: , Description: , IssuerId: Combo:,NMS,0,,,0,0,,,,,,,,,,0,,,,0,None,,,,,,,,False,False,0,False,,,,,False,,,,,None, distance: , benchmark: , projection: , legsStr: .
-- ORDRES 
-- STRATEGIES ? => dans le fichier de configuration. Mais si on veut faire un lien entre les données du scanner et les résultats de ordres
--    il serait pas mal d'avoir les stratégies en DB aussi.