import React, { Component, useRef, useEffect } from 'react';
import './App.css';
import DownloadModal from './DownloadModal';
import { Button, Modal, Space, Upload, Typography } from 'antd';
const { Title } = Typography;

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
      exportOptionsVisible: false,
      isDownloadModalOpen: false, // 모달 열림/닫힘 상태 추가
    };

    this.videoRef = React.createRef();
    this.canvasRef = React.createRef();
    this.fileInputRef = React.createRef();
    this.logFileInputRef = React.createRef();
    this.canvasRef = React.createRef();
    this.clearCanvas = this.clearCanvas.bind(this);
    this.drawPointsAndLines = this.drawPointsAndLines.bind(this);
  }

  // 모달 열기
  openDownloadModal = () => {
    this.setState({ isDownloadModalOpen: true });
  };

  // 모달 닫기
  closeDownloadModal = () => {
    this.setState({ isDownloadModalOpen: false });
  };

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
      this.setState({ videoPlaying: false }); // 이 부분 추가
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

  toggleExportOptions = () => {
    this.setState(prevState => ({ exportOptionsVisible: !prevState.exportOptionsVisible }));
  };

  saveFrame = async () => {
    const canvas = this.canvasRef.current;
    const video = this.videoRef.current;

    if (canvas && video) {
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      tempCanvas.width = video.videoWidth;
      tempCanvas.height = video.videoHeight;

      // 비디오 프레임 그리기
      tempContext.drawImage(video, 0, 0, video.videoWidth, video.videoHeight, 0, 0, tempCanvas.width, tempCanvas.height);

      // 캔버스에 그려진 내용 그리기
      tempContext.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, tempCanvas.width, tempCanvas.height);

      // 이미지 데이터를 다운로드
      const dataUrl = tempCanvas.toDataURL('image/jpeg');

      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `${this.state.videoFileName}_frame${this.state.frameNumber}.JPG`;
      link.click();
    }
  };

  saveVideo = () => {
    const video = this.videoRef.current;
    const canvas = this.canvasRef.current;

    if (video && canvas) {
      this.openDownloadModal();

      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      tempCanvas.width = video.videoWidth;
      tempCanvas.height = video.videoHeight;

      const stream = tempCanvas.captureStream(33);  // 33fps로 스트림 생성
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
      const recordedChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.state.videoFileName}_with_canvas.webm`;  // 수정된 부분
        link.click();
        URL.revokeObjectURL(url);

        this.closeDownloadModal();
      };

      mediaRecorder.start();

      let frameNumber = 0;
      const drawFrame = () => {
        if (frameNumber < video.duration * 33) {  // 33fps 기준
          video.currentTime = frameNumber / 33;
          video.onseeked = () => {
            tempContext.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            tempContext.drawImage(video, 0, 0, video.videoWidth, video.videoHeight, 0, 0, tempCanvas.width, tempCanvas.height);
            tempContext.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, tempCanvas.width, tempCanvas.height);
            frameNumber++;
            requestAnimationFrame(drawFrame);
          };
        } else {
          mediaRecorder.stop();
        }
      };

      drawFrame();
    }
  };

  // 파일 업로드 핸들러
  handleFileUpload = (file) => {
    if (file) {
      const videoFileName = file.name.split('.')[0];  // 파일 이름 가져오기
      this.setState({ videoSrc: file, videoFileName }, () => {  // videoFileName 상태 추가
        this.loadVideo();
      });
    }
  };

  // 로그 파일 업로드 핸들러
  handleLogFileUpload = (file) => {
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
      // 비디오 재생 시 pointDistances와 points 배열을 비웁니다.
      this.setState(() => {
        return {
          addingInfo: false,
          pointDistances: [],
          points: [],
        };
      }, () => {
        // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
        this.clearCanvas();
        this.drawPointsAndLines();
      });
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
    this.setState((prevState) => {
      // addingInfo 상태를 토글합니다.
      const newAddingInfo = !prevState.addingInfo;

      // addingInfo 상태가 false로 바뀌면 pointDistances와 points 배열을 비웁니다.
      if (!newAddingInfo) {
        return {
          addingInfo: newAddingInfo,
          pointDistances: [],
          points: []
        };
      }

      // addingInfo 상태가 true로 바뀌면 상태를 그대로 유지합니다.
      return { addingInfo: newAddingInfo };
    }, () => {
      // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
      this.clearCanvas();
      this.drawPointsAndLines();
    });
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
    this.setState(() => {
      return {
        addingInfo: false,
        pointDistances: [],
        points: [],
      };
    }, () => {
      // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
      this.clearCanvas();
      this.drawPointsAndLines();
    });
  };

  // >> 10 seconds forward 버튼 클릭 핸들러
  skipForward = () => {
    this.videoRef.current.currentTime += 10;
    this.setState(() => {
      return {
        addingInfo: false,
        pointDistances: [],
        points: [],
      };
    }, () => {
      // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
      this.clearCanvas();
      this.drawPointsAndLines();
    });
  };

  // Run AI Model 버튼 클릭 핸들러
  runAIModel = async () => {
    const { videoSrc } = this.state;
    if (videoSrc) {
      // FormData를 사용하여 파일을 업로드합니다.
      const formData = new FormData();
      formData.append('video_path', videoSrc);

      fetch("http://localhost:8000/run-test", {
        method: "POST",
        body: formData, // FormData를 전송합니다.
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          console.log(data);
          alert("Video path uploaded successfully");

          // 서버에서 받은 결과 데이터에서 동영상 경로 추출
          const newVideoPath = data.result.match(/Embedded Video Local Path: (.+)/)[1];

          // 추출한 경로를 사용하여 비디오를 다시 로드
          this.reLoadVideo(newVideoPath);

          this.setState({ aiModelActive: true });
        })
        .catch((error) => {
          console.error("There was a problem with the fetch operation:", error);
          alert("Failed to upload video path");
        });
    }
  };

  /// 비디오를 미리보기로 보여주는 함수
  reLoadVideo = async (newVideoPath) => {
    // 모달 열기
    this.openDownloadModal();
    // Set the initial state
    this.setState({ videoPlaying: false });

    try {
      // Now, you can replace the video source with the downloaded video URL
      const video = this.videoRef.current;
      if (video) {
        video.src = newVideoPath;
        video.crossOrigin = "anonymous"; // CORS 설정
        video.load();
        video.addEventListener('loadeddata', () => {
          video.currentTime = 0;
          this.setState({ videoPlaying: false });
        });

        this.closeDownloadModal();
      }
    } catch (error) {
      console.error('Error downloading and saving video:', error);
      this.closeDownloadModal();
    }
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

    const { points, pointColors, addingInfo, pointDistances } = this.state;

    context.clearRect(0, 0, canvas.width, canvas.height); // 캔버스 지우기

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
        context.fillStyle = 'white'; // 배경색을 흰색으로 설정
        context.fillRect(
          (points[i - 1].x + points[i].x) / 2 - 50,
          (points[i - 1].y + points[i].y) / 2 - 20,
          100,
          40
        );

        context.fillStyle = 'black'; // 글씨색을 검정색으로 설정
        context.font = "20px Arial";
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        // 선의 중간에 라벨을 추가합니다.
        const labelText = pointDistances[(i - 1) / 2]
          ? `line${(i + 1) / 2} = ${pointDistances[(i - 1) / 2].meters}(m)`
          : `line${(i + 1) / 2}`;

        context.fillText(labelText, (points[i - 1].x + points[i].x) / 2, (points[i - 1].y + points[i].y) / 2);
      }
    }
  }

  // 렌더링
  render() {
    // 화면 높이 구하기
    const screenHeight = window.innerHeight;
    const screenWidth = window.innerWidth;
    // 비디오 스타일 정의
    const videoStyle = {
      width: '100%',
      height: '80%',
      position: 'relative',
      zIndex: 0
    };

    const buttonHeightSize = screenHeight / 40;  // 버튼 크기를 화면 크기에 따라 조절합니다.
    const buttonWidthSize = screenWidth / 10;  // 버튼 크기를 화면 크기에 따라 조절합니다.
    const buttonSize = Math.min(screenHeight, screenWidth) / 10;

    const { videoPlaying, frameNumber, addingInfo, pointColors, pointDistances, allFillUpload, aiModelActive } = this.state;

    return (
      <div className="App" style={{ height: screenHeight + 'px', position: 'relative' }}>
        <Space direction="vertical" style={{ marginTop: '40px', marginLeft: '20px' }}>
          <Title level={1}>Drone Video Analysis for MARC</Title>
          <div style={{ position: 'relative' }}>
            <video
              ref={this.videoRef}
              onTimeUpdate={this.updateFrameNumber}
              onClick={this.handleVideoClick}
              style={videoStyle}
            />
            {this.state.addingInfo && this.videoRef.current && (
              <canvas
                ref={this.canvasRef}
                style={{ position: 'absolute', top: '0', left: '0', zIndex: 1, width: '100%', height: '100%' }}
                onClick={this.handleVideoClick}
              />
            )}
          </div>
          <Space>
            {this.videoRef.current && this.canvasRef.current && (
              <>
                <Button type="primary" onClick={this.saveFrame}>Save Frame</Button>
                <Button type="primary" onClick={this.saveVideo}>Save Video</Button>
              </>
            )}
          </Space>
          <div style={{ fontSize: 30 + 'px' }}>
            <p >Frame: {frameNumber}</p>
          </div>
          <Space direction="vertical">
            <Space>
              <Upload
                showUploadList={false}
                accept=".mp4,.mov"
                customRequest={({ file }) => this.handleFileUpload(file)}
              >
                <Button>Upload Video</Button>
              </Upload>
              <Upload
                showUploadList={false}
                accept=".csv"
                customRequest={({ file }) => this.handleLogFileUpload(file)}
              >
                <Button>Upload Log File</Button>
              </Upload>
              {allFillUpload && <Button onClick={this.runAIModel}>Run AI Model</Button>}
            </Space>
            {aiModelActive && (
              <Space>
                <Button onClick={this.skipBackward}>{"<< 10 seconds backward"}</Button>
                <Button onClick={this.togglePlayPause}>{videoPlaying ? 'Pause' : 'Play'}</Button>
                <Button onClick={this.skipForward}>{">> 10 seconds forward"}</Button>
              </Space>
            )}
            {aiModelActive && (
              <Button onClick={this.toggleAddingInfo}>{addingInfo ? 'Disable Adding Info' : 'Enable Adding Info'}</Button>
            )}
          </Space>
          <div>
            {this.state.pointDistances.map((distance, index) => (
              <p key={index}>Distance {index + 1}: {distance.meters} meters ({distance.pixels.toFixed(3)} pixels)</p>
            ))}
          </div>
          <Modal
            open={this.state.isDownloadModalOpen}
            onCancel={this.closeDownloadModal}
            title="Download Modal"
          >
          </Modal>
        </Space>
      </div>
    );

  }
}

export default App;
