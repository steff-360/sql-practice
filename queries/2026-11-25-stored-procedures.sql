-- Procedimientos almacenados y funciones en PL/pgSQL

-- Funcion: calcular descuento por volumen
CREATE OR REPLACE FUNCTION calcular_descuento(precio NUMERIC, cantidad INT)
RETURNS NUMERIC AS $$
BEGIN
  RETURN CASE
    WHEN cantidad >= 100 THEN precio * 0.80
    WHEN cantidad >= 50  THEN precio * 0.90
    WHEN cantidad >= 10  THEN precio * 0.95
    ELSE precio
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

SELECT nombre, precio, calcular_descuento(precio, 50) AS precio_con_descuento
FROM productos;

-- Procedimiento: procesar pedido completo
CREATE OR REPLACE PROCEDURE procesar_pedido(
    p_cliente_id INT, p_items JSONB
) LANGUAGE plpgsql AS $$
DECLARE
    v_pedido_id INT;
    v_item JSONB;
BEGIN
    INSERT INTO pedidos (cliente_id) VALUES (p_cliente_id) RETURNING id INTO v_pedido_id;
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unit)
        SELECT v_pedido_id,
               (v_item->>'producto_id')::INT,
               (v_item->>'cantidad')::INT,
               precio
        FROM productos WHERE id = (v_item->>'producto_id')::INT;
    END LOOP;
    COMMIT;
END;
$$;
