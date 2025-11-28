import logging
from datetime import datetime, timedelta

from services import CartService


logger = logging.getLogger(__name__)


def cancel_expired_orders(db, app):
    """Периодически отменяет не выкупленные заказы"""
    with app.app_context():
        cutoff = datetime.now() - timedelta(days=1)
        cart_service = CartService(db)

        expired_orders = cart_service.get_expired_orders(cutoff=cutoff)
        for order in expired_orders:
            cart_service.cancel_order(order_id=order.id)
            logger.info(f"Заказ {order.id} отменен")