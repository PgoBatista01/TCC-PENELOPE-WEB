
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# TABELA DE PASSAROS
class Passaro(db.Model):
    __tablename__ = "passaro"

    passaro_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_popular = db.Column(db.String(100), nullable=False)
    nome_binomial = db.Column(db.String(50), nullable=False)
    passaro_familia = db.Column(db.String(50), nullable=False)
    estado_conservacao = db.Column(db.CHAR(2), nullable=False)
    passaro_descricao = db.Column(db.String(1000), nullable=False)
    envergadura_cm = db.Column(db.Integer, nullable=False)

    cantos = db.relationship("Canto", back_populates="passaro")
    imagens = db.relationship("ImgPassaro", back_populates="passaro")
    imagens_preview = db.relationship(
        "ImgPassaroPreview",
        back_populates="passaro"
    )
    avistamentos_imagem = db.relationship(
        "AvistamentoImg",
        back_populates="passaro"
    )
    avistamentos_audio = db.relationship(
        "AvistamentoAudio",
        back_populates="passaro"
    )
    avistamentos_video = db.relationship(
        "AvistamentoVideo",
        back_populates="passaro"
    )


# TABELA DE CANTOS
class Canto(db.Model):
    __tablename__ = "canto"

    canto_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    canto_filename = db.Column(db.String(255))
    canto_filepath = db.Column(db.String(255), nullable=False)
    canto_filetype = db.Column(db.String(50))
    canto_filesize = db.Column(db.Integer)
    canto_origin = db.Column(db.String(255))
    canto_order = db.Column(db.Integer)
    canto_date = db.Column(db.Date)
    canto_duration_ms = db.Column(db.Integer)

    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id"),
        nullable=False
    )

    passaro = db.relationship("Passaro", back_populates="cantos")


# TABELA DE IMAGENS DAS AVES
class ImgPassaro(db.Model):
    __tablename__ = "img_passaro"

    img_passaro_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    img_passaro_filename = db.Column(db.String(255))
    img_passaro_filepath = db.Column(db.String(255), nullable=False)
    img_passaro_filetype = db.Column(db.String(50))
    img_passaro_filesize = db.Column(db.Integer)
    img_passaro_origin = db.Column(db.String(255))
    img_passaro_order = db.Column(db.Integer)
    img_passaro_date = db.Column(db.Date)

    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id"),
        nullable=False
    )

    passaro = db.relationship("Passaro", back_populates="imagens")
    previews = db.relationship("ImgPassaroPreview", back_populates="imagem")


# TABELA DE MINIATURAS DAS IMAGENS DAS AVES
class ImgPassaroPreview(db.Model):
    __tablename__ = "img_passaro_preview"

    img_preview_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    img_preview_filepath = db.Column(db.String(255), nullable=False)
    img_preview_filesize = db.Column(db.Integer)

    img_passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("img_passaro.img_passaro_id")
    )
    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id")
    )

    imagem = db.relationship("ImgPassaro", back_populates="previews")
    passaro = db.relationship("Passaro", back_populates="imagens_preview")


# TABELA DE USUARIOS
class Usuario(db.Model):
    __tablename__ = "usuario"

    usuario_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_nome = db.Column(db.String(100), nullable=False)
    usuario_img_filepath = db.Column(db.String(255))
    usuario_login = db.Column(db.String(100), nullable=False, unique=True)
    usuario_email = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(60), nullable=False)

    avistamentos_imagem = db.relationship(
        "AvistamentoImg",
        back_populates="usuario"
    )
    avistamentos_audio = db.relationship(
        "AvistamentoAudio",
        back_populates="usuario"
    )
    avistamentos_video = db.relationship(
        "AvistamentoVideo",
        back_populates="usuario"
    )


# TABELA DE AVISTAMENTOS COM IMAGEM
class AvistamentoImg(db.Model):
    __tablename__ = "avistamento_img"

    avistamento_img_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    avistamento_img_descricao = db.Column(db.String(255))
    avistamento_img_latitude = db.Column(db.Numeric(8, 6))
    avistamento_img_longitude = db.Column(db.Numeric(9, 6))
    avistamento_img_date = db.Column(db.Date)
    avistamento_img_filename = db.Column(db.String(255))
    avistamento_img_filepath = db.Column(db.String(255), nullable=False)
    avistamento_img_filetype = db.Column(db.String(50))
    avistamento_img_filesize = db.Column(db.Integer)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.usuario_id"),
        nullable=False
    )
    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id"),
        nullable=False
    )

    usuario = db.relationship("Usuario", back_populates="avistamentos_imagem")
    passaro = db.relationship("Passaro", back_populates="avistamentos_imagem")
    previews = db.relationship(
        "AvistamentoImgPreview",
        back_populates="avistamento"
    )


# TABELA DE MINIATURAS DOS AVISTAMENTOS
class AvistamentoImgPreview(db.Model):
    __tablename__ = "avistamento_img_preview"

    img_preview_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    img_preview_filepath = db.Column(db.String(255), nullable=False)
    img_preview_filesize = db.Column(db.Integer)

    avistamento_img_id = db.Column(
        db.Integer,
        db.ForeignKey("avistamento_img.avistamento_img_id")
    )

    avistamento = db.relationship(
        "AvistamentoImg",
        back_populates="previews"
    )


# TABELA DE AVISTAMENTOS COM AUDIO
class AvistamentoAudio(db.Model):
    __tablename__ = "avistamento_audio"

    avistamento_audio_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    avistamento_audio_descricao = db.Column(db.String(255))
    avistamento_audio_latitude = db.Column(db.Numeric(8, 6))
    avistamento_audio_longitude = db.Column(db.Numeric(9, 6))
    avistamento_audio_filename = db.Column(db.String(255))
    avistamento_audio_filepath = db.Column(db.String(255), nullable=False)
    avistamento_audio_filetype = db.Column(db.String(50))
    avistamento_audio_filesize = db.Column(db.Integer)
    avistamento_audio_date = db.Column(db.Date)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.usuario_id"),
        nullable=False
    )
    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id"),
        nullable=False
    )

    usuario = db.relationship("Usuario", back_populates="avistamentos_audio")
    passaro = db.relationship("Passaro", back_populates="avistamentos_audio")


# TABELA DE AVISTAMENTOS COM VIDEO
class AvistamentoVideo(db.Model):
    __tablename__ = "avistamento_video"

    avistamento_video_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    avistamento_video_descricao = db.Column(db.String(255))
    avistamento_video_latitude = db.Column(db.Numeric(8, 6))
    avistamento_video_longitude = db.Column(db.Numeric(9, 6))
    avistamento_video_filename = db.Column(db.String(255))
    avistamento_video_filepath = db.Column(db.String(255), nullable=False)
    avistamento_video_filetype = db.Column(db.String(50))
    avistamento_video_filesize = db.Column(db.Integer)
    avistamento_video_date = db.Column(db.Date)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.usuario_id"),
        nullable=False
    )
    passaro_id = db.Column(
        db.Integer,
        db.ForeignKey("passaro.passaro_id"),
        nullable=False
    )

    usuario = db.relationship("Usuario", back_populates="avistamentos_video")
    passaro = db.relationship("Passaro", back_populates="avistamentos_video")
