import os
import subprocess
import re
"""Script ini mengunduh playlist YouTube, membersihkan nama file,
dan melakukan push ke GitHub."""

# --- KONFIGURASI ---
# Ganti dengan daftar URL playlist YouTube Anda
PLAYLIST_URLS = [
    "https://www.youtube.com/playlist?list=PL5868bcJqA4Fo1HpNLSIFxMhlG2jmcUch",
    "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5ObxTlEPlkkornHXUiKX1z",
    "https://www.youtube.com/playlist?list=OLAK5uy_n7Ig_LAUbKE6_ZeQ1pwHmJcEhwX7BekBo",
    "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5QPpj0R4vVgRWk8sSq549G",
    # Tambahkan URL playlist lainnya di sini...
]

# Pesan commit untuk Gi
COMMIT_MESSAGE = "Update: Menghapus teks dalam kurung dari nama file"

# --- FUNGSI BARU UNTUK MEMBERSIHKAN NAMA FILE ---
def clean_filenames_in_directory(directory):
    """
    Mengganti nama file di dalam direktori yang diberikan dengan menghapus
    tanda kurung dan teks di dalamnya.
    Contoh: '01 - Judul Lagu (Official Video).mp3' -> '01 - Judul Lagu.mp3'
    """
    print(f"🧹 Memeriksa dan membersihkan nama file di folder: '{directory}'...")
    if not os.path.isdir(directory):
        print(f"  ⚠️ Peringatan: Direktori '{directory}' tidak ditemukan.")
        return

    # Pola regex untuk menemukan spasi diikuti tanda kurung dan isinya
    # Contoh: ' (text here)'
    pattern = re.compile(r'\s*\([^)]*\)')

    for filename in os.listdir(directory):
        # Hanya proses file mp3
        if filename.endswith(".mp3"):
            # Hapus pola regex dari nama file (tanpa ekstensi)
            name_without_ext, extension = os.path.splitext(filename)
            new_name_without_ext = pattern.sub('', name_without_ext).strip()

            # Jika nama berubah, lakukan penggantian nama file
            if new_name_without_ext != name_without_ext:
                new_filename = new_name_without_ext + extension
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)
                
                try:
                    os.rename(old_path, new_path)
                    print(f"  -> Mengganti nama: '{filename}' -> '{new_filename}'")
                except OSError as e:
                    print(f"  ❌ Gagal mengganti nama '{filename}': {e}")


# --- FUNGSI UTAMA ---

def download_playlists():
    """
    Mengunduh setiap playlist dan membersihkan nama filenya.
    """
    if not PLAYLIST_URLS:
        print("Daftar PLAYLIST_URLS kosong. Harap isi dengan URL playlist.")
        return False

    total_playlists = len(PLAYLIST_URLS)
    print(f"Total playlist yang akan diunduh: {total_playlists}")

    for playlist_url in PLAYLIST_URLS:
        print(f"\n--- Memproses Playlist ---")
        print(f"📥 Mengunduh dari: {playlist_url}")
        
        try:
            # Mendapatkan nama folder tujuan dari yt-dlp
            # Ini penting agar kita tahu di mana harus membersihkan nama file
            get_playlist_folder_cmd = ['yt-dlp', '--print', '%(playlist_title)s', '--yes-playlist', playlist_url]
            proc = subprocess.run(get_playlist_folder_cmd, capture_output=True, text=True, check=True)
            # Mengambil baris pertama dan membersihkan karakter yang tidak perlu
            playlist_folder = proc.stdout.splitlines()[0].strip()

            output_template = f'{playlist_folder}/%(playlist_index)s - %(title)s.%(ext)s'
            
            download_command = [
                'yt-dlp',
                '--ignore-errors',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--yes-playlist',
                '-o', output_template,
                playlist_url
            ]
            
            subprocess.run(download_command, check=True)
            print(f"✅ Selesai mengunduh playlist ke folder: '{playlist_folder}'")

            # --- PANGGIL FUNGSI PEMBERSIH NAMA FILE ---
            clean_filenames_in_directory(playlist_folder)

        except subprocess.CalledProcessError as e:
            print(f"❌ Gagal memproses playlist. Error: {e}")
        except Exception as e:
            print(f"❌ Terjadi kesalahan tak terduga: {e}")
    
    return True

def push_to_github():
    """
    Menjalankan perintah Git untuk menambahkan, commit, dan push file ke GitHub.
    """
    try:
        print("\n--- Memulai proses push ke GitHub ---")
        
        print(" menjalankan `git add .`...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        print(f" menjalankan `git commit` dengan pesan: '{COMMIT_MESSAGE}'...")
        subprocess.run(['git', 'commit', '-m', COMMIT_MESSAGE, '--allow-empty'], check=True)

        print(" menjalankan `git push`...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True) 
        
        print("\n✅ Sukses! Semua file berhasil di-push ke GitHub.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Proses Git gagal. Error: {e}")
    except FileNotFoundError:
        print("❌ Perintah 'git' tidak ditemukan. Pastikan Git sudah terinstall.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan tak terduga saat push ke GitHub: {e}")

if __name__ == "__main__":
    if download_playlists():
        user_input = input("\nProses download selesai. Lanjutkan push ke GitHub? (y/n): ").lower()
        if user_input == 'y':
            push_to_github()
        else:
            print("\nProses push ke GitHub dibatalkan.")