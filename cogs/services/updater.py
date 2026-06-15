import json
from datetime import datetime
from zoneinfo import ZoneInfo

from cogs.services.football_api import FootballAPI


DATA_PATH = "data/copa.json"


class CopaUpdater:
    @staticmethod
    def horario_br(data_iso):
        if not data_iso:
            return "A definir"

        try:
            data = datetime.fromisoformat(
                data_iso.replace("Z", "+00:00")
            )

            data_br = data.astimezone(
                ZoneInfo("America/Sao_Paulo")
            )

            return data_br.strftime("%d/%m/%Y"), data_br.strftime("%H:%M")

        except Exception:
            return "A definir", "A definir"

    @staticmethod
    def nome_time(time):
        if not time:
            return "A definir"

        return time.get("name") or "A definir"

    @staticmethod
    def status_partida(status):
        status_map = {
            "NS": "Em breve",
            "TBD": "A definir",
            "1H": "Ao vivo",
            "HT": "Intervalo",
            "2H": "Ao vivo",
            "ET": "Prorrogação",
            "P": "Pênaltis",
            "FT": "Encerrado",
            "AET": "Encerrado",
            "PEN": "Encerrado",
            "PST": "Adiado",
            "CANC": "Cancelado"
        }

        return status_map.get(status, status or "A definir")

    @staticmethod
    def extrair_grupos(standings):
        grupos = {letra: [] for letra in "ABCDEFGHIJKL"}

        try:
            response = standings.get("response", [])

            for liga in response:
                league = liga.get("league", {})
                standings_data = league.get("standings", [])

                for grupo in standings_data:
                    if not grupo:
                        continue

                    group_name = grupo[0].get("group", "")

                    letra = group_name[-1].upper()

                    if letra not in grupos:
                        continue

                    linhas = []

                    for time in grupo:
                        rank = time.get("rank", "-")
                        team = time.get("team", {}).get("name", "Time")
                        points = time.get("points", 0)
                        played = time.get("all", {}).get("played", 0)
                        win = time.get("all", {}).get("win", 0)
                        draw = time.get("all", {}).get("draw", 0)
                        lose = time.get("all", {}).get("lose", 0)
                        goals_diff = time.get("goalsDiff", 0)

                        linhas.append(
                            f"{rank}º {team} — {points} pts | "
                            f"J:{played} V:{win} E:{draw} D:{lose} SG:{goals_diff}"
                        )

                    grupos[letra] = linhas

        except Exception as erro:
            print(f"❌ Erro ao extrair grupos: {erro}")

        return grupos

    @staticmethod
    def extrair_brasil(standings, fixtures):
        brasil = {
            "grupo": "-",
            "posicao": "-",
            "pontos": 0,
            "jogos": 0,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 0,
            "gols_contra": 0,
            "saldo_gols": 0,
            "proximo_jogo": "A definir",
            "data": "A definir",
            "horario": "A definir",
            "status": "A definir"
        }

        try:
            for liga in standings.get("response", []):
                for grupo in liga.get("league", {}).get("standings", []):
                    for time in grupo:
                        team_name = time.get("team", {}).get("name", "")

                        if team_name.lower() == "brazil":
                            group_name = time.get("group", "")
                            brasil["grupo"] = group_name[-1].upper()
                            brasil["posicao"] = f"{time.get('rank', '-') }º"
                            brasil["pontos"] = time.get("points", 0)
                            brasil["jogos"] = time.get("all", {}).get("played", 0)
                            brasil["vitorias"] = time.get("all", {}).get("win", 0)
                            brasil["empates"] = time.get("all", {}).get("draw", 0)
                            brasil["derrotas"] = time.get("all", {}).get("lose", 0)
                            brasil["gols_pro"] = time.get("all", {}).get("goals", {}).get("for", 0)
                            brasil["gols_contra"] = time.get("all", {}).get("goals", {}).get("against", 0)
                            brasil["saldo_gols"] = time.get("goalsDiff", 0)

        except Exception as erro:
            print(f"❌ Erro ao extrair Brasil na classificação: {erro}")

        try:
            proximos = []

            for item in fixtures.get("response", []):
                teams = item.get("teams", {})
                home = teams.get("home", {})
                away = teams.get("away", {})

                home_name = CopaUpdater.nome_time(home)
                away_name = CopaUpdater.nome_time(away)

                envolve_brasil = home_name.lower() == "brazil" or away_name.lower() == "brazil"

                if not envolve_brasil:
                    continue

                status_short = item.get("fixture", {}).get("status", {}).get("short")
                status = CopaUpdater.status_partida(status_short)

                if status == "Encerrado":
                    continue

                data, horario = CopaUpdater.horario_br(
                    item.get("fixture", {}).get("date")
                )

                proximos.append({
                    "jogo": f"{home_name} x {away_name}",
                    "data": data,
                    "horario": horario,
                    "status": status
                })

            if proximos:
                proximo = proximos[0]
                brasil["proximo_jogo"] = proximo["jogo"]
                brasil["data"] = proximo["data"]
                brasil["horario"] = proximo["horario"]
                brasil["status"] = proximo["status"]

        except Exception as erro:
            print(f"❌ Erro ao buscar próximo jogo do Brasil: {erro}")

        return brasil

    @staticmethod
    def extrair_jogos(fixtures):
        jogos_hoje = []
        proximos_jogos = []

        hoje = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime("%d/%m/%Y")

        try:
            for item in fixtures.get("response", []):
                teams = item.get("teams", {})
                home = CopaUpdater.nome_time(teams.get("home", {}))
                away = CopaUpdater.nome_time(teams.get("away", {}))

                data, horario = CopaUpdater.horario_br(
                    item.get("fixture", {}).get("date")
                )

                status = CopaUpdater.status_partida(
                    item.get("fixture", {}).get("status", {}).get("short")
                )

                goals = item.get("goals", {})
                home_goals = goals.get("home")
                away_goals = goals.get("away")

                if home_goals is not None and away_goals is not None:
                    texto = f"✅ {home} {home_goals} x {away_goals} {away} — {status}"
                else:
                    texto = f"🟡 {home} x {away} — {data} às {horario}"

                if data == hoje:
                    jogos_hoje.append(texto)
                elif len(proximos_jogos) < 6 and status != "Encerrado":
                    proximos_jogos.append(texto)

        except Exception as erro:
            print(f"❌ Erro ao extrair jogos: {erro}")

        if not jogos_hoje:
            jogos_hoje = ["📌 Nenhum jogo cadastrado para hoje."]

        if not proximos_jogos:
            proximos_jogos = ["📌 Nenhum próximo jogo encontrado."]

        return jogos_hoje, proximos_jogos

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

        grupos = CopaUpdater.extrair_grupos(standings)
        brasil = CopaUpdater.extrair_brasil(standings, fixtures)
        jogos_hoje, proximos_jogos = CopaUpdater.extrair_jogos(fixtures)

        dados = {
            "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y às %H:%M"),

            "destaque": [
                "🔥 Dados sincronizados automaticamente pela API-Football.",
                "🎯 Faça seus palpites.",
                "🏆 Dispute o ranking.",
                "🇧🇷 Acompanhe o Brasil rumo ao Hexa."
            ],

            "selecao_brasil": brasil,

            "grupos": grupos,

            "jogos_hoje": jogos_hoje,

            "proximos_jogos": proximos_jogos,

            "ranking": [
                "🥇 Em breve",
                "🥈 Em breve",
                "🥉 Em breve"
            ]
        }

        with open(
            DATA_PATH,
            "w",
            encoding="utf-8"
        ) as arquivo:
            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        print("✅ Copa atualizada com estrutura padronizada.")