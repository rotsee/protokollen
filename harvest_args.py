args = [
    {
        "short": "-s", "long": "--super-dry",
        "dest": "superdryrun",
        "action": "store_true",
        "help": "A dry run where we do not even download any files."
    }, {
        "short": "-f", "long": "--file",
        "dest": "filename",
        "help": "Enter a file name, if your data is in a local CSV file."
    },
    "overwrite",
    "tempdir"
]
