#!/usr/bin/env python3
import json
import singer
import sys

from tap_zendesk.discover import discover_streams
from tap_zendesk.sync import sync_stream
from zenpy import Zenpy

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    "start_date",
    "subdomain",
    "access_token"
]

def do_discover(client):
    LOGGER.info("Starting discover")
    catalog = {"streams": discover_streams(client)}
    json.dump(catalog, sys.stdout, indent=2)
    LOGGER.info("Finished discover")


def do_sync(client, catalog, state):

    for stream in catalog.streams:
        stream_name = stream.tap_stream_id
        #if not stream_is_selected(metadata.to_map(stream.metadata)):
        #    LOGGER.info("%s: Skipping - not selected", stream_name)
        #    continue

        # if starting_stream:
        #     if starting_stream == stream_name:
        #         LOGGER.info("%s: Resuming", stream_name)
        #         starting_stream = None
        #     else:
        #         LOGGER.info("%s: Skipping - already synced", stream_name)
        #         continue
        # else:
        #     LOGGER.info("%s: Starting", stream_name)

        singer.write_state(state)
        singer.write_schema(stream_name, stream.schema.to_dict(), stream.key_properties)
        counter_value = sync_stream(client, state, stream.to_dict())
        LOGGER.info("%s: Completed sync (%s rows)", stream_name, counter_value)

    singer.write_state(state)
    LOGGER.info("Finished sync")


@singer.utils.handle_top_exception(LOGGER)
def main():
    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)

    creds = {
        "subdomain": parsed_args.config['subdomain'],
        "oauth_token": parsed_args.config['access_token'],
    }
    client = Zenpy(**creds)

    if parsed_args.discover:
        do_discover(client)
    elif parsed_args.catalog:
        state = {} #validate_state(args.config, args.catalog, args.state)
        do_sync(client, parsed_args.catalog, state)
