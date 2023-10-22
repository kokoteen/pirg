from rich.logging import RichHandler

log_config = {
    "version": 1,
    "formatters": {
        "verbose": {
            "format": "%(message)s",
            "datefmt": "[pirg]",
        },
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
    },
}
