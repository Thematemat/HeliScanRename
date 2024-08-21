import os
import cv2
from pyzbar.pyzbar import decode
from tkinter import *
from tkinter import scrolledtext


def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

def adjust_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return final

def detect_barcode(image, log_widget):
    adjusted_image = adjust_contrast(image)
    angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    
    for angle in angles:
        rotated_image = rotate_image(adjusted_image, angle)
        barcodes = decode(rotated_image)

        if barcodes:
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                log_widget.insert(END, f"Znaleziono kod kreskowy: {barcode_data} przy kącie {angle} stopni\n")
                log_widget.update_idletasks()
                return barcode_data

        # Próba wykrycia kodu kreskowego na różnych rozdzielczościach
        for scale in [0.5, 1.0, 1.5, 2.0]:
            scaled_image = cv2.resize(rotated_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            barcodes = decode(scaled_image)
            
            if barcodes:
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    log_widget.insert(END, f"Znaleziono kod kreskowy: {barcode_data} przy kącie {angle} stopni i skali {scale}\n")
                    log_widget.update_idletasks()
                    return barcode_data

    log_widget.insert(END, "Nie znaleziono kodu kreskowego.\n")
    log_widget.update_idletasks()
    return None

def process_directory(directory, log_widget, remove_leading_zeros, remove_last_four_digits, algorithm_choice):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue  # Pomiń jeśli nie jest plikiem
        try:
            # Odczytaj plik CV2
            image = cv2.imread(file_path)
            if image is None:
                log_widget.insert(END, f"Pomijanie pliku nie będącego zdjęciem: {filename}\n")
                log_widget.update_idletasks()
                continue

            barcode = None

            # Wybór algorytmu w zależności od wyboru użytkownika
            if algorithm_choice.get() == 2:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                barcodes = decode(image)
                if barcodes:
                    barcode = barcodes[0].data.decode('utf-8')
            elif algorithm_choice.get() == 3:
                barcode = detect_barcode(image, log_widget)
            else:
                # Podstawowy algorytm bez dodatkowych operacji
                barcodes = decode(image)
                if barcodes:
                    barcode = barcodes[0].data.decode('utf-8')
            
            if not barcode:
                log_widget.insert(END, f"Nie znaleziono kodu kreskowego na zdjęciu: {filename}\n")
                log_widget.update_idletasks()
                continue

            # Przetwórz Barcode na string
            if remove_leading_zeros.get():
                barcode = barcode.lstrip('0')
            if remove_last_four_digits.get():
                barcode = barcode[:-4]
            
            # Zbuduj nową nazwę pliku
            new_filename = f"{barcode}.jpg"
            new_file_path = os.path.join(directory, new_filename)
            
            # Zmień nazwę pliku
            os.rename(file_path, new_file_path)
            log_widget.insert(END, f"Zmieniono nazwę pliku '{filename}' na '{new_filename}'\n")
            log_widget.update_idletasks()
        except Exception as e:
            log_widget.insert(END, f"Błąd przetwarzania pliku {filename}: {e}\n")
            log_widget.update_idletasks()

def submit():
    path = textbox.get("1.0", END).strip()  # Pobierz ścieżkę z pola tekstowego
    if os.path.isdir(path):
        log_widget.insert(END, f"Przetwarzanie katalogu: {path}\n")
        log_widget.update_idletasks()
        process_directory(path, log_widget, remove_leading_zeros, remove_last_four_digits, algorithm_choice)
    else:
        log_widget.insert(END, "Podany katalog nie istnieje.\n")
        log_widget.update_idletasks()

# Tworzenie głównego okna aplikacji
main = Tk()
main.geometry('800x600')
main.title('HeliScanRename')

# Ramka dla ścieżki i przycisku uruchom
frame_path = Frame(main, bd=1)
frame_path.pack(side=TOP, fill=X)

# Etykieta nad polem tekstowym
tboxlabel = Label(frame_path, text='Podaj ścieżkę folderu ze zdjęciami:')
tboxlabel.pack(anchor=W)

# Pole tekstowe dla ścieżki
textbox = Text(frame_path, width=90, height=1)
textbox.pack(side=LEFT, anchor=W)

# Przycisk Uruchom
submitbutton = Button(frame_path, text='Uruchom', command=submit)
submitbutton.pack(side=RIGHT, anchor=W)


# Ramka dla wybieraków
frame_choice = Frame(main, bd=1)
frame_choice.pack()

# Ramka dla dodatkowych opcji dotyczących nazwy
frame_options = Frame(frame_choice, padx=20, pady=20, bd=1, relief=SUNKEN, height=300)
frame_options.pack(side=RIGHT, fill=X)

options_label = Label(frame_options, text='Wybierz dodatkowe opcje dotyczące nazwy:')
options_label.pack(anchor=W)

remove_leading_zeros = BooleanVar()
remove_last_four_digits = BooleanVar()

checkbox1 = Checkbutton(frame_options, text="Usuń zera z przodu", variable=remove_leading_zeros)
checkbox1.pack(anchor=W)

checkbox2 = Checkbutton(frame_options, text="Usuń cztery ostatnie cyfry", variable=remove_last_four_digits)
checkbox2.pack(anchor=W)

# Ramka dla wyboru algorytmu
frame_algorithm = Frame(frame_choice, padx=20, pady=20, bd=1, relief=SUNKEN, height=300)
frame_algorithm.pack(side=LEFT, fill=Y)

algorithm_label = Label(frame_algorithm, text='Wybierz algorytm wykrywający kody kreskowe:')
algorithm_label.pack(anchor=W)

algorithm_choice = IntVar()
algorithm_choice.set(1)  # Domyślnie ustawiony na podstawowy algorytm

radiobutton1 = Radiobutton(frame_algorithm, text="Podstawowy algorytm", variable=algorithm_choice, value=1)
radiobutton1.pack(anchor=W)

radiobutton2 = Radiobutton(frame_algorithm, text="Konwersja na odcienie szarości", variable=algorithm_choice, value=2)
radiobutton2.pack(anchor=W)

radiobutton3 = Radiobutton(frame_algorithm, text="Rotacja i skalowanie obrazu", variable=algorithm_choice, value=3)
radiobutton3.pack(anchor=W)

# ScrolledText dla log_widget
log_label = Label(main, text="Wynik:")
log_label.pack()

log_widget = scrolledtext.ScrolledText(main, width=90, height=10)
log_widget.pack()

app_label = Label(main, text="HeliScanRename Version: 1.0")
app_label.pack(side=LEFT)

author_label = Label(main, text="Aplikację wykonał: Mateusz Turzyniecki")
author_label.pack(side=RIGHT)

# Uruchomienie głównej pętli aplikacji
main.mainloop()
