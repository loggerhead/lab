-- http://www.postgresql.org/docs/9.2/static/plpgsql-trigger.html
set client_min_messages = error;

DROP TABLE IF EXISTS foo CASCADE;
CREATE TABLE foo (
    tid serial PRIMARY KEY
);

CREATE OR REPLACE FUNCTION foo_t()
  RETURNS trigger
AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RAISE NOTICE 'delete op';
        RETURN OLD; -- NEW is NULL
    ELSIF (TG_OP = 'UPDATE') THEN
        RAISE NOTICE 'update op';
        RETURN OLD; -- NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        RAISE NOTICE 'insert op';
        RETURN NEW; -- OLD is NULL
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS foo_t ON foo;
CREATE TRIGGER foo_t BEFORE DELETE OR UPDATE OR INSERT ON foo
   FOR EACH ROW EXECUTE PROCEDURE foo_t(); 

insert into foo values (1);
insert into foo values (2);
update foo set tid = tid + 1;
delete from foo;
