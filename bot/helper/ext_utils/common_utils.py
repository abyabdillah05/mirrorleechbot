SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes is None:
        return "0B"
    
    is_negative = size_in_bytes < 0
    size_in_bytes = abs(size_in_bytes)

    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1

    formatted_size = f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"
    return f"-{formatted_size}" if is_negative else formatted_size

def get_readable_time(seconds: int):
    periods = [("h", 86400), ("j", 3600), ("m", 60), ("d", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result or "0d"