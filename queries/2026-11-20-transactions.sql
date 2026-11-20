-- Transacciones: ACID, SAVEPOINT, ROLLBACK

-- Transaccion de pago de pedido
BEGIN;
  -- Verificar stock disponible
  SELECT id, stock FROM productos WHERE id = 1 FOR UPDATE;

  -- Descontar stock
  UPDATE productos SET stock = stock - 2 WHERE id = 1 AND stock >= 2;

  -- Si no hubo cambio, rollback
  -- (manejo en aplicacion: verificar rowcount)

  -- Actualizar estado del pedido
  UPDATE pedidos SET estado = 'pagado' WHERE id = 1;

  -- Registrar en log de pagos (tabla no mostrada)
  INSERT INTO pagos (pedido_id, monto, metodo) VALUES (1, 150000, 'tarjeta');

COMMIT;

-- SAVEPOINT para rollback parcial
BEGIN;
  INSERT INTO clientes (nombre, email) VALUES ('Test', 'test@test.com');
  SAVEPOINT sp1;

  INSERT INTO pedidos (cliente_id, estado) VALUES (currval('clientes_id_seq'), 'pendiente');
  -- Si algo falla:
  ROLLBACK TO sp1;
  -- continuar sin el pedido pero con el cliente

COMMIT;
