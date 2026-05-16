"""
app/tasks/rollup.py — Tarea de rollup diario de analytics.

Responsabilidades:
1. Al arrancar: rellena días faltantes (catchup)
2. Loop continuo: ejecuta rollup a medianoche UTC cada día
3. Usa asyncio puro — sin dependencias externas (Celery, APScheduler, etc.)
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from app.logger import get_logger
from app.services.analytics_service import AnalyticsService

logger = get_logger("rollup_task")


class RollupTask:
    """
    Tarea de fondo que corre rollup diario a medianoche UTC.
    Se registra como asyncio.Task en el lifespan de FastAPI.
    """

    def __init__(self, analytics: AnalyticsService):
        self.analytics = analytics
        self.running   = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """
        Lanza la tarea de fondo.
        Primero hace catchup, luego entra al loop de medianoche.
        """
        self.running = True
        self._task   = asyncio.create_task(self._run(), name="rollup_task")
        logger.info("rollup_task_scheduled")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("rollup_task_stopped")

    async def _run(self):
        """Loop principal de la tarea."""
        # 1. Catchup al arrancar — rellena días faltantes
        try:
            logger.info("rollup_catchup_starting")
            filled = await self.analytics.catchup_missing_days(days=30)
            logger.info("rollup_catchup_done", days_filled=filled)
        except Exception as e:
            logger.error("rollup_catchup_error", error=str(e))

        # 2. También rollup de ayer si no existe (puede pasar al reiniciar al final del día)
        try:
            yesterday = date.today() - timedelta(days=1)
            await self.analytics.run_daily_rollup(yesterday)
        except Exception as e:
            logger.warning("rollup_yesterday_error", error=str(e))

        # 3. Loop: esperar hasta medianoche UTC y ejecutar rollup del día anterior
        while self.running:
            try:
                seconds_until_midnight = self._seconds_until_midnight_utc()
                logger.info(
                    "rollup_next_execution_scheduled",
                    seconds_until_midnight=round(seconds_until_midnight),
                    next_run_utc=str(
                        datetime.now(timezone.utc).replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ) + timedelta(days=1)
                    ),
                )

                # Dormir hasta medianoche UTC (o hasta que se cancele)
                await asyncio.sleep(seconds_until_midnight + 5)  # +5s de margen

                if not self.running:
                    break

                # Ejecutar rollup del día que acaba de terminar (ayer en UTC)
                rollup_date = date.today() - timedelta(days=1)
                logger.info("rollup_midnight_trigger", target_date=str(rollup_date))

                await self.analytics.run_daily_rollup(rollup_date)

                logger.info("rollup_midnight_complete", target_date=str(rollup_date))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("rollup_loop_error", error=str(e))
                # En caso de error, reintentar en 5 minutos
                await asyncio.sleep(300)

    @staticmethod
    def _seconds_until_midnight_utc() -> float:
        """Calcula segundos hasta la próxima medianoche UTC."""
        now = datetime.now(timezone.utc)
        tomorrow_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return (tomorrow_midnight - now).total_seconds()
