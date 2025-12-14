#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import shutil
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class NFSManagerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pardus NFS Otomatik Bağlayıcı")
        self.set_border_width(15)
        self.set_default_size(450, 250)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        # Ana Düzen
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Başlık
        lbl_info = Gtk.Label(label="<b>Pardus ETAP - NFS İstemci Ayarı</b>")
        lbl_info.set_use_markup(True)
        vbox.pack_start(lbl_info, False, False, 5)

        # Form Grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        vbox.pack_start(grid, True, True, 0)

        # 1. Sunucu IP
        lbl_ip = Gtk.Label(label="Sunucu IP Adresi:", xalign=0)
        self.entry_ip = Gtk.Entry()
        self.entry_ip.set_text("192.168.1.100") # Örnek Varsayılan
        grid.attach(lbl_ip, 0, 0, 1, 1)
        grid.attach(self.entry_ip, 1, 0, 1, 1)

        # 2. Sunucu Paylaşım Yolu
        lbl_remote = Gtk.Label(label="Sunucudaki Klasör:", xalign=0)
        self.entry_remote = Gtk.Entry()
        self.entry_remote.set_text("/srv/nfs/ogretmen")
        grid.attach(lbl_remote, 0, 1, 1, 1)
        grid.attach(self.entry_remote, 1, 1, 1, 1)

        # 3. Yerel Bağlantı Noktası
        lbl_local = Gtk.Label(label="Tahtada Bağlanacak Yer:", xalign=0)
        self.entry_local = Gtk.Entry()
        self.entry_local.set_text("/media/ogretmen_paylasim")
        grid.attach(lbl_local, 0, 2, 1, 1)
        grid.attach(self.entry_local, 1, 2, 1, 1)

        # Buton
        self.btn_apply = Gtk.Button(label="Ayarları Uygula ve Bağla")
        self.btn_apply.get_style_context().add_class("suggested-action")
        self.btn_apply.connect("clicked", self.on_apply_clicked)
        vbox.pack_start(self.btn_apply, False, False, 10)

        # Durum Çubuğu / Log
        self.statusbar = Gtk.Label(label="Hazır.")
        vbox.pack_start(self.statusbar, False, False, 0)

    def on_apply_clicked(self, widget):
        # Root kontrolü
        if os.geteuid() != 0:
            self.show_message("Hata", "Bu işlem için uygulamayı 'sudo' ile çalıştırmalısınız.", Gtk.MessageType.ERROR)
            return

        ip = self.entry_ip.get_text().strip()
        remote_path = self.entry_remote.get_text().strip()
        local_path = self.entry_local.get_text().strip()

        if not ip or not remote_path or not local_path:
            self.statusbar.set_text("Lütfen tüm alanları doldurun.")
            return

        try:
            self.statusbar.set_text("İşlem başlıyor...")
            
            # 1. Paket Kurulumu (Basitçe kontrol edelim)
            subprocess.run(["apt-get", "install", "-y", "nfs-common"], check=True)

            # 2. Klasör Oluşturma
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            
            # 3. Fstab Yedekleme ve Yazma
            fstab_line = f"{ip}:{remote_path} {local_path} nfs defaults,_netdev,nofail 0 0\n"
            
            # Dosyada zaten var mı kontrol et
            with open("/etc/fstab", "r") as f:
                content = f.read()
            
            if fstab_line.strip() not in content:
                shutil.copyfile("/etc/fstab", "/etc/fstab.bak") # Yedek al
                with open("/etc/fstab", "a") as f:
                    f.write(f"\n# Pardus NFS Otomatik Baglanti\n{fstab_line}")
            
            # 4. Profile.d Scripti Oluşturma (Masaüstü Kısayolu için)
            script_content = f"""#!/bin/bash
KISAYOL_ADI="Öğretmen Paylaşımı"
HEDEF_KLASOR="{local_path}"
MASAUSTU_YOLU="$HOME/Masaüstü"

# Desktop veya Masaüstü kontrolü
if [ -d "$HOME/Desktop" ]; then
    MASAUSTU_YOLU="$HOME/Desktop"
fi

if [ -d "$MASAUSTU_YOLU" ]; then
    if [ ! -e "$MASAUSTU_YOLU/$KISAYOL_ADI" ]; then
        ln -s "$HEDEF_KLASOR" "$MASAUSTU_YOLU/$KISAYOL_ADI"
    fi
fi
"""
            script_path = "/etc/profile.d/ogretmen-kisayol.sh"
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)

            # 5. Bağlantıyı Test Et
            subprocess.run(["mount", "-a"], check=True)

            self.statusbar.set_text("İşlem Başarılı!")
            self.show_message("Başarılı", "NFS bağlantısı kuruldu ve kısayol ayarlandı.\nLütfen oturumu kapatıp açın.", Gtk.MessageType.INFO)

        except Exception as e:
            self.statusbar.set_text("Hata oluştu.")
            self.show_message("Hata", f"Bir sorun oluştu:\n{str(e)}", Gtk.MessageType.ERROR)

    def show_message(self, title, message, msg_type):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    win = NFSManagerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
