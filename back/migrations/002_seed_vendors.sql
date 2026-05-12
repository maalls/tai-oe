-- Seed vendor entries for known brands
INSERT INTO vendor (name, email, phone, website, created_at, updated_at)
VALUES
  ('ARNOULD', NULL, NULL, 'https://www.heure-industrielle.com/61-arnould', now(), now()),
  ('BTICINO', NULL, NULL, 'https://www.bticino.com/', now(), now()),
  ('LEGRAND', NULL, NULL, 'https://www.legrand.fr/', now(), now()),
  ('MODELEC', NULL, NULL, 'https://www.modelec.com/fr', now(), now()),
  ('NETATMO', NULL, NULL, 'https://www.netatmo.com/fr-fr', now(), now()),
  ('SARLAM', NULL, NULL, NULL, now(), now()),
  ('YUASA', NULL, NULL, 'https://www.yuasa.com/fr/', now(), now()),
  ('ZUCCHINI', NULL, NULL, 'https://www.legrand.co.uk/en/ranges/zucchini', now(), now());
