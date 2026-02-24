# Loading maps

Currently, maps are loaded only through the command line. The application can be extended with multiple import modules and one of these modules must be specified in the load command with the `-c` parameter.

Each import module has its own set of required extra options, and these are provided through the `--opts` parameter.

The most common load pattern is to use the importer for items from the LOC Sanborn map collection (`-c loc-sanborn`), which requires two extra options (`--opts identifier=<loc item id> locale=<locale slug>`). The New Iberia, La., 1892 map would be loaded like this:

```
uv run manage.py map add -c loc-sanborn --opts identifier=sanborn03375_002 locale=new-iberia-la
```

To see all available import configurations run:

```
uv run manage.py map list-importers
```

!!! note

    Only the `loc-sanborn` importer is regularly used, so there is no guarantee the others will work right now.

## Bulk loading

You can bulk load maps by specifying a configuration (`-c`) and then passing the `--bulk-file <path/to/csv>` instead of `--opts`. In this case, the provided CSV file must have columns for each required `--opts` entry for a specified configuration, and one row per map to load.
