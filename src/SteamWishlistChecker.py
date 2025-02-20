#!/usr/bin/env python
import asyncio
import json
import os
from datetime import date
from typing import List

import httpx

import Constants
from SteamGameClass import SteamGame


async def get_list_of_discounted_games() -> List:
    STEAM_STORE_API_URL = "https://store.steampowered.com/api/appdetails"
    wishlistURI = "https://api.steampowered.com/IWishlistService/GetWishlist/v1/"

    steam_game_objects = []
    output_list = []

    # Getting Wishlist from Steam
    for game in httpx.get(
        wishlistURI, params={"key": Constants.API_KEY, "steamid": Constants.STEAMID}
    ).json()["response"]["items"]:
        steam_game_objects.append(
            SteamGame(str(game["appid"]), game["priority"], game["date_added"])
        )

    # Sanity check and sorting of wishlisted items
    # print(f"Total number of wishlisted games: {len(steam_game_objects)}")
    # print("Sorting...")
    steam_game_objects = sorted(steam_game_objects, key=lambda game: game.priority)

    # Retrieving game and price data
    # print("Getting game information")
    async with httpx.AsyncClient() as client:
        for game in steam_game_objects:
            response = await client.get(
                STEAM_STORE_API_URL, params={"appids": game.appID}
            )
            game.name = response.json()[game.appID]["data"]["name"]
            game.is_free = bool(response.json()[game.appID]["data"]["is_free"])
            if game.is_free:
                pass
            else:
                try:
                    game.discount = response.json()[game.appID]["data"][
                        "price_overview"
                    ]["discount_percent"]
                    game.price = response.json()[game.appID]["data"]["price_overview"][
                        "final_formatted"
                    ]
                except KeyError:
                    # print(
                    # f"{game.name} does not have price data removing game from list"
                    # )
                    steam_game_objects.remove(game)

    # Cleaning output
    for game in steam_game_objects:
        if game.is_free:
            output_list.append(game)
        elif game.discount == 0:
            pass
        else:
            output_list.append(game)

    return output_list


def update_cached_date() -> None:
    cache_dir = "~/.cache/steamsale"
    try:
        with open(os.path.expanduser(f"{cache_dir}/.cache_date"), "w+") as file:
            file.write(str(date.today()))
    except FileNotFoundError:
        os.mkdir(os.path.expanduser(cache_dir))


def local_waybar_cache(out_data) -> None:
    cache_dir = "~/.cache/steamsale"

    try:
        with open(
            os.path.expanduser("~/.cache/steamsale/.steamsale_cache"), "w"
        ) as file:
            json.dump(out_data, file)
    except FileNotFoundError:
        os.mkdir(os.path.expanduser(cache_dir))


def tooltip_text(gamelist) -> str:
    text = ""

    for item in gamelist:
        cleaned_name = item.name
        cleaned_name = cleaned_name.translate(
            str.maketrans(
                {
                    "&": "&amp;",
                }
            )
        )
        if item.is_free:
            text = text + f'<span foreground="green">{cleaned_name} is FREE!</span>\n'
        else:
            text = (
                text
                + f'<small><span foreground="yellow" weight="bold">{cleaned_name}</span>: <span style="italic">{item.price}</span><span foreground="green">({str(item.discount)}%)</span></small>\n'
            )

    tooltip_text = '\t\t<span size="xx-large">Steam Sales</span>\t\t\n' + text
    return tooltip_text


if __name__ == "__main__":
    cache_dir = "~/.cache/steamsale/"
    with open(os.path.expanduser(f"{cache_dir}.cache_date"), "r") as file:
        cache_date = file.readline()

    if (cache_date == str(date.today())) and os.path.exists(
        os.path.expanduser(f"{cache_dir}.steamsale_cache")
    ):
        with open(os.path.expanduser(f"{cache_dir}.steamsale_cache"), "r") as file:
            out_data = json.load(file)
        print(json.dumps(out_data))
    else:
        list_of_sales = asyncio.run(get_list_of_discounted_games())
        out_data = {
            "text": " ",
            "alt": "󰂭 ",
            "tooltip": tooltip_text(list_of_sales),
        }
        print(json.dumps(out_data))
        update_cached_date()
        local_waybar_cache(out_data)
