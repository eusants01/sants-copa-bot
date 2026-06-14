import os
import aiohttp
from datetime import datetime, timezone


BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"


class FootballAPI:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_API_KEY")

    async def get(self, endpoint: str):
        if not self.api_key:
            return None

        headers = {"X-Auth-Token": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}{endpoint}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        print(f"API ERROR {response.status}: {await response.text()}")
                        return None

                    return await response.json()
        except Exception as error:
            print(f"Erro ao consultar API: {error}")
            return None

    async def get_matches(self):
        return await self.get(f"/competitions/{COMPETITION}/matches")

    async def get_standings(self):
        return await self.get(f"/competitions/{COMPETITION}/standings")

    def match_datetime_br(self, utc_date: str):
        if not utc_date:
            return "Horário indefinido"

        try:
            date = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
            return date.astimezone().strftime("%d/%m às %H:%M")
        except Exception:
            return "Horário indefinido"