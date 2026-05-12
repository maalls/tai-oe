-- Postgres schema for Supabase: ETIM + FAB-DIS seller data
-- Safe to run multiple times: uses CREATE TABLE IF NOT EXISTS
-- Note: adjust VARCHAR sizes as needed; using TEXT for flexibility.
-- 
-- ETIM Reference: Based on ETIM-9.0-ALL-SECTORS-CSV-METRIC-EI-2022-12-05
-- Official ETIM 9.0 standard structure (do NOT use modified ETIM/ folder)

-- =====================
-- ETIM Reference Schema
-- =====================

CREATE TABLE IF NOT EXISTS etim_art_group (
  artgroupid TEXT PRIMARY KEY,
  groupdesc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etim_art_class (
  artclassid TEXT PRIMARY KEY,
  artgroupid TEXT REFERENCES etim_art_group(artgroupid) ON UPDATE CASCADE ON DELETE RESTRICT,
  artclassdesc TEXT NOT NULL,
  artclassversion TEXT,
  artclassversiondate DATE
);

CREATE TABLE IF NOT EXISTS etim_feature (
  featureid TEXT PRIMARY KEY,
  featuredesc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etim_unit (
  unitofmeasid TEXT PRIMARY KEY,
  unitdesc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etim_value (
  valueid TEXT PRIMARY KEY,
  valuedesc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etim_art_class_feature_map (
  artclassfeaturenr BIGINT PRIMARY KEY,
  artclassid TEXT NOT NULL REFERENCES etim_art_class(artclassid) ON UPDATE CASCADE ON DELETE CASCADE,
  featureid TEXT NOT NULL REFERENCES etim_feature(featureid) ON UPDATE CASCADE ON DELETE CASCADE,
  featuretype CHAR(1) NOT NULL CHECK (featuretype IN ('A','N','R','L')),
  unitofmeasid TEXT REFERENCES etim_unit(unitofmeasid) ON UPDATE CASCADE ON DELETE SET NULL,
  sortnr INT
);

CREATE INDEX IF NOT EXISTS idx_etim_acfm_class ON etim_art_class_feature_map(artclassid);
CREATE INDEX IF NOT EXISTS idx_etim_acfm_feature ON etim_art_class_feature_map(featureid);

CREATE TABLE IF NOT EXISTS etim_art_class_feature_value_map (
  artclassfeaturevaluenr BIGINT PRIMARY KEY,
  artclassfeaturenr BIGINT NOT NULL REFERENCES etim_art_class_feature_map(artclassfeaturenr) ON UPDATE CASCADE ON DELETE CASCADE,
  valueid TEXT NOT NULL REFERENCES etim_value(valueid) ON UPDATE CASCADE ON DELETE CASCADE,
  sortnr INT
);

CREATE INDEX IF NOT EXISTS idx_etim_acfvm_acfnr ON etim_art_class_feature_value_map(artclassfeaturenr);
CREATE INDEX IF NOT EXISTS idx_etim_acfvm_value ON etim_art_class_feature_value_map(valueid);

CREATE TABLE IF NOT EXISTS etim_art_class_synonym (
  artclassid TEXT NOT NULL REFERENCES etim_art_class(artclassid) ON UPDATE CASCADE ON DELETE CASCADE,
  classsynonym TEXT NOT NULL,
  PRIMARY KEY (artclassid, classsynonym)
);

-- B00_CARTOUCHES: file-level metadata
CREATE TABLE IF NOT EXISTS fabdis_cartouches (
  nscript TEXT,
  cartyp TEXT,
  datedit DATE,
  dateappli DATE,
  deft TEXT,
  dev TEXT,
  carinfo TEXT,
  carinfourlt TEXT,
  nrb01 INT,
  nrc05 INT,
  fabdisv TEXT,
  lang TEXT,
  decsep TEXT,
  groupe TEXT,
  fabricant TEXT,
  carmarque TEXT,
  carmarqueurlt TEXT,
  carnom TEXT,
  carprenom TEXT,
  caremail TEXT,
  legal TEXT,
  legalurlt TEXT,
  PRIMARY KEY (carmarque)
);

-- Articles anchor: MARQUE + REFCIALE composite key


CREATE TABLE IF NOT EXISTS fabdis_article (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  PRIMARY KEY (marque, refciale),
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- B01_COMMERCE: commercial data per article
CREATE TABLE IF NOT EXISTS fabdis_commerce (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  ctyp TEXT,
  gtin TEXT,
  refinfor TEXT,
  gamme TEXT,
  fonction TEXT,
  libelle40 TEXT,
  libelle80 TEXT,
  libelle240 TEXT,
  datetarif DATE,
  tarif NUMERIC,
  tarifd NUMERIC,
  qt NUMERIC,
  tva NUMERIC,
  ub TEXT,
  qmc NUMERIC,
  mul NUMERIC,
  qmv NUMERIC,
  qmvt TEXT,
  qpki TEXT,
  uc TEXT,
  uccoef NUMERIC,
  st TEXT,
  delai NUMERIC,
  edi TEXT,
  dug TEXT,
  sta TEXT,
  dateprev DATE,
  douane TEXT,
  mkt1 TEXT,
  mkt1l TEXT,
  mkt2 TEXT,
  mkt2l TEXT,
  mkt3 TEXT,
  mkt3l TEXT,
  mkt4 TEXT,
  mkt4l TEXT,
  mkt5 TEXT,
  mkt5l TEXT,
  fam1 TEXT,
  fam1l TEXT,
  fam2 TEXT,
  fam2l TEXT,
  fam3 TEXT,
  fam3l TEXT,
  PRIMARY KEY (marque, refciale),
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- B02_LOGISTIQUE: logistics & packaging data
CREATE TABLE IF NOT EXISTS fabdis_logistique (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  ltyp TEXT,
  lcode TEXT,
  lqte NUMERIC,
  lnum TEXT,
  qc NUMERIC,
  qct NUMERIC,
  lgtin TEXT,
  haut NUMERIC,
  hautu TEXT,
  larg NUMERIC,
  largu TEXT,
  prof NUMERIC,
  profu TEXT,
  poids NUMERIC,
  poidsu TEXT,
  vol NUMERIC,
  volu TEXT,
  diam NUMERIC,
  diamu TEXT,
  sect NUMERIC,
  sectu TEXT,
  linfo TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- B03_MEDIA: marketing/media assets and texts
CREATE TABLE IF NOT EXISTS fabdis_media (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  mtyp TEXT,
  mcib TEXT,
  mnum TEXT,
  mcode TEXT,
  mlang TEXT,
  minfo TEXT,
  mval TEXT,
  mvu TEXT,
  mtexte TEXT,
  mnom TEXT,
  murl TEXT,
  murlt TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- B04_REGLEMENTAIRE: regulatory documents
CREATE TABLE IF NOT EXISTS fabdis_reglementaire (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  rtyp TEXT,
  rflag TEXT,
  rnum TEXT,
  rcode1 TEXT,
  rcode2 TEXT,
  rcode3 TEXT,
  rqte NUMERIC,
  rpct NUMERIC,
  rdate DATE,
  rval TEXT,
  rvu TEXT,
  rtexte TEXT,
  rnom TEXT,
  rurl TEXT,
  rurlt TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- C02_CORRESPONDANCE: cross-sell / upsell mappings
CREATE TABLE IF NOT EXISTS fabdis_correspondance (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  cortyp TEXT,
  cornum INT,
  corq TEXT,
  refciale_cor TEXT,
  marque_cor TEXT,
  corlot TEXT,
  coroue TEXT,
  corinfo TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- C03_VARIANTE: variants and option codes
CREATE TABLE IF NOT EXISTS fabdis_variante (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  vcode TEXT,
  vcodelibelle TEXT,
  vtyp TEXT,
  variante TEXT,
  vfabdis TEXT,
  vvaleur TEXT,
  vunite TEXT,
  vnumv INT,
  vnumr INT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- C04_ETIM: ETIM classification mapping for article features
CREATE TABLE IF NOT EXISTS fabdis_etim (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  artclassid TEXT REFERENCES etim_art_class(artclassid) ON UPDATE CASCADE ON DELETE SET NULL,
  featureid TEXT REFERENCES etim_feature(featureid) ON UPDATE CASCADE ON DELETE SET NULL,
  fvalue TEXT,
  groupdesc TEXT,
  artclassdesc TEXT,
  featuredesc TEXT,
  valuedesc TEXT,
  unitdesc TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- F01_PYRAMIDE: marketing taxonomy hierarchy
CREATE TABLE IF NOT EXISTS fabdis_pyramide (
  niv INT,
  mktc TEXT,
  mkt TEXT,
  mktl TEXT,
  gammep TEXT,
  marquep TEXT
);

-- C01_EXTENSION: additional info linked to articles
CREATE TABLE IF NOT EXISTS fabdis_extension (
  marque TEXT NOT NULL,
  refciale TEXT NOT NULL,
  etyp TEXT,
  eflag TEXT,
  enum TEXT,
  ecode1 TEXT,
  ecode2 TEXT,
  eqte NUMERIC,
  epct NUMERIC,
  edate DATE,
  eval1 TEXT,
  evu1 TEXT,
  eval2 TEXT,
  evu2 TEXT,
  etexte TEXT,
  enom TEXT,
  eurl TEXT,
  eurlt TEXT,
  FOREIGN KEY (marque, refciale) REFERENCES fabdis_article(marque, refciale) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (marque) REFERENCES fabdis_cartouches(carmarque) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- C05_ARRET: end-of-life / discontinuation
CREATE TABLE IF NOT EXISTS fabdis_arret (
  mqerefarret TEXT,
  refarret TEXT PRIMARY KEY,
  atyp TEXT,
  adate DATE,
  refcialeass TEXT,
  marqueass TEXT,
  acode TEXT,
  aqte NUMERIC,
  aval TEXT,
  avu TEXT,
  atexte TEXT,
  anom TEXT,
  aurl TEXT,
  aurlt TEXT
);

-- C06_SUBSTITUTION: substitution mapping old→new
CREATE TABLE IF NOT EXISTS fabdis_substitution (
  mqerefold TEXT,
  refold TEXT NOT NULL,
  refcialesub TEXT NOT NULL,
  marquesub TEXT,
  styp TEXT,
  sinfo TEXT,
  sqd TEXT,
  sqb TEXT,
  slot TEXT,
  spct NUMERIC,
  PRIMARY KEY (refold, refcialesub)
);


-- Additional FAB-DIS sheets declared below.

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_fabdis_commerce_gtin ON fabdis_commerce(gtin);
CREATE INDEX IF NOT EXISTS idx_fabdis_media_murl ON fabdis_media(murl);
CREATE INDEX IF NOT EXISTS idx_fabdis_logistique_lgtin ON fabdis_logistique(lgtin);

CREATE INDEX IF NOT EXISTS idx_fabdis_cartouches_carmarque ON fabdis_cartouches(carmarque);
CREATE INDEX IF NOT EXISTS idx_fabdis_article_marque ON fabdis_article(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_commerce_marque ON fabdis_commerce(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_logistique_marque ON fabdis_logistique(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_media_marque ON fabdis_media(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_reglementaire_marque ON fabdis_reglementaire(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_correspondance_marque ON fabdis_correspondance(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_variante_marque ON fabdis_variante(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_etim_marque ON fabdis_etim(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_extension_marque ON fabdis_extension(marque);
CREATE INDEX IF NOT EXISTS idx_fabdis_arret_marqueass ON fabdis_arret(marqueass);
CREATE INDEX IF NOT EXISTS idx_fabdis_substitution_marquesub ON fabdis_substitution(marquesub);
CREATE INDEX IF NOT EXISTS idx_fabdis_pyramide_marquep ON fabdis_pyramide(marquep);

 
