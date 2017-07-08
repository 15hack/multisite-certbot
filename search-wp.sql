select table_schema, table_name wp_blogs from (
  select table_schema, table_name, count(*) N from information_schema.COLUMNS where
  column_name in ('blog_id', 'site_id', 'domain') and table_name like '%blogs%'group by table_schema, table_name
) T1 where T1.N=3;
