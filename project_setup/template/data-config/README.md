# Project-data setup-tree files

`project-data --proj-dir-like FILE` accepts a JSON file with a `subfolders` list
or a plain text file with one directory name per line. Directory names are created
under the external data directory, and may use `/` to describe a nested tree.

The bundled presets reflect the layouts inspected in the public GDP and GMRTCAL
repositories. They are starting points, not claims that every project needs every
folder. Copy and edit a preset for a project-specific layout.

```sh
project-data --project SKA --proj-dir ~/Documents \
  --destination /Volumes/Work/Data --proj-dir-like \
  ~/.local/lib/project-setup/project_setup/template/data-config/gdp-v1.json
```
