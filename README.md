sqlalchemy-auditlog
================

Auditlog extension for sqlalchemy that uses Elasticsearch for storing logs.

Requirements
------------

- [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)

Installation
------------
```shell
pip install git+https://github.com/dealflowteam/sqlalchemy-auditlog.git@master#egg=sqlalchemy_auditlog
```

Usage
------------

- Set environment variables:

```
AUDITLOG_ELASTICSEARCH_HOST=localhost
AUDITLOG_ELASTICSEARCH_PORT=9200
AUDITLOG_INDEX_NAME=auditlog-test
```

- register sqlalchemy event listeners:

```python
from sqlalchemy import create_engine, event
from auditlog.receivers import save_log_entries_after_commit, track_instances_after_flush

event.listen(Session, "after_flush", track_instances_after_flush)
event.listen(Session, "after_commit", save_log_entries_after_commit)
```
