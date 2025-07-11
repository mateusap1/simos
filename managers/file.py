class FileSystem:
    def __init__(self, disk_size: int):
        # _ significa espaço vazio
        self.blocks: list[str] = ["_" for _ in range(disk_size)]

    def insert_file(self, name: str, offset: int, space: int):
        for i in range(offset, offset+space):
            self.blocks[i] = name


def main():
    system = FileSystem(10)
    system.insert_file("X", 0, 2)
    system.insert_file("Y", 3, 1)
    system.insert_file("Z", 5, 3)
    print(system.blocks)


if __name__ == "__main__":
    main()