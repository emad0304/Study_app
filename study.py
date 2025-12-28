import flet as ft
import csv
import os
import time
import threading
from datetime import datetime, timedelta

# تابع اصلی برای اجرا در اندروید
def main(page: ft.Page):
    filename = "study_data.csv"
    state = {"running": False, "start_time": None, "elapsed_seconds": 0}

    page.title = "دستیار مطالعه"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family="sans-serif")
    page.scroll = ft.ScrollMode.AUTO

    def format_minutes_to_hrs(minutes):
        try:
            m = int(minutes)
            return f"{m // 60}:{m % 60:02d}"
        except: return "0:00"

    def calculate_percent(total, correct, wrong):
        try:
            t, c, w = int(total), int(correct), int(wrong)
            if t <= 0: return 0.0
            return ((c * 3) - w) / (t * 3) * 100
        except: return 0.0

    # المان‌های صفحه
    sub_input = ft.TextField(label="نام درس", width=250)
    coeff_input = ft.TextField(label="ضریب", value="1", width=70, text_align=ft.TextAlign.CENTER)
    time_input = ft.TextField(label="زمان (دقیقه)", width=120, text_align=ft.TextAlign.CENTER)
    tot_input = ft.TextField(label="کل تست", value="0", width=80)
    cor_input = ft.TextField(label="صحیح", value="0", width=80)
    wro_input = ft.TextField(label="غلط", value="0", width=80)
    timer_text = ft.Text("00:00:00", size=50, color="red", weight="bold")
    log_column = ft.Column(spacing=10)

    def timer_thread():
        while state["running"]:
            try:
                state["elapsed_seconds"] = int(time.time() - state["start_time"])
                h, m, s = state["elapsed_seconds"] // 3600, (state["elapsed_seconds"] % 3600) // 60, state["elapsed_seconds"] % 60
                timer_text.value = f"{h:02d}:{m:02d}:{s:02d}"
                page.update()
                time.sleep(1)
            except: break

    def start_study(e):
        if not sub_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("نام درس را وارد کنید")); page.snack_bar.open = True; page.update(); return
        state["running"] = True
        state["start_time"] = time.time()
        btn_start.disabled = True; btn_stop.disabled = False; page.update()
        threading.Thread(target=timer_thread, daemon=True).start()

    def stop_study(e):
        state["running"] = False
        btn_start.disabled = False; btn_stop.disabled = True
        time_input.value = str(max(1, state["elapsed_seconds"] // 60)); page.update()

    btn_start = ft.ElevatedButton("شروع", on_click=start_study, bgcolor="green", color="white")
    btn_stop = ft.ElevatedButton("توقف", on_click=stop_study, bgcolor="red", color="white", disabled=True)

    def load_logs():
        log_column.controls.clear()
        if os.path.exists(filename):
            with open(filename, mode='r', encoding='utf-16') as f:
                rows = list(csv.reader(f, delimiter='\t'))
                for r in reversed(rows):
                    if len(r) >= 7:
                        p = calculate_percent(r[4], r[5], r[6])
                        p_str = f"{p:.1f}%"
                        log_column.controls.append(ft.Container(
                            content=ft.Text(f"📘 {r[2]} | زمان: {format_minutes_to_hrs(r[3])} | درصد: {p_str}"),
                            bgcolor="blue50", padding=10, border_radius=8))
        page.update()

    def save_data(e):
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            with open(filename, mode='a', newline='', encoding='utf-16') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow([date_str, datetime.now().strftime("%H:%M"), sub_input.value, time_input.value, tot_input.value, cor_input.value, wro_input.value, coeff_input.value])
            load_logs()
            page.snack_bar = ft.SnackBar(ft.Text("ثبت شد ✅")); page.snack_bar.open = True; page.update()
        except: pass

    page.add(ft.Column([
        ft.Text("دستیار مطالعه", size=25, weight="bold"),
        timer_text, ft.Row([btn_start, btn_stop], alignment="center"),
        sub_input, ft.Row([time_input, coeff_input], alignment="center"),
        ft.Row([tot_input, cor_input, wro_input], alignment="center"),
        ft.ElevatedButton("ذخیره", on_click=save_data, width=200),
        ft.Divider(),
        log_column
    ], horizontal_alignment="center"))
    load_logs()

ft.app(target=main)
