#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

OKUL_ADI = "Ticaret ve Sanayi Odası TMTAL"
LOGO_YOLU = "/usr/share/pixmaps/okul-logo.png"


class OgretmenEtapPenceresi(Gtk.Window):
    def __init__(self):
        super().__init__(title="Öğretmen Paylaşımı Kurucu (ETAP)")
        self.set_default_size(640, 420)
        self.set_border_width(10)

        if os.geteuid() != 0:
            self.hata_mesaji(
                "Bu uygulama sistem ayarlarını değiştirdiği için\n"
                "yönetici (root) yetkisiyle çalıştırılmalıdır.\n\n"
                "Örnek:\n  pkexec /usr/local/sbin/ogretmen_paylasim_etap.py"
            )

        self.css_yukle()
        self.arayuz_olustur()

    def css_yukle(self):
        css = b"""
        window {
            background-color: #f5f5f5;
        }
        .banner-box {
            background: #004d7a;
            padding: 12px;
        }
        .banner-title {
            color: #ffffff;
            font-weight: bold;
            font-size: 16px;
        }
        .banner-subtitle {
            color: #e0e0e0;
            font-size: 10px;
        }
        .form-label {
            font-weight: 600;
        }
        .apply-button {
            font-weight: bold;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def arayuz_olustur(self):
        ana = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(ana)

        # Üst banner
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        banner.get_style_context().add_class("banner-box")

        if os.path.exists(LOGO_YOLU):
            img = Gtk.Image.new_from_file(LOGO_YOLU)
            banner.pack_start(img, False, False, 0)

        yazi_kutu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_title = Gtk.Label(label=OKUL_ADI)
        lbl_title.get_style_context().add_class("banner-title")
        lbl_title.set_xalign(0.0)

        lbl_sub = Gtk.Label(label="ETAP (Cinnamon) üzerinde öğretmen paylaşımını otomatik bağlayan yapılandırma aracı")
        lbl_sub.get_style_context().add_class("banner-subtitle")
        lbl_sub.set_xalign(0.0)

        yazi_kutu.pack_start(lbl_title, False, False, 0)
        yazi_kutu.pack_start(lbl_sub, False, False, 0)
        banner.pack_start(yazi_kutu, True, True, 0)

        ana.pack_start(banner, False, False, 0)

        # Form
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        form.set_margin_top(10)
        form.set_margin_bottom(10)
        form.set_margin_start(10)
        form.set_margin_end(10)
        ana.pack_start(form, True, True, 0)

        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        form.pack_start(grid, True, True, 0)

        satir = 0

        def etiket(text):
            lbl = Gtk.Label(label=text)
            lbl.set_xalign(1.0)
            lbl.get_style_context().add_class("form-label")
            return lbl

        # Sunucu
        self.entry_server = Gtk.Entry()
        self.entry_server.set_text("10.46.197.90")
        grid.attach(etiket("Sunucu IP / Ad:"), 0, satir, 1, 1)
        grid.attach(self.entry_server,          1, satir, 2, 1)
        satir += 1

        # Paylaşım
        self.entry_share = Gtk.Entry()
        self.entry_share.set_text("ogretmen")
        grid.attach(etiket("Paylaşım Adı:"), 0, satir, 1, 1)
        grid.attach(self.entry_share,        1, satir, 2, 1)
        satir += 1

        # Mount
        self.entry_mount = Gtk.Entry()
        self.entry_mount.set_text("/mnt/ogretmen")
        grid.attach(etiket("Mount Noktası:"), 0, satir, 1, 1)
        grid.attach(self.entry_mount,         1, satir, 2, 1)
        satir += 1

        # Kullanıcı
        self.entry_user = Gtk.Entry()
        self.entry_user.set_text("ogrt")
        grid.attach(etiket("Windows Kullanıcı Adı:"), 0, satir, 1, 1)
        grid.attach(self.entry_user,                 1, satir, 2, 1)
        satir += 1

        # Şifre
        self.entry_pass = Gtk.Entry()
        self.entry_pass.set_visibility(False)
        self.entry_pass.set_invisible_char("•")
        grid.attach(etiket("Windows Şifre:"), 0, satir, 1, 1)
        grid.attach(self.entry_pass,          1, satir, 2, 1)
        satir += 1

        # Domain
        self.entry_domain = Gtk.Entry()
        self.entry_domain.set_text("WORKGROUP")
        grid.attach(etiket("Domain / Workgroup:"), 0, satir, 1, 1)
        grid.attach(self.entry_domain,             1, satir, 2, 1)
        satir += 1

        not_lbl = Gtk.Label(
            label="Not: Bu ayarlar ETAP Cinnamon oturumundaki tüm kullanıcılar için geçerlidir.\n"
                  "Öğretmenler tekrar giriş yaptığında masaüstlerinde 'Öğretmen Paylaşımı' kısayolu oluşur."
        )
        not_lbl.set_xalign(0.0)
        form.pack_start(not_lbl, False, False, 8)

        # Alt kısmı
        alt = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ana.pack_start(alt, False, False, 0)

        self.status_label = Gtk.Label(label="Hazır.")
        self.status_label.set_xalign(0.0)
        alt.pack_start(self.status_label, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        alt.pack_start(btn_box, False, False, 0)

        self.btn_apply = Gtk.Button(label="Ayarları Uygula")
        self.btn_apply.get_style_context().add_class("apply-button")
        self.btn_apply.connect("clicked", self.ayarlar_uygula)
        btn_box.pack_start(self.btn_apply, False, False, 0)

        btn_close = Gtk.Button(label="Kapat")
        btn_close.connect("clicked", lambda w: Gtk.main_quit())
        btn_box.pack_start(btn_close, False, False, 0)

    def set_status(self, text):
        self.status_label.set_text(text)
        print(text)

    def hata_mesaji(self, mesaj):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Hata",
        )
        dialog.format_secondary_text(mesaj)
        dialog.run()
        dialog.destroy()

    def info_mesaji(self, baslik, mesaj):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=baslik,
        )
        dialog.format_secondary_text(mesaj)
        dialog.run()
        dialog.destroy()

    def onay_sor(self, mesaj):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Onay",
        )
        dialog.format_secondary_text(mesaj)
        cevap = dialog.run()
        dialog.destroy()
        return cevap == Gtk.ResponseType.YES

    def ayarlar_uygula(self, widget):
        server = self.entry_server.get_text().strip()
        share = self.entry_share.get_text().strip()
        mount = self.entry_mount.get_text().strip()
        user = self.entry_user.get_text().strip()
        passwd = self.entry_pass.get_text().strip()
        domain = self.entry_domain.get_text().strip() or "WORKGROUP"

        if not all([server, share, mount, user, passwd]):
            self.hata_mesaji("Lütfen tüm alanları doldurun.")
            return

        if not self.onay_sor(
            f"Aşağıdaki ayarlar uygulanacak:\n\n"
            f"Sunucu   : {server}\n"
            f"Paylaşım : {share}\n"
            f"Mount    : {mount}\n"
            f"Kullanıcı: {user}\n"
            f"Domain   : {domain}\n\n"
            f"Devam etmek istiyor musunuz?"
        ):
            return

        try:
            self.btn_apply.set_sensitive(False)
            self.sistem_ayarlari_uygula(server, share, mount, user, passwd, domain)
            self.info_mesaji(
                "İşlem Tamamlandı",
                "Öğretmen paylaşımı başarıyla yapılandırıldı.\n"
                "Öğretmenler tekrar giriş yaptığında masaüstlerinde\n"
                "'Öğretmen Paylaşımı' kısayolunu görecekler."
            )
            self.set_status("Başarılı.")
        except Exception as e:
            self.hata_mesaji(f"İşlem sırasında bir hata oluştu:\n\n{e}")
            self.set_status("Hata oluştu.")
        finally:
            self.btn_apply.set_sensitive(True)

    def sistem_ayarlari_uygula(self, server, share, mount, user, passwd, domain):
        os.makedirs(mount, exist_ok=True)

        cred_path = f"/etc/samba/creds-{share}"
        with open(cred_path, "w", encoding="utf-8") as f:
            f.write(f"username={user}\npassword={passwd}\ndomain={domain}\n")
        os.chmod(cred_path, 0o600)

        backup_name = f"/etc/fstab.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copy("/etc/fstab", backup_name)

        marker_start = "# OGRETMEN_PAYLASIM_BASLA"
        marker_end = "# OGRETMEN_PAYLASIM_BITIR"

        new_lines = []
        if os.path.exists("/etc/fstab"):
            with open("/etc/fstab", "r", encoding="utf-8") as f:
                skip = False
                for line in f:
                    if marker_start in line:
                        skip = True
                        continue
                    if marker_end in line:
                        skip = False
                        continue
                    if not skip:
                        new_lines.append(line)

        new_lines.append("\n")
        new_lines.append(f"{marker_start}\n")
        new_lines.append(f"//{server}/{share}  {mount}  cifs  credentials={cred_path},"
                         f"iocharset=utf8,uid=1000,gid=1000,file_mode=0777,dir_mode=0777,"
                         f"noperm,nofail  0  0\n")
        new_lines.append(f"{marker_end}\n")

        with open("/etc/fstab", "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        res = subprocess.run(["mount", "-a"], text=True, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f"mount -a başarısız.\nSTDERR: {res.stderr}\nYedek: {backup_name}")

        kisayol_script = "/usr/local/bin/ogretmen-kisayol.sh"
        script_icerik = f"""#!/bin/bash
MOUNT_DIR="{mount}"

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null)"

if [ -z "$DESKTOP_DIR" ]; then
    if [ -d "$HOME/Masaüstü" ]; then
        DESKTOP_DIR="$HOME/Masaüstü"
    elif [ -d "$HOME/Desktop" ]; then
        DESKTOP_DIR="$HOME/Desktop"
    else
        DESKTOP_DIR="$HOME/Masaüstü"
        mkdir -p "$DESKTOP_DIR"
    fi
fi

mkdir -p "$DESKTOP_DIR"

SHORTCUT="$DESKTOP_DIR/ogretmen-paylasim.desktop"

cat <<EOD > "$SHORTCUT"
[Desktop Entry]
Type=Application
Name=Öğretmen Paylaşımı
Icon=folder-remote
Exec=xdg-open "{mount}"
Terminal=false
EOD

chmod +x "$SHORTCUT"
"""
        with open(kisayol_script, "w", encoding="utf-8") as f:
            f.write(script_icerik)
        os.chmod(kisayol_script, 0o755)

        autostart_dir = "/etc/xdg/autostart"
        os.makedirs(autostart_dir, exist_ok=True)
        autostart_file = os.path.join(autostart_dir, "ogretmen-kisayol.desktop")
        desktop_icerik = """[Desktop Entry]
Type=Application
Name=Öğretmen Paylaşımı Kısayol Oluşturucu
Exec=/usr/local/bin/ogretmen-kisayol.sh
OnlyShowIn=X-Cinnamon;
NoDisplay=true
"""
        with open(autostart_file, "w", encoding="utf-8") as f:
            f.write(desktop_icerik)
        os.chmod(autostart_file, 0o644)


def main():
    win = OgretmenEtapPenceresi()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

