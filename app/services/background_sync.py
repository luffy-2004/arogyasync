import logging
import threading
import time

from app.services.sync_engine import sync_engine

logger = logging.getLogger(__name__)

_background_thread = None
_background_thread_lock = threading.Lock()


def start_background_sync() -> bool:
    """
    Start the background sync thread once if it is not already running.
    """
    global _background_thread

    with _background_thread_lock:
        if _background_thread is not None and _background_thread.is_alive():
            return False

        logger.info("Background sync started.")

        def run():
            while True:
                if sync_engine.check_cloud_connectivity():
                    logger.info("Background sync cycle executed.")
                    sync_engine.sync_local_to_cloud()
                else:
                    logger.info("Background sync: connectivity unavailable.")
                time.sleep(30)

        _background_thread = threading.Thread(
            target=run,
            daemon=True,
            name="background-sync-thread"
        )
        _background_thread.start()
        return True
