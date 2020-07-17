from arez.utils import group_by


class Element:
    id: int = 0

    def __new__(cls, *args):
        self = super().__new__(cls)
        self.id = cls.id
        cls.id += 1
        return self

    def __init__(self, group: int):
        self.group: int = group

    def __repr__(self) -> str:
        return f"Element({self.id}, {self.group!r})"


items = [
    Element(4),
    Element(1),
    Element(2),
    Element(3),
    Element(4),
    Element(2),
    Element(3),
    Element(4),
    Element(3),
    Element(4),
]


def test_group_by():
    grouped_items = group_by(items, lambda e: e.group)
    for num in range(1, 5):  # 1-4
        group_list = grouped_items[num]
        assert len(group_list) == num and all(e.group == num for e in group_list)
