import dramatiq

from dramatiq.brokers.redis import RedisBroker

from .steam import Archivist, SteamApp, Archive
from .facades import Settings


# Set up dramatiq with a redis broker
redis_broker = RedisBroker(host=Settings().system['redis-host'])
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def archive_steam_app(archive_id: int, app_id: int) -> None:
    archivist = Archivist()
    archive = archivist.get_archive(archive_id)
    steam_app = SteamApp.from_app_id(app_id)
    archivist.archive(steam_app, archive)