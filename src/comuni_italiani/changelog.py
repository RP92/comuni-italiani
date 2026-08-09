def diff_datasets(old, new):
    old_by = {c["codice"]: c for c in old}
    new_by = {c["codice"]: c for c in new}
    old_ids, new_ids = set(old_by), set(new_by)
    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    modified = sorted(
        cid for cid in old_ids & new_ids if old_by[cid] != new_by[cid]
    )
    return {"added": added, "removed": removed, "modified": modified}
