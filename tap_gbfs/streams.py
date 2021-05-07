from datetime import datetime
from singer import bookmarks, logger, messages, utils
import pytz

LOGGER = logger.get_logger()
MIN_TIME = "2015-12-15T00:00:00"


class Stream:
    def __init__(self, client, config, state):
        self.client = client
        self.config = config
        self.state = state


class StationInformationV1(Stream):
    """A stream for describing GBFS station information in v1 format."""

    stream_id = "station_information"
    stream_name = "station_information"
    key_properties = ["station_id"]
    replication_method = "INCREMENTAL"
    replication_keys = ["last_updated"]

    def sync(self):
        bookmark = bookmarks.get_bookmark(
            self.state,
            self.stream_name,
            self.replication_keys[0],
            MIN_TIME,
        )

        start_dt = utils.strptime_to_utc(bookmark)
        resp = self.client.request_feed(self.stream_name)
        last_updated = resp.get("last_updated").replace(tzinfo=pytz.UTC)

        if start_dt >= last_updated:
            return

        for station in resp.get("data").get("stations"):
            # Delete array/complex properties because we're not powerful enough yet
            if "rental_methods" in station:
                del station["rental_methods"]
            if "rental_uris" in station:
                del station["rental_uris"]
            yield station

        bookmarks.write_bookmark(
            self.state,
            self.stream_name,
            self.replication_keys[0],
            utils.strftime(last_updated),
        )
        messages.write_state(self.state)


class StationStatusV1(Stream):
    """A stream for describing GBFS station status in v1 format."""

    stream_id = "station_status"
    stream_name = "station_status"
    key_properties = ["station_id", "last_reported"]
    replication_method = "INCREMENTAL"
    replication_keys = ["last_reported"]

    def sync(self):
        bookmark = bookmarks.get_bookmark(
            self.state,
            self.stream_name,
            self.replication_keys[0],
            MIN_TIME,
        )

        start_dt = utils.strptime_to_utc(bookmark)
        resp = self.client.request_feed(self.stream_name)

        max_dt = start_dt
        for station in resp.get("data").get("stations"):
            last_reported = station.get("last_reported")
            last_reported_dt = datetime.fromtimestamp(last_reported).replace(
                tzinfo=pytz.UTC
            )
            if last_reported_dt > max_dt:
                max_dt = last_reported_dt
            if last_reported_dt > start_dt:
                yield station

        bookmarks.write_bookmark(
            self.state,
            self.stream_name,
            self.replication_keys[0],
            utils.strftime(max_dt),
        )
        messages.write_state(self.state)


STREAM_OBJECTS = {
    "station_information_v1": StationInformationV1,
    "station_status_v1": StationStatusV1,
}
