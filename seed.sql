
-- seven-tags-module/seed.sql
INSERT IGNORE INTO tags (slug, label) VALUES
('best-multibagger', 'Best Multibagger'),
('lowest-pe', 'Lowest PE'),
('high-volume', 'High Volume'),
('breakout-today', 'Breakout Today'),
('below-book-value', 'Below Book Value'),
('profit-jump', 'Profit Jump'),
('sales-jump', 'Sales Jump');

-- sample stocks
INSERT INTO stocks (symbol, name, price, change_pct, volume) VALUES
('RELIANCE', 'Reliance Industries', 2450.00, 1.25, 12003450),
('TCS', 'Tata Consultancy Services', 3888.50, -0.42, 950340),
('HDFCBANK', 'HDFC Bank', 1560.25, 0.88, 3200345)
ON DUPLICATE KEY UPDATE price=VALUES(price), change_pct=VALUES(change_pct), volume=VALUES(volume);

-- tag mapping examples
INSERT IGNORE INTO stock_tags (stock_id, tag_id)
SELECT s.id, t.id FROM stocks s JOIN tags t ON s.symbol='RELIANCE' AND t.slug IN ('best-multibagger','high-volume');
INSERT IGNORE INTO stock_tags (stock_id, tag_id)
SELECT s.id, t.id FROM stocks s JOIN tags t ON s.symbol='TCS' AND t.slug IN ('lowest-pe');
INSERT IGNORE INTO stock_tags (stock_id, tag_id)
SELECT s.id, t.id FROM stocks s JOIN tags t ON s.symbol='HDFCBANK' AND t.slug IN ('breakout-today','profit-jump');
