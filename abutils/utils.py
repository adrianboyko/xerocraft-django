# Standard
import uuid

# Third Party
from django.db.models import Model

# Local


def generate_hex_string(length, uniqueness_check=None):
    assert(length <= 32)
    result = str(uuid.uuid4()).replace('-', '')[:length]
    if uniqueness_check is None or uniqueness_check(result):
        return result
    else:
        # Collision detected, so try again.
        return generate_hex_string(length, uniqueness_check)


def generate_ctrlid(model: Model) -> str:
    """Generate a unique ctrlid for the given model."""
    # TODO: Move this to ETL App if that refactorization is pursued.
    def is_unique(ctrlid: str) -> bool:
        return model.objects.filter(ctrlid=ctrlid).count() == 0
    return "GEN:" + generate_hex_string(8, is_unique)