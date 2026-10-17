"""Dagster partition definitions for the dagster-elt-template pipeline.

The pipeline operates over whole directories of source files (PDF and
DOCX), not per-file. The set of files changes when the user drops new
content into ``data/sources/`` — assets run over the directory contents
on every materialisation, no partitions needed.

This module is intentionally a placeholder. If you want per-file
partitions (so you can re-run a single file's conversion), use a
``DynamicPartitionsDefinition`` with a sensor that scans the source
directory on each tick — see
https://docs.dagster.io/concepts/partitions-schedules-sensors/dynamic-partitions
for the pattern.
"""
