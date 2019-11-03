from typing import List

from utils import IndexedModel


def reorder_models_indexes(indexed_models: List[IndexedModel], new_order):
    for model in indexed_models:
        key = str(model.pk)
        if key in new_order:
            try:
                int(new_order[key])
                model.index = int(new_order[key])
                model.save()
            except ValueError:
                continue
