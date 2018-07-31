#!/usr/bin/env python


class ApolloLookupDatasource(object):
    def __init__(self, service_object_registry, **kwargs):
        pass

    def lookup_DummyEmail(self, target_field_name, source_record, field_value_map):
        return 'dev@null.net'

