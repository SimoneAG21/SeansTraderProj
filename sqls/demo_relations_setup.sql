-- Drop existing tables if they exist
DROP TABLE IF EXISTS trade_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS traders CASCADE;
DROP TABLE IF EXISTS telegram_messages CASCADE;

-- Create tables
CREATE TABLE traders (
    trader_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    trader_id INTEGER NOT NULL UNIQUE,
    bio TEXT,
    risk_level VARCHAR(50),
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id) ON DELETE CASCADE
);

CREATE TABLE trades (
    trade_id SERIAL PRIMARY KEY,
    trader_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    trade_date TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id) ON DELETE CASCADE
);

CREATE TABLE tags (
    tag_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE trade_tags (
    trade_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (trade_id, tag_id),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO traders (name, email) VALUES
('Alice Smith', 'alice@trading.com'),
('Bob Jones', 'bob@trading.com'),
('Charlie Brown', 'charlie@trading.com');

INSERT INTO profiles (trader_id, bio, risk_level) VALUES
(1, 'Experienced trader focusing on crypto', 'High'),
(2, 'New trader interested in forex', 'Low'),
(3, 'Swing trader with 5 years experience', 'Medium');

INSERT INTO trades (trader_id, symbol, amount, trade_date) VALUES
(1, 'BTC/USD', 5000.00, '2025-04-14T09:00:00+00:00'),
(1, 'ETH/USD', 2000.00, '2025-04-14T10:00:00+00:00'),
(2, 'EUR/USD', 1000.00, '2025-04-14T11:00:00+00:00'),
(3, 'AAPL', 3000.00, '2025-04-14T12:00:00+00:00'),
(3, 'TSLA', 1500.00, '2025-04-14T13:00:00+00:00');

INSERT INTO tags (name) VALUES
('Long'),
('Short'),
('Crypto'),
('Forex'),
('Stock');

INSERT INTO trade_tags (trade_id, tag_id) VALUES
(1, 1), (1, 3),
(2, 1), (2, 3),
(3, 2), (3, 4),
(4, 1), (4, 5),
(5, 2), (5, 5);