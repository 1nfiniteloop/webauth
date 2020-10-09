from application import Host


class HostAttribute:
    """String literals for valid "Host" attributes"""
    HOST_ID, HOST_NAME = "id", "name"


class JsonFormattedHost(dict):

    def __init__(self, host: Host):
        host_data = {
            HostAttribute.HOST_ID: host.id,
            HostAttribute.HOST_NAME: host.name,
        }
        super().__init__(host_data)
