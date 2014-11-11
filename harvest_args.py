args = [
    {
        "short": "-s", "long": "--super-dry",
        "dest": "superdryrun",
        "action": "store_true",
        "help": "A dry run where we do not even download any files."
    }, {
        "short": "-t", "long": "--tolarated-changes",
        "type": int,
        "default": 1,
        "dest": "tolaratedchanges",
        "metavar": "CHANGES",
        "help": """When should we warn about suspicios changes in the
                   number of protocols?
                   1 means that anything other that zero or one new
                   protocols is considered suspicios."""
    }, {
        "short": "-f", "long": "--file",
        "dest": "filename",
        "help": "Enter a file name, if your data is in a local CSV file."
    }
]