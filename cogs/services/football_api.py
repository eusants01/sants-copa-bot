import os
import aiohttp


class FootballAPI:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.host = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
        self.base_url = f"https://{self.host}"

        self.league_id = os.getenv("WORLD_CUP_LEAGUE_ID", "732")
        self.season = os.getenv("WORLD_CUP_SEASON", "2026")

    async def get(self, endpoint: str, params: dict | None = None):
        if not self.api_key:
            print("❌ API_FOOTBALL_KEY não encontrada.")
            return None

        headers = {
            "x-apisports-key": self.api_key
        }

        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:

                    data = await response.json()

                    if response.status != 200:
                        print("=" * 60)
                        print("❌ API-FOOTBALL ERROR")
                        print(f"STATUS: {response.status}")
                        print(f"URL: {url}")
                        print(f"PARAMS: {params}")
                        print(f"RESPOSTA: {data}")
                        print("=" * 60)
                        return None

                    return data

        except Exception as error:
            print("=" * 60)
            print("❌ ERRO AO CONSULTAR API-FOOTBALL")
            print(f"ERRO: {error}")
            print("=" * 60)
            return None

    async def get_fixtures(self):
        return await self.get(
            "/fixtures",
            {
                "league": self.league_id,
                "season": self.season
            }
        )

    async def get_standings(self):
        return await self.get(
            "/standings",
            {
                "league": self.league_id,
                "season": self.season
            }
        )

    async def test_connection(self):
        return await self.get(
            "/status"
        )