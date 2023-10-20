import React, { Component } from 'react';
import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      videoSrc: null,             // 비디오 파일 Blob 객체
      videoPlaying: false,        // 비디오 재생 상태
      frameNumber: 0,             // 현재 프레임 번호
      addingInfo: false,          // 추가 정보 입력 모드 활성화 여부
      points: [],                 // 입력한 점 좌표
      pointColors: [],            // 입력한 점 색상
      pointDistances: [],         // 입력한 점 사이의 거리
      distanceInputs: [],         // 입력한 거리 값
    };

    this.videoRef = React.createRef();
    this.fileInputRef = React.createRef();
  }

  // 비디오 파일 로드
  loadVideo = () => {
    const { videoSrc } = this.state;

    if (videoSrc) {
      this.videoRef.current.src = URL.createObjectURL(videoSrc);
      this.videoRef.current.load();
      this.videoRef.current.addEventListener('loadeddata', () => {
        // 비디오 데이터 로드 후 1번째 프레임으로 이동
        this.videoRef.current.currentTime = 0;
        this.setState({ videoPlaying: false });

        // 비디오 크기 조절
        this.videoRef.current.width = window.innerWidth; // 화면 너비에 맞게 조절
        this.videoRef.current.height = window.innerHeight; // 화면 높이에 맞게 조절
      });
      this.videoRef.current.addEventListener('timeupdate', this.updateFrameNumber);
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
    this.setState({ frameNumber: Math.floor(this.videoRef.current.currentTime * 30) }); // 30fps 기준
  };

  // 추가 정보 입력 모드 활성화/비활성화 토글
  toggleAddingInfo = () => {
    this.setState((prevState) => ({ addingInfo: !prevState.addingInfo }));
  };

  // 비디오 클릭 시 점 추가
  handleVideoClick = (e) => {
    if (this.state.addingInfo) {
      const { clientX, clientY } = e;
      const rect = this.videoRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const y = clientY - rect.top;
      const points = [...this.state.points, { x, y }];
      const pointColors = [...this.state.pointColors, `rgb(${Math.random() * 255},${Math.random() * 255},${Math.random() * 255})`];
      this.setState({ points, pointColors }, () => {
        if (points.length % 2 === 0) {
          // 두 점을 클릭한 경우
          this.calculateDistance(points.length - 2);
        }
      });
    }
  };

  // 두 점 사이의 거리 계산
  calculateDistance = (pointIndex) => {
    const { points } = this.state;
    const point1 = points[pointIndex];
    const point2 = points[pointIndex + 1];
    const distancePixels = Math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2);
    const distanceMeters = parseFloat(prompt(`Enter distance between point ${pointIndex / 2 + 1} and point ${pointIndex / 2 + 2} in meters:`));
    if (!isNaN(distanceMeters)) {
      const pointDistances = [...this.state.pointDistances, { meters: distanceMeters, pixels: distancePixels }];
      this.setState({ pointDistances });
    } else {
      alert('Invalid input. Please enter a valid number for the distance.');
    }
  };

  // 렌더링
  render() {
    // 화면 높이 구하기
    const screenHeight = window.innerHeight;

    // 비디오 스타일 정의
    const videoStyle = {
      width: '100%', // 부모 요소에 맞게 너비 조절
      height: '80%', // 부모 요소에 맞게 높이 조절
    };
    const { videoPlaying, frameNumber, addingInfo, pointColors, pointDistances } = this.state;

    return (
      <div className="App" style={{ height: screenHeight + 'px' }}> {/* 부모 요소인 div의 높이를 화면 높이로 조절 */}
        <h1>Video Player</h1>
        <video
          ref={this.videoRef}
          onClick={this.handleVideoClick}
          style={videoStyle} // 비디오 스타일 적용
        />
        <div>
          <p>Frame: {frameNumber}</p>
        </div>
        <div>
          <input type="file" accept=".mp4,.mov" ref={this.fileInputRef} style={{ display: 'none' }} onChange={this.handleFileUpload} />
          <button onClick={() => this.fileInputRef.current.click()}>Upload Video</button>
          <button onClick={this.togglePlayPause}>{videoPlaying ? 'Pause' : 'Play'}</button>
          <button onClick={this.toggleAddingInfo}>{addingInfo ? 'Disable Adding Info' : 'Enable Adding Info'}</button>
        </div>
        <div>
          {pointDistances.map((distance, index) => (
            <p key={index}>Distance {index + 1}: {distance.meters} meters ({distance.pixels} pixels)</p>
          ))}
        </div>
      </div>
    );
  }
}

export default App;
