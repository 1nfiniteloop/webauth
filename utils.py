
def url_path_join(*paths: str, base_url: str = ""):
    joined_paths = "/" + "/".join(path.strip("/") for path in paths)
    if base_url:
        return base_url.rstrip("/") + joined_paths
    else:
        return joined_paths
