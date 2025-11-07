-- Script de création de table pour exemple SQLite
CREATE TABLE IF NOT EXISTS scannerresults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id INTEGER NOT NULL, 
    rank INTEGER NOT NULL, 
    contract_id INTEGER NOT NULL,
    contract_symbol TEXT NOT NULL, 
    contract_sectype TEXT NOT NULL,
    contract_currency TEXT NOT NULL,
    -- chiffres en lien avec le scanner => valeurs en lien avec le ranking du scanner
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now'),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_details TEXT NOT NULL,
    create_date  TEXT NOT NULL DEFAULT (datetime('now')),
    update_date  TEXT NOT NULL DEFAULT (datetime('now')
);

-- Table des ordres passés par les stratégies
-- Permet de suivre les ordres et leurs statuts. 
-- On pourra donc faire un suivi des gains/pertes
-- On pourra aussi vérifier ce qui n'est pas encore vendu afin de forcer une vente si besoin
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    order_details TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_buy REAL NOT NULL DEFAULT 0,
    amount_sell REAL,
    amount_currency TEXT NOT NULL, -- USD, EUR, etc. vient de la stratégie
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