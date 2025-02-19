#!/usr/bin/env python
import asyncio
import json
from typing import List

import httpx

import Constants
from SteamGameClass import SteamGame


async def main() -> List:
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


if __name__ == "__main__":
    list_of_sales = asyncio.run(main())
    text = ""
    for item in list_of_sales:
        cleaned_name = item.name
        cleaned_name = cleaned_name.translate(
            str.maketrans(
                {
                    "&": "&amp;",
                }
            )
        )
        if item.is_free:
            text = text + f"<small>{cleaned_name} is FREE!</small>\n"
        else:
            text = (
                text
                + f"<small>{cleaned_name}: {item.price}({str(item.discount)}%)</small>\n"
            )

    tooltip_text = '\t\t<span size="x-large">Steam Sales</span>\t\t\n' + text
    out_data = {
        "text": " ",
        "alt": "󰂭 ",
        "tooltip": tooltip_text,
    }
    print(json.dumps(out_data))
    # try:
    #     with open(os.path.expanduser("~/.cache/.steamsale_cache"), "w") as file:
    #         file.write(json.dumps(out_data))
    # except:
    #     pass
