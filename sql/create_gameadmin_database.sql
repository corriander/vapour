CREATE DATABASE gameadmin;

\c gameadmin;

CREATE SCHEMA fraps;

CREATE TABLE fraps.dataset (
    id serial PRIMARY KEY NOT NULL,
    filepath text UNIQUE NOT NULL,
    notes text
);
-- ALTER TABLE fraps.dataset ADD CONSTRAINT dataset_filepath_key UNIQUE (filepath);
-- ALTER TABLE fraps.dataset ADD COLUMN notes text;

DROP TABLE IF EXISTS fraps.frames;
CREATE TABLE fraps.frames (
    dataset_id bigint REFERENCES fraps.dataset (id),
    frame int NOT NULL,
    t_delta float NOT NULL,
    UNIQUE (dataset_id, frame)
);

COMMENT ON TABLE fraps.frames IS 'Each frame recorded by Fraps and the time delta (ms)';

CREATE OR REPLACE FUNCTION fraps.import_frames (p_path varchar(260), p_notes text DEFAULT NULL)
RETURNS void
AS
$DEF$

BEGIN

    DROP TABLE IF EXISTS pg_temp._import_frames;
    CREATE TEMPORARY TABLE pg_temp._import_frames (frame int, t_delta float);

    EXECUTE format(
                $$
                COPY pg_temp._import_frames
                FROM '%s' DELIMITER ',' CSV HEADER;
                $$,
                p_path
            );

       WITH dataset_insert AS (
                INSERT INTO fraps.dataset (filepath, notes)
                VALUES (p_path, p_notes)
                ON CONFLICT DO NOTHING
                RETURNING id
            )
     INSERT INTO fraps.frames
     SELECT dsi.id
          , frame
          , t_delta
       FROM dataset_insert dsi
          , pg_temp._import_frames
      WHERE dsi.id IS NOT NULL
      ORDER BY dsi.id
          , frame
         ON CONFLICT DO NOTHING
     ;

     REFRESH MATERIALIZED VIEW fraps.dataset_view;

END
$DEF$
LANGUAGE plpgsql
;

COMMENT ON FUNCTION fraps.import_frames(varchar(260)) IS 'Import *frametimes.csv generated by Fraps.';

-- Example usage:
-- SELECT fraps.import_frametimes('L:\data\fraps\fps\WolfNewOrder_x64 2017-03-19 10-07-16-62 frametimes.csv');

-- Remove data:
-- TRUNCATE fraps.frametimes;
-- DELETE FROM fraps.dataset;

DROP MATERIALIZED VIEW IF EXISTS fraps.dataset_view;
CREATE MATERIALIZED VIEW fraps.dataset_view AS
  WITH dataset_parsed AS (
           SELECT id
                , filepath
                , regexp_replace(filepath, '.*[\\/]([^ ]+).*$', '\1') AS exe
                , to_timestamp(
                     regexp_replace(
                         filepath,
                         '.*(\d\d\d\d-\d\d-\d\d \d\d-\d\d-\d\d-\d\d).*',
                         '\1'
                     ),
                     'YYYY-MM-DD HH24-MI-SS-MS'
                  ) AS t0
                , coalesce(notes, '')
             FROM fraps.dataset
       )
     , dataset_duration AS (
           SELECT ds.id
                , max(t_delta) * INTERVAL '1 millisecond' AS dt
             FROM fraps.frames fr
             JOIN dataset_parsed ds
               ON ds.id = fr.dataset_id
            GROUP BY ds.id
       )
SELECT t.*
     , t.t0 + dt AS tn
  FROM dataset_duration
  JOIN dataset_parsed t
 USING (id)
;


DROP FUNCTION IF EXISTS fraps.fps(bigint);
 CREATE OR REPLACE FUNCTION fraps.fps (p_id bigint)
RETURNS TABLE (
    second bigint,
    fps bigint
)
AS
$DEF$
BEGIN

RETURN QUERY
  WITH binned_frames AS (
           SELECT div(t_delta::integer, 1000)::bigint AS bin
                , *
             FROM fraps.frames
            WHERE dataset_id = p_id
       )
SELECT bin
     , count(*)
  FROM binned_frames
 WHERE bin != (SELECT max(bin) FROM binned_frames) -- last bin always partial by definition.
 GROUP BY bin
 ORDER BY bin
;

END
$DEF$
LANGUAGE plpgsql
;

-- GPU-Z data.
CREATE SCHEMA gpuz;

DROP TABLE IF EXISTS gpuz.sensor;
CREATE TABLE gpuz.sensor (
    t timestamp PRIMARY KEY NOT NULL,
    f_core float,
    f_mem float,
    temp float,
    speed_fan_pc smallint,
    speed_fan_rpm int,
    load smallint,
    mem_controller_load smallint,
    mem_usage_dedicated int,
    mem_usage_dynamic int,
    vddc float
);

COMMENT ON TABLE gpuz.sensor IS 'Frequencies (f_*) are [MHz], Temperature [degC], Mem. usage in [MiB], VDDC in [V]. The rest are [%].';

CREATE OR REPLACE FUNCTION gpuz.import_sensor (p_path varchar(260))
RETURNS void
AS
$DEF$
BEGIN

	CREATE TEMPORARY TABLE pg_temp._import (LIKE gpuz.sensor);

	EXECUTE format(
        $$COPY pg_temp._import FROM '%s' DELIMITER AS ',' NULL AS '-' CSV;$$,
        p_path
    );

	INSERT INTO gpuz.sensor
    SELECT *
      FROM pg_temp._import
    ON CONFLICT DO NOTHING;

    DROP TABLE pg_temp._import;

    REFRESH MATERIALIZED VIEW public.gpuz_data;

END
$DEF$
language plpgsql;

-- SELECT gpuz.import_sensor('L:\data\gpuz\sensor.log.csv');



-- In-situ data post-processing
-- ----------------------------
CREATE MATERIALIZED VIEW public.gpuz_data AS
  WITH differenced AS (
          SELECT *
               , (t - (lag(t, 1) OVER (ORDER BY t ASC))) AS t_delta
            FROM gpuz.sensor
       )
SELECT *
     , sum(CASE WHEN extract('epoch' FROM t_delta) < 30 THEN 0 ELSE 1 END) OVER (ORDER BY t) AS session_id
  FROM differenced
;

CREATE SCHEMA perfmon;

DROP TABLE IF EXISTS perfmon.proctime;
CREATE TABLE perfmon.proctime (
           t timestamp PRIMARY KEY NOT NULL,
           core0 float DEFAULT NULL,
           core1 float DEFAULT NULL,
           core2 float DEFAULT NULL,
           core3 float DEFAULT NULL
       )
;

CREATE OR REPLACE FUNCTION perfmon.import_proctime(p_path varchar)
RETURNS void
AS
$DEF$
BEGIN

       DROP TABLE IF EXISTS pg_temp._import_proctime;
     CREATE TEMPORARY TABLE pg_temp._import_proctime (LIKE perfmon.proctime INCLUDING DEFAULTS);

    EXECUTE format(
                $$
                COPY pg_temp._import_proctime
                FROM '%s' DELIMITER ',' HEADER NULL AS '-' CSV;
                $$,
                p_path
            );

     INSERT INTO perfmon.proctime
     SELECT *
       FROM pg_temp._import_proctime
      ORDER BY t
         ON CONFLICT DO NOTHING
;

END
$DEF$
LANGUAGE plpgsql
;
