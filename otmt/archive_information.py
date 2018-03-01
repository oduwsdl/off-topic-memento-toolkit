# -*- coding: utf-8 -*-

"""
otmt.archive_information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the idiosyncracies between archives.
"""

archive_mappings = {
    "wayback.archive-it.org": ( '/http', 'id_/http' ),
    "web.archive.org": ( '/http', 'id_/http' )
}

def generate_raw_urim(urim):
    """Generates a raw URI-M based on the archive it belongs to. Supported
    URI patterns are found in `archive_mappings`.
    """

    raw_urim = urim

    for domainname in archive_mappings:

        if domainname in urim:

            search_pattern = archive_mappings[domainname][0]
            replacement_pattern = archive_mappings[domainname][1]

            # if urim is already a raw urim, do nothing
            if replacement_pattern not in urim:

                raw_urim = urim.replace(
                    search_pattern, replacement_pattern
                )

            break

    return raw_urim