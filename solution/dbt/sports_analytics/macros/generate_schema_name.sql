{#
  Target-aware schema routing:
  - No custom schema (staging): use the target dataset
    (dev -> nba_staging_dev, prod -> nba_staging).
  - Custom schema (marts, +schema: nba_marts): use it as-is on prod,
    suffix with _dev on any other target (dev -> nba_marts_dev).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ custom_schema_name | trim }}_dev
    {%- endif -%}
{%- endmacro %}
