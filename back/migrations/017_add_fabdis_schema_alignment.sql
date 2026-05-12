-- Align FAB-DIS tables with schema expectations (safe to run multiple times)

ALTER TABLE IF EXISTS fabdis_arret
  ADD COLUMN IF NOT EXISTS refcialeass TEXT,
  ADD COLUMN IF NOT EXISTS marqueass TEXT;

ALTER TABLE IF EXISTS fabdis_substitution
  ADD COLUMN IF NOT EXISTS marquesub TEXT;

-- Add FAB-DIS marque-related indexes
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_cartouches') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_cartouches_carmarque ON fabdis_cartouches(carmarque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_article') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_article_marque ON fabdis_article(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_commerce') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_commerce_marque ON fabdis_commerce(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_logistique') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_logistique_marque ON fabdis_logistique(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_media') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_media_marque ON fabdis_media(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_reglementaire') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_reglementaire_marque ON fabdis_reglementaire(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_correspondance') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_correspondance_marque ON fabdis_correspondance(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_variante') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_variante_marque ON fabdis_variante(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_etim') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_etim_marque ON fabdis_etim(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_extension') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_extension_marque ON fabdis_extension(marque);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_arret') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_arret_marqueass ON fabdis_arret(marqueass);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_substitution') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_substitution_marquesub ON fabdis_substitution(marquesub);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'fabdis_pyramide') THEN
    CREATE INDEX IF NOT EXISTS idx_fabdis_pyramide_marquep ON fabdis_pyramide(marquep);
  END IF;
END $$;
