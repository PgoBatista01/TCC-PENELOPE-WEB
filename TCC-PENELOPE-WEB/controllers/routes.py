
import os
from datetime import date
from types import SimpleNamespace
from werkzeug.utils import secure_filename
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from sqlalchemy import func

from models.database import (
    db,
    Passaro,
    Canto,
    ImgPassaro,
    Usuario,
    AvistamentoImg,
    AvistamentoAudio,
    AvistamentoVideo,
)


EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
TAMANHO_MAXIMO_FOTO = 16 * 1024 * 1024


def init_app(app):

    # ==========================================
    # PÁGINA INICIAL
    # ==========================================
    @app.route("/")
    def home():
        return render_template("index.html")

    # ==========================================
    # CATÁLOGO DE AVES
    # ==========================================
    @app.route("/aves")
    def aves():
        pesquisa = request.args.get("pesquisa", "").strip()

        consulta = Passaro.query

        if pesquisa:
            termo = f"%{pesquisa}%"
            consulta = consulta.filter(
                db.or_(
                    Passaro.nome_popular.ilike(termo),
                    Passaro.nome_binomial.ilike(termo),
                )
            )

        listaPassaros = consulta.order_by(
            Passaro.nome_popular
        ).all()

        return render_template(
            "aves.html",
            listaPassaros=listaPassaros,
            pesquisa=pesquisa,
        )

    # ==========================================
    # DETALHES DE UMA AVE
    # ==========================================
    @app.route("/aves/<int:id>")
    def detalhes_ave(id):
        passaro = Passaro.query.get_or_404(id)

        imagens = (
            ImgPassaro.query
            .filter_by(passaro_id=id)
            .order_by(ImgPassaro.img_passaro_order)
            .all()
        )

        cantos = (
            Canto.query
            .filter_by(passaro_id=id)
            .order_by(Canto.canto_order)
            .all()
        )

        return render_template(
            "detalhes_aves.html",
            passaro=passaro,
            imagens=imagens,
            cantos=cantos,
        )

    # ==========================================
    # CADASTRO DE AVES
    # ==========================================
    @app.route("/cadastro_ave", methods=["GET", "POST"])
    def cadastro_ave():
        if request.method == "POST":
            nome_popular = request.form.get(
                "nome_popular", ""
            ).strip()

            nome_binomial = request.form.get(
                "nome_binomial", ""
            ).strip()

            familia = request.form.get(
                "passaro_familia", ""
            ).strip()

            estado = request.form.get(
                "estado_conservacao", ""
            ).strip().upper()

            descricao = request.form.get(
                "passaro_descricao", ""
            ).strip()

            envergadura_texto = request.form.get(
                "envergadura_cm", ""
            ).strip()

            if not nome_popular or not nome_binomial:
                flash(
                    "Preencha o nome popular e o nome científico.",
                    "error",
                )
                return redirect(url_for("cadastro_ave"))

            if estado and len(estado) != 2:
                flash(
                    "O estado de conservação deve usar a sigla de duas letras.",
                    "error",
                )
                return redirect(url_for("cadastro_ave"))

            try:
                envergadura = (
                    float(envergadura_texto)
                    if envergadura_texto
                    else None
                )

                if envergadura is not None and envergadura <= 0:
                    raise ValueError

            except ValueError:
                flash(
                    "Informe uma envergadura válida em centímetros.",
                    "error",
                )
                return redirect(url_for("cadastro_ave"))

            novo_passaro = Passaro(
                nome_popular=nome_popular,
                nome_binomial=nome_binomial,
                passaro_familia=familia or None,
                estado_conservacao=estado or None,
                passaro_descricao=descricao or None,
                envergadura_cm=envergadura,
            )

            try:
                db.session.add(novo_passaro)
                db.session.commit()
                flash("Ave cadastrada com sucesso!", "success")
                return redirect(
                    url_for(
                        "detalhes_ave",
                        id=novo_passaro.passaro_id,
                    )
                )

            except Exception:
                db.session.rollback()
                current_app.logger.exception(
                    "Erro ao cadastrar ave."
                )
                flash(
                    "Não foi possível cadastrar a ave. Confira os dados e o banco.",
                    "error",
                )

            return redirect(url_for("cadastro_ave"))

        return render_template("cadastro_aves.html")

    # ==========================================
    # AVISTAMENTOS
    # ==========================================
    @app.route("/avistamentos", methods=["GET", "POST"])
    def avistamentos():
        lista_aves = Passaro.query.order_by(
            Passaro.nome_popular
        ).all()

        if request.method == "POST":
            passaro_id = request.form.get("passaro_id", "").strip()
            data_texto = request.form.get(
                "data_avistamento", ""
            ).strip()
            descricao = request.form.get("descricao", "").strip()
            latitude_texto = request.form.get("latitude", "").strip()
            longitude_texto = request.form.get("longitude", "").strip()
            foto = request.files.get("foto")

            try:
                passaro_id = int(passaro_id)
                passaro = Passaro.query.get(passaro_id)

                if passaro is None:
                    raise ValueError("Ave não encontrada.")

                data_avistamento = (
                    date.fromisoformat(data_texto)
                    if data_texto
                    else date.today()
                )

                latitude = (
                    float(latitude_texto)
                    if latitude_texto
                    else None
                )

                longitude = (
                    float(longitude_texto)
                    if longitude_texto
                    else None
                )

                if latitude is not None and not -90 <= latitude <= 90:
                    raise ValueError("Latitude inválida.")

                if longitude is not None and not -180 <= longitude <= 180:
                    raise ValueError("Longitude inválida.")

            except (ValueError, TypeError):
                flash(
                    "Confira a ave selecionada, a data e as coordenadas.",
                    "error",
                )
                return redirect(url_for("avistamentos"))

            # A tabela atual de avistamentos é baseada em imagens.
            if not foto or not foto.filename:
                flash(
                    "Selecione uma foto para registrar o avistamento.",
                    "error",
                )
                return redirect(url_for("avistamentos"))

            nome_arquivo = secure_filename(foto.filename)

            if (
                not nome_arquivo
                or "." not in nome_arquivo
                or nome_arquivo.rsplit(".", 1)[1].lower()
                not in EXTENSOES_PERMITIDAS
            ):
                flash(
                    "Formato inválido. Use PNG, JPG, JPEG ou WEBP.",
                    "error",
                )
                return redirect(url_for("avistamentos"))

            # Esta versão usa o primeiro usuário cadastrado como autor.
            # Depois, podemos substituir pela sessão do usuário autenticado.
            usuario = Usuario.query.first()

            if usuario is None:
                flash(
                    "Cadastre um usuário antes de enviar avistamentos.",
                    "error",
                )
                return redirect(url_for("avistamentos"))

            pasta_upload = os.path.join(
                current_app.static_folder,
                "uploads",
                "avistamentos",
            )
            os.makedirs(pasta_upload, exist_ok=True)

            caminho = os.path.join(pasta_upload, nome_arquivo)

            # Evita sobrescrever uma foto que já exista.
            base, extensao = os.path.splitext(nome_arquivo)
            contador = 1

            while os.path.exists(caminho):
                nome_arquivo = f"{base}_{contador}{extensao}"
                caminho = os.path.join(pasta_upload, nome_arquivo)
                contador += 1

            try:
                foto.save(caminho)

                novo_registro = AvistamentoImg(
                    avistamento_img_descricao=descricao or None,
                    avistamento_img_latitude=latitude,
                    avistamento_img_longitude=longitude,
                    avistamento_img_date=data_avistamento,
                    avistamento_img_filename=nome_arquivo,
                    avistamento_img_filepath=(
                        f"uploads/avistamentos/{nome_arquivo}"
                    ),
                    avistamento_img_filetype=(
                        foto.mimetype or "application/octet-stream"
                    ),
                    avistamento_img_filesize=os.path.getsize(caminho),
                    usuario_id=usuario.usuario_id,
                    passaro_id=passaro_id,
                )

                db.session.add(novo_registro)
                db.session.commit()

                flash(
                    "Avistamento registrado com sucesso!",
                    "success",
                )
                return redirect(url_for("avistamentos"))

            except Exception:
                db.session.rollback()

                if os.path.exists(caminho):
                    os.remove(caminho)

                current_app.logger.exception(
                    "Erro ao salvar avistamento."
                )
                flash(
                    "Não foi possível salvar o avistamento. Confira o banco de dados.",
                    "error",
                )
                return redirect(url_for("avistamentos"))

        return render_template(
            "avistamentos.html",
            lista_aves=lista_aves,
        )

    # ==========================================
    # MAPA DE AVISTAMENTOS
    # ==========================================
    @app.route("/mapa")
    def mapa():
        registros = (
            db.session.query(
                AvistamentoImg,
                Passaro.nome_popular,
            )
            .outerjoin(
                Passaro,
                AvistamentoImg.passaro_id == Passaro.passaro_id,
            )
            .all()
        )

        pontos_mapa = []

        for registro, nome_popular in registros:
            latitude = registro.avistamento_img_latitude
            longitude = registro.avistamento_img_longitude

            if latitude is None or longitude is None:
                continue

            pontos_mapa.append({
                "latitude": latitude,
                "longitude": longitude,
                "nome": nome_popular or "Ave não identificada",
                "data": str(
                    registro.avistamento_img_date or ""
                ),
                "descricao": (
                    registro.avistamento_img_descricao or ""
                ),
            })

        return render_template(
            "mapa.html",
            pontos_mapa=pontos_mapa,
        )

    # ==========================================
    # ESTATÍSTICAS
    # ==========================================
    @app.route("/estatisticas")
    def estatisticas():
        total_passaros = Passaro.query.count()
        total_avistamentos = AvistamentoImg.query.count()

        total_fotos = AvistamentoImg.query.filter(
            AvistamentoImg.avistamento_img_filepath.isnot(None)
        ).count()

        total_cantos = Canto.query.count()

        ranking = (
            db.session.query(
                Passaro.nome_popular.label("nome_popular"),
                func.count(
                    AvistamentoImg.avistamento_img_id
                ).label("total"),
            )
            .join(
                AvistamentoImg,
                Passaro.passaro_id == AvistamentoImg.passaro_id,
            )
            .group_by(
                Passaro.passaro_id,
                Passaro.nome_popular,
            )
            .order_by(
                func.count(
                    AvistamentoImg.avistamento_img_id
                ).desc()
            )
            .limit(5)
            .all()
        )

        return render_template(
            "estatisticas.html",
            total_passaros=total_passaros,
            total_avistamentos=total_avistamentos,
            total_fotos=total_fotos,
            total_cantos=total_cantos,
            ranking=ranking,
        )

    # ==========================================
    # SOBRE O PROJETO
    # ==========================================
    @app.route("/sobre")
    def sobre():
        return render_template("sobre.html")

    # ==========================================
    # VALIDAÇÃO DOS REGISTROS
    # ==========================================
    @app.route("/validacao")
    def validacao():
        registros_banco = (
            db.session.query(
                AvistamentoImg,
                Passaro.nome_popular,
            )
            .outerjoin(
                Passaro,
                AvistamentoImg.passaro_id == Passaro.passaro_id,
            )
            .order_by(
                AvistamentoImg.avistamento_img_date.desc()
            )
            .all()
        )

        registros = []

        for registro, nome_popular in registros_banco:
            # O modelo atual não possui um status de validação confirmado.
            # "Pendente" é apenas um valor visual, não salvo no banco.
            registros.append(
                SimpleNamespace(
                    nome_ave=nome_popular or "Ave não identificada",
                    data=registro.avistamento_img_date,
                    descricao=registro.avistamento_img_descricao,
                    status="Pendente",
                )
            )

        return render_template(
            "validacao.html",
            registros=registros,
        )
