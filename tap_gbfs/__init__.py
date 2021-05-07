#!/usr/bin/env python3
from singer import utils, logger
from singer.catalog import Catalog, write_catalog
from gbfs.services import SystemDiscoveryService
from tap_gbfs.discovery import do_discover
from tap_gbfs.sync import do_sync
from tap_gbfs.exceptions import UnknownSystemError

LOGGER = logger.get_logger()


def _load_gbfs_client(config):
    system_id = config.get("system_id")
    ds = SystemDiscoveryService()
    client = ds.instantiate_client(system_id)

    if client is None:
        raise UnknownSystemError(system_id)

    return client


@utils.handle_top_exception(LOGGER)
def main():
    required_config_keys = ["system_id"]
    args = utils.parse_args(required_config_keys)

    config = args.config
    client = _load_gbfs_client(config)
    catalog = args.catalog or Catalog([])
    state = args.state

    if args.discover:
        LOGGER.info("Starting discovery mode")
        catalog = do_discover(client)
        write_catalog(catalog)
    else:
        LOGGER.info("Starting sync mode")
        do_sync(client, config, state, catalog)


if __name__ == "__main__":
    main()
