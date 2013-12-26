-- #python code
-- cnt = psycopg2.connect(...)
-- cur = cnt.cursor()
-- cur.execute('select bar(%s)', (['a', 'b', 'c'], ))
-- cnt.commit()

create table foo (
    id serial primary key,
    name varchar(33)
);

create or replace function bar (args varchar[]) 
  returns void as
$$
declare
    _name varchar;
begin
    foreach _name in ARRAY $1
    loop
        insert into foo (name) values (_name);
    end loop;
end;
$$ language plpgsql;
