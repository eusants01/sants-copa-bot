import json
from datetime import datetime


class CopaUpdater:

    @staticmethod
    async def atualizar():

        with open(
            "data/copa.json",
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

        dados["ultima_atualizacao"] = datetime.now().strftime(
            "%d/%m/%Y às %H:%M"
        )

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

        print(
            "✅ Copa atualizada."
        )