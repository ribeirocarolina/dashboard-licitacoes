#!/usr/bin/env python3
"""Radar de licitações de tecnologia: servidor local + dashboard.

Uso:  python3 servidor.py
Abre o dashboard em http://127.0.0.1:8765 (mantenha index.html na mesma pasta).
Só usa a biblioteca padrão do Python 3.8+. Nada para instalar.

O navegador conversa com este servidor, e o servidor consulta o PNCP.
Assim não há bloqueio de CORS e não precisa importar JSON.
"""
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORTA = 8765
PNCP = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
HTML = Path(__file__).with_name("index.html")
TIMEOUT = 40

# Termos que descartam o edital mesmo se casar com as palavras-chave.
EXCLUIR = [r"medicament", r"merenda", r"obra de engenharia", r"veiculo"]
CONSULTORIA = [r"consultoria", r"assessoria", r"mentoria", r"treinamento"]


def norm(txt):
    txt = unicodedata.normalize("NFD", txt or "")
    return "".join(c for c in txt if unicodedata.category(c) != "Mn").lower()


def casa(padroes, texto):
    return any(p.search(texto) for p in padroes)


def compilar(lista):
    saida = []
    for s in lista:
        s = norm(s.strip())
        if not s:
            continue
        try:
            saida.append(re.compile(s))
        except re.error:
            saida.append(re.compile(re.escape(s)))
    return saida


PAD_EXCLUIR = compilar(EXCLUIR)
PAD_CONSULT = compilar(CONSULTORIA)


def consultar_pncp(params):
    url = PNCP + "?" + urllib.parse.urlencode(params)
    for tentativa in range(3):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                corpo = r.read().decode("utf-8")
                return json.loads(corpo) if corpo.strip() else {"data": []}
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return {"data": []}
            detalhe = e.read().decode("utf-8", "replace")[:300]
            if e.code >= 500 and tentativa < 2:
                time.sleep(2 * (tentativa + 1))
                continue
            raise RuntimeError(f"O PNCP respondeu HTTP {e.code}. {detalhe}")
        except (urllib.error.URLError, TimeoutError) as e:
            if tentativa == 2:
                raise RuntimeError(f"Não consegui falar com o PNCP: {e}")
            time.sleep(2 * (tentativa + 1))


def converter(c, incluir):
    objeto = c.get("objetoCompra") or ""
    t = norm(objeto)
    if not casa(incluir, t) or casa(PAD_EXCLUIR, t):
        return None
    org = c.get("orgaoEntidade") or {}
    uni = c.get("unidadeOrgao") or {}
    cnpj, ano, seq = org.get("cnpj", ""), c.get("anoCompra"), c.get("sequencialCompra")
    link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}" if cnpj and ano and seq else (c.get("linkSistemaOrigem") or "")
    valor = c.get("valorTotalEstimado")
    return {
        "id": str(c.get("numeroControlePNCP") or f"{cnpj}-{ano}-{seq}"),
        "titulo": objeto.strip()[:220],
        "publico": "consultor" if casa(PAD_CONSULT, t) else "empresa",
        "orgao": org.get("razaoSocial", ""),
        "local": " - ".join(x for x in [uni.get("municipioNome"), uni.get("ufSigla")] if x),
        "modalidade": c.get("modalidadeNome", ""),
        "prazo": (c.get("dataEncerramentoProposta") or "")[:10],
        "valor": valor if isinstance(valor, (int, float)) and valor > 0 else None,
        "link": link,
    }


def buscar_pagina(q):
    def um(chave, padrao=""):
        return (q.get(chave) or [padrao])[0]

    dias = max(1, min(365, int(um("dias", "60"))))
    pagina = max(1, int(um("pagina", "1")))
    params = {
        "dataFinal": (date.today() + timedelta(days=dias)).strftime("%Y%m%d"),
        "codigoModalidadeContratacao": int(um("mod", "6")),
        "pagina": pagina,
        "tamanhoPagina": 50,
    }
    if um("uf"):
        params["uf"] = um("uf")[:2].upper()
    incluir = compilar(um("termos").split(","))
    r = consultar_pncp(params)
    dados = r.get("data") or []
    itens = [i for i in (converter(c, incluir) for c in dados) if i]
    return {"itens": itens, "pagina": pagina, "totalPaginas": r.get("totalPaginas") or 1, "lidos": len(dados)}


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo, tipo):
        dados = corpo if isinstance(corpo, bytes) else corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            if not HTML.exists():
                return self.responder(500, "index.html não encontrado ao lado do servidor.py", "text/plain; charset=utf-8")
            return self.responder(200, HTML.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/api/pagina":
            try:
                saida = buscar_pagina(urllib.parse.parse_qs(url.query))
                return self.responder(200, json.dumps(saida, ensure_ascii=False), "application/json; charset=utf-8")
            except Exception as e:  # erro vai para a tela, sem derrubar o servidor
                return self.responder(502, json.dumps({"erro": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")
        self.responder(404, "Não encontrado", "text/plain; charset=utf-8")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # 127.0.0.1: acessível só neste computador.
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    endereco = f"http://127.0.0.1:{PORTA}"
    print(f"Radar rodando em {endereco}  (Ctrl+C para encerrar)")
    try:
        webbrowser.open(endereco)
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
