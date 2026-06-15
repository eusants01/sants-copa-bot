import json

from cogs.services.football_api import FootballAPI


class CopaUpdater:

    @staticmethod
    async def atualizar():

        api = FootballAPI()

        fixtures = await api.get_fixtures()

        standings = await api.get_standings()

        if not fixtures:
            print("❌ Fixtures indisponíveis.")
            return

        if not standings:
            print("❌ Standings indisponíveis.")
            return

        dados = {
            "fixtures": fixtures,
            "standings": standings
        }

        with open(
            "data/copa.json",
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        print("✅ Copa atualizada com sucesso.")