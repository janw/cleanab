from logzero import logger


def print_results(results, verbose=False):
    bulk = results.data
    duplicates = getattr(bulk, "duplicate_import_ids", [])
    new = getattr(bulk, "transaction_ids", [])

    logger.info(f"Created {len(new)} new transactions")
    if verbose:
        for entry in new:
            logger.info(f"New: {entry}")

    logger.info(f"Saw {len(duplicates)} duplicates")
    if verbose:
        for entry in duplicates:
            logger.info(f"Duplicate: {entry}")
