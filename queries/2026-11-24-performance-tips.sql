-- Tips de rendimiento y queries comunes de diagnostico

-- Conexiones activas
SELECT pid, usename, application_name, state, query_start,
  NOW() - query_start AS duracion, left(query, 100) AS query_preview
FROM pg_stat_activity WHERE state != 'idle' ORDER BY duracion DESC;

-- Tablas con mas escrituras (candidatas a optimizar)
SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
FROM pg_stat_user_tables ORDER BY n_tup_upd + n_tup_del DESC LIMIT 10;

-- Indices no usados (candidatos a eliminar)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY tablename;

-- Bloat de tablas (espacio desperdiciado)
SELECT tablename,
  pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS total,
  pg_size_pretty(pg_relation_size(tablename::regclass)) AS table_only
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- VACUUM y ANALYZE para mantenimiento
VACUUM ANALYZE pedidos;
VACUUM ANALYZE productos;
