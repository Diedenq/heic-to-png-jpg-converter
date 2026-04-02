"""
HEIC to PNG/JPG конвертер с графическим интерфейсом
Использует ImageMagick для конвертации HEIC файлов
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
from pathlib import Path
import threading

class HEICConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HEIC Конвертер")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        # Проверяем ImageMagick
        if not self.check_imagemagick():
            self.show_install_instructions()
            return
        
        self.files = []
        self.output_folder = None
        self.setup_ui()
    
    def check_imagemagick(self):
        """Проверяет установлен ли ImageMagick"""
        try:
            result = subprocess.run(['magick', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def show_install_instructions(self):
        """Показывает инструкции по установке ImageMagick"""
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="ImageMagick не найден!", 
                         font=('Arial', 14, 'bold'), foreground='red')
        title.pack(pady=10)
        
        instructions = """
Для работы конвертера необходим ImageMagick.

Варианты установки:

1. Через MSYS2:
   pacman -S mingw-w64-ucrt-x86_64-imagemagick

2. С официального сайта:
   https://imagemagick.org/script/download.php#windows
   При установке отметьте 'Install legacy utilities'

3. Через Chocolatey:
   choco install imagemagick

После установки перезапустите программу.
        """
        
        text = tk.Text(frame, height=15, width=60, wrap=tk.WORD)
        text.insert(1.0, instructions)
        text.config(state=tk.DISABLED)
        text.pack(pady=10)
        
        ttk.Button(frame, text="Закрыть", 
                  command=self.root.quit).pack(pady=10)
    
    def setup_ui(self):
        """Создает графический интерфейс"""
        # Заголовок
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        title = ttk.Label(header, text="HEIC Конвертер", 
                         font=('Arial', 16, 'bold'))
        title.pack()
        
        status = ttk.Label(header, text="ImageMagick найден ✓", 
                          foreground='green')
        status.pack()
        
        # Кнопки добавления файлов
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(buttons_frame, text="Добавить файлы", 
                  command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Добавить папку", 
                  command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить список", 
                  command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # Список файлов
        list_frame = ttk.LabelFrame(self.root, text="Файлы для конвертации", 
                                    padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, 
                                       yscrollcommand=scrollbar.set,
                                       selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Настройки конвертации
        settings_frame = ttk.LabelFrame(self.root, text="Настройки", 
                                        padding=10)
        settings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Папка для сохранения
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Папка для сохранения:").pack(side=tk.LEFT)
        
        self.output_label = ttk.Label(output_frame, 
                                      text="(рядом с исходными файлами)", 
                                      foreground='gray')
        self.output_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(output_frame, text="Выбрать папку", 
                  command=self.select_output_folder).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(output_frame, text="Сбросить", 
                  command=self.reset_output_folder).pack(side=tk.LEFT)
        
        # Формат
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="Формат вывода:").pack(side=tk.LEFT)
        
        self.format_var = tk.StringVar(value="png")
        ttk.Radiobutton(format_frame, text="PNG", 
                       variable=self.format_var, 
                       value="png").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="JPG", 
                       variable=self.format_var, 
                       value="jpg").pack(side=tk.LEFT, padx=10)
        
        # Качество для JPG
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_frame, text="Качество JPG (1-100):").pack(side=tk.LEFT)
        
        self.quality_var = tk.IntVar(value=95)
        quality_spinbox = ttk.Spinbox(quality_frame, from_=1, to=100, 
                                      textvariable=self.quality_var, 
                                      width=10)
        quality_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Кнопка конвертации
        convert_frame = ttk.Frame(self.root)
        convert_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.convert_button = ttk.Button(convert_frame, 
                                        text="Конвертировать", 
                                        command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(convert_frame, 
                                       mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Статус
        self.status_label = ttk.Label(self.root, text="Готов к работе")
        self.status_label.pack(pady=5)
    
    def add_files(self):
        """Добавляет файлы в список"""
        files = filedialog.askopenfilenames(
            title="Выберите HEIC файлы",
            filetypes=[("HEIC файлы", "*.heic *.HEIC"), 
                      ("Все файлы", "*.*")]
        )
        
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)
    
    def add_folder(self):
        """Добавляет все HEIC файлы из папки"""
        folder = filedialog.askdirectory(title="Выберите папку с HEIC файлами")
        
        if folder:
            folder_path = Path(folder)
            heic_files = list(folder_path.glob('*.heic')) + \
                        list(folder_path.glob('*.HEIC'))
            
            for file in heic_files:
                file_str = str(file)
                if file_str not in self.files:
                    self.files.append(file_str)
                    self.file_listbox.insert(tk.END, file.name)
            
            if heic_files:
                messagebox.showinfo("Успех", 
                                  f"Добавлено {len(heic_files)} файлов")
            else:
                messagebox.showwarning("Предупреждение", 
                                      "HEIC файлы не найдены")
    
    def clear_files(self):
        """Очищает список файлов"""
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.status_label.config(text="Список очищен")
    
    def select_output_folder(self):
        """Выбирает папку для сохранения результатов"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения результатов"
        )
        
        if folder:
            self.output_folder = folder
            # Показываем только имя папки, если путь длинный
            display_path = Path(folder).name
            self.output_label.config(text=display_path, foreground='green')
            self.status_label.config(text=f"Результаты будут сохранены в: {folder}")
    
    def reset_output_folder(self):
        """Сбрасывает выбранную папку"""
        self.output_folder = None
        self.output_label.config(text="(рядом с исходными файлами)", 
                                foreground='gray')
        self.status_label.config(text="Результаты будут сохраняться рядом с исходными файлами")
    
    def convert_file(self, input_path, output_format, quality):
        """Конвертирует один файл"""
        input_file = Path(input_path)
        
        # Определяем путь для сохранения
        if self.output_folder:
            output_path = Path(self.output_folder) / f"{input_file.stem}.{output_format.lower()}"
        else:
            output_path = input_file.with_suffix(f'.{output_format.lower()}')
        
        cmd = ['magick', str(input_file)]
        
        if output_format.lower() == 'jpg':
            cmd.extend(['-quality', str(quality)])
        
        cmd.append(str(output_path))
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, output_path.name
        except subprocess.CalledProcessError as e:
            return False, str(e)
    
    def start_conversion(self):
        """Запускает конвертацию в отдельном потоке"""
        if not self.files:
            messagebox.showwarning("Предупреждение", 
                                  "Добавьте файлы для конвертации")
            return
        
        # Запускаем конвертацию в отдельном потоке
        thread = threading.Thread(target=self.convert_all)
        thread.daemon = True
        thread.start()
    
    def convert_all(self):
        """Конвертирует все файлы"""
        self.convert_button.config(state=tk.DISABLED)
        
        total = len(self.files)
        converted = 0
        
        output_format = self.format_var.get()
        quality = self.quality_var.get()
        
        self.progress['maximum'] = total
        self.progress['value'] = 0
        
        for i, file in enumerate(self.files):
            filename = Path(file).name
            self.status_label.config(text=f"Конвертация: {filename}")
            
            success, result = self.convert_file(file, output_format, quality)
            
            if success:
                converted += 1
            
            self.progress['value'] = i + 1
            self.root.update_idletasks()
        
        self.convert_button.config(state=tk.NORMAL)
        self.status_label.config(text="Конвертация завершена!")
        
        messagebox.showinfo("Готово", 
                          f"Конвертировано: {converted}/{total} файлов")
        
        self.clear_files()

def main():
    root = tk.Tk()
    app = HEICConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()