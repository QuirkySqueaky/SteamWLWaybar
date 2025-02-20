#!/usr/bin/env python
import asyncio
import json
import os
import sys
from datetime import date
from typing import List

import httpx

import Constants
from SteamGameClass import SteamGame


def get_wishlist() -> List:
    wishlistURI = "https://api.steampowered.com/IWishlistService/GetWishlist/v1/"
    wishlistAPIresp = httpx.get(
        wishlistURI, params={"key": Constants.API_KEY, "steamid": Constants.STEAMID}
    )

    steam_game_objects = []

    # Getting Wishlist from Steam API
    for game in wishlistAPIresp.json()["response"]["items"]:
        if game["appid"] is None:
            pass
        else:
            steam_game_objects.append(
                SteamGame(str(game["appid"]), game["priority"], game["date_added"])
            )

    # Sanity check and sorting of wishlisted items
    steam_game_objects = sorted(steam_game_objects, key=lambda game: game.priority)
    return steam_game_objects


async def get_list_of_discounted_games(wishlist: List) -> List:
    # Retrieving game and price data
    # print("Getting game information")
    STEAM_STORE_API_URL = "https://store.steampowered.com/api/appdetails"
    output_list = []
    async with httpx.AsyncClient() as client:
        for game in wishlist:
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
                    wishlist.remove(game)

    # Cleaning output
    for game in wishlist:
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
            json.dump(out_data, file, ensure_ascii=False)
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
                + f'<span foreground="yellow" weight="bold">{cleaned_name}</span>: <span style="italic">{item.price}</span><span foreground="green">({str(item.discount)}%)</span>\n'
            )

    tooltip_footer = "<small>Click this module to force reload</ small>"
    tooltip_text = (
        '<span size="xx-large" foreground="#66c0f4">Steam Sales</span>\n'
        + text
        + tooltip_footer
    )
    return tooltip_text


if __name__ == "__main__":
    cache_dir = "~/.cache/steamsale/"

    with open(os.path.expanduser(f"{cache_dir}.cache_date"), "r") as file:
        cache_date = file.readline()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--force-update":
            list_of_sales = asyncio.run(get_list_of_discounted_games(get_wishlist()))
            out_data = {
                "text": " ",
                "alt": "󰂭 ",
                "tooltip": tooltip_text(list_of_sales),
            }
            print(json.dumps(out_data), flush=True)
            update_cached_date()
            local_waybar_cache(out_data)
    else:
        if (cache_date == str(date.today())) and os.path.exists(
            os.path.expanduser(f"{cache_dir}.steamsale_cache")
        ):
            with open(os.path.expanduser(f"{cache_dir}.steamsale_cache"), "r") as file:
                out_data = json.load(file)
            print(json.dumps(out_data), flush=True)
        else:
            list_of_sales = asyncio.run(get_list_of_discounted_games(get_wishlist()))
            out_data = {
                "text": " ",
                "alt": "󰂭 ",
                "tooltip": tooltip_text(list_of_sales),
            }
            print(json.dumps(out_data), flush=True)
            update_cached_date()
            local_waybar_cache(out_data)
