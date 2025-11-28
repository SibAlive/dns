from flask_apscheduler import APScheduler

from sheduler import cancel_expired_orders


def setup_scheduler(db, app) -> APScheduler:
    """Настраивает и возвращает экземпляр планировщика
        с зарегистрированными задачами."""
    scheduler = APScheduler()

    # Каждый час отменяет просроченные заказы
    scheduler.add_job(
        id='cancel_expired_orders',
        func=cancel_expired_orders,
        kwargs={'db': db, 'app': app},
        trigger='interval',
        hours=1
    )

    return scheduler