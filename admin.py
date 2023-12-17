import hashlib
import streamlit as st
import pandas as pd
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad, pad
import os
import base64
from io import BytesIO
import PyPDF2
from PIL import Image
import mysql.connector
from streamlit_option_menu import option_menu


selected = option_menu(None, ["Dashboard", "Encryption", "Decryption", "Database"],
                       icons=['cloud-upload', 'gear', "kanban", 'house'],
                       menu_icon="cast", default_index=0, orientation="horizontal")


def encrypt_file(key, input_file, output_file):
    iv = os.urandom(16)  # Generate random IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(input_file)

    with open(input_file, 'rb') as file:
        plaintext = file.read()

    encrypted_data = cipher.encrypt(pad(plaintext, 16))

    with open(output_file, 'wb') as file:
        file.write(iv)
        file.write(encrypted_data)


def save_uploaded_file(uploaded_file):
    with open(uploaded_file.name, 'wb') as file:
        file.write(uploaded_file.getbuffer())
    # st.success(f"File '{uploaded_file.name}' berhasil disimpan.")


def decrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as file:
        iv = file.read(16)
        ciphertext = file.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext), 16)

    with open(output_file, 'wb') as file:
        file.write(decrypted_data)


def read_pdf(file_content):
    pdf_file = BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    num_pages = len(pdf_reader.pages)

    st.text(f"Jumlah halaman: {num_pages}")
    st.text("Isi file terdekripsi (hanya halaman pertama ditampilkan):")
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        st.write(page.extract_text())


def read_image(file_content):
    image = Image.open(BytesIO(file_content))
    st.image(image)


def read_text(file_content):
    st.text("Isi file terdekripsi:")
    st.text(file_content.decode())


def download_file(file_content, file_name, file_format):
    b64 = base64.b64encode(file_content).decode()
    href = f'<a href="data:file/{file_format};base64,{b64}" download="{file_name}">Download {file_name}</a>'
    st.markdown(href, unsafe_allow_html=True)


# Fungsi untuk membuat koneksi ke database MySQL
def create_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kriptografi"
    )
    return conn


# Fungsi untuk menyimpan file PDF ke dalam database
def save_file_to_db(nama_file, file_path):
    conn = create_connection()
    cursor = conn.cursor()

    with open(file_path, 'rb') as file:
        file_data = file.read()

    query = "INSERT INTO pdf_files (nama_file, data) VALUES (%s, %s)"
    values = (nama_file, file_data)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


# Fungsi untuk menyimpan hasil enkripsi ke dalam tabel
def save_encrypted_file(input_file, output_file, key, table_name):
    conn = create_connection()
    cursor = conn.cursor()

    query = f"INSERT INTO {table_name} (nama_file, file_terenkripsi, kunci) VALUES (%s, %s, %s)"
    cursor.execute(query, (input_file, output_file, key))
    conn.commit()

    cursor.close()
    conn.close()


if selected == "Dashboard":
    st.title("Pengamanan File Rekap Transaksi Emiten")

    image_path = "coba.jpg"  
    st.image(image_path, width=600)  
        
    deskripsi = "Pengamanan File Rekap Transaksi Emiten dengan AES 256 adalah antarmuka pengguna untuk melindungi file rekap transaksi emiten menggunakan algoritma AES 256. Fitur-fitur termasuk pengunggahan file, enkripsi, pengelolaan kunci, dekripsi, dan manajemen keamanan. Tujuannya adalah memastikan keamanan file dan melindungi informasi sensitif dari akses tidak sah."
    st.write(deskripsi)



if selected == 'Encryption':
    st.write("Pilih file yang akan dienkripsi (PDF/JPG/TXT):")
    input_file = st.file_uploader("Upload File")

    if input_file:
        save_uploaded_file(input_file)
        key = st.text_input("Masukkan Kunci Enkripsi (32 karakter):")

        if len(key) == 32:
            output_file = f"encrypted_{input_file.name}"
            encrypt_file(key.encode(), input_file.name, output_file)

            st.success(f"File '{input_file.name}' berhasil dienkripsi dan disimpan sebagai '{output_file}' dan ditransfer ke Database.")

            # Simpan hasil enkripsi ke dalam tabel pdf_enkripsi
            save_encrypted_file(input_file.name, output_file, key, "pdf_enkripsi")

        elif len(key) > 0:
            st.error("Kunci enkripsi harus memiliki 32 karakter.")

        if len(key) == 0:
            st.info("Masukkan kunci enkripsi.")


if selected == "Decryption":
    st.write("Pilih file yang akan didekripsi (PDF/JPG/TXT):")
    input_file = st.file_uploader("Upload File")

    if input_file:
        save_uploaded_file(input_file)
        key = st.text_input("Masukkan Kunci Dekripsi (32 karakter):")

        if len(key) == 32:
            output_file = f"decrypted_{input_file.name}"

            if input_file.type == 'application/pdf':
                decrypt_file(key.encode(), input_file.name, output_file)
                with open(output_file, 'rb') as file:
                    file_content = file.read()
                read_pdf(file_content)
            elif input_file.type.startswith('image/'):
                decrypt_file(key.encode(), input_file.name, output_file)
                with open(output_file, 'rb') as file:
                    file_content = file.read()
                read_image(file_content)
            elif input_file.type == 'text/plain':
                decrypt_file(key.encode(), input_file.name, output_file)
                with open(output_file, 'rb') as file:
                    file_content = file.read()
                read_text(file_content)
            else:
                st.error("Format file tidak didukung.")

            st.success(f"File '{input_file.name}' berhasil didekripsi dan disimpan sebagai '{output_file}'.")

            st.write("Pilih format file yang akan diunduh:")
            download_format = st.selectbox("Format", [".pdf", ".jpg", ".txt"])
            if download_format == ".pdf" and input_file.type == 'application/pdf':
                st.text("Download file terdekripsi sebagai:")
                download_file(file_content, output_file, "application/pdf")
            elif download_format == ".jpg" and input_file.type.startswith('image/'):
                st.text("Download file terdekripsi sebagai:")
                download_file(file_content, output_file, "image/jpeg")
            elif download_format == ".txt" and input_file.type == 'text/plain':
                st.text("Download file terdekripsi sebagai:")
                download_file(file_content, output_file, "text/plain")
            else:
                st.warning("Tidak dapat mengunduh file dalam format yang dipilih atau format file tidak sesuai.")

            # Simpan file terdekripsi ke dalam tabel decrypted_files
            save_file_to_db(output_file, output_file, "pdf_dekripsi")

        elif len(key) > 0:
            st.error("Kunci dekripsi harus memiliki 32 karakter.")

        if len(key) == 0:
            st.info("Masukkan kunci dekripsi.")


# Fungsi untuk menampilkan isi tabel
def display_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = [column[0] for column in cursor.fetchall()]

    query = f"SELECT {', '.join(columns)} FROM {table_name}"
    cursor.execute(query)
    data = cursor.fetchall()

    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df)


if selected == 'Database':
    st.title("Database PDF/JPG/TXT")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    selected_table = st.selectbox("Pilih Tabel", tables)

    if selected_table in ["pdf_files", "pdf_enkripsi", "pdf_dekripsi"]:
        display_table(conn, selected_table)

    cursor.close()
    conn.close()
