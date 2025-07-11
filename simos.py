class FileSystem:
    def __init__(self, disk_size: int):
        # _ significa espaço vazio
        self.blocks: list[str] = ["_" for _ in range(disk_size)]

    def insert_file(self, name: str, first: int, space: int):
        for i in range(first, first+space):
            self.blocks[i] = name


# class OperatingSystem:
#     def __init__(self):
#         pass