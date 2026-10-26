
import requests

API_URL = "https://commons.wikimedia.org/w/api.php"


def buscar_imagens(nome_passaro, limite=6):
    parametros = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{nome_passaro} bird",
        "gsrnamespace": 6,
        "gsrlimit": limite,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 600,
        "format": "json"
    }

    try:
        resposta = requests.get(
            API_URL,
            params=parametros,
            headers={
                "User-Agent": "PenelopeProjeto/1.0 (site educacional)"
            },
            timeout=10
        )

        resposta.raise_for_status()
        dados = resposta.json()

        paginas = dados.get("query", {}).get("pages", {})
        imagens = []

        for pagina in paginas.values():
            informacoes = pagina.get("imageinfo", [])

            if not informacoes:
                continue

            info = informacoes[0]
            metadados = info.get("extmetadata", {})

            imagens.append({
                "titulo": pagina.get("title", ""),
                "url": info.get(
                    "thumburl",
                    info.get("url", "")
                ),
                "pagina_origem": info.get("descriptionurl", ""),
                "autor": metadados.get(
                    "Artist", {}
                ).get("value", "Não informado"),
                "licenca": metadados.get(
                    "LicenseShortName", {}
                ).get("value", "Verificar licença")
            })

        return imagens

    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao buscar imagens de aves: {erro}")
        return []
