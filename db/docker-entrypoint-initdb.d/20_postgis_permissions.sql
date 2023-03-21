CREATE EXTENSION IF NOT EXISTS postgis;
ALTER VIEW geometry_columns OWNER TO ckan;
ALTER TABLE spatial_ref_sys OWNER TO ckan;
