import os

try:
    ELASTICSEARCH_HOST = os.environ['AUDITLOG_ELASTICSEARCH_HOST']
    ELASTICSEARCH_PORT = os.environ['AUDITLOG_ELASTICSEARCH_PORT']
    INDEX_NAME = os.environ['AUDITLOG_INDEX_NAME']
except KeyError as e:
    raise ValueError(f"Set {e} as environment variable.")
