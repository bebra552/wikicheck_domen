import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import time
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import webbrowser
import threading
import os

class WikiCheckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WikiCheck - Проверка доменов в Wikipedia")
        self.root.geometry("700x500")
        
        # Заголовки для запросов
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DropDomainBot/1.0; +mailto:veprik8900@mail.ru)"
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="WikiCheck - Поиск обратных ссылок с Wikipedia", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Кнопка выбора файла
        ttk.Label(main_frame, text="Файл с доменами:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Выбрать", command=self.select_file).grid(row=1, column=2, pady=5)
        
        # Кнопка запуска
        self.start_button = ttk.Button(main_frame, text="Начать проверку", command=self.start_check)
        self.start_button.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Статус
        self.status_label = ttk.Label(main_frame, text="Готов к работе")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=5)
        
        # Логи
        ttk.Label(main_frame, text="Логи:").grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(main_frame, width=80, height=15)
        self.log_text.grid(row=6, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка связи
        contact_button = ttk.Button(main_frame, text="📞 Связаться с автором", 
                                   command=self.open_contact)
        contact_button.grid(row=7, column=0, columnspan=3, pady=10)
        
        # Настройка растягивания
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с доменами",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
            
    def open_contact(self):
        webbrowser.open("https://t.me/Userspoi")
        
    def log(self, message):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def search_wikipedia_links(self, domain):
        """
        Использует Bing для поиска ссылок с Wikipedia на указанный домен
        """
        try:
            query = f"site:en.wikipedia.org OR site:ru.wikipedia.org {domain}"
            url = f"https://www.bing.com/search?q={query}"
            response = requests.get(url, headers=self.headers, timeout=10)

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for li in soup.find_all("li", class_="b_algo"):
                link = li.find("a")
                if link and "wikipedia.org" in link['href']:
                    title = link.get_text(strip=True)
                    href = link['href']
                    results.append((href, title))
            return results
        except Exception as e:
            self.log(f"❌ Ошибка при поиске для {domain}: {e}")
            return []
    
    def start_check(self):
        if not self.file_path.get():
            messagebox.showerror("Ошибка", "Выберите файл с доменами")
            return
            
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Ошибка", "Файл не найден")
            return
            
        # Запускаем проверку в отдельном потоке
        self.start_button.config(state='disabled')
        thread = threading.Thread(target=self.check_domains)
        thread.daemon = True
        thread.start()
        
    def check_domains(self):
        try:
            # Читаем домены из файла
            with open(self.file_path.get(), 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            if not domains:
                messagebox.showerror("Ошибка", "Файл пуст или не содержит доменов")
                self.start_button.config(state='normal')
                return
            
            self.log(f"Загружено {len(domains)} доменов для проверки")
            
            # Настраиваем прогресс бар
            self.progress.config(maximum=len(domains))
            self.progress.config(value=0)
            
            results = []
            
            for i, domain in enumerate(domains, 1):
                self.status_label.config(text=f"Проверяю: {domain} ({i}/{len(domains)})")
                self.log(f"[{i}/{len(domains)}] Проверяю: {domain}")
                
                links = self.search_wikipedia_links(domain)
                
                for url, anchor in links:
                    results.append([domain, datetime.now().strftime('%Y-%m-%d'), url, anchor])
                    self.log(f"  ✅ Найдена ссылка: {url}")
                
                if not links:
                    self.log(f"  ❌ Ссылок не найдено")
                
                # Обновляем прогресс
                self.progress.config(value=i)
                self.root.update()
                
                time.sleep(1.5)  # не спамим
            
            # Сохраняем результаты
            if results:
                output_file = 'wikipedia_backlinks.csv'
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Домен', 'Дата', 'Wiki-ссылка', 'Текст ссылки'])
                    writer.writerows(results)
                
                self.log(f"\n✅ Найдено: {len(results)} доменов со ссылками")
                self.log(f"Результаты сохранены в {output_file}")
                self.status_label.config(text=f"Готово! Найдено {len(results)} ссылок")
                messagebox.showinfo("Готово", f"Найдено {len(results)} ссылок с Wikipedia.\nРезультаты сохранены в {output_file}")
            else:
                self.log("\n❌ Ссылок с Wikipedia не найдено")
                self.status_label.config(text="Готово! Ссылок не найдено")
                messagebox.showinfo("Готово", "Ссылок с Wikipedia не найдено")
                
        except Exception as e:
            self.log(f"❌ Общая ошибка: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
        finally:
            self.start_button.config(state='normal')
            self.progress.config(value=0)

def main():
    root = tk.Tk()
    app = WikiCheckApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()