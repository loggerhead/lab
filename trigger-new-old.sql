-- http://www.postgresql.org/docs/9.2/static/plpgsql-trigger.html
DROP TABLE IF EXISTS foo CASCADE;
CREATE TABLE foo (
    tid serial PRIMARY KEY
);

CREATE OR REPLACE FUNCTION foo_t()
  RETURNS trigger
AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD; -- NEW is NULL
    ELSIF (TG_OP = 'UPDATE') THEN
        RETURN OLD; -- NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        RETURN NEW; -- OLD is NULL
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS foo_t ON foo;
CREATE TRIGGER foo_t BEFORE DELETE OR UPDATE OR INSERT ON foo
   FOR EACH ROW EXECUTE PROCEDURE foo_t(); 
