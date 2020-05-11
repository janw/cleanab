from logzero import logger


def print_results(results):
    logger.info("Done.")
    bulk = results.data
    for entry in getattr(bulk, "duplicate_import_ids", []):
        logger.info(f"Duplicate transactions: {entry}")

    for entry in getattr(bulk, "transaction_ids", []):
        logger.info(f"New transactions: {entry}")
