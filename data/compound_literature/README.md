# Compound literature (git-tracked)

Structured per-compound citations and activity data. **Raw Paperclip output** stays in [`pvjthomas/local/literature/`](../../../pvjthomas/local/README.md).

## Files

One JSON per compound when populated:

```
refs/T19860.json
refs/T1262.json
…
```

## `{compound_id}.json` shape

```json
{
  "compound_id": "T19860",
  "match": "yes",
  "support": "strong",
  "entries": [
    {
      "source": "paperclip",
      "pmid": null,
      "chembl_id": null,
      "ic50_uM": null,
      "assay": "nitrocefin",
      "note": "classic TEM-1 suicide inhibitor"
    }
  ],
  "raw_local": "pvjthomas/local/literature/T19860/"
}
```

Summaries are referenced from [`compound_dossiers.json`](../../compound_dossiers.json).

See also [`refs/README.md`](refs/README.md) for the ref JSON schema.
