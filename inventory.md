# Inventory

A **run** is one datasheet extraction. A datasheet may describe a single orderable module or several SKUs side by side. **Inventory** is the module catalog derived from `runs/`: one JSON file per SKU, with that module’s general envelope and only the operating modes that belong to it.

Runs are not rewritten. They remain the extraction audit trail (`specs.json`, `modes.json`, `mode_atoms.json`). Inventory is a deterministic projection, rebuilt on demand.

Canonical splits — the contract every other run is measured against:

- `runs/20260821_081405` — Cisco `QDD-8X100G-FR` and `QDD-2X400G-FR4`. Two SKUs, each mode tagged with `model`, one operating mode each.
- `runs/20260821_093751` — Cisco `QDD-400G-ZR-S` and `QDD-400G-ZRP-S`. Two SKUs, each mode tagged with `model`. ZR-S has one mode; ZRP-S has many.

## Shape

```
inventory/
  index.json
  Cisco__QDD-400G-ZR-S.json
  Cisco__QDD-400G-ZRP-S.json
  ...
```

Each module file:

```json
{
  "vendor": "Cisco",
  "model": "QDD-400G-ZRP-S",
  "source_run": "20260821_093751",
  "source_file": "...",
  "split": "by_mode_model",
  "warnings": [],
  "general": {
    "vendor": "Cisco",
    "model": "QDD-400G-ZRP-S",
    "form_factor": "QSFP-DD",
    "wavelength_band": "C-band"
  },
  "modes": [
    {
      "label": "QDD-400G-ZRP-S 400G 16-QAM",
      "bit_rate_gbps": 400.0,
      "modulation_format": "16-QAM"
    }
  ]
}
```

`split` is `"single_model"` or `"by_mode_model"`. Filenames are `{vendor}__{model}.json` with characters that Windows will not accept stripped. `index.json` lists every module, its file, source run, mode count, and warnings.

`general.model` is always the one SKU this file represents, even when the source run listed several.

## Logic

Grain:

- **Module** = one orderable model / part number.
- **Mode** = one selectable configuration of that module (application code, line rate, amplified vs unamplified).
- A mode is not a module. The linker prompt that treated “each extra model number as a mode” is the wrong grain; inventory undoes that flattening.

SKU discovery is dynamic. Nothing in the builder hard-codes vendor names or part numbers. For each run it takes, in order:

1. `specs.json` → `model`
2. else `mode_atoms.json` → `general.model`
3. else unique `model` values on the mode objects

`model` may be a string (one SKU) or a list (several). A one-element list is a single-model run.

### Split rules

**One SKU** (`split: single_model`). The model lives in `general` (that is what `separate_atoms` does when `model` is not multi-valued). Modes are not required to repeat it. Every mode in the run belongs to that SKU. This is a datasheet that describes a single module with one or more operating modes.

**Two or more SKUs** (`split: by_mode_model`). Canonical pattern: every mode has a `model` field naming one of the declared SKUs. Modes are partitioned by that field. A mode is never left unassigned and never copied onto every SKU.

There are no unassigned modes in a valid run:

- Missing `model` on a mode is only legal when there is a single SKU in general. In that case the mode is assigned to that SKU, not left hanging.
- On a multi-SKU run, a mode with no `model` is a defect in the extraction (the run should be fixed to match `20260821_081405` / `20260821_093751`). The builder records a warning and does **not** attach that mode to all modules.

Fallback on multi-SKU runs only: if `model` is absent, an exact token in the mode `label` that equals a declared SKU is accepted (`DP08QSDD-ZRB-A1 Amplified`). Substring matching is not used — `QDD-400G-ZR-S` is a prefix of `QDD-400G-ZRP-S`.

A SKU declared in `specs.model` with no matching modes is still written (`modes: []`) and warned. A `model` value on a mode that was not in `specs.model` is written as an extra module and warned as undeclared.

If the same vendor+model appears in more than one run, the newer run id wins and the record notes which run it supersedes.

### Per-SKU general

Start from the run’s `mode_atoms.general` (module envelope shared by the datasheet: vendor, connector, temperature, notes, provenance). Set `model` to this SKU.

Then lift **identity** fields that are constant across this SKU’s modes into `general`:

- `form_factor`
- `wavelength_band`, `wavelength_min_nm`, `wavelength_max_nm`, `wavelength_center_nm`
- `frequency_min_thz`, `frequency_max_thz`
- `channel_total`

Those describe the hardware, not a selectable line rate. That is why `20260821_081405` puts `QSFP-DD` on `QDD-8X100G-FR` and `QSFP-DD800` on `QDD-2X400G-FR4`.

Operating fields stay on the mode even when they are constant for that SKU (`bit_rate_gbps`, `modulation_format`, host/media codes, OSNR, FEC, reach, power). Single-element lists in `general` are unwrapped to scalars.

`model` and the lifted identity fields are removed from the mode objects in the inventory file. The source `modes.json` is unchanged.

## Process

```bash
python build_inventory.py
python build_inventory.py --dry-run
python build_inventory.py --run 20260821_081405 --run 20260821_093751
```

1. Scan `runs/` (or the `--run` ids). Skip nothing by vendor or date; every directory with `specs.json` is a candidate.
2. Load `specs.json`, `mode_atoms.json`, `modes.json`. If `mode_atoms.json` is missing, `general` is derived with `separate_atoms`.
3. Discover SKUs, split modes, build one record per SKU.
4. Replace `inventory/*.json` (the directory is always a fresh projection, same idea as `refresh_reports.py`).
5. Print the split per run and any warnings. Warnings on a multi-SKU run mean that extraction should be fixed to the canonical pattern — do not patch them by cloning modes.

Rebuild after editing `specs.json` / `modes.json`, or after a new extraction. Inventory does not call the LLM.
