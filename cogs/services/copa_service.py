import json
from pathlib import Path


DATA_PATH = Path("data/copa.json")


class CopaService:
    @staticmethod
    def carregar():
        try:
            with DATA_PATH.open("r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except Exception:
            return {
                "ultima_atualizacao": "",
                "destaque": "",
                "grupos": {},
                "jogos_hoje": [],
                "proximos_jogos": [],
                "ranking": []
            }

    @staticmethod
    def salvar(dados):
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

        with DATA_PATH.open("w", encoding="utf-8") as arquivo:
            json.dump(
                dados,
                arquivo,
                indent=4,
                ensure_ascii=False
            )