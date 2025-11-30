import flet as ft
import random
import time
import math

def main(page: ft.Page):
    page.title = "E-Nose AI Dashboard (Modern UI)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#0F172A" # Dark Navy Background

    # --- STATE ---
    is_running = False
    chart_data = [ft.LineChartDataPoint(0, 0)]

    # --- COMPONENTS ---

    # 1. SIDEBAR
    sidebar = ft.Container(
        width=250,
        bgcolor="#1E293B",
        padding=20,
        content=ft.Column(
            controls=[
                ft.Text("E-NOSE\nPRO", size=30, weight=ft.FontWeight.W_900, color=ft.Colors.BLUE_400),
                ft.Divider(color=ft.Colors.BLUE_GREY_700),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Dashboard", 
                    icon=ft.Icons.DASHBOARD, 
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    height=50,
                    width=200
                ),
                ft.Container(height=10),
                ft.TextButton("Riwayat Data", icon=ft.Icons.HISTORY, width=200),
                ft.TextButton("Pengaturan", icon=ft.Icons.SETTINGS, width=200),
                ft.Container(expand=True), # REPLACED SPACER
                ft.Text("v3.0 Flet Edition", color=ft.Colors.GREY_500, size=12)
            ]
        )
    )

    # 2. STAT CARDS
    def create_card(title, value, unit, icon, color):
        return ft.Container(
            expand=True,
            padding=20,
            bgcolor="#1E293B",
            border_radius=15,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=24),
                            ft.Text(title, color=ft.Colors.GREY_400, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    ft.Text(f"{value} {unit}", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ]
            )
        )

    txt_temp = ft.Text("28.5 °C", size=28, weight=ft.FontWeight.BOLD)
    txt_hum = ft.Text("65 %", size=28, weight=ft.FontWeight.BOLD)
    
    card_temp = ft.Container(
        expand=True, padding=20, bgcolor="#1E293B", border_radius=15,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.ORANGE), ft.Text("SUHU", color=ft.Colors.GREY_400)]),
            txt_temp
        ])
    )
    card_hum = ft.Container(
        expand=True, padding=20, bgcolor="#1E293B", border_radius=15,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.WATER_DROP, color=ft.Colors.BLUE), ft.Text("KELEMBABAN", color=ft.Colors.GREY_400)]),
            txt_hum
        ])
    )
    card_pres = ft.Container(
        expand=True, padding=20, bgcolor="#1E293B", border_radius=15,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.SPEED, color=ft.Colors.GREEN), ft.Text("TEKANAN", color=ft.Colors.GREY_400)]),
            ft.Text("1005 hPa", size=28, weight=ft.FontWeight.BOLD)
        ])
    )

    # 3. RESULT WIDGET (Big Panel)
    result_status = ft.Text("READY", size=14, color=ft.Colors.WHITE70)
    result_main = ft.Text("MENUNGGU INPUT", size=24, weight=ft.FontWeight.BOLD)
    result_icon = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREY, size=50)
    result_container = ft.Container(
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=20,
        padding=30,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("HASIL DETEKSI", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                ft.Container(height=10),
                result_icon,
                ft.Container(height=10),
                result_main,
                result_status
            ]
        )
    )

    # 4. CHART
    chart_series = ft.LineChartData(
        color=ft.Colors.CYAN,
        stroke_width=3,
        curved=True,
        stroke_cap_round=True,
        below_line_bgcolor=ft.with_opacity(0.2, ft.Colors.CYAN),
        data_points=chart_data
    )
    
    chart = ft.LineChart(
        data_series=[chart_series],
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.GREY)),
        left_axis=ft.ChartAxis(labels_size=40),
        bottom_axis=ft.ChartAxis(labels_size=40),
        tooltip_bgcolor=ft.with_opacity(0.8, ft.Colors.BLUE_GREY),
        min_y=0,
        max_y=100,
        expand=True
    )

    # 5. CONTROL BUTTON
    def toggle_scan(e):
        nonlocal is_running
        is_running = not is_running
        btn_start.text = "Stop Deteksi" if is_running else "Mulai Deteksi"
        btn_start.bgcolor = ft.Colors.RED_600 if is_running else ft.Colors.BLUE_600
        btn_start.icon = ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW
        
        if is_running:
            result_container.bgcolor = ft.Colors.BLUE_600
            result_main.value = "MENGAMBIL DATA..."
            result_icon.name = ft.Icons.SEARCH
            result_icon.color = ft.Colors.WHITE
            page.update()
            simulate_data()
        else:
            result_container.bgcolor = ft.Colors.GREEN_600
            result_main.value = "TIDAK TERDETEKSI"
            result_status.value = "Akurasi: 99.2%"
            result_icon.name = ft.Icons.CHECK_CIRCLE
            result_icon.color = ft.Colors.WHITE
            page.update()

    btn_start = ft.ElevatedButton(
        "Mulai Deteksi",
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=20
        ),
        width=300,
        on_click=toggle_scan
    )

    # --- SIMULATION LOGIC ---
    def simulate_data():
        x = 0
        while is_running:
            # Update Sensor Data Randomly
            val = 50 + (20 * math.sin(x * 0.5)) + random.randint(-5, 5)
            chart_data.append(ft.LineChartDataPoint(x, val))
            if len(chart_data) > 50:
                chart_data.pop(0)
            
            txt_temp.value = f"{28 + random.randint(-1,1)}.0 °C"
            txt_hum.value = f"{65 + random.randint(-2,2)} %"
            
            chart.update()
            txt_temp.update()
            txt_hum.update()
            
            x += 1
            time.sleep(0.1)

    # --- LAYOUT ASSEMBLY ---
    
    # Right Panel Content
    main_content = ft.Container(
        expand=True,
        padding=30,
        content=ft.Column(
            controls=[
                # Top Row: Cards
                ft.Row(
                    controls=[card_temp, card_hum, card_pres],
                    spacing=20
                ),
                ft.Container(height=20),
                # Middle: Chart & Result
                ft.Row(
                    expand=True,
                    controls=[
                        # Left: Chart
                        ft.Container(
                            expand=2,
                            bgcolor="#1E293B",
                            border_radius=15,
                            padding=20,
                            content=ft.Column([
                                ft.Text("Grafik Respon Sensor (MQ135)", weight=ft.FontWeight.BOLD),
                                chart
                            ])
                        ),
                        # Right: Result & Control
                        ft.Container(
                            expand=1,
                            content=ft.Column(
                                controls=[
                                    result_container,
                                    ft.Container(expand=True), # REPLACED SPACER
                                    btn_start
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                            )
                        )
                    ],
                    spacing=20
                )
            ]
        )
    )

    page.add(
        ft.Row(
            controls=[sidebar, main_content],
            expand=True,
            spacing=0
        )
    )

ft.app(target=main)