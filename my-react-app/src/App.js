import React, { Component, useRef, useEffect } from 'react';
import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      videoSrc: null,
      logFile: null,
      videoPlaying: false,
      frameNumber: 0,
      addingInfo: false,
      points: [],
      pointColors: [],
      pointDistances: [],
      distanceInputs: [],
      allFillUpload: false,
      aiModelActive: false,
    };

    this.videoRef = React.createRef();
    this.fileInputRef = React.createRef();
    this.logFileInputRef = React.createRef();
    this.canvasRef = React.createRef();
    this.clearCanvas = this.clearCanvas.bind(this);
    this.drawPointsAndLines = this.drawPointsAndLines.bind(this);
  }

  componentDidUpdate(prevProps, prevState) {
    const video = this.videoRef.current;
    const canvas = this.canvasRef.current;

    if (canvas && video) {
      if (!this.context) {
        this.context = canvas.getContext('2d');
        video.addEventListener('loadeddata', this.handleVideoLoaded);
      }
      canvas.width = video.offsetWidth;
      canvas.height = video.offsetHeight;
    } else {
      console.error("Canvas or Video element is not available.");
    }
  }

  handleVideoLoaded = () => {
    const video = this.videoRef.current;
    const canvas = this.canvasRef.current;
    if (canvas && video) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      this.drawInterval = setInterval(this.drawPointsAndLines, 100);
    }
  };

  // clearCanvas 함수 수정
  clearCanvas() {
    const canvas = this.canvasRef.current;

    if (canvas) {
      const context = canvas.getContext('2d');
      if (context) {
        context.clearRect(0, 0, canvas.width, canvas.height);
      } else {
        console.error("Canvas context is not available.");
      }
    } else {
      console.error("Canvas element is not available.");
    }
  }

  // 비디오 파일 로드
  loadVideo = () => {
    const { videoSrc } = this.state;
    if (videoSrc) {
      this.videoRef.current.src = URL.createObjectURL(videoSrc);
      this.videoRef.current.load();
      this.videoRef.current.addEventListener('loadeddata', () => {
        this.videoRef.current.currentTime = 0;
        this.setState({ videoPlaying: false });
      });
    }
  };


  // 파일 업로드 핸들러
  handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      this.setState({ videoSrc: file }, () => {
        this.loadVideo();
      });
    }
  };

  // 로그 파일 업로드 핸들러
  handleLogFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      this.setState({ logFile: file });
      this.setState({ allFillUpload: true });
    }
  };

  // 비디오 재생/일시정지 토글
  togglePlayPause = () => {
    const { videoPlaying } = this.state;
    if (videoPlaying) {
      this.videoRef.current.pause();
    } else {
      this.videoRef.current.play();
    }
    this.setState({ videoPlaying: !videoPlaying });
  };

  // 현재 프레임 번호 업데이트
  updateFrameNumber = () => {
    const { videoSrc } = this.state;
    if (videoSrc) {
      this.setState({ frameNumber: Math.floor(this.videoRef.current.currentTime * 30) }); // 30fps 기준
    }
  };

  // 추가 정보 입력 모드 활성화/비활성화 토글
  toggleAddingInfo = () => {
    this.setState((prevState) => ({ addingInfo: !prevState.addingInfo }));
  };

  // handleVideoClick 함수 수정
  handleVideoClick = (e) => {
    if (this.state.addingInfo) {
      const rect = this.canvasRef.current.getBoundingClientRect();
      const { clientX, clientY } = e.nativeEvent;
      const x = clientX - rect.left;
      const y = clientY - rect.top;

      this.setState((prevState) => {
        const points = [...prevState.points, { x, y }];
        const pointColors = [...prevState.pointColors, `rgb(${Math.random() * 255},${Math.random() * 255},${Math.random() * 255})`];

        return { points, pointColors };
      }, () => {
        // Check if there are even points and more than 1 point
        if (this.state.points.length % 2 === 0 && this.state.points.length > 1) {
          const lastPointIndex = this.state.points.length - 1;
          // Calculate the distance for the last two points
          this.calculateDistance(lastPointIndex); // Calculate distance for the previous pair of points
        }

        // Draw points and lines after adding the second point
        this.drawPointsAndLines();
      });
    }
  };

  // calculateDistance 함수 수정
  calculateDistance = (pointIndex) => {
    const { points } = this.state;
    console.log(points);
    const point1 = points[pointIndex - 1];
    const point2 = points[pointIndex];

    const distancePixels = Math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2);

    // Prompt for distance input after drawing points and lines
    setTimeout(() => {
      const distanceMeters = parseFloat(prompt(`Enter distance between point ${pointIndex - 1} and point ${pointIndex} in meters:`));
      if (!isNaN(distanceMeters)) {
        const pointDistances = [...this.state.pointDistances, { meters: distanceMeters, pixels: distancePixels }];
        this.setState({ pointDistances }, () => {
          // 상태 업데이트 후에 점과 선을 다시 그립니다.
          this.drawPointsAndLines();
        });
      } else {
        alert('Invalid input. Please enter a valid number for the distance.');
      }
    }, 0);
  };

  // << 10 seconds backward 버튼 클릭 핸들러
  skipBackward = () => {
    this.videoRef.current.currentTime -= 10;
  };

  // >> 10 seconds forward 버튼 클릭 핸들러
  skipForward = () => {
    this.videoRef.current.currentTime += 10;
  };

  // AI 모델 실행 핸들러
  runAIModel = () => {
    // AI 모델 실행 로직 추가
    setTimeout(() => {
      // AI 모델 실행 후, << 10 seconds backward, play(pause), >> 10 seconds forward 버튼 활성화
      this.setState({ aiModelActive: true });
    }, 1000);
  };

  // 점과 선 그리기 함수
  drawPointsAndLines() {
    const canvas = this.canvasRef.current;
    if (!canvas) {
      console.error("Canvas element is not available.");
      return;
    }

    const context = canvas.getContext('2d');
    if (!context) {
      console.error("Canvas context is not available.");
      return;
    }

    const { points, pointColors, addingInfo } = this.state;

    for (let i = 0; i < points.length; i++) {
      // 현재 점의 색상을 설정합니다.
      context.fillStyle = pointColors[i % 2 === 0 ? i : i - 1];
      context.beginPath();
      context.arc(points[i].x, points[i].y, 10, 0, Math.PI * 2);
      context.fill();

      // 짝수 인덱스일 때 선을 그립니다.
      if (i % 2 === 1 && i > 0) {
        // 이전 점의 색상을 사용하여 선의 색상을 설정합니다.
        context.strokeStyle = pointColors[i - 1];
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(points[i - 1].x, points[i - 1].y);
        context.lineTo(points[i].x, points[i].y);
        context.stroke();

        // 선에 텍스트를 추가합니다.
        // 이전 점의 색상을 사용하여 텍스트의 색상을 설정합니다.
        context.fillStyle = pointColors[i - 1];
        context.font = "20px Arial";
        // 선의 중간에 라벨을 추가합니다.
        context.fillText(`line${(i + 1) / 2}`, (points[i - 1].x + points[i].x) / 2, (points[i - 1].y + points[i].y) / 2 - 10);
      }
    }
  }

  // 렌더링
  render() {
    // 화면 높이 구하기
    const screenHeight = window.innerHeight;

    // 비디오 스타일 정의
    const videoStyle = {
      width: '100%', // 부모 요소에 맞게 너비 조절
      height: '80%', // 부모 요소에 맞게 높이 조절
      position: 'relative',  // 이 줄을 추가하세요
      zIndex: 0  // 이 줄을 추가하세요
    };
    const { videoPlaying, frameNumber, addingInfo, pointColors, pointDistances, allFillUpload, aiModelActive } = this.state;

    return (
      <div className="App" style={{ height: screenHeight + 'px' }}>
        <h1>Video Player</h1>
        <video
          ref={this.videoRef}
          onTimeUpdate={this.updateFrameNumber}
          onClick={this.handleVideoClick}
          style={videoStyle}
        />
        <div>
          <p>Frame: {frameNumber}</p>
        </div>
        <div>
          <input type="file" accept=".mp4,.mov" ref={this.fileInputRef} style={{ display: 'none' }} onChange={this.handleFileUpload} />
          <input type="file" accept=".csv" ref={this.logFileInputRef} style={{ display: 'none' }} onChange={this.handleLogFileUpload} />
          <button onClick={() => this.fileInputRef.current.click()}>Upload Video</button>
          <button onClick={() => this.logFileInputRef.current.click()}>Upload Log File</button>
          {allFillUpload && (
            <button onClick={this.runAIModel}>Run AI Model</button>
          )}
          <div>
            {aiModelActive && (
              <>
                <button onClick={this.skipBackward}>{"<< 10 seconds backward"}</button>
                <button onClick={this.togglePlayPause}>{videoPlaying ? 'Pause' : 'Play'}</button>
                <button onClick={this.skipForward}>{">> 10 seconds forward"}</button>
              </>
            )}
          </div>
          <div>
            {aiModelActive && (
              <>
                <button onClick={this.toggleAddingInfo}>{addingInfo ? 'Disable Adding Info' : 'Enable Adding Info'}</button>
              </>
            )}
          </div>
        </div>
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '80%' }}>
          {this.state.addingInfo && this.videoRef.current && (
            <canvas
              ref={this.canvasRef}
              style={{ position: 'absolute', top: '0', left: '0', zIndex: 1, width: '100%', height: '100%' }}
              onClick={this.handleVideoClick}
            />
          )}
        </div>
        <div>
          {pointDistances.map((distance, index) => (
            <p key={index}>Distance {index + 1}: {distance.meters} meters ({distance.pixels.toFixed(3)} pixels)</p>
          ))}
        </div>

      </div>
    );
  }
}

export default App;
