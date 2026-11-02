-- Demo records use the application's deterministic Python seeder so password hashes,
-- timestamps, database IDs, and QR files stay in sync. After running schema.sql, use:
--   flask --app app setup-demo
-- This creates the admin account using ADMIN_PASSWORD (default admin123), 100 assets,
-- 180 linked verification events, and one reproducible QR PNG per asset.
-- The seeder is idempotent and avoids duplicating a populated demo database.
SELECT 'Run flask --app app setup-demo to create demo records and QR labels.' AS next_step;
