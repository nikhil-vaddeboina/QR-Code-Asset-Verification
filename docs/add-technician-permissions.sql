-- Manual fallback only. The START_ASSETVERIFY launcher adds this column during init-db.
-- Use this script once only if you are upgrading the schema manually.
-- Existing technicians keep the standard technician permissions until edited
-- in the admin portal; their NULL value is handled by the application.
ALTER TABLE `user`
    ADD COLUMN `permissions` JSON NULL;
