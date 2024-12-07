class Storage:
    def __init__(self) -> None:
        self._store: list[dict[str, str]] = []
        self._index = 0

    def add(self, data: dict):
        self._store.append(data)

    def get_by_index(self, index: int):
        if self._index > 0 and index < len(self._store) - 1:
            return self._store[index]

    def get_all(self):
        return self._store

    def print_items(self):
        sep = "#" * 20
        for item in self._store:
            found = "нашелся" if item.get("found") else "не нашелся"
            msg = f"Пользователь {item['username']} {item['birthday']} {found}"
            link = item.get("link")
            if link:
                msg = f"{msg}\n\n{link}"

            print(f"{sep}\n{msg}\n{sep}", end="\n\n")
