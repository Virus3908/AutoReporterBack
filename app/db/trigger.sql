CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применим к каждой таблице
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['tasks', 'convert', 'diarize', 'transcribe', 'report']
  LOOP
    EXECUTE format('
      CREATE TRIGGER trg_set_updated_at_%1$s
      BEFORE UPDATE ON %1$s
      FOR EACH ROW
      EXECUTE FUNCTION set_updated_at();
    ', tbl);
  END LOOP;
END $$;