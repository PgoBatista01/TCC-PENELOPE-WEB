
from datetime import date
import os

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify
)
from werkzeug.utils import secure_filename

from controllers.api_imagens import buscar_imagens

from models.database import (
    db,
    Passaro,
    ImgPassaro,
    Canto,
    Usuario,
    AvistamentoImg,
    AvistamentoAudio,
    AvistamentoVideo
)


def init_app(app):

    # Página inicial
    @app.route("/")
    def home():
        return render_template("index.html")

    # Catálogo de aves
    @app.route("/aves")
    def aves():
        pesquisa = request.args.get("q", "").strip()

        consulta = Passaro.query

        if pesquisa:
            consulta = consulta.filter(
                db.or_(
                    Passaro.nome_popular.ilike(f"%{pesquisa}%"),
                    Passaro.nome_binomial.ilike(f"%{pesquisa}%"),
                    Passaro.passaro_familia.ilike(f"%{pesquisa}%")
                )
            )

        lista_aves = consulta.order_by(
            Passaro.nome_popular
        ).all()

        return render_template(
            "aves.html",
            aves=lista_aves,
            pesquisa=pesquisa
        )

    # Cadastro de aves
    @app.route("/cadastro-aves", methods=["GET", "POST"])
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
            ).strip()

            descricao = request.form.get(
                "passaro_descricao", ""
            ).strip()

            envergadura_texto = request.form.get(
                "envergadura_cm", ""
            ).strip()

            if not all([
                nome_popular,
                nome_binomial,
                familia,
                estado,
                descricao,
                envergadura_texto
            ]):
                flash(
                    "Preencha todos os campos obrigatórios.",
                    "erro"
                )
                return redirect(url_for("cadastro_ave"))

            try:
                envergadura = int(
                    envergadura_texto.replace(",", ".")
                )

                if envergadura <= 0:
                    raise ValueError

            except ValueError:
                flash(
                    "Informe uma envergadura inteira válida.",
                    "erro"
                )
                return redirect(url_for("cadastro_ave"))

            ave = Passaro(
                nome_popular=nome_popular,
                nome_binomial=nome_binomial,
                passaro_familia=familia,
                estado_conservacao=estado,
                passaro_descricao=descricao,
                envergadura_cm=envergadura
            )

            try:
                db.session.add(ave)
                db.session.flush()

                arquivo = request.files.get("imagem")

                if arquivo and arquivo.filename:
                    nome_arquivo = secure_filename(
                        arquivo.filename
                    )

                    if not nome_arquivo:
                        raise ValueError("Nome de imagem inválido.")

                    pasta = os.path.join(
                        app.static_folder,
                        "uploads",
                        "aves"
                    )
                    os.makedirs(pasta, exist_ok=True)

                    caminho = os.path.join(pasta, nome_arquivo)
                    arquivo.save(caminho)

                    imagem = ImgPassaro(
                        passaro_id=ave.passaro_id,
                        img_passaro_filename=nome_arquivo,
                        img_passaro_filepath=(
                            f"uploads/aves/{nome_arquivo}"
                        ),
                        img_passaro_filetype=arquivo.mimetype
                    )

                    db.session.add(imagem)

                db.session.commit()

                flash("Ave cadastrada com sucesso!", "sucesso")

                return redirect(
                    url_for(
                        "detalhes_aves",
                        passaro_id=ave.passaro_id
                    )
                )

            except Exception as erro:
                db.session.rollback()
                app.logger.exception(
                    "Erro ao cadastrar ave: %s", erro
                )
                flash(
                    "Não foi possível cadastrar a ave. "
                    "Confira os dados e tente novamente.",
                    "erro"
                )
                return redirect(url_for("cadastro_ave"))

        return render_template("cadastro_aves.html")

    # Detalhes de uma ave
    @app.route(
        "/aves/<int:passaro_id>",
        endpoint="detalhes_aves"
    )
    def detalhes_aves(passaro_id):
        passaro = Passaro.query.get_or_404(passaro_id)

        imagens = ImgPassaro.query.filter_by(
            passaro_id=passaro_id
        ).all()

        cantos = Canto.query.filter_by(
            passaro_id=passaro_id
        ).all()

        return render_template(
            "detalhes_aves.html",
            passaro=passaro,
            ave=passaro,
            imagens=imagens,
            cantos=cantos
        )

    # API externa de imagens
    @app.route("/api/imagens-aves")
    def api_imagens_aves():
        nome = request.args.get("nome", "").strip()

        if not nome:
            return jsonify({
                "erro": "Informe o nome popular ou científico da ave."
            }), 400

        imagens = buscar_imagens(nome)

        return jsonify({
            "passaro": nome,
            "total": len(imagens),
            "imagens": imagens
        })

    # Avistamentos com imagem
    @app.route("/avistamentos", methods=["GET", "POST"])
    def avistamentos():
        if request.method == "POST":
            usuario_id = session.get("usuario_id")

            if not usuario_id:
                flash(
                    "Faça login para registrar um avistamento.",
                    "erro"
                )
                return redirect(url_for("login"))

            passaro_id = request.form.get("passaro_id", "").strip()
            descricao = request.form.get(
                "descricao", ""
            ).strip()

            latitude_texto = request.form.get(
                "latitude", ""
            ).strip()

            longitude_texto = request.form.get(
                "longitude", ""
            ).strip()

            arquivo = request.files.get("imagem")

            if not passaro_id:
                flash("Selecione uma ave.", "erro")
                return redirect(url_for("avistamentos"))

            if not arquivo or not arquivo.filename:
                flash(
                    "Envie uma imagem para registrar o avistamento.",
                    "erro"
                )
                return redirect(url_for("avistamentos"))

            try:
                passaro_id = int(passaro_id)

                passaro = Passaro.query.get(passaro_id)
                usuario = Usuario.query.get(usuario_id)

                if not passaro or not usuario:
                    flash(
                        "A ave ou o usuário informado não foi encontrado.",
                        "erro"
                    )
                    return redirect(url_for("avistamentos"))

                latitude = (
                    float(latitude_texto.replace(",", "."))
                    if latitude_texto else None
                )

                longitude = (
                    float(longitude_texto.replace(",", "."))
                    if longitude_texto else None
                )

                if latitude is not None and not -90 <= latitude <= 90:
                    raise ValueError("Latitude fora do intervalo permitido.")

                if longitude is not None and not -180 <= longitude <= 180:
                    raise ValueError("Longitude fora do intervalo permitido.")

            except ValueError:
                flash(
                    "Confira o código da ave e as coordenadas informadas.",
                    "erro"
                )
                return redirect(url_for("avistamentos"))

            nome_arquivo = secure_filename(arquivo.filename)

            if not nome_arquivo:
                flash("O nome do arquivo é inválido.", "erro")
                return redirect(url_for("avistamentos"))

            pasta = os.path.join(
                app.static_folder,
                "uploads",
                "avistamentos"
            )
            os.makedirs(pasta, exist_ok=True)

            caminho = os.path.join(pasta, nome_arquivo)
            caminho_relativo = f"uploads/avistamentos/{nome_arquivo}"

            try:
                arquivo.save(caminho)

                avistamento = AvistamentoImg(
                    usuario_id=usuario_id,
                    passaro_id=passaro_id,
                    avistamento_img_descricao=descricao,
                    avistamento_img_latitude=latitude,
                    avistamento_img_longitude=longitude,
                    avistamento_img_date=date.today(),
                    avistamento_img_filename=nome_arquivo,
                    avistamento_img_filepath=caminho_relativo,
                    avistamento_img_filetype=arquivo.mimetype
                )

                tamanho = os.path.getsize(caminho)
                avistamento.avistamento_img_filesize = tamanho

                db.session.add(avistamento)
                db.session.commit()

                flash(
                    "Avistamento registrado com sucesso!",
                    "sucesso"
                )

                return redirect(url_for("avistamentos"))

            except Exception as erro:
                db.session.rollback()

                if os.path.exists(caminho):
                    os.remove(caminho)

                app.logger.exception(
                    "Erro ao registrar avistamento: %s", erro
                )

                flash(
                    "Não foi possível registrar o avistamento.",
                    "erro"
                )
                return redirect(url_for("avistamentos"))

        lista_aves = Passaro.query.order_by(
            Passaro.nome_popular
        ).all()

        lista_avistamentos = AvistamentoImg.query.order_by(
            AvistamentoImg.avistamento_img_id.desc()
        ).all()

        return render_template(
            "avistamentos.html",
            aves=lista_aves,
            avistamentos=lista_avistamentos
        )

    # Estatísticas
    @app.route("/estatisticas")
    def estatisticas():
        total_aves = Passaro.query.count()

        total_imagens = AvistamentoImg.query.count()
        total_audios = AvistamentoAudio.query.count()
        total_videos = AvistamentoVideo.query.count()

        total_avistamentos = (
            total_imagens + total_audios + total_videos
        )

        return render_template(
            "estatisticas.html",
            total_aves=total_aves,
            total_avistamentos=total_avistamentos
        )

    # Mapa: registros com coordenadas
    @app.route("/mapa")
    def mapa():
        lista_avistamentos = AvistamentoImg.query.filter(
            AvistamentoImg.avistamento_img_latitude.isnot(None),
            AvistamentoImg.avistamento_img_longitude.isnot(None)
        ).order_by(
            AvistamentoImg.avistamento_img_date.desc()
        ).all()

        return render_template(
            "mapa.html",
            avistamentos=lista_avistamentos
        )

    # Sobre o projeto
    @app.route("/sobre")
    def sobre():
        return render_template("sobre.html")

    # Validação de registros
    @app.route("/validacao")
    def validacao():
        lista_avistamentos = AvistamentoImg.query.order_by(
            AvistamentoImg.avistamento_img_id.desc()
        ).all()

        return render_template(
            "validacao.html",
            avistamentos=lista_avistamentos
        )
