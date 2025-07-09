import os
import subprocess
import re

# --- KONFIGURASI ---
# Ganti dengan daftar URL playlist YouTube Anda yang valid
PLAYLIST_URLS = [
    "https://www.youtube.com/playlist?list=PLCi2gmF270m1gZuPF_cbUk5Ml-Sawjvo8",
    "https://www.youtube.com/playlist?list=PL9l5iOOqS0F8yickz_Bt6HVSAHMey7Oj3",
    # "https://www.youtube.com/playlist?list=PL5868bcJqA4Fo1HpNLSIFxMhlG2jmcUch",
    # "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5ObxTlEPlkkornHXUiKX1z",
    # Tambahkan URL playlist lainnya di sini...
]

# --- FUNGSI PEMBERSIH NAMA FILE ---
def clean_filenames_in_directory(directory):
    """
    Mengganti nama file dengan menghapus teks dalam kurung dan mengembalikan
    True jika ada file yang diubah namanya.
    """
    print(f"🧹 Memeriksa dan membersihkan nama file di folder: '{directory}'...")
    if not os.path.isdir(directory):
        print(f"  ⚠️  Peringatan: Direktori '{directory}' tidak ditemukan.")
        return False

    renamed_anything = False
    pattern = re.compile(r'\s*\([^)]*\)')

    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            name_without_ext, extension = os.path.splitext(filename)
            # Hapus juga potensi kurung siku `[]`
            name_no_brackets = re.sub(r'\s*\[[^\]]*\]', '', name_without_ext)
            new_name_without_ext = pattern.sub('', name_no_brackets).strip()

            if new_name_without_ext != name_without_ext:
                new_filename = new_name_without_ext + extension
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)
                
                try:
                    os.rename(old_path, new_path)
                    print(f"  -> Mengganti nama: '{filename}' -> '{new_filename}'")
                    renamed_anything = True
                except OSError as e:
                    print(f"  ❌ Gagal mengganti nama '{filename}': {e}")
    
    return renamed_anything

# --- FUNGSI GIT BARU ---
def commit_and_push_changes(folder_path, commit_message):
    """
    Menjalankan 'git add', 'commit', dan 'push' untuk folder tertentu.
    Hanya berjalan jika ada perubahan yang terdeteksi.
    """
    try:
        print(f"\n--- Memulai proses Git untuk '{folder_path}' ---")

        # Cek status HANYA untuk folder yang relevan untuk melihat apakah ada perubahan
        # Ini penting agar kita tidak melakukan commit kosong
        status_proc = subprocess.run(
            ['git', 'status', '--porcelain', folder_path], 
            capture_output=True, text=True, check=True, encoding='utf-8'
        )

        if not status_proc.stdout.strip():
            print("✅ Tidak ada file baru atau perubahan untuk di-commit di playlist ini.")
            return

        print(f"📦 Menambahkan perubahan dari '{folder_path}' ke staging...")
        subprocess.run(['git', 'add', folder_path], check=True)
        # Tambahkan juga file yang mungkin telah diganti namanya (dihapus)
        subprocess.run(['git', 'add', '-u', folder_path], check=True)
        
        print(f"📝 Melakukan commit dengan pesan: '{commit_message}'")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        print("🚀 Mendorong (push) ke remote origin 'main'...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True) 
        
        print(f"\n✅ Sukses! Perubahan untuk '{folder_path}' berhasil di-push ke GitHub.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Proses Git gagal. Mungkin tidak ada perubahan untuk di-commit atau terjadi error lain.")
        print(f"   Error: {e.stderr}")
    except FileNotFoundError:
        print("❌ Perintah 'git' tidak ditemukan. Pastikan Git sudah terinstall dan ada di PATH.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan tak terduga saat proses Git: {e}")

# --- FUNGSI UTAMA YANG DIMODIFIKASI ---
def download_and_sync_playlists():
    """
    Mengunduh setiap playlist, membersihkan nama filenya, dan langsung melakukan
    commit & push untuk setiap playlist yang selesai diproses.
    """
    if not any(url for url in PLAYLIST_URLS if "http://googleusercontent.com/youtube.com/" in url):
        print("Daftar PLAYLIST_URLS kosong atau tidak valid. Harap isi dengan URL playlist YouTube yang benar.")
        return

    # <-- KUNCI PERUBAHAN: Minta konfirmasi di awal
    user_input = input(f"Akan memproses dan push {len(PLAYLIST_URLS)} playlist. Lanjutkan? (y/n): ").lower()
    if user_input != 'y':
        print("\nProses dibatalkan oleh pengguna.")
        return

    total_playlists = len(PLAYLIST_URLS)
    for i, playlist_url in enumerate(PLAYLIST_URLS):
        print(f"\n--- Memproses Playlist {i + 1}/{total_playlists} ---")
        print(f"🔗 URL: {playlist_url}")
        
        playlist_folder = "" # Inisialisasi nama folder
        try:
            # Dapatkan judul playlist untuk nama folder
            get_playlist_folder_cmd = [
                'yt-dlp', '--print', '%(playlist_title)s',
                '--flat-playlist', '--playlist-items', '1', playlist_url
            ]
            print("⚡ Mendapatkan judul playlist...")
            proc = subprocess.run(get_playlist_folder_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
            playlist_folder = proc.stdout.splitlines()[0].strip()

            print(f"📂 Nama Folder: '{playlist_folder}'")
            print(f"📥 Memulai unduhan...")
            
            output_template = os.path.join(playlist_folder, '%(playlist_index)s - %(title)s.%(ext)s')
            
            download_command = [
                'yt-dlp', '--ignore-errors', '--extract-audio', '--audio-format', 'mp3',
                '--audio-quality', '0', '--yes-playlist', '-o', output_template, playlist_url
            ]
            
            subprocess.run(download_command, check=True)
            print(f"✅ Selesai mengunduh ke folder: '{playlist_folder}'")

            # Bersihkan nama file setelah download selesai
            clean_filenames_in_directory(playlist_folder)

            # <-- KUNCI PERUBAHAN: Panggil fungsi git di dalam loop
            # Buat pesan commit yang dinamis dan informatif
            commit_msg = f"Update: Sinkronisasi playlist '{playlist_folder}'"
            commit_and_push_changes(playlist_folder, commit_msg)

        except subprocess.CalledProcessError as e:
            print(f"❌ Gagal memproses playlist. Periksa kembali URL dan koneksi Anda.")
            print(f"   stdout: {e.stdout}")
            print(f"   stderr: {e.stderr}")
        except Exception as e:
            print(f"❌ Terjadi kesalahan tak terduga: {e}")

if __name__ == "__main__":
    download_and_sync_playlists()
    print("\n\n🎉 Semua proses telah selesai.")