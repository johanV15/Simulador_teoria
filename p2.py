import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Rectangle
from matplotlib.widgets import Slider, Button, RadioButtons
import matplotlib.patches as mpatches

class BeamformingSimulator:
    def __init__(self):
        # Configuraciones por defecto para cada tecnología
        self.configs = {
            '5G': {
                'freq_range': (3.5, 28),  # GHz
                'max_power': 40,  # dBm
                'max_distance': 1000,  # metros
                'antenna_elements': 64,
                'subcarrier_spacing': 30,  # kHz
                'bandwidth': 100,  # MHz
                'modulation': '256-QAM'
            },
            '5G Advanced': {
                'freq_range': (3.5, 71),  # GHz
                'max_power': 43,  # dBm
                'max_distance': 1500,  # metros
                'antenna_elements': 256,
                'subcarrier_spacing': 60,  # kHz
                'bandwidth': 400,  # MHz
                'modulation': '1024-QAM'
            },
            '6G': {
                'freq_range': (95, 300),  # GHz (sub-THz)
                'max_power': 30,  # dBm
                'max_distance': 500,  # metros
                'antenna_elements': 1024,
                'subcarrier_spacing': 120,  # kHz
                'bandwidth': 1000,  # MHz
                'modulation': '4096-QAM'
            }
        }
        
        self.current_tech = '5G'
        self.frequency = 3.5  # GHz
        self.power = 30  # dBm
        self.distance = 100  # metros
        self.beam_angle = 0  # grados
        self.beam_width = 30  # grados
        
        self.updating = False
        
        self.setup_plot()
        
    def setup_plot(self):
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.suptitle('Simulador de Beamforming: 5G / 5G Advanced / 6G', fontsize=14, fontweight='bold')
        
        gs = self.fig.add_gridspec(2, 3, hspace=0.4, wspace=0.3, 
                                   left=0.08, right=0.95, top=0.90, bottom=0.15)
        
        self.ax_beam = self.fig.add_subplot(gs[0, :2])
        self.ax_beam.set_title('Formación de Haz (Beamforming)')
        self.ax_beam.set_xlabel('Distancia X (metros)')
        self.ax_beam.set_ylabel('Distancia Y (metros)')
        self.ax_beam.grid(True, alpha=0.3)
        
        self.ax_metrics = self.fig.add_subplot(gs[1, :])
        self.ax_metrics.axis('off')
        
        self.ax_control = self.fig.add_subplot(gs[0, 2])
        self.ax_control.axis('off')
        
        self.create_visual_elements()
        self.setup_controls()
        
        rax = plt.axes([0.82, 0.55, 0.12, 0.12])
        self.radio = RadioButtons(rax, ('5G', '5G Advanced', '6G'))
        self.radio.on_clicked(self.change_technology)
        
        self.btn_transmit_ax = plt.axes([0.82, 0.48, 0.12, 0.04])
        self.btn_transmit = Button(self.btn_transmit_ax, 'Transmitir', color='lightgreen')
        self.btn_transmit.on_clicked(self.transmit_signal)

        # Nuevo botón de análisis detallado
        self.btn_analysis_ax = plt.axes([0.82, 0.43, 0.12, 0.04])
        self.btn_analysis = Button(self.btn_analysis_ax, 'Análisis detallado', color='lightblue')
        self.btn_analysis.on_clicked(self.show_detailed_analysis)
        
        self.update_display()
        
    def create_visual_elements(self):
        self.base_station = Rectangle((0, -5), 10, 10, 
                                     facecolor='blue', 
                                     edgecolor='darkblue',
                                     alpha=0.7)
        self.ax_beam.add_patch(self.base_station)
        self.ax_beam.text(5, 0, 'BS', ha='center', va='center', 
                         color='white', fontweight='bold', fontsize=10)
        self.beam_wedge = None
        self.user_marker, = self.ax_beam.plot([], [], 'ro', markersize=12)
        
    def setup_controls(self):
        slider_color = 'lightgray'
        
        self.ax_freq = plt.axes([0.2, 0.08, 0.55, 0.02])
        self.slider_freq = Slider(self.ax_freq, 'Frecuencia (GHz)', 
                                  1, 300, valinit=self.frequency, 
                                  color=slider_color, valstep=0.5)
        self.slider_freq.on_changed(self.update_parameters)
        
        self.ax_power = plt.axes([0.2, 0.05, 0.55, 0.02])
        self.slider_power = Slider(self.ax_power, 'Potencia (dBm)', 
                                   0, 50, valinit=self.power, 
                                   color=slider_color, valstep=1)
        self.slider_power.on_changed(self.update_parameters)
        
        self.ax_dist = plt.axes([0.2, 0.02, 0.55, 0.02])
        self.slider_dist = Slider(self.ax_dist, 'Distancia (m)', 
                                  10, 2000, valinit=self.distance, 
                                  color=slider_color, valstep=10)
        self.slider_dist.on_changed(self.update_parameters)
        
        self.ax_angle = plt.axes([0.2, 0.11, 0.55, 0.02])
        self.slider_angle = Slider(self.ax_angle, 'Ángulo del haz', 
                                   -90, 90, valinit=self.beam_angle, 
                                   color=slider_color, valstep=5)
        self.slider_angle.on_changed(self.update_parameters)
        
    def calculate_metrics(self):
        path_loss = 32.4 + 20 * np.log10(self.frequency * 1000) + 20 * np.log10(self.distance / 1000)
        if self.current_tech == '6G':
            path_loss += 10
        elif self.current_tech == '5G Advanced' and self.frequency > 28:
            path_loss += 5
            
        config = self.configs[self.current_tech]
        beamforming_gain = 10 * np.log10(config['antenna_elements'])
        rx_power = self.power - path_loss + beamforming_gain
        snr = max(0, rx_power + 30)
        spectral_efficiency = min(12, np.log2(1 + 10**(snr/10)))
        data_rate = config['bandwidth'] * spectral_efficiency
        
        return {
            'path_loss': path_loss,
            'beamforming_gain': beamforming_gain,
            'rx_power': rx_power,
            'snr': snr,
            'spectral_efficiency': spectral_efficiency,
            'data_rate': data_rate
        }
    
    def draw_beam_simple(self):
        if self.beam_wedge:
            self.beam_wedge.remove()
        color = {'5G': 'green', '5G Advanced': 'blue', '6G': 'purple'}[self.current_tech]
        start_angle = self.beam_angle - self.beam_width/2 + 90
        end_angle = self.beam_angle + self.beam_width/2 + 90
        self.beam_wedge = Wedge((5, 0), self.distance, start_angle, end_angle,
                               facecolor=color, alpha=0.3, edgecolor=color)
        self.ax_beam.add_patch(self.beam_wedge)
        ue_x = self.distance * np.cos(np.radians(self.beam_angle + 90))
        ue_y = self.distance * np.sin(np.radians(self.beam_angle + 90))
        self.user_marker.set_data([ue_x + 5], [ue_y])
        max_range = max(300, self.distance * 1.2)
        self.ax_beam.set_xlim(-max_range + 5, max_range + 5)
        self.ax_beam.set_ylim(-50, max_range)
        
    def update_metrics_display(self):
        self.ax_metrics.clear()
        self.ax_metrics.axis('off')
        config = self.configs[self.current_tech]
        metrics = self.calculate_metrics()
        metrics_text = f"""
TECNOLOGÍA: {self.current_tech}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIGURACIÓN:
• Frecuencia: {self.frequency:.1f} GHz    • Potencia Tx: {self.power} dBm    • Distancia: {self.distance} m
• Ancho de banda: {config['bandwidth']} MHz    • Modulación: {config['modulation']}    • Elementos: {config['antenna_elements']}

ANÁLISIS DE ENLACE:
• Pérdida de trayectoria: {metrics['path_loss']:.1f} dB    • Ganancia Beamforming: {metrics['beamforming_gain']:.1f} dB
• Potencia recibida: {metrics['rx_power']:.1f} dBm    • Tasa de datos: {metrics['data_rate']:.0f} Mbps
• Estado: {'✓ EXCELENTE' if metrics['rx_power'] > -70 else '⚠ BUENO' if metrics['rx_power'] > -85 else '✗ DÉBIL'}
"""
        self.ax_metrics.text(0.05, 0.5, metrics_text, 
                           transform=self.ax_metrics.transAxes,
                           fontfamily='monospace', fontsize=9,
                           va='center')
        
    def update_control_panel(self):
        self.ax_control.clear()
        self.ax_control.axis('off')
        config = self.configs[self.current_tech]
        info_text = f"""
PATRÓN DE RADIACIÓN

Tecnología: {self.current_tech}
━━━━━━━━━━━━━━━━━

Ángulo: {self.beam_angle}°
Ancho: {self.beam_width}°

Rango de frecuencia:
{config['freq_range'][0]}-{config['freq_range'][1]} GHz

Características:
• Latencia: {'<1ms' if self.current_tech == '6G' else '<5ms' if self.current_tech == '5G Advanced' else '<10ms'}
• MIMO: {config['antenna_elements']} antenas
"""
        self.ax_control.text(0.1, 0.5, info_text,
                           transform=self.ax_control.transAxes,
                           fontsize=9, fontfamily='monospace',
                           va='center')
    
    def transmit_signal(self, event):
        original_title = self.ax_beam.get_title()
        self.ax_beam.set_title('⚡ TRANSMITIENDO...', color='red')
        plt.pause(0.3)
        self.ax_beam.set_title('✓ SEÑAL RECIBIDA', color='green')
        plt.pause(0.3)
        self.ax_beam.set_title(original_title, color='black')
        
    def change_technology(self, label):
        self.current_tech = label
        config = self.configs[label]
        freq_min, freq_max = config['freq_range']
        self.slider_freq.valmin = freq_min
        self.slider_freq.valmax = freq_max
        self.slider_freq.set_val(freq_min)
        self.slider_power.valmax = config['max_power']
        self.slider_dist.valmax = config['max_distance']
        self.update_display()
        
    def update_parameters(self, val):
        if not self.updating:
            self.updating = True
            self.frequency = self.slider_freq.val
            self.power = self.slider_power.val
            self.distance = self.slider_dist.val
            self.beam_angle = self.slider_angle.val
            self.update_display()
            self.updating = False
        
    def update_display(self):
        self.draw_beam_simple()
        self.update_metrics_display()
        self.update_control_panel()
        self.fig.canvas.draw_idle()
        
    def show_detailed_analysis(self, event):
        """Abre una segunda ventana con fórmulas en LaTeX y análisis visual"""
        metrics = self.calculate_metrics()
        config = self.configs[self.current_tech]

        fig2 = plt.figure(figsize=(9, 9), facecolor="#f9f9f9")
        fig2.suptitle(f"📊 Análisis Detallado - {self.current_tech}",
                      fontsize=16, fontweight='bold', color="navy")

        # Estado del enlace
        if metrics['rx_power'] > -70:
            enlace_estado = "✓ EXCELENTE"
            color_estado = "green"
        elif metrics['rx_power'] > -85:
            enlace_estado = "⚠ BUENO"
            color_estado = "orange"
        else:
            enlace_estado = "✗ DÉBIL"
            color_estado = "red"

        if metrics['data_rate'] > 1000:
            capacidad = "Muy alta capacidad (ideal para VR/8K)"
            color_capacidad = "green"
        elif metrics['data_rate'] > 300:
            capacidad = "Capacidad alta (servicios intensivos)"
            color_capacidad = "orange"
        else:
            capacidad = "Capacidad limitada (uso básico)"
            color_capacidad = "red"

        # --- BLOQUE DE FÓRMULAS (arriba) ---
        formulas = (
            r"$\mathbf{1)}\ \mathrm{Pérdida\ de\ trayectoria:}\ "
            r"PL = 32.4 + 20\log_{10}(f\,[MHz]) + 20\log_{10}(d\,[km])$" "\n"
            r"   Donde $f$ = frecuencia y $d$ = distancia." "\n"
            fr"   Resultado: $PL = {metrics['path_loss']:.2f}\ dB$" "\n\n"

            r"$\mathbf{2)}\ \mathrm{Ganancia\ por\ beamforming:}\ "
            r"G_{bf} = 10 \log_{10}(N)$" "\n"
            r"   Donde $N$ = número de antenas." "\n"
            fr"   Resultado: $G_{{bf}} = {metrics['beamforming_gain']:.2f}\ dB$" "\n\n"

            r"$\mathbf{3)}\ \mathrm{Potencia\ recibida:}\ "
            r"P_{rx} = P_{tx} - PL + G_{bf}$" "\n"
            r"   Donde $P_{tx}$ = potencia de transmisión." "\n"
            fr"   Resultado: $P_{{rx}} = {metrics['rx_power']:.2f}\ dBm$" "\n\n"

            r"$\mathbf{4)}\ \mathrm{Relación\ señal/ruido:}\ "
            r"SNR \approx P_{rx} + 30$" "\n"
            r"   (Aproximación considerando el ruido de referencia)." "\n"
            fr"   Resultado: $SNR = {metrics['snr']:.2f}\ dB$" "\n\n"

            r"$\mathbf{5)}\ \mathrm{Eficiencia\ espectral:}\ "
            r"\eta = \log_2(1 + 10^{SNR/10})$" "\n"
            r"   Indica cuántos bits se transmiten por Hz de ancho de banda." "\n"
            fr"   Resultado: $\eta = {metrics['spectral_efficiency']:.2f}\ bps/Hz$" "\n\n"

            r"$\mathbf{6)}\ \mathrm{Tasa\ de\ datos:}\ "
            r"R = BW \cdot \eta$" "\n"
            r"   Donde $BW$ = ancho de banda." "\n"
            fr"   Resultado: $R = {metrics['data_rate']:.2f}\ Mbps$"
        )

        plt.figtext(0.05, 0.90, formulas, ha="left", va="top",
                    fontsize=11, color="black", family="serif")

        # --- BLOQUE DE INTERPRETACIÓN (abajo) ---
        plt.figtext(0.05, 0.35,
                    f"✔ Estado del enlace: {enlace_estado}",
                    ha="left", fontsize=12, fontweight="bold",
                    color=color_estado)

        plt.figtext(0.05, 0.28,
                    f"★ Capacidad: {capacidad}",
                    ha="left", fontsize=12, fontweight="bold",
                    color=color_capacidad)

        conclusion = (
            f"✍ Conclusión:\n"
            f"En {self.current_tech}, a {self.distance} m y {self.frequency:.1f} GHz,\n"
            f"el desempeño depende fuertemente de la frecuencia.\n"
            f"A frecuencias altas la pérdida de trayectoria crece,\n"
            f"pero el beamforming y el ancho de banda "
            f"({config['bandwidth']} MHz) compensan en gran medida."
        )

        plt.figtext(0.05, 0.15, conclusion,
                    ha="left", fontsize=11, color="navy", family="sans-serif")

        plt.show()


    def run(self):
        """Ejecuta el simulador"""
        plt.show()

if __name__ == "__main__":
    simulator = BeamformingSimulator()
    simulator.run()