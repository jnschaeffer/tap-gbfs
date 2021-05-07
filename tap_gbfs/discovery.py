import os
import json

from singer import logger, metadata
from singer.catalog import Catalog
from tap_gbfs.streams import STREAM_OBJECTS

LOGGER = logger.get_logger()


def _get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


# Load schemas from schemas folder
def _load_schemas():
    schemas = {}

    schemas_path = _get_abs_path("schemas")

    for filename in os.listdir(schemas_path):
        path = os.path.join(schemas_path, filename)
        file_raw = filename.replace(".json", "")
        with open(path) as f:
            schemas[file_raw] = json.load(f)

    return schemas


def do_discover(client):
    raw_schemas = _load_schemas()
    catalog_entries = []
    major_ver = client.request_feed("gbfs_versions").get("version")[0]
    feed_names = client.feed_names

    for feed_name in feed_names:
        versioned_feed = f"{feed_name}_v{major_ver}"
        # create and add catalog entry
        stream = STREAM_OBJECTS.get(versioned_feed)
        if stream is None:
            continue

        schema = raw_schemas[versioned_feed]

        catalog_entry = {
            "stream": versioned_feed,
            "tap_stream_id": versioned_feed,
            "schema": schema,
            "metadata": metadata.get_standard_metadata(
                schema=schema,
                key_properties=stream.key_properties,
                valid_replication_keys=stream.replication_keys,
                replication_method=stream.replication_method,
            ),
            "key_properties": stream.key_properties,
        }
        catalog_entries.append(catalog_entry)

    return Catalog.from_dict({"streams": catalog_entries})
