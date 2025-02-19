from dataclasses import dataclass


@dataclass
class SteamGame:
    appID: str
    priority: int
    date_added: int
    name: str = ""
    is_free: bool = False
    discount: int = 0
    price: str = ""
    store_url: str = ""

    def __post_init__(self) -> None:
        self.store_url = f"https://store.steampowered.com/app/{self.appID}"
