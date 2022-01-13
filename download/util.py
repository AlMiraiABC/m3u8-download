def human_size(length: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    radix = 1024.0
    for i in range(len(units)):
        if (length / radix) < 1:
            return "%.2f%s" % (length, units[i])
        length = length / radix
