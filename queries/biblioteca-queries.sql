-- Consultas de practica sobre el schema de biblioteca

-- 1. Libros disponibles con nombre del autor
SELECT
    l.titulo,
    a.nombre AS autor,
    l.genero,
    l.publicado
FROM libros l
JOIN autores a ON l.autor_id = a.id
WHERE l.disponible = TRUE
ORDER BY l.publicado DESC;

-- 2. Cantidad de libros por autor
SELECT
    a.nombre,
    COUNT(l.id) AS total_libros
FROM autores a
LEFT JOIN libros l ON l.autor_id = a.id
GROUP BY a.id, a.nombre
ORDER BY total_libros DESC;

-- 3. Usuarios con prestamos activos
SELECT
    u.nombre,
    u.email,
    COUNT(p.id) AS prestamos_activos
FROM usuarios u
JOIN prestamos p ON p.usuario_id = u.id
WHERE p.devuelto = FALSE
GROUP BY u.id, u.nombre, u.email;

-- 4. CTE: libros nunca prestados
WITH prestados AS (
    SELECT DISTINCT libro_id FROM prestamos
)
SELECT l.titulo, a.nombre AS autor
FROM libros l
JOIN autores a ON l.autor_id = a.id
WHERE l.id NOT IN (SELECT libro_id FROM prestados);

-- 5. Window function: ranking de libros mas prestados
SELECT
    l.titulo,
    COUNT(p.id) AS veces_prestado,
    RANK() OVER (ORDER BY COUNT(p.id) DESC) AS ranking
FROM libros l
LEFT JOIN prestamos p ON p.libro_id = l.id
GROUP BY l.id, l.titulo;
