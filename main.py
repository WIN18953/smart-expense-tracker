from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ColorProperty, StringProperty, ListProperty, ObjectProperty
from kivy.utils import get_color_from_hex
import json
from datetime import datetime
import matplotlib.pyplot as plt
import io
import csv
import os
from kivy.core.image import Image as CoreImage

# ---------- Translations (พจนานุกรมคำแปล) ----------
TRANSLATIONS = {
    'en': {
        'income': 'Income', 'expense': 'Expense', 'balance': 'Balance',
        'transactions': 'Transactions:', 'select_month': 'Select Month:', 'all_time': 'All Time',
        'menu_home': 'Add Transaction', 'menu_report': 'View Report', 'menu_settings': 'Settings',
        'add_title': 'Add Transaction', 'hint_amount': 'Amount', 'hint_note': 'Note', 'hint_date': 'Date (DD/MM/YYYY)',
        'btn_save': 'Save', 'btn_cancel': 'Cancel', 'btn_back': 'Back',
        'report_title': 'Monthly Report',
        'setting_title': 'Settings', 'general': 'GENERAL', 'currency': 'Currency',
        'data_mgmt': 'DATA MANAGEMENT', 'btn_export': 'Export to CSV', 'btn_clear': 'Clear All Data',
        'appearance': 'APPEARANCE', 'language': 'LANGUAGE', 'theme_dark': 'Dark Mode', 'theme_light': 'Light Mode',
        'cat_general': 'General', 'cat_food': 'Food', 'cat_travel': 'Travel', 'cat_study': 'Study', 'cat_other': 'Other',
        'type_income': 'Income', 'type_expense': 'Expense'
    },
    'th': {
        'income': 'รายรับ', 'expense': 'รายจ่าย', 'balance': 'คงเหลือ',
        'transactions': 'รายการล่าสุด:', 'select_month': 'เลือกเดือน:', 'all_time': 'ทั้งหมด',
        'menu_home': 'เพิ่มรายการ', 'menu_report': 'ดูรายงาน', 'menu_settings': 'ตั้งค่า',
        'add_title': 'บันทึกรายการ', 'hint_amount': 'จำนวนเงิน', 'hint_note': 'บันทึกช่วยจำ', 'hint_date': 'วันที่ (วว/ดด/ปปปป)',
        'btn_save': 'บันทึก', 'btn_cancel': 'ยกเลิก', 'btn_back': 'ย้อนกลับ',
        'report_title': 'รายงานประจำเดือน',
        'setting_title': 'การตั้งค่า', 'general': 'ทั่วไป', 'currency': 'สกุลเงิน',
        'data_mgmt': 'จัดการข้อมูล', 'btn_export': 'ส่งออกเป็น CSV', 'btn_clear': 'ล้างข้อมูลทั้งหมด',
        'appearance': 'รูปลักษณ์', 'language': 'ภาษา', 'theme_dark': 'โหมดมืด', 'theme_light': 'โหมดสว่าง',
        'cat_general': 'ทั่วไป', 'cat_food': 'อาหาร', 'cat_travel': 'เดินทาง', 'cat_study': 'การเรียน', 'cat_other': 'อื่นๆ',
        'type_income': 'รายรับ', 'type_expense': 'รายจ่าย'
    }
}

class TransactionItem(BoxLayout):
    text_content = StringProperty("")
    indicator_color = ColorProperty([1, 1, 1, 1])
    text_color = ColorProperty([1, 1, 1, 1])
    delete_callback = ObjectProperty(None)

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class HomeScreen(Screen):
    def on_kv_post(self, base_widget):
        self.load_month_list() 
        self.refresh()

    def on_enter(self, *args):
        self.load_month_list()
        Clock.schedule_once(lambda dt: self.refresh(), 0)

    def load_month_list(self):
        data = load_data()
        months = set()
        for item in data:
            date_str = item.get("date", "")
            parts = date_str.split('/')
            if len(parts) == 3:
                months.add(f"{parts[1]}/{parts[2]}")
        sorted_months = sorted(list(months), reverse=True)
        
        if "month_filter" in self.ids:
            app = App.get_running_app()
            default_txt = app.txt_all_time if app else "All Time"
            current = self.ids.month_filter.text
            self.ids.month_filter.values = [default_txt] + sorted_months
            if current not in self.ids.month_filter.values:
                self.ids.month_filter.text = default_txt

    def filter_data_with_index(self):
        data = load_data()
        if "month_filter" not in self.ids: 
            return [(i, x) for i, x in enumerate(data)]
        
        app = App.get_running_app()
        default_txt = app.txt_all_time if app else "All Time"
        selected = self.ids.month_filter.text
        
        if selected == default_txt:
            return [(i, x) for i, x in enumerate(data)]
            
        filtered = []
        for i, item in enumerate(data):
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                if f"{parts[1]}/{parts[2]}" == selected:
                    filtered.append((i, item))
        return filtered

    def refresh(self, *args):
        indexed_data = self.filter_data_with_index()
        only_data = [x[1] for x in indexed_data]
        self.update_summary(only_data)
        self.display_transactions(indexed_data)

    def update_summary(self, data):
        income = sum(item["amount"] for item in data if item.get("type") == "income")
        expense = sum(item["amount"] for item in data if item.get("type") == "expense")
        balance = income - expense

        app = App.get_running_app()
        sym = app.currency_symbol

        if "income_label" in self.ids: 
            self.ids.income_label.text = f"{sym} {income:,.2f}"
        if "expense_label" in self.ids: 
            self.ids.expense_label.text = f"{sym} {expense:,.2f}"
        if "balance_label" in self.ids: 
            self.ids.balance_label.text = f"{sym} {balance:,.2f}"

    def display_transactions(self, indexed_data):
        container = self.ids.get("transaction_list")
        if not container: return

        container.clear_widgets()
        app = App.get_running_app()
        sym = app.currency_symbol
        
        for index, (real_index, item) in enumerate(reversed(indexed_data)):
            note = item.get('note', '')
            date = item.get('date', '')
            t_type = item.get('type', '')
            amount = item.get('amount', 0)
            category = item.get('category', '')
            
            if t_type == "income":
                color = get_color_from_hex('#00E676')
                sign = "+"
            else:
                color = get_color_from_hex('#FF5252')
                sign = "-"
            
            full_text = f"{date} | {category} | {sign} {sym}{amount:,.2f}"
            if note:
                full_text += f"\n{note}"

            item_widget = TransactionItem(
                text_content=full_text,
                indicator_color=color,
                text_color=app.col_text,
                delete_callback=lambda idx=real_index: self.delete_transaction(idx)
            )
            container.add_widget(item_widget)

    def delete_transaction(self, index):
        data = load_data()
        if 0 <= index < len(data):
            data.pop(index)
            save_data(data)
            self.refresh()

class AddScreen(Screen):
    def save_transaction(self):
        amount_text = self.ids.amount_input.text.strip()
        note = self.ids.note_input.text.strip()
        t_type_raw = self.ids.type_spinner.text.strip()
        category = self.ids.category_spinner.text.strip()
        date_text = self.ids.date_input.text.strip()

        if not amount_text: return
        try:
            amount = float(amount_text)
        except ValueError: return

        if not date_text:
            date_text = datetime.now().strftime("%d/%m/%Y")
        
        app = App.get_running_app()
        translations = TRANSLATIONS[self.current_lang]
        
        final_type = "expense"
        if t_type_raw == t['type_income'] or t_type_raw == "Income":
            final_type = "income"
        
        data = load_data()
        data.append({
            "amount": amount,
            "note": note,
            "type": final_type,
            "category": category,
            "date": date_text
        })
        save_data(data)

        self.ids.amount_input.text = ""
        self.ids.note_input.text = ""
        self.ids.date_input.text = ""
        self.manager.current = "home"

class ReportScreen(Screen):
    def on_enter(self, *args):
        self.load_months()
    def load_months(self):
        data = load_data()
        months = set()
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                months.add(f"{parts[1]}/{parts[2]}")
        sorted_months = sorted(list(months), reverse=True)
        if sorted_months and "month_spinner" in self.ids:
            if self.ids.month_spinner.text not in sorted_months:
                self.ids.month_spinner.values = sorted_months
                self.ids.month_spinner.text = sorted_months[0]
            else:
                self.ids.month_spinner.values = sorted_months
                self.filter_report()
    def filter_report(self):
        if "month_spinner" not in self.ids: return
        selected = self.ids.month_spinner.text
        data = load_data()
        filtered = []
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                if f"{parts[1]}/{parts[2]}" == selected:
                    filtered.append(item)
        income = sum(item["amount"] for item in filtered if item.get("type") == "income")
        expense = sum(item["amount"] for item in filtered if item.get("type") == "expense")
        balance = income - expense
        
        app = App.get_running_app()
        sym = app.currency_symbol

        if "report_income" in self.ids: self.ids.report_income.text = f"{sym} {income:,.2f}"
        if "report_expense" in self.ids: self.ids.report_expense.text = f"{sym} {expense:,.2f}"
        if "report_balance" in self.ids: self.ids.report_balance.text = f"{sym} {balance:,.2f}"
        self.generate_chart(income, expense)
        
    def generate_chart(self, income, expense):
        app = App.get_running_app()
        bg_hex = '#121212' if app.is_dark_mode else '#F5F5F5'
        text_hex = 'white' if app.is_dark_mode else 'black'
        plt.clf()
        fig = plt.figure(figsize=(5, 4), facecolor=bg_hex)
        ax = plt.gca()
        ax.set_facecolor(bg_hex)
        categories = [app.txt_income, app.txt_expense]
        values = [income, expense]
        colors = ['#00E676', '#FF5252']
        bars = plt.bar(categories, values, color=colors, width=0.5)
        plt.title('Income vs Expense', color=text_hex, fontsize=14, pad=20, fontname='Tahoma')
        plt.xticks(color=text_hex, fontname='Tahoma')
        plt.yticks(color=text_hex, fontname='Tahoma')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#888888')
        ax.spines['left'].set_color('#888888')
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, height,
                    f'{height:,.0f}', ha='center', va='bottom', color=text_hex)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        texture = CoreImage(buf, ext='png').texture
        self.ids.chart_image.texture = texture
        plt.close(fig)

class SettingScreen(Screen):
    def clear_data(self):
        save_data([]) 
        self.manager.current = "home"
        self.manager.get_screen('home').refresh()
    def export_data(self):
        data = load_data()
        if not data: return
        filename = "expense_export.csv"
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Category", "Amount", "Note"])
                for item in data:
                    writer.writerow([
                        item.get("date", ""), item.get("type", ""),
                        item.get("category", ""), item.get("amount", ""),
                        item.get("note", "")
                    ])
            print(f"Exported to {os.path.abspath(filename)}")
        except Exception as e:
            print(f"Error export: {e}")

class ExpenseApp(App):
    # --- Theme Properties ---
    is_dark_mode = True
    col_bg = ColorProperty(get_color_from_hex('#121212'))
    col_text = ColorProperty([1, 1, 1, 1])
    col_subtext = ColorProperty([0.5, 0.5, 0.5, 1])
    col_card = ColorProperty(get_color_from_hex('#222222'))
    col_input_bg = ColorProperty(get_color_from_hex('#E0E0E0'))
    
    # --- Language Properties ---
    current_lang = 'en'
    font_name = StringProperty("Roboto")
    
    txt_income = StringProperty("Income")
    txt_expense = StringProperty("Expense")
    txt_balance = StringProperty("Balance")
    txt_transactions = StringProperty("Transactions:")
    txt_select_month = StringProperty("Select Month:")
    txt_all_time = StringProperty("All Time")
    txt_menu_home = StringProperty("Add Transaction")
    txt_menu_report = StringProperty("View Report")
    txt_menu_settings = StringProperty("Settings")
    txt_add_title = StringProperty("Add Transaction")
    txt_hint_amount = StringProperty("Amount")
    txt_hint_note = StringProperty("Note")
    txt_hint_date = StringProperty("Date (DD/MM/YYYY)")
    txt_btn_save = StringProperty("Save")
    txt_btn_cancel = StringProperty("Cancel")
    txt_btn_back = StringProperty("Back")
    txt_report_title = StringProperty("Monthly Report")
    txt_setting_title = StringProperty("Settings")
    txt_general = StringProperty("GENERAL")
    txt_currency = StringProperty("Currency")
    txt_data_mgmt = StringProperty("DATA MANAGEMENT")
    txt_btn_export = StringProperty("Export to CSV")
    txt_btn_clear = StringProperty("Clear All Data")
    txt_appearance = StringProperty("APPEARANCE")
    txt_language = StringProperty("LANGUAGE")
    txt_theme_mode = StringProperty("Dark Mode")

    type_values = ListProperty([])
    category_values = ListProperty([])
    currency_symbol = StringProperty("฿")


    def build(self):
        self.update_language_texts()
        self.update_theme_colors()
        pass


    def change_currency(self, value):
        if "(" in value and ")" in value:
            symbol = value.split("(")[1].strip(")")
            self.currency_symbol = symbol
            if self.root and self.root.get_screen('home'):
                self.root.get_screen('home').refresh()


    def switch_language(self):
        self.current_lang = 'th' if self.current_lang == 'en' else 'en'
        self.update_language_texts()
        if self.root:
            self.root.get_screen('home').load_month_list()


    def update_language_texts(self):
        t = TRANSLATIONS[self.current_lang]
        self.txt_income = t['income']; self.txt_expense = t['expense']; self.txt_balance = t['balance']
        self.txt_transactions = t['transactions']; self.txt_select_month = t['select_month']; self.txt_all_time = t['all_time']
        self.txt_menu_home = t['menu_home']; self.txt_menu_report = t['menu_report']; self.txt_menu_settings = t['menu_settings']
        self.txt_add_title = t['add_title']; self.txt_hint_amount = t['hint_amount']; self.txt_hint_note = t['hint_note']; self.txt_hint_date = t['hint_date']
        self.txt_btn_save = t['btn_save']; self.txt_btn_cancel = t['btn_cancel']; self.txt_btn_back = t['btn_back']
        self.txt_report_title = t['report_title']; self.txt_setting_title = t['setting_title']
        self.txt_general = t['general']; self.txt_currency = t['currency']
        self.txt_data_mgmt = t['data_mgmt']; self.txt_btn_export = t['btn_export']; self.txt_btn_clear = t['btn_clear']
        self.txt_appearance = t['appearance']; self.txt_language = t['language']
        self.txt_theme_mode = t['theme_light'] if self.is_dark_mode else t['theme_dark']

        self.type_values = [t['type_income'], t['type_expense']]
        self.category_values = [
            t['cat_general'], t['cat_food'], t['cat_travel'], 
            t['cat_study'], t['cat_other']
        ]

        if self.current_lang == 'th':
            self.font_name = "Tahoma"
        else:
            self.font_name = "Roboto"


    def switch_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.update_theme_colors()
        t = TRANSLATIONS[self.current_lang]
        self.txt_theme_mode = t['theme_light'] if self.is_dark_mode else t['theme_dark']


# Update UI colors based on current theme (dark / light)
    def update_theme_colors(self):
        if self.is_dark_mode:
            # Background color for main screen
            self.col_bg = get_color_from_hex('#121212')
            # Text and subtext colors
            self.col_text = [1, 1, 1, 1]
            self.col_subtext = [0.5, 0.5, 0.5, 1]
            
            self.col_card = get_color_from_hex('#222222')
            self.col_input_bg = get_color_from_hex('#E0E0E0')
        else:
            self.col_bg = get_color_from_hex('#F5F5F5')
            self.col_text = [0, 0, 0, 1]
            self.col_subtext = [0.4, 0.4, 0.4, 1]
            
            self.col_card = get_color_from_hex('#FFFFFF')
            self.col_input_bg = get_color_from_hex('#FFFFFF')

if __name__ == "__main__":
    try:
        open("data.json", "x", encoding="utf-8").write("[]")
    except FileExistsError:
        pass
    ExpenseApp().run()