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
import socket
import whois
import re
from urllib.parse import urlparse

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
        
    def validate_domain(self, domain):
        """
        Проверка валидности домена
        """
        domain_regex = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.([a-zA-Z]{2,}\.?)+$"
        )
        return domain_regex.match(domain) is not None
    
    def check_domain_exists(self, domain):
        """
        Проверка существования домена через DNS
        """
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
    
    def check_website_status(self, domain):
        """
        Проверка доступности сайта
        """
        try:
            response = requests.get(f"http://{domain}", timeout=5, allow_redirects=True)
            return response.status_code
        except:
            try:
                response = requests.get(f"https://{domain}", timeout=5, allow_redirects=True)
                return response.status_code
            except:
                return None
    
    def get_whois_info(self, domain):
        """
        Получение WHOIS информации
        """
        try:
            w = whois.whois(domain)
            info = {
                'domain_name': getattr(w, 'domain_name', 'N/A'),
                'creation_date': getattr(w, 'creation_date', 'N/A'),
                'expiration_date': getattr(w, 'expiration_date', 'N/A'),
                'updated_date': getattr(w, 'updated_date', 'N/A'),
                'registrar': getattr(w, 'registrar', 'N/A'),
                'registrant_name': getattr(w, 'name', 'N/A'),
                'registrant_org': getattr(w, 'org', 'N/A'),
                'registrant_country': getattr(w, 'country', 'N/A'),
                'registrant_email': getattr(w, 'email', 'N/A'),
                'status': getattr(w, 'status', 'N/A')
            }
            return info
        except Exception as e:
            self.log(f"    ❌ Ошибка WHOIS для {domain}: {e}")
            return None
    
    def calculate_domain_age(self, creation_date):
        """
        Вычисление возраста домена
        """
        try:
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if isinstance(creation_date, datetime):
                age = datetime.now() - creation_date
                return age.days
            return None
        except:
            return None
    
    def analyze_domain_flags(self, domain_info, domain_age, website_status):
        """
        Анализ красных флагов домена
        """
        flags = []
        
        # Проверка возраста
        if domain_age is not None:
            if domain_age < 180:  # младше 6 месяцев
                flags.append("Молодой домен")
        
        # Проверка доступности
        if website_status is None:
            flags.append("Сайт недоступен")
        elif website_status >= 400:
            flags.append(f"HTTP ошибка {website_status}")
        
        # Проверка WHOIS данных
        if domain_info:
            if domain_info.get('registrant_name') == 'N/A':
                flags.append("Скрытые данные владельца")
            
            # Проверка регистратора
            registrar = domain_info.get('registrar', '')
            if isinstance(registrar, str) and any(word in registrar.lower() for word in ['namecheap', 'godaddy']):
                # Это нормальные регистраторы, не флаг
                pass
        
        return flags
    
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
            self.log(f"    ❌ Ошибка при поиске для {domain}: {e}")
            return []
    
    def process_domain(self, domain):
        """
        Полная обработка домена с проверками
        """
        results = []
        
        # 1. Валидация домена
        if not self.validate_domain(domain):
            self.log(f"    ❌ Некорректный формат домена: {domain}")
            return results
        
        # 2. Проверка существования
        if not self.check_domain_exists(domain):
            self.log(f"    ❌ Домен не найден в DNS: {domain}")
            return results
        
        self.log(f"    ✅ Домен найден в DNS")
        
        # 3. Проверка доступности сайта
        website_status = self.check_website_status(domain)
        if website_status:
            self.log(f"    ✅ Сайт доступен (HTTP {website_status})")
        else:
            self.log(f"    ❌ Сайт недоступен")
        
        # 4. Получение WHOIS информации
        self.log(f"    🔍 Получение WHOIS данных...")
        domain_info = self.get_whois_info(domain)
        
        if domain_info:
            # Вычисление возраста домена
            domain_age = self.calculate_domain_age(domain_info.get('creation_date'))
            if domain_age:
                self.log(f"    📅 Возраст домена: {domain_age} дней ({domain_age//365} лет)")
            
            # Информация о владельце
            if domain_info.get('registrant_name') != 'N/A':
                self.log(f"    👤 Владелец: {domain_info.get('registrant_name')}")
            if domain_info.get('registrant_country') != 'N/A':
                self.log(f"    🌍 Страна: {domain_info.get('registrant_country')}")
            if domain_info.get('registrar') != 'N/A':
                self.log(f"    🏢 Регистратор: {domain_info.get('registrar')}")
            
            # Анализ красных флагов
            flags = self.analyze_domain_flags(domain_info, domain_age, website_status)
            if flags:
                self.log(f"    🚩 Красные флаги: {', '.join(flags)}")
        
        # 5. Поиск ссылок в Wikipedia
        self.log(f"    🔍 Поиск ссылок в Wikipedia...")
        links = self.search_wikipedia_links(domain)
        
        for url, anchor in links:
            # Расширенная информация для CSV
            row = [
                domain,
                datetime.now().strftime('%Y-%m-%d'),
                url,
                anchor,
                domain_age if domain_age else 'N/A',
                domain_info.get('registrant_country', 'N/A') if domain_info else 'N/A',
                domain_info.get('registrar', 'N/A') if domain_info else 'N/A',
                website_status if website_status else 'N/A',
                '; '.join(flags) if flags else 'Нет'
            ]
            results.append(row)
            self.log(f"    ✅ Найдена ссылка: {url}")
        
        return results
    
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
                
                # Используем новый метод полной обработки
                domain_results = self.process_domain(domain)
                results.extend(domain_results)
                
                if not domain_results:
                    self.log(f"    ❌ Ссылок не найдено")
                
                # Обновляем прогресс
                self.progress.config(value=i)
                self.root.update()
                
                time.sleep(2)  # увеличиваем паузу из-за WHOIS запросов
            
            # Сохраняем результаты с расширенными данными
            if results:
                output_file = 'wikipedia_backlinks_extended.csv'
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Домен', 
                        'Дата', 
                        'Wiki-ссылка', 
                        'Текст ссылки',
                        'Возраст домена (дни)',
                        'Страна владельца',
                        'Регистратор',
                        'HTTP статус',
                        'Красные флаги'
                    ])
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
