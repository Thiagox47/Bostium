#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Pacotes .deb nativos para o Bostium Browser (Debian, Ubuntu, Mint, Pop!_OS)
Compatível com as especificações oficiais do formato Debian Binary Package (ar).
"""

import os
import io
import time
import tarfile
import gzip

def make_ar_header(filename, size, mtime=None, mode=0o100644, uid=0, gid=0):
    if mtime is None:
        mtime = int(time.time())
    header = io.BytesIO()
    # Name: 16 bytes (filename/ space-padded)
    name_field = (filename + "/").ljust(16).encode("ascii")[:16]
    header.write(name_field)
    # Mtime: 12 bytes
    header.write(str(mtime).ljust(12).encode("ascii")[:12])
    # UID: 6 bytes
    header.write(str(uid).ljust(6).encode("ascii")[:6])
    # GID: 6 bytes
    header.write(str(gid).ljust(6).encode("ascii")[:6])
    # Mode: 8 bytes octal
    header.write(oct(mode).ljust(8).encode("ascii")[:8])
    # Size: 10 bytes
    header.write(str(size).ljust(10).encode("ascii")[:10])
    # Magic end of header: 2 bytes
    header.write(b"`\n")
    return header.getvalue()

def create_control_tar_gz():
    control_content = (
        "Package: bostium\n"
        "Version: 1.0\n"
        "Section: web\n"
        "Priority: optional\n"
        "Architecture: all\n"
        "Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1 | gir1.2-webkit2-4.0\n"
        "Maintainer: Bostium Project <bostium@project.org>\n"
        "Description: Navegador Web Ultraleve Bostium\n"
        " Bostium e um navegador web projetado para baixissimo consumo de memoria RAM,\n"
        " apresentando o sistema de abas virtuais Ghost Tabs e motor WebKitGTK nativo.\n"
    ).encode("utf-8")

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
        ti = tarfile.TarInfo(name="./control")
        ti.size = len(control_content)
        ti.mtime = int(time.time())
        ti.mode = 0o644
        tar.addfile(ti, io.BytesIO(control_content))

    return tar_stream.getvalue()

def create_data_tar_gz(base_dir):
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
        # Diretórios padrão
        dirs = [
            "./usr",
            "./usr/bin",
            "./usr/lib",
            "./usr/lib/bostium",
            "./usr/share",
            "./usr/share/applications",
            "./usr/share/icons",
            "./usr/share/icons/hicolor",
            "./usr/share/icons/hicolor/256x256",
            "./usr/share/icons/hicolor/256x256/apps",
        ]
        now = int(time.time())
        for d in dirs:
            ti = tarfile.TarInfo(name=d)
            ti.type = tarfile.DIRTYPE
            ti.mode = 0o755
            ti.mtime = now
            tar.addfile(ti)

        # Arquivos
        # 1. /usr/bin/bostium
        bin_path = os.path.join(base_dir, "bostium")
        if os.path.exists(bin_path):
            with open(bin_path, "rb") as f:
                data = f.read()
            ti = tarfile.TarInfo(name="./usr/bin/bostium")
            ti.size = len(data)
            ti.mode = 0o755
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(data))

        # 2. /usr/lib/bostium/bostium.py
        py_path = os.path.join(base_dir, "bostium.py")
        if os.path.exists(py_path):
            with open(py_path, "rb") as f:
                data = f.read()
            ti = tarfile.TarInfo(name="./usr/lib/bostium/bostium.py")
            ti.size = len(data)
            ti.mode = 0o755
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(data))

        # 3. /usr/share/applications/bostium.desktop
        desk_path = os.path.join(base_dir, "bostium.desktop")
        if os.path.exists(desk_path):
            with open(desk_path, "rb") as f:
                data = f.read()
            ti = tarfile.TarInfo(name="./usr/share/applications/bostium.desktop")
            ti.size = len(data)
            ti.mode = 0o644
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(data))

        # 4. /usr/share/icons/hicolor/256x256/apps/bostium.png
        icon_path = os.path.join(base_dir, "bostium.png")
        if os.path.exists(icon_path):
            with open(icon_path, "rb") as f:
                data = f.read()
            ti = tarfile.TarInfo(name="./usr/share/icons/hicolor/256x256/apps/bostium.png")
            ti.size = len(data)
            ti.mode = 0o644
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(data))

    return tar_stream.getvalue()

def build_deb(base_dir, output_deb_path):
    print("Gerando control.tar.gz...")
    control_data = create_control_tar_gz()
    print("Gerando data.tar.gz...")
    data_data = create_data_tar_gz(base_dir)

    debian_binary = b"2.0\n"

    print(f"Empacotando arquivo .deb oficial: {output_deb_path}...")
    with open(output_deb_path, "wb") as deb:
        # Magic number AR
        deb.write(b"!<arch>\n")

        # 1. debian-binary
        deb.write(make_ar_header("debian-binary", len(debian_binary)))
        deb.write(debian_binary)
        if len(debian_binary) % 2 != 0:
            deb.write(b"\n")

        # 2. control.tar.gz
        deb.write(make_ar_header("control.tar.gz", len(control_data)))
        deb.write(control_data)
        if len(control_data) % 2 != 0:
            deb.write(b"\n")

        # 3. data.tar.gz
        deb.write(make_ar_header("data.tar.gz", len(data_data)))
        deb.write(data_data)
        if len(data_data) % 2 != 0:
            deb.write(b"\n")

    print(f"[SUCESSO] Pacote {output_deb_path} gerado com sucesso! ({os.path.getsize(output_deb_path)} bytes)")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    target_deb = os.path.join(parent_dir, "bostium_1.0_all.deb")
    build_deb(current_dir, target_deb)
