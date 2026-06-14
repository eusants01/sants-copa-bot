import os
import aiohttp

from datetime import datetime
from zoneinfo import ZoneInfo


BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"


class FootballAPI:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_API_KEY")

    async def get(self, endpoint: str):
        if not self.api_key:
            print("❌ FOOTBALL_API_KEY não encontrada nas variáveis de ambiente.")
            return None

        headers = {
            "X-Auth-Token": self.api_key
        }

        url = f"{BASE_URL}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()

                        print("=" * 60)
                        print("❌ FOOTBALL DATA API ERROR")
                        print(f"STATUS: {response.status}")
                        print(f"URL: {url}")
                        print(f"ENDPOINT: {endpoint}")
                        print(f"RESPOSTA: {error_text}")
                        print("=" * 60)

                        return None

                    return await response.json()

        except Exception as error:
            print("=" * 60)
            print("❌ ERRO AO CONSULTAR API")
            print(f"URL: {url}")
            print(f"ERRO: {error}")
            print("=" * 60)

            return None

    async def get_matches(self):
        return await self.get(f"/competitions/{COMPETITION}/matches")

    async def get_standings(self):
        return await self.get(f"/competitions/{COMPETITION}/standings")

    async def test_connection(self):
        return await self.get("/competitions")

    def match_datetime_br(self, utc_date: str):
        if not utc_date:
            return "Horário indefinido"

        try:
            date = datetime.fromisoformat(
                utc_date.replace("Z", "+00:00")
            )

            br_date = date.astimezone(
                ZoneInfo("America/Sao_Paulo")
            )

            return br_date.strftime("%d/%m às %H:%M")

        except Exception:
            return "Horário indefinido"
        