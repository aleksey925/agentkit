---
name: debezium-conf-explain
description: Parse and explain a Debezium connector config JSON in a human-readable
  format. Use when the user pastes a Debezium connector config and wants to
  understand what it does - which tables are captured, how events are
  transformed, and where they are published.
---

# Debezium Config Explainer

When the user provides a Debezium connector config JSON, produce a structured
human-readable summary following the format and conventions below.

## Output Format

### Source section

```
## Source
Database: {database.dbname} on {database.hostname}:{database.port}
Change reading method: {plugin.name} (built-in Postgres plugin, no extra setup)
Data before connector started: {snapshot.mode} - {snapshot mode explanation}
```

List all business tables (one line each) right after Database, then the
change reading method and snapshot lines.

Snapshot mode explanations:
- `initial` - read all existing rows first, then switch to live changes
- `never` - skip existing rows, capture only new changes from now on
- `always` - read all existing rows on every connector restart

### Per-table section

For each table in `table.include.list`, excluding `debezium.signals` and
`debezium.heartbeat` (those go into Infrastructure section), list
`{table_name} -> {final_topic}` right after the Database line as shown above.
Then render the transform blocks below the snapshot line (no indentation).

The final topic is determined by looking at the transforms chain for a
RegexRouter that matches this table's topic pattern and extracting its
`replacement` value.

Then for each transform that applies to this table (via predicate or direct
match), render the relevant block:

**Filter transform** (`io.confluent.connect.transforms.Filter$Value` or similar):

Parse the filter condition and render each rule on its own line:

```
Filter:
  {condition in readable form}  : {filter.type}  =>  {what events reach the topic}
  op is missing or null         : {missing.or.null.behavior}
```

For the condition, translate JSONPath like `$[?(@.op == "d" || @.op == "t")]`
into `op == d | t` form.

For the `[result]` line: describe which operation types (`c`=insert, `u`=update,
`d`=delete, `t`=truncate) pass through based on the filter type (include/exclude)
and condition. Use plain English: "only inserts (c) and updates (u) reach the topic".

**Extract key transform** (`ExtractField$Key`):

```
Message key source field: {field}
```

**Remove fields transform** (`ReplaceField$Value` with blacklist/exclude):

```
Fields stripped before publishing: {comma-separated field list}
```

### Infrastructure section

```
## Infrastructure
Signals topic: {debezium_signals replacement topic}
Heartbeat topic: {debezium_heartbeat replacement topic}
  interval: {heartbeat.interval.ms}ms
```

## Parameter Reference

These are the Debezium parameters used in the summary and what they mean:

**plugin.name** - how the connector reads changes from Postgres. Postgres uses
a write-ahead log (WAL) internally; this plugin decodes it into change events.
`pgoutput` is built into Postgres 10+, no extra installation needed.

**snapshot.mode** - what to do with data that existed in the table before the
connector first started. `initial` means send it all to the topic first, then
switch to live streaming. `never` means ignore it.

**table.include.list** - which tables to capture changes from.

**topic.prefix** - base prefix for all generated topic names. By default a
table `public.campaign_user` gets topic
`{prefix}.public.campaign_user`. Route transforms override this.

**transforms (filter)** - gates which change events reach the topic. The
`op` field in a Debezium message is the operation type: `c`=insert,
`u`=update, `d`=delete, `t`=truncate, `m`=message. `filter.type: exclude`
means matching events are dropped; `include` means only matching events pass.
`missing.or.null.behavior: exclude` means if the `op` field is absent
(malformed or internal message), drop it too.

**transforms (ExtractField$Key)** - by default the Kafka message key is the
full primary key struct. This transform replaces it with a single field value.
Everything with the same key goes to the same Kafka partition and is ordered.

**transforms (ReplaceField blacklist)** - removes fields from the message
value before publishing. Used to strip Debezium internal metadata that
consumers don't need.

**transforms (RegexRouter)** - overrides the default topic name with a custom
one using a regex replacement. This is how tables get routed to business-named
topics instead of the default `{prefix}.{schema}.{table}` pattern.

**predicates** - a predicate gates a transform so it only runs on messages
from matching topics. `TopicNameMatches` with a regex pattern means the
transform only applies to tables whose topic name matches.

## Notes

- Render the output as a code block so spacing is preserved.
- Keep descriptions concise - one line per parameter, two lines max.
- Do not list transforms that only apply to infrastructure tables
  (debezium.signals, debezium.heartbeat) in the per-table section.
- If `column.exclude.list` is non-empty, add a line under the table section:
  `Excluded columns: {list}`
- If there are multiple business tables, produce one `## table -> topic`
  section per table.
