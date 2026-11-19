-- Schema: Sistema de Biblioteca
-- PostgreSQL

CREATE TABLE IF NOT EXISTS autores (
    id         SERIAL PRIMARY KEY,
    nombre     VARCHAR(100) NOT NULL,
    pais       VARCHAR(60),
    nacimiento DATE
);

CREATE TABLE IF NOT EXISTS libros (
    id          SERIAL PRIMARY KEY,
    titulo      VARCHAR(200) NOT NULL,
    autor_id    INT REFERENCES autores(id) ON DELETE SET NULL,
    genero      VARCHAR(60),
    publicado   INT,
    disponible  BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id        SERIAL PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL,
    email     VARCHAR(150) UNIQUE NOT NULL,
    registrado TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prestamos (
    id          SERIAL PRIMARY KEY,
    libro_id    INT REFERENCES libros(id),
    usuario_id  INT REFERENCES usuarios(id),
    fecha_out   DATE DEFAULT CURRENT_DATE,
    fecha_in    DATE,
    devuelto    BOOLEAN DEFAULT FALSE
);

-- Indices para mejorar performance
CREATE INDEX idx_libros_autor     ON libros(autor_id);
CREATE INDEX idx_prestamos_libro  ON prestamos(libro_id);
CREATE INDEX idx_prestamos_usuario ON prestamos(usuario_id);

-- Datos de prueba
INSERT INTO autores (nombre, pais, nacimiento) VALUES
  ('Gabriel Garcia Marquez', 'Colombia', '1927-03-06'),
  ('Isabel Allende',          'Chile',   '1942-08-02'),
  ('Jorge Luis Borges',       'Argentina','1899-08-24');

INSERT INTO libros (titulo, autor_id, genero, publicado) VALUES
  ('Cien anos de soledad',   1, 'Realismo magico', 1967),
  ('El amor en los tiempos del colera', 1, 'Novela', 1985),
  ('La casa de los espiritus', 2, 'Realismo magico', 1982),
  ('Ficciones',               3, 'Cuento',  1944);
