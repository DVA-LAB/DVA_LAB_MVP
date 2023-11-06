from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QLineEdit, QMessageBox, QFormLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QEvent, QUrl
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QDoubleValidator
import sys
import cv2
import random
import csv  # 추가: CSV 파일을 처리하기 위한 모듈

class VideoPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)

        # 프레임 라벨 구분선 추가
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(self.line)

        button_row_layout = QHBoxLayout()

        self.load_video_button = QPushButton("Load Video")
        button_row_layout.addWidget(self.load_video_button)
        self.load_video_button.clicked.connect(self.load_video)

        self.load_log_button = QPushButton("Load Log File")
        button_row_layout.addWidget(self.load_log_button)
        self.load_log_button.clicked.connect(self.upload_log_file)

        self.run_ai_model_button = QPushButton("Run AI Model")
        button_row_layout.addWidget(self.run_ai_model_button)
        self.run_ai_model_button.clicked.connect(self.run_ai_models)
        self.run_ai_model_button.hide()

        self.layout.addLayout(button_row_layout)

        self.add_info_button = QPushButton("Add Information")
        self.layout.addWidget(self.add_info_button)
        self.add_info_button.clicked.connect(self.add_information)
        self.add_info_button.hide()

        # 프레임 라벨 구분선 추가
        self.layout.addWidget(self.line)

        self.controls_layout = QHBoxLayout()
        self.skip_backward_button = QPushButton("<< 10s backward")
        self.controls_layout.addWidget(self.skip_backward_button)
        self.skip_backward_button.clicked.connect(self.skip_backward)
        self.skip_backward_button.hide()

        self.play_pause_button = QPushButton("Play")
        self.controls_layout.addWidget(self.play_pause_button)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.hide()

        self.skip_forward_button = QPushButton("10s forward >>")
        self.controls_layout.addWidget(self.skip_forward_button)
        self.skip_forward_button.clicked.connect(self.skip_forward)
        self.skip_forward_button.hide()

        self.layout.addLayout(self.controls_layout)

        # 추가 정보 입력을 위한 폼 레이아웃
        self.form_layout = QFormLayout()
        self.distance_text_fields = []

        self.add_info_button = QPushButton("Add Information")
        self.add_info_button.clicked.connect(self.add_information)
        self.layout.addWidget(self.add_info_button)
        self.add_info_button.hide()

        # Done 버튼 추가
        self.done_button = QPushButton("Done")
        self.done_button.clicked.connect(self.calculate_distances)
        self.done_button.hide()
        self.layout.addWidget(self.done_button)

        # 비디오 관련 변수
        self.video_capture = cv2.VideoCapture()
        self.playing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_frame)
        self.frame = None

        # 추가 정보 입력 모드 관련 변수
        self.adding_info = False
        self.points = []
        self.point_colors = []
        self.point_text_fields = []
        self.point_distances = []
        self.distance_line_edits = []
        self.log_data = None
        self.info_dialog_shown = False
        self.mouse_pressed = False

        # distance_layout 변수 추가
        self.distance_layout = None

    def toggle_play_pause(self):
        if not self.playing:
            self.play_video()
            self.play_pause_button.setText("Pause")
        else:
            self.pause_video()
            self.play_pause_button.setText("Play")

    def play_video(self):
        self.playing = True
        self.timer.start(33)

    def pause_video(self):
        self.playing = False
        self.timer.stop()

    def read_frame(self):
        _, self.frame = self.video_capture.read()
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        
        # 고정된 크기로 QImage 및 QPixmap 생성
        fixed_width = self.video_label.width()
        fixed_height = self.video_label.height()
        q_image = QImage(frame.data, w, h, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image).scaled(fixed_width, fixed_height, Qt.AspectRatioMode.KeepAspectRatio)

        self.video_label.setPixmap(pixmap)

        pixmap = self.video_label.pixmap()
        painter = QPainter(pixmap)
        
        # 프레임 번호 텍스트 추가
        frame_number_text = f"Frame: {int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))}"
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(10, 20, frame_number_text)

        painter.end()
        self.video_label.setPixmap(pixmap)

    def draw_frame(self):
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

        pixmap = self.video_label.pixmap()
        painter = QPainter(pixmap)

        if self.adding_info:
            for i, point in enumerate(self.points):
                color = self.point_colors[i // 2]
                pen = QPen(color)
                pen.setWidth(16)
                painter.setPen(pen)
                painter.drawPoint(point)

            # 두 번째 점 셋트를 기다리지 않고 바로 라인을 그림
            for j in range(0, len(self.points), 2):
                if j + 1 < len(self.points):
                    point1 = self.points[j]
                    point2 = self.points[j + 1]
                    line_color = self.point_colors[j// 2]
                    line_pen = QPen(line_color)
                    line_pen.setWidth(2)
                    painter.setPen(line_pen)
                    painter.drawLine(point1, point2)
                    pair_index = j // 2 + 1
                    point_text = f"Point {pair_index}"
                    painter.drawText(point1.x(), point1.y() - 10, point_text)

        # 프레임 번호 텍스트 추가
        frame_number_text = f"Frame: {int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))}"
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(10, 20, frame_number_text)

        painter.end()
        self.video_label.setPixmap(pixmap)

    def run_ai_models(self):
        # Call AI API function
        # 10초 후에 버튼 비활성화
        timer = QTimer()
        timer.singleShot(1000, self.after_timer)

    def after_timer(self):
        self.run_ai_model_button.setEnabled(False)
        self.play_pause_button.setText("Play")
        self.play_pause_button.show()
        self.skip_forward_button.show()
        self.skip_backward_button.show()
        self.add_info_button.show()

    def load_video(self):
        file_info = QFileDialog.getOpenFileUrl(self, "Open Video File", QUrl(""), "Video Files (*.mp4 *.avi *.mov);;All Files (*)")
        if file_info[1]:
            file_path = file_info[0].toLocalFile()
            self.video_capture.open(file_path)
            self.read_frame()
            self.run_ai_model_button.show()
    
    def upload_log_file(self):
        file_info, _ = QFileDialog.getOpenFileName(self, "Upload Log File", "", "CSV Files (*.csv);;All Files (*)")
        
        if file_info:
            with open(file_info, "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                self.log_data = list(csv_reader)
                print(self.log_data[:10])
            # self.upload_log_button.hide()  # 파일 업로드 후 버튼 숨김
            # self.load_video_button.show()  # 로그 파일이 업로드되면 비디오 로드 버튼 표시

    def skip_forward(self):
        current_frame = self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        target_frame = current_frame + 10 * fps
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self.read_frame()  # 프레임 이동 후 UI 업데이트

    def skip_backward(self):
        current_frame = self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        target_frame = current_frame - 10 * fps
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self.read_frame()  # 프레임 이동 후 UI 업데이트

    def eventFilter(self, obj, event):
        if obj is self.video_label and self.adding_info and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                point = event.position().toPoint()  # 수정: localPos() -> position()
                self.points.append(point)
                color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                self.point_colors.append(color)
                if len(self.points) % 2 == 0:
                    self.draw_frame()
                    self.create_distance_text_fields()
        return super().eventFilter(obj, event)


    def add_information(self):
        # 마우스 클릭 이벤트 활성화 유지
        self.adding_info = True
        if self.adding_info and not self.info_dialog_shown:
            self.video_label.installEventFilter(self)
            self.adding_info = True
            self.point_colors = []  # 이 부분 추가 (점 색상도 초기화)
            self.draw_frame()
            self.show_info_dialog()
            self.info_dialog_shown = True
        self.add_info_button.setDisabled(True)  # 버튼을 비활성화


    def show_info_dialog(self):
        message_box = QMessageBox()
        message_box.setText("Click two points on the video to add information.")
        message_box.setWindowTitle("Add Information")
        message_box.exec()

    def create_distance_text_fields(self):
        # 이전 텍스트 필드 및 레이블 제거
        self.distance_layout = None
        self.point_text_fields = []  # 이전 텍스트 필드 초기화

        # 이전 distance_container_widget을 삭제
        if hasattr(self, 'distance_container_widget') and self.distance_container_widget:
            self.distance_container_widget.deleteLater()
            self.distance_container_widget = None
            
        self.distance_container_widget = QWidget(self)
        self.distance_layout = QFormLayout(self.distance_container_widget)
        self.layout.addWidget(self.distance_container_widget)  # 레이아웃에 추가

        # 추가해야 할 텍스트 필드 인덱스 계산
        start_index = 0
        end_index = len(self.points) // 2

        for i in range(start_index, end_index):
            text_field = QLineEdit(self)
            validator = QDoubleValidator()
            text_field.setValidator(validator)
            self.distance_layout.addRow(f"Distance {i + 1} (m):", text_field)
            self.point_text_fields.append(text_field)
            text_field.textChanged.connect(self.check_text_fields)  # 텍스트 변경 이벤트 연결

        self.done_button.show()

    def check_text_fields(self):
        all_filled = all(text_field.hasAcceptableInput() for text_field in self.point_text_fields)
        self.done_button.setEnabled(all_filled)  # 모든 텍스트 필드에 숫자가 있을 때만 Done 버튼 활성화
    
    def calculate_distances(self):
        self.add_info_button.setEnabled(True)
        distances_meters = []
        distances_pixels = []

        for i in range(1, len(self.points) // 2 + 1):
            text_field = self.point_text_fields[i - 1]
            distance_meters = float(text_field.text())  # 텍스트를 부동 소수점으로 변환
            point1 = self.points[2 * i - 2]
            point2 = self.points[2 * i - 1]
            distance_x = abs(point2.x() - point1.x())
            distance_y = abs(point2.y() - point1.y())
            distance_pixels = (distance_x ** 2 + distance_y ** 2) ** 0.5
            distances_meters.append(distance_meters)
            distances_pixels.append(distance_pixels)

        if len(self.points) % 2 != 0:
            error_message = QMessageBox()
            error_message.setText("The number of points should be even.")
            error_message.setWindowTitle("Error")
            error_message.exec()
            return

        # 두 점 간의 거리(m)와 픽셀 수 출력
        for i in range(0, len(self.points), 2):
            if i + 1 < len(self.points):
                point1_index = i // 2 + 1
                print(f"Point {point1_index}:")
                print(f"Distance (meters): {distances_meters[i // 2]}")
                print(f"Pixel distance: {distances_pixels[i // 2]} pixels")
                print()

        # self.points 초기화
        self.points = []
        self.point_colors = []
        self.point_text_fields = []

        # Distance 텍스트 필드와 레이블을 모두 제거
        if hasattr(self, 'distance_layout') and self.distance_layout is not None:
            while self.distance_layout.rowCount() > 0:
                self.distance_layout.removeRow(0)

        # 이전 distance_container_widget을 삭제
        if hasattr(self, 'distance_container_widget') and self.distance_container_widget:
            self.distance_container_widget.deleteLater()
            self.distance_container_widget = None

        self.done_button.setEnabled(False)  # Done 버튼을 다시 비활성화
        self.draw_frame()

        # 마우스 클릭 이벤트 활성화 유지
        self.adding_info = False

if __name__ == "__main__":
    app = QApplication([])
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec())